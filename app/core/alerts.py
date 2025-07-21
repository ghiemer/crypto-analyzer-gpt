import asyncio
import pandas as pd
from typing import Dict, Any, Optional, List
from .settings import settings
from ..services.telegram_bot import send as tg_send
from ..workers.alert_worker import AlertWorker
from ..helpers.error_handlers import handle_api_errors, ErrorHandler
from ..utils.validation import validate_symbol

# Simple in-memory alert system (production-ready fallback)
_memory_alerts: Dict[str, Dict[str, str]] = {}

class SimpleAlertSystem:
    """Simple in-memory alert system for reliable operation."""
    
    def __init__(self):
        self._monitoring = False
        
    async def add_alert(self, user: str, symbol: str, expr: str):
        """Add new alert to in-memory storage."""
        if user not in _memory_alerts:
            _memory_alerts[user] = {}
        _memory_alerts[user][symbol] = expr
        print(f"✅ Alert added: {user}:{symbol} = {expr}")
    
    async def delete_alert(self, user: str, symbol: str):
        """Delete alert from in-memory storage."""
        if user in _memory_alerts and symbol in _memory_alerts[user]:
            del _memory_alerts[user][symbol]
            print(f"✅ Alert deleted: {user}:{symbol}")
    
    async def list_alerts(self, user: str) -> Dict[str, str]:
        """List all alerts for user from in-memory storage."""
        return _memory_alerts.get(user, {})

# Global alert system instance
simple_alert_system = SimpleAlertSystem()

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

# Compatibility functions for existing code
async def add_alert(user: str, symbol: str, expr: str):
    """Add alert using simple alert system."""
    symbol = validate_symbol(symbol)
    await simple_alert_system.add_alert(user, symbol, expr)

async def delete_alert(user: str, symbol: str):
    """Delete alert using simple alert system."""
    symbol = validate_symbol(symbol)
    await simple_alert_system.delete_alert(user, symbol)

async def list_alerts(user: str):
    """List alerts using simple alert system."""
    return await simple_alert_system.list_alerts(user)

# Spam-Lock (simplified for in-memory system)
_spam_locks: Dict[str, float] = {}

async def _spam_lock(lock_key: str) -> bool:
    """Simple spam protection using in-memory timestamps."""
    import time
    current_time = time.time()
    
    # Check if lock exists and is still valid (10 seconds)
    if lock_key in _spam_locks:
        if current_time - _spam_locks[lock_key] < 10:
            return False  # Still locked
    
    # Set new lock
    _spam_locks[lock_key] = current_time
    return True

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