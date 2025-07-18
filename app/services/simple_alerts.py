"""
Simple Redis-based Alert System for GPT
No fixed percentages - flexible price alerts
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import uuid

from ..core.settings import settings
from ..services.telegram_bot import send
from ..services.bitget import candles

logger = logging.getLogger(__name__)

class AlertType(str, Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    BREAKOUT = "breakout"

class SimpleAlert:
    """Simple alert for specific price targets"""
    
    def __init__(self, symbol: str, alert_type: AlertType, target_price: float, description: str = ""):
        self.id = str(uuid.uuid4())
        self.symbol = symbol.upper()
        self.alert_type = alert_type
        self.target_price = target_price
        self.description = description
        self.created_at = datetime.now().isoformat()
        self.triggered = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "alert_type": self.alert_type.value,
            "target_price": self.target_price,
            "description": self.description,
            "created_at": self.created_at,
            "triggered": self.triggered
        }

class SimpleAlertSystem:
    """Enhanced alert system with real-time streaming and Redis caching"""
    
    def __init__(self):
        self.alerts: Dict[str, SimpleAlert] = {}
        self.running = False
        self.check_interval = 10  # Reduced from 20 to 10 seconds for faster monitoring
        self.price_cache: Dict[str, float] = {}
        self.price_streams: Dict[str, asyncio.Task] = {}  # Active price streams per symbol
        self.last_alert_times: Dict[str, datetime] = {}  # Prevent spam
        
        # Try to initialize Redis for caching
        self.redis_client = None
        try:
            import redis
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Redis available for caching")
        except Exception as e:
            logger.info(f"ℹ️ Redis not available, using in-memory storage: {e}")
    
    def create_alert(self, symbol: str, alert_type: AlertType, target_price: float, description: str = "") -> str:
        """Create a new alert and start monitoring"""
        alert = SimpleAlert(symbol, alert_type, target_price, description)
        self.alerts[alert.id] = alert
        
        # Try to cache in Redis
        if self.redis_client:
            try:
                self.redis_client.set(f"alert:{alert.id}", json.dumps(alert.to_dict()))
                self.redis_client.sadd("active_alerts", alert.id)
            except Exception as e:
                logger.warning(f"Redis cache failed: {e}")
        
        logger.info(f"📝 Alert created: {symbol} {alert_type.value} @ ${target_price}")
        
        # Start price stream for this symbol if monitoring is active
        if self.running:
            asyncio.create_task(self.ensure_symbol_stream(symbol))
        
        return alert.id
    
    def get_alert(self, alert_id: str) -> Optional[SimpleAlert]:
        """Get alert by ID"""
        return self.alerts.get(alert_id)
    
    def get_active_alerts(self) -> List[SimpleAlert]:
        """Get all active alerts"""
        return [alert for alert in self.alerts.values() if not alert.triggered]
    
    def delete_alert(self, alert_id: str):
        """Delete alert and clean up streams if needed"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            symbol = alert.symbol
            del self.alerts[alert_id]
            
            # Remove from Redis
            if self.redis_client:
                try:
                    self.redis_client.delete(f"alert:{alert_id}")
                    self.redis_client.srem("active_alerts", alert_id)
                except Exception:
                    pass
            
            logger.info(f"🗑️ Alert deleted: {alert_id}")
            
            # Check if we need to stop the stream for this symbol
            if self.running:
                asyncio.create_task(self.ensure_symbol_stream(symbol))
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol with enhanced error handling"""
        try:
            data = await candles(symbol, limit=1)
            if data is not None and not data.empty and len(data) > 0:
                price = float(data.iloc[-1]["close"])
                # Cache the price for quick access
                self.price_cache[symbol] = price
                return price
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
        return None

    async def check_alert(self, alert: SimpleAlert, current_price: float) -> bool:
        """Check if alert should trigger with spam protection"""
        
        # Check spam protection - don't trigger same alert within 60 seconds
        alert_key = f"{alert.symbol}_{alert.alert_type.value}_{alert.target_price}"
        if alert_key in self.last_alert_times:
            time_since_last = (datetime.now() - self.last_alert_times[alert_key]).total_seconds()
            if time_since_last < 60:  # 60 second cooldown
                return False
        
        triggered = False
        
        if alert.alert_type == AlertType.PRICE_ABOVE:
            if current_price >= alert.target_price:
                triggered = True
                
        elif alert.alert_type == AlertType.PRICE_BELOW:
            if current_price <= alert.target_price:
                triggered = True
                
        elif alert.alert_type == AlertType.BREAKOUT:
            if current_price > alert.target_price:
                triggered = True
        
        if triggered:
            self.last_alert_times[alert_key] = datetime.now()
            await self.trigger_alert(alert, current_price)
            
        return triggered

    async def trigger_alert(self, alert: SimpleAlert, current_price: float):
        """Trigger alert and send notification"""
        try:
            # Mark as triggered
            alert.triggered = True
            
            # Create message
            message = self.create_alert_message(alert, current_price)
            
            # Send Telegram notification
            if message:
                try:
                    await send(message)
                    logger.info(f"📨 Alert triggered and sent: {alert.symbol} @ ${current_price}")
                except Exception as e:
                    logger.error(f"❌ Failed to send Telegram message: {e}")
            
            # Remove alert from system (one-time alerts)
            self.delete_alert(alert.id)
            logger.info(f"🗑️ Alert removed after trigger: {alert.id}")
            
        except Exception as e:
            logger.error(f"❌ Error triggering alert: {e}")
            import traceback
            traceback.print_exc()
    
    async def start_price_stream(self, symbol: str):
        """Start dedicated price stream for a symbol"""
        if symbol in self.price_streams:
            return  # Stream already running
        
        async def price_monitor():
            """Continuous price monitoring for specific symbol"""
            consecutive_failures = 0
            max_failures = 3
            
            while self.running and symbol in self.price_streams:
                try:
                    current_price = await self.get_current_price(symbol)
                    if current_price:
                        consecutive_failures = 0  # Reset failure counter
                        
                        # Check all alerts for this symbol
                        symbol_alerts = [alert for alert in self.get_active_alerts() 
                                       if alert.symbol == symbol]
                        
                        if symbol_alerts:
                            logger.debug(f"🔍 {symbol}: ${current_price:.2f} - checking {len(symbol_alerts)} alerts")
                            
                            for alert in symbol_alerts:
                                try:
                                    await self.check_alert(alert, current_price)
                                except Exception as e:
                                    logger.error(f"❌ Error checking alert {alert.id}: {e}")
                        else:
                            # No more alerts for this symbol, stop stream
                            logger.info(f"📴 No more alerts for {symbol}, stopping stream")
                            break
                    else:
                        consecutive_failures += 1
                        logger.warning(f"⚠️ Failed to get price for {symbol} ({consecutive_failures}/{max_failures})")
                        
                        if consecutive_failures >= max_failures:
                            logger.error(f"❌ Too many failures for {symbol}, stopping stream")
                            break
                    
                    # Stream interval - check every 5 seconds for active symbols
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    consecutive_failures += 1
                    logger.error(f"❌ Error in price stream for {symbol}: {e}")
                    if consecutive_failures >= max_failures:
                        break
                    await asyncio.sleep(10)
            
            # Cleanup
            if symbol in self.price_streams:
                del self.price_streams[symbol]
            logger.info(f"🛑 Price stream stopped for {symbol}")
        
        # Start the stream
        task = asyncio.create_task(price_monitor())
        self.price_streams[symbol] = task
        logger.info(f"🚀 Price stream started for {symbol}")

    async def stop_price_stream(self, symbol: str):
        """Stop price stream for a symbol"""
        if symbol in self.price_streams:
            task = self.price_streams[symbol]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.price_streams[symbol]
            logger.info(f"🛑 Price stream stopped for {symbol}")

    async def ensure_symbol_stream(self, symbol: str):
        """Ensure a price stream is running for symbol if it has alerts"""
        symbol_alerts = [alert for alert in self.get_active_alerts() if alert.symbol == symbol]
        
        if symbol_alerts and symbol not in self.price_streams:
            await self.start_price_stream(symbol)
        elif not symbol_alerts and symbol in self.price_streams:
            await self.stop_price_stream(symbol)

    def create_alert_message(self, alert: SimpleAlert, current_price: float) -> str:
        """Create formatted alert message"""
        symbol = alert.symbol
        target = alert.target_price
        description = alert.description or "No description"
        
        if alert.alert_type == AlertType.PRICE_ABOVE:
            return f"""🚀 PRICE ALERT 🚀

{symbol}: ${current_price:,.2f}
Target: ${target:,.2f}
Status: 📈 ABOVE TARGET

Time: {datetime.now().strftime('%H:%M:%S')}

{description}"""
        
        elif alert.alert_type == AlertType.PRICE_BELOW:
            return f"""📉 PRICE ALERT 📉

{symbol}: ${current_price:,.2f}
Target: ${target:,.2f}
Status: 📉 BELOW TARGET

Time: {datetime.now().strftime('%H:%M:%S')}

{description}"""
        
        elif alert.alert_type == AlertType.BREAKOUT:
            return f"""🚀 BREAKOUT ALERT 🚀

{symbol}: ${current_price:,.2f}
Level: ${target:,.2f}
Status: ⚡ BREAKOUT

Time: {datetime.now().strftime('%H:%M:%S')}

{description}"""
        
        return f"Alert: {symbol} @ ${current_price:,.2f}"
    
    async def start_monitoring(self):
        """Start enhanced price monitoring with symbol streams"""
        if self.running:
            return
        
        self.running = True
        
        # Log system status
        redis_status = "✅ Connected" if self.redis_client else "❌ Not available"
        telegram_status = "✅ Configured" if (settings.TG_BOT_TOKEN and settings.TG_CHAT_ID) else "❌ Not configured"
        
        logger.info(f"🚀 Enhanced Alert System started")
        logger.info(f"   Redis: {redis_status}")
        logger.info(f"   Telegram: {telegram_status}")
        logger.info(f"   Stream monitoring: Every 5 seconds per symbol")
        logger.info(f"   Fallback check: Every {self.check_interval} seconds")
        
        while self.running:
            try:
                alerts = self.get_active_alerts()
                
                if alerts:
                    # Get unique symbols with alerts
                    symbols_with_alerts = set(alert.symbol for alert in alerts)
                    
                    # Ensure streams for all symbols with alerts
                    for symbol in symbols_with_alerts:
                        await self.ensure_symbol_stream(symbol)
                    
                    # Clean up streams for symbols without alerts
                    symbols_to_remove = []
                    for symbol in self.price_streams.keys():
                        if symbol not in symbols_with_alerts:
                            symbols_to_remove.append(symbol)
                    
                    for symbol in symbols_to_remove:
                        await self.stop_price_stream(symbol)
                    
                    # Log status
                    stream_count = len(self.price_streams)
                    alert_count = len(alerts)
                    logger.info(f"📊 Monitoring: {alert_count} alerts, {stream_count} active streams")
                    
                    # Fallback check - verify all alerts are being monitored
                    if stream_count == 0 and alert_count > 0:
                        logger.warning("⚠️ No streams running but alerts exist - running fallback check")
                        await self._fallback_check(alerts)
                        
                else:
                    # No alerts - stop all streams
                    if self.price_streams:
                        logger.info("🛑 No alerts found, stopping all price streams")
                        for symbol in list(self.price_streams.keys()):
                            await self.stop_price_stream(symbol)
                    
                    # Only log occasionally when no alerts
                    if hasattr(self, '_last_no_alerts_log'):
                        if (datetime.now() - self._last_no_alerts_log).total_seconds() > 300:  # 5 minutes
                            logger.info("💤 No active alerts to monitor")
                            self._last_no_alerts_log = datetime.now()
                    else:
                        logger.info("💤 No active alerts to monitor")
                        self._last_no_alerts_log = datetime.now()
                
                # Main monitoring loop interval
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(30)

    async def _fallback_check(self, alerts: List[SimpleAlert]):
        """Fallback check when streams fail"""
        logger.info("🔄 Running fallback price check")
        
        # Group by symbol for efficient API calls
        symbol_alerts: Dict[str, List[SimpleAlert]] = {}
        for alert in alerts:
            if alert.symbol not in symbol_alerts:
                symbol_alerts[alert.symbol] = []
            symbol_alerts[alert.symbol].append(alert)
        
        # Check each symbol
        for symbol, alert_list in symbol_alerts.items():
            try:
                current_price = await self.get_current_price(symbol)
                if current_price:
                    logger.info(f"📊 Fallback: {symbol}: ${current_price:.2f} (checking {len(alert_list)} alerts)")
                    
                    for alert in alert_list:
                        try:
                            await self.check_alert(alert, current_price)
                        except Exception as e:
                            logger.error(f"❌ Error checking alert {alert.id}: {e}")
                else:
                    logger.warning(f"⚠️ Fallback: Could not get price for {symbol}")
            except Exception as e:
                logger.error(f"❌ Error in fallback check for {symbol}: {e}")
    
    async def stop_monitoring(self):
        """Stop monitoring and all price streams"""
        self.running = False
        
        # Stop all price streams
        for symbol in list(self.price_streams.keys()):
            await self.stop_price_stream(symbol)
        
        logger.info("⏹️ Enhanced alert monitoring stopped")

    def get_stats(self) -> Dict:
        """Get enhanced alert statistics"""
        active_alerts = self.get_active_alerts()
        symbol_counts = {}
        for alert in active_alerts:
            symbol_counts[alert.symbol] = symbol_counts.get(alert.symbol, 0) + 1
            
        return {
            "total_active": len(active_alerts),
            "active_streams": len(self.price_streams),
            "by_symbol": symbol_counts,
            "price_cache": self.price_cache,
            "streaming_symbols": list(self.price_streams.keys()),
            "check_interval": self.check_interval,
            "spam_protection": len(self.last_alert_times)
        }

# Global instance
alert_system = SimpleAlertSystem()

async def start_alert_monitoring():
    """Start alert monitoring"""
    await alert_system.start_monitoring()

async def stop_alert_monitoring():
    """Stop alert monitoring"""
    await alert_system.stop_monitoring()

def get_alert_system() -> SimpleAlertSystem:
    """Get alert system instance"""
    return alert_system
