from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from .settings import settings

async def init_cache():
    if not settings.CACHE_ENABLED:
        print("🔄 Cache is disabled, skipping Redis initialization")
        return
    
    try:
        redis = aioredis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
        # Test connection
        await redis.ping()
        FastAPICache.init(RedisBackend(redis), prefix="gptcrypto")
        print(f"✅ Cache initialized successfully with Redis at {settings.REDIS_URL}")
    except Exception as e:
        print(f"❌ Cache initialization failed: {str(e)}")
        print(f"Redis URL: {settings.REDIS_URL}")
        print("⚠️  Application will continue without cache")
        # Don't raise the exception - let the app run without cache
        pass