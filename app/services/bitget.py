import httpx, pandas as pd, datetime as dt
from fastapi_cache import FastAPICache
from ..core.errors import BAD_ARGUMENT, UPSTREAM
from ..core.settings import settings

BASE = "https://api.bitget.com/api/v2"
ALLOWED = {"1min","3min","5min","15min","30min","1h","2h","4h","6h","12h",
           "1day","3day","1week","1M"}

def _normalize(g: str) -> str:
    g = g.lower()
    if g.endswith("m") and not g.endswith("min"): g = g.replace("m", "min")
    if g not in ALLOWED:
        raise BAD_ARGUMENT("granularity unsupported")
    return g

def _ms(t: dt.datetime) -> int:
    return int(t.replace(tzinfo=dt.timezone.utc).timestamp()*1000)

async def _get(path: str, params: dict, ttl: int = 15):
    key = f"bg:{path}:{params}"
    
    # Try to get from cache if enabled and initialized
    cached = None
    if settings.CACHE_ENABLED:
        try:
            if hasattr(FastAPICache, '_backend') and FastAPICache._backend:
                cached = await FastAPICache.get(key)  # type: ignore
        except Exception:
            pass  # Cache not initialized or other cache error
    
    if cached:
        return cached
    
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{BASE}{path}", params=params)
        if r.status_code >= 400:
            raise UPSTREAM(f"Bitget API error: {r.status_code} - {r.text}")
        data = r.json()
        if "data" not in data:
            raise UPSTREAM(f"Unexpected Bitget API response format: {data}")
        result = data["data"]
        
        # Try to cache if enabled and initialized
        if settings.CACHE_ENABLED:
            try:
                if hasattr(FastAPICache, '_backend') and FastAPICache._backend:
                    await FastAPICache.set(key, result, expire=ttl)  # type: ignore
            except Exception:
                pass  # Cache not initialized or other cache error
            
        return result
    except httpx.RequestError as e:
        raise UPSTREAM(f"Bitget API request failed: {str(e)}")
    except Exception as e:
        raise UPSTREAM(f"Bitget API error: {str(e)}")

async def candles(symbol: str, granularity="1h", limit=200,
                  product_type: str | None = None, start=None, end=None):
    granularity = _normalize(granularity)
    path = "/mix/market/candles" if product_type else "/spot/market/candles"
    p = {"symbol": symbol, "granularity": granularity, "limit": limit}
    if product_type:
        p["productType"] = product_type
    if start:
        p["startTime"] = int(start) if start.isdigit() else _ms(dt.datetime.fromisoformat(start))
    if end:
        p["endTime"] = int(end) if end.isdigit() else _ms(dt.datetime.fromisoformat(end))
    raw = await _get(path, p)
    cols = ["ts","open","high","low","close","vol_base","vol_quote","vol_usdt"]
    df = (pd.DataFrame(raw, columns=cols)
          .astype({"open": float, "high": float, "low": float, "close": float, "vol_base": float, "vol_quote": float, "vol_usdt": float})
          .assign(ts=lambda d: pd.to_datetime(pd.to_numeric(d.ts, errors='coerce'), unit="ms", utc=True))
          .sort_values("ts")
          .reset_index(drop=True))
    return df

async def orderbook(symbol: str, limit=5):
    raw = await _get("/spot/market/merge-depth", {"symbol": symbol, "limit": limit})
    bids = [(float(p), float(q)) for p, q in raw["bids"]]
    asks = [(float(p), float(q)) for p, q in raw["asks"]]
    spread = asks[0][0] - bids[0][0]
    return {"bestBid": bids[0][0], "bestAsk": asks[0][0], "spread": spread,
            "bids": bids, "asks": asks}

async def funding(symbol: str):
    # Bitget v2 API requires productType for funding rate
    return await _get("/mix/market/current-fund-rate", {"symbol": symbol, "productType": "usdt-futures"})

async def open_interest(symbol: str):
    # Bitget v2 API requires productType for open interest
    return await _get("/mix/market/open-interest", {"symbol": symbol, "productType": "usdt-futures"})