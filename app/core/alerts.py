import asyncio
import pandas as pd
from redis import asyncio as aioredis
from typing import Dict, Any, Optional
from .settings import settings
from ..services.telegram_bot import send as tg_send
from ..workers.alert_worker import AlertWorker
from ..helpers.cache_helpers import CacheHelper
from ..helpers.error_handlers import handle_api_errors, ErrorHandler
from ..utils.validation import validate_symbol

redis = aioredis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)

# Enhanced Alert System with Worker Management
class EnhancedAlertSystem:
    """Enhanced alert system using AlertWorker with proper lifecycle management."""
    
    def __init__(self):
        self._worker: Optional[AlertWorker] = None
        
    async def initialize(self, candles_func):
        """Initialize the alert worker with candles function."""
        if self._worker is None:
            self._worker = AlertWorker(
                candles_func=candles_func,
                interval=60.0,
                name="crypto_alert_worker"
            )
    
    async def start_monitoring(self) -> bool:
        """Start the alert monitoring worker."""
        if self._worker:
            return await self._worker.start()
        return False
        
    async def stop_monitoring(self) -> bool:
        """Stop the alert monitoring worker."""
        if self._worker:
            return await self._worker.stop()
        return False
        
    def get_status(self) -> Dict[str, Any]:
        """Get worker status information."""
        if self._worker:
            return self._worker.get_status()
        return {"is_running": False, "error": "Worker not initialized"}

# Global alert system instance
_alert_system = EnhancedAlertSystem()

# CRUD with Enhanced Error Handling ----------------------------------------
@handle_api_errors("Failed to add alert")
async def add_alert(user: str, symbol: str, expr: str) -> None:
    """Add alert with validation and enhanced error handling."""
    symbol = validate_symbol(symbol)  # Validate symbol format
    key = CacheHelper.make_cache_key("alert", user)
    await CacheHelper.save_to_cache(key, {symbol: expr}, ttl=0)  # Permanent storage

@handle_api_errors("Failed to delete alert")
async def delete_alert(user: str, symbol: str) -> None:
    """Delete alert with validation."""
    symbol = validate_symbol(symbol)
    await redis.hdel(f"alert:{user}", symbol)  # type: ignore

@handle_api_errors("Failed to list alerts")
async def list_alerts(user: str) -> Dict[str, str]:
    """List all alerts for a user."""
    return await redis.hgetall(f"alert:{user}")  # type: ignore

# Spam-Lock (10 s) ----------------------------------------------------------
async def _spam_lock(lock_key: str) -> bool:
    ok = await redis.setnx(lock_key, 1)  # type: ignore
    if ok:
        await redis.expire(lock_key, 10)  # type: ignore
    return ok

# Background‑Worker - Legacy Compatibility (DEPRECATED) -------------------
async def alert_worker(fetch_df):
    """
    DEPRECATED: Legacy alert worker - use EnhancedAlertSystem instead.
    This function is kept for backward compatibility but will be removed in future versions.
    
    Use EnhancedAlertSystem for new implementations:
    ```python
    system = EnhancedAlertSystem()
    await system.initialize(fetch_df)
    await system.start_monitoring()
    ```
    """
    import warnings
    warnings.warn(
        "alert_worker() is deprecated. Use EnhancedAlertSystem instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Initialize and start enhanced system for backward compatibility
    await _alert_system.initialize(fetch_df)
    await _alert_system.start_monitoring()
    
    # Keep original function running for compatibility
    while True:
        try:
            status = _alert_system.get_status()
            if not status.get("is_running", False):
                # Worker stopped, try to restart
                await _alert_system.start_monitoring()
        except Exception as e:
            # Log error using enhanced error handling
            error_response = ErrorHandler.create_error_response(
                e, default_message="Alert worker encountered an error"
            )
            print(f"❌ Alert Worker Error: {error_response.body}")
        
        await asyncio.sleep(60)

# Public API for Enhanced Alert System -------------------------------------
async def initialize_alert_system(candles_func) -> None:
    """Initialize the enhanced alert system."""
    await _alert_system.initialize(candles_func)

async def start_alert_monitoring() -> bool:
    """Start alert monitoring."""
    return await _alert_system.start_monitoring()

async def stop_alert_monitoring() -> bool:
    """Stop alert monitoring."""
    return await _alert_system.stop_monitoring()

def get_alert_system_status() -> Dict[str, Any]:
    """Get alert system status."""
    return _alert_system.get_status()