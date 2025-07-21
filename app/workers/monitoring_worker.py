"""
System monitoring worker for health checks and metrics collection.
"""

import asyncio
import logging
import os
from typing import Dict, Any
from datetime import datetime
from .base_worker import BaseWorker

logger = logging.getLogger(__name__)

class MonitoringWorker(BaseWorker):
    """
    Worker for system monitoring and health checks.
    Consolidates monitoring functionality from main.py.
    """
    
    def __init__(self, interval: float = 60.0, name: str = "monitoring_worker"):
        super().__init__(name, interval)
        self.metrics_history = []
        self.max_history = 100  # Keep last 100 metrics
    
    async def _work(self):
        """Collect system metrics and perform health checks"""
        try:
            metrics = await self._collect_metrics()
            
            # Store metrics in history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            # Check for alerts based on metrics
            await self._check_system_health(metrics)
            
            logger.debug(f"System metrics collected: Memory={metrics['memory_usage_mb']}MB")
            
        except Exception as e:
            logger.error(f"Monitoring worker error: {e}")
            raise
    
    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics using basic OS commands"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "process_id": os.getpid(),
        }
        
        try:
            # Basic memory info (if available)
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                metrics["load_average"] = {
                    "1min": load_avg[0],
                    "5min": load_avg[1], 
                    "15min": load_avg[2]
                }
            
            # Memory usage estimation (basic)
            import resource
            memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # On Linux, ru_maxrss is in KB, on macOS it's in bytes
            if os.name != 'nt':  # Unix-like systems
                metrics["memory_usage_mb"] = memory_usage // 1024 if hasattr(os, 'uname') and os.uname().sysname == 'Linux' else memory_usage // (1024 * 1024)
            else:
                metrics["memory_usage_mb"] = memory_usage // (1024 * 1024)
                
        except ImportError:
            metrics["memory_usage_mb"] = 0
            logger.debug("Resource module not available for memory tracking")
        except Exception as e:
            logger.debug(f"Error collecting detailed metrics: {e}")
            metrics["memory_usage_mb"] = 0
        
        return metrics
    
    async def _check_system_health(self, metrics: Dict[str, Any]):
        """Check system health and log warnings"""
        memory_threshold_mb = 1024  # 1GB threshold
        
        if metrics.get("memory_usage_mb", 0) > memory_threshold_mb:
            logger.warning(f"High memory usage detected: {metrics['memory_usage_mb']}MB")
        
        # Check load average if available
        if "load_average" in metrics:
            load_1min = metrics["load_average"]["1min"]
            if load_1min > 5.0:  # High load threshold
                logger.warning(f"High system load detected: {load_1min}")
    
    def get_latest_metrics(self) -> Dict[str, Any]:
        """Get the most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else {}
    
    def get_metrics_history(self, limit: int = 50) -> list:
        """Get metrics history"""
        return self.metrics_history[-limit:] if self.metrics_history else []
    
    def get_status(self):
        """Get enhanced status with monitoring-specific metrics"""
        status = super().get_status()
        status["metrics_collected"] = len(self.metrics_history)
        status["latest_metrics"] = self.get_latest_metrics()
        return status
