"""
Klassenbasierte Cache Manager Implementation
Erweitert das bestehende Cache System um strukturierte Klassen
Behält Backward Compatibility bei
"""

import asyncio
import json
import logging
from typing import Any, Optional, Dict, Union, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from redis.exceptions import RedisError

from .settings import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Klassenbasierte Cache Manager für strukturiertes Caching
    
    Features:
    - Redis Backend Support
    - Automatic JSON serialization/deserialization
    - TTL management
    - Cache statistics
    - Bulk operations
    - Agent Framework Integration
    """
    
    def __init__(self, 
                 redis_url: Optional[str] = None, 
                 prefix: str = "gptcrypto",
                 default_ttl: int = 300):
        """
        Initialize Cache Manager
        
        Args:
            redis_url: Redis connection URL (defaults to settings.REDIS_URL)
            prefix: Cache key prefix
            default_ttl: Default TTL in seconds
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.prefix = prefix
        self.default_ttl = default_ttl
        self.redis_client: Optional[aioredis.Redis] = None
        self.is_initialized = False
        self.stats: Dict[str, Any] = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    async def initialize(self) -> bool:
        """
        Initialize cache connections
        
        Returns:
            bool: True if initialization successful
        """
        if not settings.CACHE_ENABLED:
            logger.info("🔄 Cache is disabled, skipping initialization")
            return False
        
        try:
            # Initialize Redis client
            self.redis_client = aioredis.from_url(
                self.redis_url, 
                encoding="utf8", 
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Initialize FastAPICache if not already done
            if not hasattr(FastAPICache, '_backend') or not FastAPICache._backend:
                redis_backend = RedisBackend(self.redis_client)
                FastAPICache.init(redis_backend, prefix=self.prefix)
            
            self.is_initialized = True
            logger.info(f"✅ Cache initialized successfully with Redis at {self.redis_url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache initialization failed: {str(e)}")
            self.is_initialized = False
            return False
    
    async def close(self):
        """Close cache connections"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
        self.is_initialized = False
    
    @asynccontextmanager
    async def session(self):
        """Async context manager for cache operations"""
        if not self.is_initialized:
            await self.initialize()
        try:
            yield self
        finally:
            # Keep connection alive for reuse
            pass
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        if not self.is_initialized:
            return default
        
        try:
            cache_key = self._make_key(key)
            
            if self.redis_client:
                value = await self.redis_client.get(cache_key)
                if value is not None:
                    self.stats["hits"] += 1
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                else:
                    self.stats["misses"] += 1
                    return default
            
            # Fallback to FastAPICache
            if hasattr(FastAPICache, '_backend') and FastAPICache._backend:
                cache_backend = FastAPICache._backend
                value = await cache_backend.get(cache_key)
                if value is not None:
                    self.stats["hits"] += 1
                    return value
            
            self.stats["misses"] += 1
            return default
            
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            self.stats["errors"] += 1
            return default
    
    async def set(self, 
                  key: str, 
                  value: Any, 
                  ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        if not self.is_initialized:
            return False
        
        ttl = ttl or self.default_ttl
        
        try:
            cache_key = self._make_key(key)
            
            # Serialize value if needed
            if isinstance(value, (dict, list, tuple)):
                cached_value = json.dumps(value, default=str)
            else:
                cached_value = value
            
            if self.redis_client:
                await self.redis_client.setex(cache_key, ttl, cached_value)
                self.stats["sets"] += 1
                return True
            
            # Fallback to FastAPICache
            if hasattr(FastAPICache, '_backend') and FastAPICache._backend:
                cache_backend = FastAPICache._backend
                if isinstance(value, (dict, list, tuple)):
                    await cache_backend.set(cache_key, json.dumps(value, default=str), expire=ttl)
                else:
                    await cache_backend.set(cache_key, str(value), expire=ttl)
                self.stats["sets"] += 1
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            bool: True if successful
        """
        if not self.is_initialized:
            return False
        
        try:
            cache_key = self._make_key(key)
            
            if self.redis_client:
                result = await self.redis_client.delete(cache_key)
                if result > 0:
                    self.stats["deletes"] += 1
                return result > 0
            
            # Note: FastAPICache doesn't have a direct delete method
            # This functionality is primarily available through Redis client
            return False
            
            return False
            
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key to check
            
        Returns:
            bool: True if key exists
        """
        if not self.is_initialized:
            return False
        
        try:
            cache_key = self._make_key(key)
            
            if self.redis_client:
                result = await self.redis_client.exists(cache_key)
                return result > 0
            
            return False
            
        except Exception as e:
            logger.warning(f"Cache exists check failed for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for a key
        
        Args:
            key: Cache key
            
        Returns:
            int: Remaining TTL in seconds, None if key doesn't exist
        """
        if not self.is_initialized or not self.redis_client:
            return None
        
        try:
            cache_key = self._make_key(key)
            ttl = await self.redis_client.ttl(cache_key)
            return ttl if ttl > 0 else None
            
        except Exception as e:
            logger.warning(f"Cache TTL check failed for key {key}: {e}")
            return None
    
    async def extend_ttl(self, key: str, additional_seconds: int) -> bool:
        """
        Extend TTL for existing key
        
        Args:
            key: Cache key
            additional_seconds: Additional seconds to add
            
        Returns:
            bool: True if successful
        """
        if not self.is_initialized or not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(key)
            current_ttl = await self.redis_client.ttl(cache_key)
            
            if current_ttl > 0:
                new_ttl = current_ttl + additional_seconds
                await self.redis_client.expire(cache_key, new_ttl)
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Cache TTL extension failed for key {key}: {e}")
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dict mapping keys to their values
        """
        if not self.is_initialized:
            return {}
        
        results = {}
        
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results[key] = value
        
        return results
    
    async def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in cache
        
        Args:
            data: Dict of key-value pairs to cache
            ttl: Time to live in seconds
            
        Returns:
            bool: True if all operations successful
        """
        if not self.is_initialized:
            return False
        
        success = True
        
        for key, value in data.items():
            result = await self.set(key, value, ttl)
            success = success and result
        
        return success
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            int: Number of keys deleted
        """
        if not self.is_initialized or not self.redis_client:
            return 0
        
        try:
            full_pattern = self._make_key(pattern)
            keys = await self.redis_client.keys(full_pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.stats["deletes"] += deleted
                return deleted
            
            return 0
            
        except Exception as e:
            logger.warning(f"Cache pattern clear failed for pattern {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dict with cache statistics
        """
        extended_stats = self.stats.copy()
        extended_stats["initialized"] = self.is_initialized
        extended_stats["redis_connected"] = self.redis_client is not None
        extended_stats["hit_rate"] = (
            self.stats["hits"] / (self.stats["hits"] + self.stats["misses"]) 
            if (self.stats["hits"] + self.stats["misses"]) > 0 else 0
        )
        
        return extended_stats
    
    async def clear_stats(self):
        """Clear statistics"""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for Agent Framework
        
        Returns:
            Dict with tool metadata and available methods
        """
        return {
            "name": "CacheManager",
            "description": "Redis-based cache management service",
            "methods": {
                "get": {
                    "description": "Get value from cache",
                    "parameters": {
                        "key": {"type": "string", "required": True},
                        "default": {"type": "any", "required": False}
                    }
                },
                "set": {
                    "description": "Set value in cache",
                    "parameters": {
                        "key": {"type": "string", "required": True},
                        "value": {"type": "any", "required": True},
                        "ttl": {"type": "integer", "required": False}
                    }
                },
                "delete": {
                    "description": "Delete key from cache",
                    "parameters": {
                        "key": {"type": "string", "required": True}
                    }
                },
                "get_stats": {
                    "description": "Get cache statistics",
                    "parameters": {}
                }
            }
        }


# Singleton instance for global access
_cache_manager_instance: Optional[CacheManager] = None

def get_cache_manager() -> CacheManager:
    """Get global CacheManager instance"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager()
    return _cache_manager_instance


# Backward compatibility wrapper function
async def init_cache():
    """Backward compatibility wrapper for cache initialization"""
    cache_manager = get_cache_manager()
    await cache_manager.initialize()
