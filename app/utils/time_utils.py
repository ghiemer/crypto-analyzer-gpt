"""
Time utility functions for timestamp conversions and datetime handling.
"""

import datetime as dt
from typing import Union

def timestamp_to_ms(timestamp: dt.datetime) -> int:
    """
    Convert datetime to milliseconds timestamp.
    
    Args:
        timestamp: datetime object to convert
        
    Returns:
        Milliseconds timestamp as integer
    """
    return int(timestamp.replace(tzinfo=dt.timezone.utc).timestamp() * 1000)

def datetime_from_iso(iso_string: str) -> dt.datetime:
    """
    Convert ISO format string to datetime object.
    
    Args:
        iso_string: ISO format datetime string
        
    Returns:
        datetime object
    """
    return dt.datetime.fromisoformat(iso_string)

def parse_time_input(time_input: Union[str, int, dt.datetime]) -> int:
    """
    Parse various time input formats to milliseconds timestamp.
    
    Args:
        time_input: Time input in various formats (ISO string, timestamp, datetime)
        
    Returns:
        Milliseconds timestamp as integer
    """
    if isinstance(time_input, dt.datetime):
        return timestamp_to_ms(time_input)
    elif isinstance(time_input, (int, float)):
        return int(time_input)
    elif isinstance(time_input, str):
        if time_input.isdigit():
            return int(time_input)
        else:
            return timestamp_to_ms(datetime_from_iso(time_input))
    else:
        raise ValueError(f"Unsupported time input format: {type(time_input)}")

def current_timestamp_ms() -> int:
    """
    Get current timestamp in milliseconds.
    
    Returns:
        Current timestamp in milliseconds
    """
    return timestamp_to_ms(dt.datetime.now())

def format_timestamp_iso(timestamp_ms: int) -> str:
    """
    Format milliseconds timestamp to ISO string.
    
    Args:
        timestamp_ms: Timestamp in milliseconds
        
    Returns:
        ISO formatted datetime string
    """
    return dt.datetime.fromtimestamp(timestamp_ms / 1000, tz=dt.timezone.utc).isoformat()
