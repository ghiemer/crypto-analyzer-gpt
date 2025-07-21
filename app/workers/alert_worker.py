"""
Alert monitoring worker for background alert processing.
"""

import asyncio
import logging
from typing import Callable, Optional
from .base_worker import BaseWorker

logger = logging.getLogger(__name__)

class AlertWorker(BaseWorker):
    """
    Worker for processing crypto alerts in the background.
    Consolidates alert monitoring functionality from main.py.
    """
    
    def __init__(self, 
                 candles_func: Callable,
                 interval: float = 30.0,
                 name: str = "alert_worker"):
        super().__init__(name, interval)
        self.candles_func = candles_func
        self.processed_alerts = 0
    
    async def _work(self):
        """Process alerts for monitored symbols"""
        # This would contain the logic from alert_worker() in main.py
        # For now, just a placeholder that calls the candles function
        try:
            # Example: Process alerts for major symbols
            symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # Could be dynamic
            
            for symbol in symbols:
                try:
                    candles_data = await self.candles_func(symbol, limit=50)
                    if candles_data is not None and not candles_data.empty:
                        # Process alert logic here
                        self.processed_alerts += 1
                        logger.debug(f"Processed alerts for {symbol}")
                        
                except Exception as e:
                    logger.error(f"Error processing alerts for {symbol}: {e}")
                    continue
            
            logger.debug(f"Alert worker cycle completed. Total processed: {self.processed_alerts}")
            
        except Exception as e:
            logger.error(f"Alert worker error: {e}")
            raise
    
    def get_status(self):
        """Get enhanced status with alert-specific metrics"""
        status = super().get_status()
        status["processed_alerts"] = self.processed_alerts
        return status
