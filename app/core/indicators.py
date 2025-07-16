import pandas_ta as ta
import pandas as pd
from typing import Callable

_REG: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {}

def _wrap(s: pd.Series | None, name: str):
    if s is None:
        # Return an empty series with the correct name if indicator returns None
        return pd.Series(dtype=float, name=name).to_frame()
    return s.rename(name).to_frame()

def _safe_indicator(indicator_func, name: str):
    """Wrapper to safely handle indicators that might return None"""
    def wrapper(df):
        try:
            result = indicator_func(df)
            if result is None:
                # Return empty series if indicator fails
                return pd.Series(dtype=float, name=name).to_frame()
            return result
        except Exception:
            # Return empty series if indicator throws exception
            return pd.Series(dtype=float, name=name).to_frame()
    return wrapper

def register_defaults() -> None:
    add = lambda k, fn: _REG.setdefault(k, fn)

    # Moving Averages - with safe wrappers
    add("sma50",   _safe_indicator(lambda d: _wrap(ta.sma(d.close, length=50),  "sma50"), "sma50"))
    add("sma200",  _safe_indicator(lambda d: _wrap(ta.sma(d.close, length=200), "sma200"), "sma200"))

    # Momentum
    add("rsi14",   _safe_indicator(lambda d: _wrap(ta.rsi(d.close, length=14),  "rsi14"), "rsi14"))
    add("macd",    _safe_indicator(lambda d: ta.macd(d.close) if ta.macd(d.close) is not None else pd.DataFrame(), "macd"))

    # Volatility
    add("bb20_u", _safe_indicator(lambda d: ta.bbands(d.close, length=20)["BBU_20_2.0"].to_frame("bb20_u") if ta.bbands(d.close, length=20) is not None else pd.DataFrame(), "bb20_u"))
    add("bb20_l", _safe_indicator(lambda d: ta.bbands(d.close, length=20)["BBL_20_2.0"].to_frame("bb20_l") if ta.bbands(d.close, length=20) is not None else pd.DataFrame(), "bb20_l"))
    add("atr14",  _safe_indicator(lambda d: _wrap(ta.atr(d.high, d.low, d.close, length=14), "atr14"), "atr14"))

register_defaults()

def available() -> list[str]:
    return sorted(_REG)

def compute(df: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    for n in names:
        fn = _REG.get(n)
        if not fn:
            raise ValueError(f"indicator '{n}' not found")
        try:
            indicator_result = fn(df)
            if indicator_result is not None and not indicator_result.empty:
                df = pd.concat([df, indicator_result], axis=1)
        except Exception as e:
            # Skip indicators that fail but don't crash the entire request
            print(f"Warning: Failed to compute indicator '{n}': {str(e)}")
            continue
    return df

def register(name: str, fn: Callable[[pd.DataFrame], pd.DataFrame]) -> None:
    if name in _REG:
        raise ValueError("duplicate indicator")
    _REG[name] = fn