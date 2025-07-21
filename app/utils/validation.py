"""
Validation utilities for common input validation across the application.
"""

from typing import Union, List, Any
from ..core.errors import BAD_ARGUMENT

# Common validation constants
ALLOWED_GRANULARITIES = {
    "1min", "3min", "5min", "15min", "30min", 
    "1h", "2h", "4h", "6h", "12h",
    "1day", "3day", "1week", "1M"
}

def validate_granularity(granularity: str) -> str:
    """
    Validate and normalize granularity string.
    
    Args:
        granularity: Time granularity string
        
    Returns:
        Normalized granularity string
        
    Raises:
        BAD_ARGUMENT: If granularity is not supported
    """
    granularity = granularity.lower()
    
    # Normalize common formats
    if granularity.endswith("m") and not granularity.endswith("min"):
        granularity = granularity.replace("m", "min")
    
    if granularity not in ALLOWED_GRANULARITIES:
        raise BAD_ARGUMENT(f"Granularity '{granularity}' not supported. Allowed: {', '.join(ALLOWED_GRANULARITIES)}")
    
    return granularity

def validate_limit(limit: int, min_val: int = 1, max_val: int = 1000) -> int:
    """
    Validate and clamp limit parameter.
    
    Args:
        limit: Limit value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Clamped limit value
    """
    if limit < min_val:
        return min_val
    elif limit > max_val:
        return max_val
    return limit

def validate_symbol(symbol: str) -> str:
    """
    Validate trading symbol format.
    
    Args:
        symbol: Trading symbol to validate
        
    Returns:
        Validated symbol (normalized to uppercase)
        
    Raises:
        BAD_ARGUMENT: If symbol format is invalid
    """
    if not symbol or not isinstance(symbol, str):
        raise BAD_ARGUMENT("Symbol must be a non-empty string")
    
    symbol = symbol.upper().strip()
    
    if len(symbol) < 2:
        raise BAD_ARGUMENT("Symbol must be at least 2 characters long")
    
    # Basic symbol format validation (alphanumeric + allowed separators)
    allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_/")
    if not all(c in allowed_chars for c in symbol):
        raise BAD_ARGUMENT("Symbol contains invalid characters")
    
    return symbol

def validate_fear_greed_days(days: int) -> int:
    """
    Validate days parameter for Fear & Greed index.
    
    Args:
        days: Number of days to validate
        
    Returns:
        Validated days value
        
    Raises:
        BAD_ARGUMENT: If days value is invalid
    """
    if days < 1:
        raise BAD_ARGUMENT("Days must be at least 1")
    elif days > 365:
        raise BAD_ARGUMENT("Days cannot exceed 365")
    
    return days

def validate_percentage(value: Union[int, float], min_val: float = 0, max_val: float = 100) -> float:
    """
    Validate percentage values.
    
    Args:
        value: Percentage value to validate
        min_val: Minimum allowed percentage
        max_val: Maximum allowed percentage
        
    Returns:
        Validated percentage value
        
    Raises:
        BAD_ARGUMENT: If percentage is out of range
    """
    if not isinstance(value, (int, float)):
        raise BAD_ARGUMENT("Percentage must be a number")
    
    if value < min_val or value > max_val:
        raise BAD_ARGUMENT(f"Percentage must be between {min_val}% and {max_val}%")
    
    return float(value)

def validate_required_fields(data: dict, required_fields: List[str]) -> dict:
    """
    Validate that required fields are present in data.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        Validated data dictionary
        
    Raises:
        BAD_ARGUMENT: If required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise BAD_ARGUMENT(f"Missing required fields: {', '.join(missing_fields)}")
    
    return data
