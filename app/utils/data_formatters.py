"""
Data formatting utilities for consistent API responses and data transformation.
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

def format_candle_data(raw_data: List[List[Any]], symbol: str = "") -> pd.DataFrame:
    """
    Format raw candle data into standardized DataFrame.
    
    Args:
        raw_data: Raw candle data from API
        symbol: Trading symbol (optional)
        
    Returns:
        Formatted DataFrame with standardized columns
    """
    if not raw_data:
        # Return empty DataFrame with expected columns
        columns = ["ts", "open", "high", "low", "close", "vol_base", "vol_quote", "vol_usdt"]
        return pd.DataFrame(columns=columns)
    
    columns = ["ts", "open", "high", "low", "close", "vol_base", "vol_quote", "vol_usdt"]
    
    df = (pd.DataFrame(raw_data, columns=columns)
          .astype({
              "open": float, 
              "high": float, 
              "low": float, 
              "close": float, 
              "vol_base": float, 
              "vol_quote": float, 
              "vol_usdt": float
          })
          .assign(ts=lambda d: pd.to_datetime(pd.to_numeric(d.ts, errors='coerce'), unit="ms", utc=True))
          .sort_values("ts")
          .reset_index(drop=True))
    
    if symbol:
        df["symbol"] = symbol
    
    return df

def format_orderbook_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format raw orderbook data into standardized format.
    
    Args:
        raw_data: Raw orderbook data from API
        
    Returns:
        Formatted orderbook data
    """
    bids = [(float(p), float(q)) for p, q in raw_data.get("bids", [])]
    asks = [(float(p), float(q)) for p, q in raw_data.get("asks", [])]
    
    if not bids or not asks:
        return {
            "bestBid": 0.0,
            "bestAsk": 0.0,
            "spread": 0.0,
            "bids": bids,
            "asks": asks
        }
    
    best_bid = bids[0][0]
    best_ask = asks[0][0]
    spread = best_ask - best_bid
    
    return {
        "bestBid": best_bid,
        "bestAsk": best_ask,
        "spread": spread,
        "bids": bids,
        "asks": asks
    }

def format_api_response(data: Any, message: str = "Success", status: str = "success") -> Dict[str, Any]:
    """
    Format data into standardized API response format.
    
    Args:
        data: Response data
        message: Response message
        status: Response status
        
    Returns:
        Formatted API response
    """
    return {
        "status": status,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

def format_error_response(error_message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
    """
    Format error into standardized error response format.
    
    Args:
        error_message: Error message
        error_code: Optional error code
        
    Returns:
        Formatted error response
    """
    response = {
        "status": "error",
        "message": error_message,
        "timestamp": datetime.now().isoformat()
    }
    
    if error_code:
        response["error_code"] = error_code
    
    return response

def format_fear_greed_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format Fear & Greed index data.
    
    Args:
        raw_data: Raw Fear & Greed data
        
    Returns:
        Formatted Fear & Greed data
    """
    if not raw_data or "data" not in raw_data:
        return {}
    
    data = raw_data["data"]
    if isinstance(data, list) and len(data) > 0:
        current = data[0]
        return {
            "value": int(current.get("value", 0)),
            "value_classification": current.get("value_classification", "Unknown"),
            "timestamp": current.get("timestamp", ""),
            "time_until_update": current.get("time_until_update", ""),
            "fetched_at": datetime.now().isoformat()
        }
    
    return {}

def sanitize_telegram_markdown(text: str) -> str:
    """
    Sanitize text for Telegram Markdown parsing.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text safe for Telegram Markdown
    """
    if not text:
        return ""
    
    # Escape special Markdown characters
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    
    return text

def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format float value as percentage string.
    
    Args:
        value: Float value to format
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
