"""
Cache helper utilities for consistent cache operations across services.
"""

import logging
from typing import Any, Optional, Union
from fastapi_cache import FastAPICache
from ..core.settings import settings

logger = logging.getLogger(__name__)

class CacheHelper:
    """
    Helper class for common cache operations with consistent error handling.
    Consolidates the duplicate cache logic found across multiple services.
    """
    
    @staticmethod
    def make_cache_key(prefix: str, *args, **kwargs) -> str:
        """
        Create a standardized cache key.
        
        Args:
            prefix: Key prefix (usually service name)
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key
            
        Returns:
            Standardized cache key string
        """
        key_parts = [prefix]
        
        # Add positional arguments
        key_parts.extend(str(arg) for arg in args)
        
        # Add keyword arguments (sorted for consistency)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend(f"{k}:{v}" for k, v in sorted_kwargs)
        
        return ":".join(key_parts)
    
    @staticmethod
    async def get_from_cache(key: str) -> Optional[Any]:
        """
        Get value from cache with consistent error handling.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/error
        """
        if not settings.CACHE_ENABLED:
            return None
        
        try:
            if hasattr(FastAPICache, '_backend') and FastAPICache._backend:
                # Use the backend directly to match the service implementations
                backend = FastAPICache._backend
                if hasattr(backend, 'get'):
                    return await backend.get(key)  # type: ignore
                # FastAPICache doesn't have get method, use backend directly
        except Exception as e:
            logger.debug(f"Cache get error for key '{key}': {e}")
        
        return None
    
    @staticmethod
    async def save_to_cache(key: str, data: Any, ttl: int = 300):
        """
        Save value to cache with consistent error handling.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds
        """
        if not settings.CACHE_ENABLED:
            return
        
        try:
            if hasattr(FastAPICache, '_backend') and FastAPICache._backend:
                # Use the backend directly to match the service implementations
                backend = FastAPICache._backend
                if hasattr(backend, 'set'):
                    await backend.set(key, data, expire=ttl)  # type: ignore
                # FastAPICache doesn't have set method, use backend directly
        except Exception as e:
            logger.debug(f"Cache set error for key '{key}': {e}")
    
    @staticmethod
    async def delete_from_cache(key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not settings.CACHE_ENABLED:
            return False
        
        try:
            if hasattr(FastAPICache, '_backend') and FastAPICache._backend:
                backend = FastAPICache._backend
                if hasattr(backend, 'delete'):
                    result = await backend.delete(key)  # type: ignore
                    return result > 0 if isinstance(result, int) else bool(result)
                # Fallback - return False if no delete method
                return False
        except Exception as e:
            logger.debug(f"Cache delete error for key '{key}': {e}")
        
        return False
    
    @staticmethod
    async def clear_cache_pattern(pattern: str) -> int:
        """
        Clear cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "bitget:*")
            
        Returns:
            Number of keys deleted
        """
        if not settings.CACHE_ENABLED:
            return 0
        
        deleted = 0
        try:
            if hasattr(FastAPICache, '_backend') and FastAPICache._backend:
                backend = FastAPICache._backend
                
                # For Redis backend
                if hasattr(backend, 'scan_iter'):
                    async for key in backend.scan_iter(match=pattern):  # type: ignore
                        if await backend.delete(key):  # type: ignore
                            deleted += 1
        except Exception as e:
            logger.error(f"Cache pattern clear error for pattern '{pattern}': {e}")
        
        return deleted
    
    @staticmethod
    def is_cache_enabled() -> bool:
        """
        Check if cache is enabled and available.
        
        Returns:
            True if cache is enabled and backend is available
        """
        return (settings.CACHE_ENABLED and 
                hasattr(FastAPICache, '_backend') and 
                FastAPICache._backend is not None)
    
    @staticmethod
    async def get_cache_stats() -> dict:
        """
        Get cache statistics if available.
        
        Returns:
            Dictionary with cache statistics
        """
        if not CacheHelper.is_cache_enabled():
            return {"enabled": False}
        
        stats = {"enabled": True}
        
        try:
            backend = FastAPICache._backend
            
            # For Redis backend
            if backend and hasattr(backend, 'info'):
                info = await backend.info()  # type: ignore
                stats.update({
                    "memory_usage": info.get("used_memory", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "connected_clients": info.get("connected_clients", 0)
                })
        except Exception as e:
            logger.debug(f"Error getting cache stats: {e}")
        
        return stats
