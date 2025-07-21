"""
Security validation and rate limiting for the Crypto Analyzer API
"""

import hashlib
import hmac
import time
from functools import wraps
from typing import Dict, List, Optional
from fastapi import HTTPException, Request, status
from .settings import settings
from ..helpers.response_helpers import ResponseHelper
from ..helpers.error_handlers import handle_api_errors, ErrorHandler
from ..utils.validation import validate_symbol as utils_validate_symbol

class RateLimiter:
    """Simple in-memory rate limiting implementation"""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str, limit: int | None = None, window: int | None = None) -> bool:
        """Checks if request is under rate limit"""
        limit = limit or settings.RATE_LIMIT_REQUESTS
        window = window or settings.RATE_LIMIT_WINDOW
        
        now = time.time()
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old entries
        self.requests[key] = [
            req_time for req_time in self.requests[key] 
            if now - req_time < window
        ]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= limit:
            return False
        
        # Add request
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str, limit: int | None = None) -> int:
        """Returns remaining requests"""
        limit = limit or settings.RATE_LIMIT_REQUESTS
        if key not in self.requests:
            return limit
        return max(0, limit - len(self.requests[key]))

# Global rate limiter instance
rate_limiter = RateLimiter()

def verify_api_key(provided_key: str) -> bool:
    """Secure API key validation with constant-time comparison"""
    expected_key = settings.API_KEY
    return hmac.compare_digest(provided_key.encode(), expected_key.encode())

def get_client_ip(request: Request) -> str:
    """Extracts client IP (considers proxy headers)"""
    # Render uses X-Forwarded-For
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Fallback to other headers
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Last fallback
    return request.client.host if request.client else "unknown"

def validate_input_length(value: str, max_length: int = 100) -> str:
    """Validates input length against DoS attacks"""
    if len(value) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input too long (max {max_length} characters)"
        )
    return value

@handle_api_errors("Symbol validation failed")
def sanitize_symbol(symbol: str) -> str:
    """
    Sanitizes trading symbol for safe usage.
    
    DEPRECATED: This function now delegates to utils.validation.validate_symbol()
    for consistency across the application.
    """
    import warnings
    warnings.warn(
        "sanitize_symbol() is deprecated. Use utils.validation.validate_symbol() directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Delegate to utils validation for consistency
    return utils_validate_symbol(symbol)

def check_rate_limit(request: Request) -> None:
    """Checks rate limit for request with enhanced error responses"""
    if settings.ENVIRONMENT == "development":
        return  # No rate limiting in development
    
    client_ip = get_client_ip(request)
    
    if not rate_limiter.is_allowed(client_ip):
        # Enhanced response using ResponseHelper
        error_response = ResponseHelper.rate_limited(
            "API rate limit exceeded. Please try again later."
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_response.get("message", "Rate limit exceeded"),
            headers={
                "Retry-After": str(settings.RATE_LIMIT_WINDOW),
                "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + settings.RATE_LIMIT_WINDOW),
                "X-API-Version": error_response.get("api_version", "1.0")
            }
        )

def add_security_headers(response) -> None:
    """Adds security headers"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
