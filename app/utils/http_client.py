"""
Base HTTP client with common patterns used across all services.
"""

import httpx
from typing import Optional, Dict, Any, Union
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseAsyncHttpClient(ABC):
    """
    Base class for async HTTP clients with common functionality:
    - Session management
    - Error handling patterns
    - Timeout configuration
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def _ensure_session(self):
        """Ensure session is created"""
        if not self.session:
            self.session = httpx.AsyncClient(timeout=self.timeout)
    
    async def _handle_http_error(self, response: httpx.Response):
        """Common HTTP error handling"""
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_msg = error_data.get("msg", response.text)
                return error_msg
            except ValueError:
                return response.text
        return None
    
    @abstractmethod
    async def _make_request(self, *args, **kwargs) -> Any:
        """Abstract method for making HTTP requests - must be implemented by subclasses"""
        pass
