from fastapi import APIRouter, Query
import httpx, asyncio
from fastapi_cache import FastAPICache
from ..core.settings import settings
from ..core.errors import UPSTREAM

router = APIRouter(prefix="/news", tags=["news"])

async def _newsapi(client, coin):
    if not settings.NEWS_API_KEY:
        return []
    try:
        url = (f"https://newsapi.org/v2/everything?q={coin}"
               f"&sortBy=publishedAt&language=en&pageSize=5&apiKey={settings.NEWS_API_KEY}")
        r = await client.get(url); r.raise_for_status()
        return [{"title": a["title"], "url": a["url"],
                 "source": a["source"]["name"], "publishedAt": a["publishedAt"], "tags": []}
                for a in r.json().get("articles", [])]
    except Exception as e:
        print(f"NewsAPI error: {e}")
        return []

async def _cryptopanic(client, coin):
    if not settings.CRYPTOPANIC_API_KEY:
        return []
    try:
        url = (f"https://cryptopanic.com/api/developer/v2/posts/"
               f"?auth_token={settings.CRYPTOPANIC_API_KEY}&currencies={coin.upper()}&public=true")
        r = await client.get(url); r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        
        news_items = []
        for p in results:
            try:
                news_items.append({
                    "title": p["title"], 
                    "url": p.get("url", p.get("original_url", "")), 
                    "source": p.get("source", {}).get("domain", "CryptoPanic"),
                    "publishedAt": p.get("published_at", p.get("created_at", "")),
                    "tags": [i["code"] for i in p.get("instruments", [])]
                })
            except KeyError as e:
                print(f"CryptoPanic item parsing error: {e}, item: {p}")
                continue
        
        return news_items
    except Exception as e:
        print(f"CryptoPanic error: {e}")
        return []

@router.get(
    "",
    summary="Crypto news",
    description="""
    Retrieves current news for a crypto asset.
    
    **Sources:**
    - NewsAPI (general news)
    - CryptoPanic (crypto-specific news)
    
    **Examples:**
    - `/news?coin=bitcoin` - Bitcoin news
    - `/news?coin=ethereum` - Ethereum news
    """
)
async def news(
    coin: str = Query(..., description="Name of the crypto asset (e.g. bitcoin, ethereum)", example="bitcoin")
):
    cache_key = f"news:{coin.lower()}"
    # Try to get cached data, handle cache not available
    try:
        if cached := await FastAPICache.get(cache_key):  # type: ignore
            return cached
    except Exception:
        pass  # Cache not available, continue without cache
        
    if not (settings.NEWS_API_KEY or settings.CRYPTOPANIC_API_KEY):
        # Return a helpful message instead of raising an error
        return {
            "message": "News API keys not configured. Please configure NEWS_API_KEY or CRYPTOPANIC_API_KEY environment variables.",
            "coin": coin,
            "sources": {
                "newsapi": "❌ Not configured",
                "cryptopanic": "❌ Not configured"
            },
            "items": []
        }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Call both APIs and collect results
            newsapi_results = await _newsapi(client, coin)
            cryptopanic_results = await _cryptopanic(client, coin)
            
        # Combine results
        items = newsapi_results + cryptopanic_results
        items.sort(key=lambda x: x["publishedAt"], reverse=True)
        
        # Try to cache the result, handle cache not available
        try:
            await FastAPICache.set(cache_key, items, expire=300)  # type: ignore
        except Exception:
            pass  # Cache not available, continue without cache
            
        return {
            "coin": coin,
            "sources": {
                "newsapi": f"✅ {len(newsapi_results)} articles" if settings.NEWS_API_KEY else "❌ Not configured",
                "cryptopanic": f"✅ {len(cryptopanic_results)} posts" if settings.CRYPTOPANIC_API_KEY else "❌ Not configured"
            },
            "total_items": len(items),
            "items": items
        }
        
    except Exception as e:
        return {
            "error": f"Failed to fetch news: {str(e)}",
            "coin": coin,
            "sources": {
                "newsapi": "❌ Error" if settings.NEWS_API_KEY else "❌ Not configured",
                "cryptopanic": "❌ Error" if settings.CRYPTOPANIC_API_KEY else "❌ Not configured"
            },
            "items": []
        }