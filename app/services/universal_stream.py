"""
Universal Stream Service
Flexible price streaming service for alerts, trading monitoring, and other use cases
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
import uuid

from ..core.settings import settings
from ..services.bitget import candles

logger = logging.getLogger(__name__)

class StreamType(str, Enum):
    ALERT_MONITORING = "alert_monitoring"
    TRADING_POSITION = "trading_position"
    PORTFOLIO_WATCH = "portfolio_watch"
    CUSTOM_MONITORING = "custom_monitoring"

class StreamSubscription:
    """A subscription to a price stream"""
    
    def __init__(
        self, 
        symbol: str, 
        stream_type: StreamType, 
        callback: Callable, 
        interval: int = 5,
        metadata: Optional[Dict] = None
    ):
        self.id = str(uuid.uuid4())
        self.symbol = symbol.upper()
        self.stream_type = stream_type
        self.callback = callback
        self.interval = interval
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.last_update: Optional[datetime] = None
        self.last_price: Optional[float] = None
        self.active = True
        self.error_count = 0
        self.max_errors = 5

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "stream_type": self.stream_type.value,
            "interval": self.interval,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "last_price": self.last_price,
            "active": self.active,
            "error_count": self.error_count
        }

class UniversalStreamService:
    """Universal streaming service for cryptocurrency prices"""
    
    def __init__(self):
        self.subscriptions: Dict[str, StreamSubscription] = {}
        self.streams: Dict[str, asyncio.Task] = {}  # symbol -> task
        self.running = False
        self.price_cache: Dict[str, Dict] = {}  # symbol -> {price, timestamp, volume, etc}
        self.performance_stats = {
            "total_subscriptions": 0,
            "active_streams": 0,
            "api_calls_per_minute": 0,
            "last_api_call": None,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Try to initialize Redis for caching
        self.redis_client = None
        try:
            import redis
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Universal Stream Service: Redis available")
        except Exception as e:
            logger.info(f"ℹ️ Universal Stream Service: Redis not available, using in-memory cache: {e}")

    async def subscribe(
        self, 
        symbol: str, 
        stream_type: StreamType, 
        callback: Callable,
        interval: int = 5,
        metadata: Optional[Dict] = None
    ) -> str:
        """Subscribe to price updates for a symbol"""
        symbol = symbol.upper()
        
        subscription = StreamSubscription(symbol, stream_type, callback, interval, metadata)
        self.subscriptions[subscription.id] = subscription
        
        logger.info(f"📡 New subscription: {symbol} for {stream_type.value} (interval: {interval}s)")
        
        # Start stream for symbol if not already running
        await self._ensure_stream(symbol)
        
        self.performance_stats["total_subscriptions"] += 1
        return subscription.id

    async def unsubscribe(self, subscription_id: str):
        """Unsubscribe from price updates"""
        if subscription_id in self.subscriptions:
            subscription = self.subscriptions[subscription_id]
            symbol = subscription.symbol
            del self.subscriptions[subscription_id]
            
            logger.info(f"📴 Unsubscribed: {subscription_id} for {symbol}")
            
            # Check if we can stop the stream for this symbol
            await self._cleanup_stream(symbol)

    async def _ensure_stream(self, symbol: str):
        """Ensure a stream is running for the symbol"""
        if symbol not in self.streams and self.running:
            task = asyncio.create_task(self._price_stream(symbol))
            self.streams[symbol] = task
            logger.info(f"🚀 Started price stream for {symbol}")
            self.performance_stats["active_streams"] += 1

    async def _cleanup_stream(self, symbol: str):
        """Stop stream if no more subscriptions exist for symbol"""
        # Check if any subscriptions still exist for this symbol
        has_subscriptions = any(
            sub.symbol == symbol and sub.active 
            for sub in self.subscriptions.values()
        )
        
        if not has_subscriptions and symbol in self.streams:
            task = self.streams[symbol]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.streams[symbol]
            logger.info(f"🛑 Stopped price stream for {symbol}")
            self.performance_stats["active_streams"] -= 1

    async def _price_stream(self, symbol: str):
        """Price streaming loop for a specific symbol"""
        consecutive_failures = 0
        
        while symbol in self.streams and self.running:
            try:
                # Get current price with enhanced data
                price_data = await self._get_enhanced_price_data(symbol)
                
                if price_data:
                    consecutive_failures = 0
                    self.price_cache[symbol] = price_data
                    self.performance_stats["last_api_call"] = datetime.now().isoformat()
                    
                    # Notify all subscriptions for this symbol
                    await self._notify_subscribers(symbol, price_data)
                else:
                    consecutive_failures += 1
                    logger.warning(f"⚠️ Failed to get price for {symbol} ({consecutive_failures}/3)")
                    
                    if consecutive_failures >= 3:
                        logger.error(f"❌ Too many failures for {symbol}, pausing stream")
                        await asyncio.sleep(30)
                        consecutive_failures = 0
                
                # Dynamic interval based on subscription requirements
                min_interval = min(
                    (sub.interval for sub in self.subscriptions.values() 
                     if sub.symbol == symbol and sub.active),
                    default=5
                )
                await asyncio.sleep(min_interval)
                
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"❌ Error in price stream for {symbol}: {e}")
                if consecutive_failures >= 5:
                    break
                await asyncio.sleep(10)
        
        # Cleanup
        if symbol in self.streams:
            del self.streams[symbol]
        logger.info(f"🔚 Price stream ended for {symbol}")

    async def _get_enhanced_price_data(self, symbol: str) -> Optional[Dict]:
        """Get enhanced price data including volume, change, etc."""
        try:
            # Get recent candles for more data
            data = await candles(symbol, limit=2)
            if data is not None and not data.empty and len(data) >= 2:
                current = data.iloc[-1]
                previous = data.iloc[-2]
                
                current_price = float(current["close"])
                previous_price = float(previous["close"])
                change = current_price - previous_price
                change_percent = (change / previous_price) * 100 if previous_price > 0 else 0
                
                # Handle different volume column names (Bitget uses vol_base)
                volume = 0
                for vol_col in ["vol_base", "volume", "vol_quote", "vol_usdt"]:
                    if vol_col in current.index:
                        volume = float(current[vol_col])
                        break
                
                return {
                    "symbol": symbol,
                    "price": current_price,
                    "timestamp": datetime.now().isoformat(),
                    "open": float(current["open"]),
                    "high": float(current["high"]),
                    "low": float(current["low"]),
                    "volume": volume,
                    "change": change,
                    "change_percent": change_percent,
                    "previous_price": previous_price
                }
        except Exception as e:
            logger.error(f"Error getting enhanced price data for {symbol}: {e}")
            # Log available columns for debugging
            try:
                data = await candles(symbol, limit=1)
                if data is not None and not data.empty:
                    logger.debug(f"Available columns for {symbol}: {list(data.columns)}")
            except:
                pass
        return None

    async def _notify_subscribers(self, symbol: str, price_data: Dict):
        """Notify all subscribers for a symbol"""
        symbol_subscribers = [
            sub for sub in self.subscriptions.values() 
            if sub.symbol == symbol and sub.active
        ]
        
        for subscription in symbol_subscribers:
            try:
                # Update subscription
                subscription.last_update = datetime.now()
                subscription.last_price = price_data["price"]
                subscription.error_count = 0
                
                # Call the callback
                await subscription.callback(subscription, price_data)
                
            except Exception as e:
                subscription.error_count += 1
                logger.error(f"❌ Error notifying subscriber {subscription.id}: {e}")
                
                # Disable subscription if too many errors
                if subscription.error_count >= subscription.max_errors:
                    subscription.active = False
                    logger.warning(f"⚠️ Disabled subscription {subscription.id} due to too many errors")

    async def start(self):
        """Start the universal stream service"""
        if self.running:
            return
        
        self.running = True
        logger.info("🚀 Universal Stream Service started")
        
        # Start streams for existing subscriptions
        symbols = set(sub.symbol for sub in self.subscriptions.values() if sub.active)
        for symbol in symbols:
            await self._ensure_stream(symbol)

    async def stop(self):
        """Stop the universal stream service"""
        self.running = False
        
        # Stop all streams
        for symbol in list(self.streams.keys()):
            task = self.streams[symbol]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.streams.clear()
        self.performance_stats["active_streams"] = 0
        logger.info("⏹️ Universal Stream Service stopped")

    def get_subscriptions(self, symbol: Optional[str] = None, stream_type: Optional[StreamType] = None) -> List[StreamSubscription]:
        """Get subscriptions with optional filtering"""
        subscriptions = list(self.subscriptions.values())
        
        if symbol:
            subscriptions = [sub for sub in subscriptions if sub.symbol == symbol.upper()]
        
        if stream_type:
            subscriptions = [sub for sub in subscriptions if sub.stream_type == stream_type]
        
        return subscriptions

    def get_stats(self) -> Dict:
        """Get comprehensive service statistics"""
        active_subs = sum(1 for sub in self.subscriptions.values() if sub.active)
        
        symbol_stats = {}
        for sub in self.subscriptions.values():
            if sub.active:
                if sub.symbol not in symbol_stats:
                    symbol_stats[sub.symbol] = {"subscriptions": 0, "stream_active": False}
                symbol_stats[sub.symbol]["subscriptions"] += 1
                symbol_stats[sub.symbol]["stream_active"] = sub.symbol in self.streams
        
        return {
            "running": self.running,
            "total_subscriptions": len(self.subscriptions),
            "active_subscriptions": active_subs,
            "active_streams": len(self.streams),
            "symbols_monitored": list(symbol_stats.keys()),
            "symbol_details": symbol_stats,
            "price_cache_size": len(self.price_cache),
            "performance": self.performance_stats
        }

    async def get_current_data(self, symbol: str) -> Optional[Dict]:
        """Get current cached data for a symbol"""
        symbol = symbol.upper()
        
        # Check cache first
        if symbol in self.price_cache:
            cached_data = self.price_cache[symbol]
            cache_age = (datetime.now() - datetime.fromisoformat(cached_data["timestamp"])).total_seconds()
            
            # Use cache if less than 30 seconds old
            if cache_age < 30:
                self.performance_stats["cache_hits"] += 1
                return cached_data
        
        # Cache miss - get fresh data
        self.performance_stats["cache_misses"] += 1
        return await self._get_enhanced_price_data(symbol)

# Global instance
stream_service = UniversalStreamService()

async def start_stream_service():
    """Start the universal stream service"""
    await stream_service.start()

async def stop_stream_service():
    """Stop the universal stream service"""
    await stream_service.stop()

def get_stream_service() -> UniversalStreamService:
    """Get the stream service instance"""
    return stream_service
