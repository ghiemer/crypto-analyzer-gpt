from fastapi import APIRouter, Query
from ..services import bitget
from ..core.indicators import compute, available
from ..core.errors import BAD_ARGUMENT
from ..core.settings import settings

router = APIRouter(prefix="/candles", tags=["market"])

@router.get(
    "", 
    summary="Candlestick data with technical indicators",
    description="""
    Retrieves candlestick data (OHLCV) from Bitget and optionally calculates technical indicators.
    
    **Examples:**
    - `/candles?symbol=BTCUSDT&limit=100` - 100 BTC candles
    - `/candles?symbol=BTCUSDT&indicators=rsi14,sma50` - With RSI and SMA
    - `/candles?symbol=BTCUSDT&indicators=all` - All available indicators
    """
)
async def candles(
    symbol: str = Query(..., description="Trading symbol (e.g. BTCUSDT)", example="BTCUSDT"),
    granularity: str = Query("1h", description="Candle timeframe", example="1h"),
    timeframe: str | None = Query(None, description="Alias for granularity (compatibility)", example="1h"),
    limit: int = Query(200, le=settings.MAX_CANDLES, description="Number of candles"),
    indicators: str | None = Query(None, description="Comma-separated indicators or 'all'", example="rsi14,sma50"),
    product_type: str | None = Query(None, description="Product type for futures (optional)")
):
    # Use timeframe parameter if provided (for CustomGPT compatibility)
    if timeframe:
        granularity = timeframe
    
    try:
        df = await bitget.candles(symbol, granularity, limit, product_type)
        ind_list: list[str] = []
        if indicators:
            if indicators.lower() in ("*", "all"):
                ind_list = available()
            else:
                ind_list = [i.strip() for i in indicators.split(",") if i.strip()]
                if len(ind_list) > settings.MAX_INDICATORS:
                    raise BAD_ARGUMENT(f"Maximum {settings.MAX_INDICATORS} indicators allowed")
            try:
                df = compute(df, ind_list)
            except ValueError as e:
                raise BAD_ARGUMENT(str(e))

        # Convert DataFrame to the expected response format
        candles_data = []
        for _, row in df.iterrows():
            candle = {
                "timestamp": row.get("ts", "").isoformat() if hasattr(row.get("ts", ""), "isoformat") else str(row.get("ts", "")),
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": float(row.get("vol_base", 0))
            }
            candles_data.append(candle)

        # Extract indicators data
        indicators_data = {}
        for indicator in ind_list:
            if indicator in df.columns:
                indicators_data[indicator] = df[indicator].dropna().tolist()

        return {
            "symbol": symbol,
            "timeframe": granularity,
            "candles": candles_data,
            "indicators": indicators_data,
            "timestamp": candles_data[0]["timestamp"] if candles_data else None
        }
    except Exception as e:
        # Log the error for debugging
        print(f"Error in candles endpoint: {str(e)}")
        raise