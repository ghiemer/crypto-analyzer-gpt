"""
Cache cleanup worker for maintaining cache health and removing expired entries.
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
from .base_worker import BaseWorker

logger = logging.getLogger(__name__)

class CacheCleanupWorker(BaseWorker):
    """
    Worker for cleaning up expired cache entries and maintaining cache health.
    """
    
    def __init__(self, 
                 cache_backend=None,
                 interval: float = 300.0,  # 5 minutes
                 name: str = "cache_cleanup_worker"):
        super().__init__(name, interval)
        self.cache_backend = cache_backend
        self.cleaned_entries = 0
    
    async def _work(self):
        """Clean up expired cache entries"""
        try:
            if not self.cache_backend:
                logger.debug("No cache backend available for cleanup")
                return
            
            # Get cache statistics before cleanup
            pre_cleanup_stats = await self._get_cache_stats()
            
            # Perform cleanup operations
            cleaned = await self._cleanup_expired_entries()
            
            # Get cache statistics after cleanup
            post_cleanup_stats = await self._get_cache_stats()
            
            if cleaned > 0:
                logger.info(f"Cache cleanup completed. Cleaned {cleaned} entries")
                logger.debug(f"Cache stats - Before: {pre_cleanup_stats}, After: {post_cleanup_stats}")
            
            self.cleaned_entries += cleaned
            
        except Exception as e:
            logger.error(f"Cache cleanup worker error: {e}")
            raise
    
    async def _cleanup_expired_entries(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of entries cleaned
        """
        try:
            # This would depend on the specific cache backend implementation
            # For Redis, we could use SCAN and TTL to find expired keys
            # For now, just a placeholder
            
            cleaned = 0
            
            # Example cleanup logic (would need to be adapted for specific cache backend)
            # if hasattr(self.cache_backend, 'scan_iter'):
            #     async for key in self.cache_backend.scan_iter():
            #         ttl = await self.cache_backend.ttl(key)
            #         if ttl == -2:  # Key doesn't exist
            #             continue
            #         elif ttl == -1:  # Key exists but has no TTL
            #             continue
            #         elif ttl == 0:  # Key is expired
            #             await self.cache_backend.delete(key)
            #             cleaned += 1
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
            return 0
    
    async def _get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            # Placeholder for cache statistics
            # This would depend on the cache backend implementation
            return {
                "timestamp": datetime.now().isoformat(),
                "total_keys": 0,  # Would query actual number of keys
                "memory_usage": 0,  # Would query actual memory usage
                "hit_rate": 0.0   # Would calculate from cache metrics
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    async def force_cleanup(self) -> int:
        """
        Force an immediate cache cleanup.
        
        Returns:
            Number of entries cleaned
        """
        logger.info("Forcing immediate cache cleanup")
        return await self._cleanup_expired_entries()
    
    def get_status(self):
        """Get enhanced status with cache-specific metrics"""
        status = super().get_status()
        status["cleaned_entries"] = self.cleaned_entries
        return status
