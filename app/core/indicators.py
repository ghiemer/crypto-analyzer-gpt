"""
DEPRECATED: Legacy Indicators Module

This module is deprecated and will be removed in future versions.
Please use the modern indicators_service.py for new implementations.

This file now serves as a backward compatibility wrapper around indicators_service.py.
"""
import warnings
import pandas as pd
from typing import Callable, List

# Import the modern service
try:
    from .indicators_service import get_indicator_service
    _service = get_indicator_service()
    _MODERN_SERVICE_AVAILABLE = True
except ImportError:
    _MODERN_SERVICE_AVAILABLE = False
    warnings.warn(
        "indicators_service not available, falling back to legacy implementation",
        DeprecationWarning
    )

def _emit_deprecation_warning(function_name: str):
    """Emit deprecation warning for legacy functions."""
    warnings.warn(
        f"{function_name}() is deprecated. Use indicators_service.get_indicator_service().{function_name.replace('_', '')}() instead.",
        DeprecationWarning,
        stacklevel=3
    )

# Legacy implementation for fallback (kept minimal)
import pandas_ta as ta

_REG: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {}

def _wrap(s: pd.Series | None, name: str):
    if s is None:
        return pd.Series(dtype=float, name=name).to_frame()
    return s.rename(name).to_frame()

def _safe_indicator(indicator_func, name: str):
    """Wrapper to safely handle indicators that might return None"""
    def wrapper(df):
        try:
            result = indicator_func(df)
            if result is None:
                return pd.Series(dtype=float, name=name).to_frame()
            return result
        except Exception:
            return pd.Series(dtype=float, name=name).to_frame()
    return wrapper

def register_defaults() -> None:
    """Register default indicators - DEPRECATED"""
    if _MODERN_SERVICE_AVAILABLE:
        # Modern service handles this automatically
        return
        
    # Legacy fallback implementation
    add = lambda k, fn: _REG.setdefault(k, fn)
    
    # Basic indicators for backward compatibility
    add("sma50",   _safe_indicator(lambda d: _wrap(ta.sma(d.close, length=50),  "sma50"), "sma50"))
    add("sma200",  _safe_indicator(lambda d: _wrap(ta.sma(d.close, length=200), "sma200"), "sma200"))
    add("rsi14",   _safe_indicator(lambda d: _wrap(ta.rsi(d.close, length=14),  "rsi14"), "rsi14"))
    add("macd",    _safe_indicator(lambda d: ta.macd(d.close) if ta.macd(d.close) is not None else pd.DataFrame(), "macd"))
    add("bb20_u", _safe_indicator(lambda d: ta.bbands(d.close, length=20)["BBU_20_2.0"].to_frame("bb20_u") if ta.bbands(d.close, length=20) is not None else pd.DataFrame(), "bb20_u"))
    add("bb20_l", _safe_indicator(lambda d: ta.bbands(d.close, length=20)["BBL_20_2.0"].to_frame("bb20_l") if ta.bbands(d.close, length=20) is not None else pd.DataFrame(), "bb20_l"))
    add("atr14",  _safe_indicator(lambda d: _wrap(ta.atr(d.high, d.low, d.close, length=14), "atr14"), "atr14"))

# Initialize indicators
register_defaults()

# PUBLIC API - Backward Compatibility Wrappers ----------------------------

def available() -> List[str]:
    """Get available indicators - DEPRECATED"""
    _emit_deprecation_warning("available")
    
    if _MODERN_SERVICE_AVAILABLE:
        return _service.get_available_indicators()
    else:
        return sorted(_REG.keys())

def compute(df: pd.DataFrame, names: List[str]) -> pd.DataFrame:
    """Compute indicators - DEPRECATED"""  
    _emit_deprecation_warning("compute")
    
    if _MODERN_SERVICE_AVAILABLE:
        return _service.calculate_multiple(df, names)
    else:
        # Legacy fallback
        for n in names:
            fn = _REG.get(n)
            if not fn:
                raise ValueError(f"indicator '{n}' not found")
            try:
                indicator_result = fn(df)
                if indicator_result is not None and not indicator_result.empty:
                    df = pd.concat([df, indicator_result], axis=1)
            except Exception as e:
                print(f"Warning: Failed to compute indicator '{n}': {str(e)}")
                continue
        return df

def register(name: str, fn: Callable[[pd.DataFrame], pd.DataFrame]) -> None:
    """Register custom indicator - DEPRECATED"""
    _emit_deprecation_warning("register")
    
    if _MODERN_SERVICE_AVAILABLE:
        _service.register_indicator(name, fn)
    else:
        if name in _REG:
            raise ValueError("duplicate indicator")
        _REG[name] = fn