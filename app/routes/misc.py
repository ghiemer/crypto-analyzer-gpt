from fastapi import APIRouter, HTTPException
from ..services.feargreed import fear_greed
from ..core.settings import settings
from ..core.cache import get_cache_worker_status
from ..core.alerts import get_alert_system_status
from redis import asyncio as aioredis
import httpx

router = APIRouter(tags=["misc"])

@router.get("/feargreed")
async def index():
    return await fear_greed()

@router.get("/status")
async def status():
    """Authenticated status endpoint with detailed service health"""
    status = {
        "status": "ok",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "services": {}
    }
    
    # Test Redis connection only if cache is enabled
    if settings.CACHE_ENABLED:
        try:
            redis = aioredis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
            await redis.ping()  # type: ignore
            await redis.close()  # Close connection after test
            status["services"]["redis"] = "healthy"
        except Exception as e:
            status["services"]["redis"] = f"unhealthy: {str(e)}"
            status["status"] = "degraded"
    else:
        status["services"]["redis"] = "disabled"
    
    # Test Bitget API
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("https://api.bitget.com/api/v2/spot/public/time")
            if r.status_code == 200:
                status["services"]["bitget"] = "healthy"
            else:
                status["services"]["bitget"] = f"unhealthy: HTTP {r.status_code}"
                status["status"] = "degraded"
    except Exception as e:
        status["services"]["bitget"] = f"unhealthy: {str(e)}"
        status["status"] = "degraded"
    
    # Enhanced Worker Status Monitoring
    try:
        # Alert System Status
        alert_status = get_alert_system_status()
        status["services"]["alert_system"] = {
            "status": "healthy" if alert_status.get("is_running") else "stopped",
            "details": alert_status
        }
        
        # Cache Cleanup Worker Status
        cache_worker_status = get_cache_worker_status()
        status["services"]["cache_cleanup_worker"] = {
            "status": "healthy" if cache_worker_status.get("is_running") else "stopped", 
            "details": cache_worker_status
        }
        
    except Exception as e:
        status["services"]["workers"] = f"error: {str(e)}"
        status["status"] = "degraded"
    
    return status