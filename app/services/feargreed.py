import httpx
from fastapi_cache import FastAPICache

async def fear_greed():
    # Try to get cached data, handle cache not available
    try:
        if cached := await FastAPICache.get("fng"):  # type: ignore
            return cached
    except Exception:
        pass  # Cache not available, continue without cache
        
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get("https://api.alternative.me/fng/")
        r.raise_for_status()
    data = r.json()["data"][0]
    
    # Try to cache the result, handle cache not available
    try:
        await FastAPICache.set("fng", data, expire=3600)  # type: ignore
    except Exception:
        pass  # Cache not available, continue without cache
        
    return data