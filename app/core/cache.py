from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from .settings import settings

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from typing import Optional
from .settings import settings
from ..workers.cache_cleanup_worker import CacheCleanupWorker
from ..helpers.cache_helpers import CacheHelper
from ..helpers.error_handlers import ErrorHandler

# Global cache cleanup worker instance
_cleanup_worker: Optional[CacheCleanupWorker] = None

async def init_cache():
    """Enhanced cache initialization with health monitoring and cleanup worker"""
    global _cleanup_worker
    
    if not settings.CACHE_ENABLED:
        print("🔄 Cache is disabled, skipping Redis initialization")
        return
    
    try:
        # Standard Redis initialization
        redis = aioredis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
        await redis.ping()
        FastAPICache.init(RedisBackend(redis), prefix="gptcrypto")
        
        # Health monitoring using CacheHelper
        try:
            stats = await CacheHelper.get_cache_stats()
            print(f"✅ Cache initialized successfully - Redis Stats: {stats}")
        except Exception as e:
            print(f"✅ Cache initialized (stats unavailable: {str(e)})")
        
        # Start automated cleanup worker
        try:
            _cleanup_worker = CacheCleanupWorker(
                cache_backend=redis,
                interval=300.0,  # 5 minutes
                name="cache_cleanup_worker"
            )
            await _cleanup_worker.start()
            print("🧹 Cache cleanup worker started (5min intervals)")
        except Exception as e:
            print(f"⚠️ Cache cleanup worker failed to start: {str(e)}")
        
        print(f"🎯 Cache system fully operational at {settings.REDIS_URL}")
        
    except Exception as e:
        # Enhanced error handling
        error_response = ErrorHandler.create_error_response(
            e, default_message="Cache initialization failed"
        )
        print(f"❌ {error_response.body}")
        print(f"Redis URL: {settings.REDIS_URL}")
        print("⚠️  Application will continue without cache")

async def shutdown_cache():
    """Gracefully shutdown cache components"""
    global _cleanup_worker
    
    if _cleanup_worker:
        try:
            await _cleanup_worker.stop()
            print("🛑 Cache cleanup worker stopped")
        except Exception as e:
            print(f"⚠️ Error stopping cache cleanup worker: {str(e)}")

def get_cache_worker_status():
    """Get status of cache cleanup worker"""
    if _cleanup_worker:
        return _cleanup_worker.get_status()
    return {"is_running": False, "error": "Worker not initialized"}