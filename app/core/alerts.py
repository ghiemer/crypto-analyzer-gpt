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
print(f"🔍 DEBUG: alerts.py loaded - _memory_alerts initialized: {_memory_alerts}")
print(f"🔍 DEBUG: alerts.py module name: {__name__}")
print(f"🔍 DEBUG: alerts.py file path: {__file__}")

# Check for any Redis imports in the entire module
import sys
current_module = sys.modules[__name__]
module_dict = dir(current_module)
redis_imports = [item for item in module_dict if 'redis' in item.lower()]
print(f"🔍 DEBUG: Redis-related items in module: {redis_imports}")

class SimpleAlertSystem:
    """Simple in-memory alert system for reliable operation."""
    
    def __init__(self):
        self._monitoring = False
        print(f"🔍 DEBUG: SimpleAlertSystem.__init__ called")
        print(f"🔍 DEBUG: SimpleAlertSystem module: {self.__class__.__module__}")
        
    async def add_alert(self, user: str, symbol: str, expr: str):
        """Add new alert to in-memory storage."""
        print(f"🔍 DEBUG: SimpleAlertSystem.add_alert called: user='{user}', symbol='{symbol}', expr='{expr}'")
        if user not in _memory_alerts:
            _memory_alerts[user] = {}
        _memory_alerts[user][symbol] = expr
        print(f"✅ Alert added: {user}:{symbol} = {expr}")
        print(f"🔍 DEBUG: _memory_alerts now: {_memory_alerts}")
    
    async def delete_alert(self, user: str, symbol: str):
        """Delete alert from in-memory storage."""
        print(f"🔍 DEBUG: SimpleAlertSystem.delete_alert called: user='{user}', symbol='{symbol}'")
        if user in _memory_alerts and symbol in _memory_alerts[user]:
            del _memory_alerts[user][symbol]
            print(f"✅ Alert deleted: {user}:{symbol}")
        print(f"🔍 DEBUG: _memory_alerts after delete: {_memory_alerts}")
    
    async def list_alerts(self, user: str) -> Dict[str, str]:
        """List all alerts for user from in-memory storage."""
        print(f"🔍 DEBUG: SimpleAlertSystem.list_alerts called: user='{user}'")
        print(f"🔍 DEBUG: Current _memory_alerts: {_memory_alerts}")
        result = _memory_alerts.get(user, {})
        print(f"🔍 DEBUG: SimpleAlertSystem.list_alerts returning: {result}")
        return result

# Global alert system instance
simple_alert_system = SimpleAlertSystem()
print(f"🔍 DEBUG: simple_alert_system created: {simple_alert_system}")
print(f"🔍 DEBUG: simple_alert_system type: {type(simple_alert_system)}")
print(f"🔍 DEBUG: simple_alert_system methods: {[m for m in dir(simple_alert_system) if not m.startswith('_')]}")

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
    """List alerts using simple alert system - FIXED VERSION."""
    import traceback
    import sys
    import os
    
    # COMPREHENSIVE ERROR LOGGING FOR DEBUGGING
    print(f"🔍 DEBUG: list_alerts called with user='{user}'")
    print(f"🔍 DEBUG: Python path: {sys.path}")
    print(f"🔍 DEBUG: Current working directory: {os.getcwd()}")
    print(f"🔍 DEBUG: File location: {__file__}")
    print(f"🔍 DEBUG: Function location: {list_alerts.__module__}.{list_alerts.__name__}")
    print(f"🔍 DEBUG: simple_alert_system type: {type(simple_alert_system)}")
    print(f"🔍 DEBUG: simple_alert_system location: {simple_alert_system.__class__.__module__}")
    
    try:
        print(f"🔍 DEBUG: About to call simple_alert_system.list_alerts('{user}')")
        result = await simple_alert_system.list_alerts(user)
        print(f"🔍 DEBUG: simple_alert_system.list_alerts returned: {result}")
        print(f"🔍 DEBUG: Result type: {type(result)}")
        return result
    except Exception as e:
        print(f"❌ ERROR in list_alerts: {e}")
        print(f"❌ ERROR type: {type(e)}")
        print(f"❌ ERROR args: {e.args}")
        print(f"❌ FULL TRACEBACK:")
        traceback.print_exc()
        
        # Check if there are any Redis imports or references
        import inspect
        frame = inspect.currentframe()
        try:
            while frame:
                print(f"🔍 STACK FRAME: {frame.f_code.co_filename}:{frame.f_lineno} in {frame.f_code.co_name}")
                locals_info = {k: str(type(v)) for k, v in frame.f_locals.items() if not k.startswith('_')}
                print(f"   Locals: {locals_info}")
                frame = frame.f_back
        finally:
            del frame
        
        raise e

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