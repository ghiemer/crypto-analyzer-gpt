"""
Base worker class with common patterns for background tasks.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BaseWorker(ABC):
    """
    Base class for background workers with common functionality:
    - Task lifecycle management
    - Error handling and recovery
    - Status tracking
    - Graceful shutdown
    """
    
    def __init__(self, name: str, interval: float = 60.0):
        self.name = name
        self.interval = interval
        self.task: Optional[asyncio.Task] = None
        self.is_running = False
        self.last_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
    
    @abstractmethod
    async def _work(self) -> Any:
        """Abstract method for worker logic - must be implemented by subclasses"""
        pass
    
    async def start(self) -> bool:
        """
        Start the worker task.
        
        Returns:
            True if started successfully, False if already running
        """
        if self.is_running:
            logger.warning(f"Worker '{self.name}' is already running")
            return False
        
        logger.info(f"Starting worker '{self.name}' with interval {self.interval}s")
        self.task = asyncio.create_task(self._run_loop())
        return True
    
    async def stop(self, timeout: float = 10.0) -> bool:
        """
        Stop the worker task gracefully.
        
        Args:
            timeout: Maximum time to wait for graceful shutdown
            
        Returns:
            True if stopped successfully, False on timeout
        """
        if not self.is_running or not self.task:
            return True
        
        logger.info(f"Stopping worker '{self.name}'")
        self.task.cancel()
        
        try:
            await asyncio.wait_for(self.task, timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Worker '{self.name}' did not stop within {timeout}s")
            return False
        except asyncio.CancelledError:
            pass
        
        self.task = None
        logger.info(f"Worker '{self.name}' stopped successfully")
        return True
    
    async def _run_loop(self):
        """Main worker loop"""
        self.is_running = True
        
        try:
            while self.is_running:
                try:
                    await self._work()
                    self.run_count += 1
                    self.last_run = datetime.now()
                    
                except asyncio.CancelledError:
                    logger.info(f"Worker '{self.name}' received cancellation")
                    break
                    
                except Exception as e:
                    self.error_count += 1
                    self.last_error = str(e)
                    logger.error(f"Worker '{self.name}' error: {e}", exc_info=True)
                    
                    # Add exponential backoff on errors
                    error_delay = min(self.interval * (2 ** min(self.error_count, 5)), 300)
                    await asyncio.sleep(error_delay)
                    continue
                
                # Normal interval sleep
                await asyncio.sleep(self.interval)
                
        finally:
            self.is_running = False
            logger.info(f"Worker '{self.name}' loop ended")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get worker status information.
        
        Returns:
            Dictionary with worker status details
        """
        return {
            "name": self.name,
            "is_running": self.is_running,
            "interval": self.interval,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_error": self.last_error,
            "uptime": (datetime.now() - self.last_run).total_seconds() if self.last_run else 0
        }
    
    async def restart(self) -> bool:
        """
        Restart the worker by stopping and starting again.
        
        Returns:
            True if restarted successfully
        """
        await self.stop()
        return await self.start()

class PeriodicWorker(BaseWorker):
    """
    Worker that runs a function periodically with built-in error handling.
    """
    
    def __init__(self, name: str, work_func, interval: float = 60.0):
        super().__init__(name, interval)
        self.work_func = work_func
    
    async def _work(self):
        """Execute the work function"""
        if asyncio.iscoroutinefunction(self.work_func):
            return await self.work_func()
        else:
            return self.work_func()
