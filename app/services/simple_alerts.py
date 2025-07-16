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
    """In-memory alert system with Redis caching"""
    
    def __init__(self):
        self.alerts: Dict[str, SimpleAlert] = {}
        self.running = False
        self.check_interval = 20
        self.price_cache: Dict[str, float] = {}
        
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
        """Create a new alert"""
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
        return alert.id
    
    def get_alert(self, alert_id: str) -> Optional[SimpleAlert]:
        """Get alert by ID"""
        return self.alerts.get(alert_id)
    
    def get_active_alerts(self) -> List[SimpleAlert]:
        """Get all active alerts"""
        return [alert for alert in self.alerts.values() if not alert.triggered]
    
    def delete_alert(self, alert_id: str):
        """Delete alert"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            
            # Remove from Redis
            if self.redis_client:
                try:
                    self.redis_client.delete(f"alert:{alert_id}")
                    self.redis_client.srem("active_alerts", alert_id)
                except Exception:
                    pass
            
            logger.info(f"🗑️ Alert deleted: {alert_id}")
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        try:
            data = await candles(symbol, limit=1)
            if data is not None and not data.empty and len(data) > 0:
                return float(data.iloc[-1]["close"])
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
        return None
    
    async def check_alert(self, alert: SimpleAlert, current_price: float) -> bool:
        """Check if alert should trigger"""
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
    
    def create_alert_message(self, alert: SimpleAlert, current_price: float) -> str:
        """Create formatted alert message"""
        symbol = alert.symbol
        target = alert.target_price
        
        if alert.alert_type == AlertType.PRICE_ABOVE:
            return f"""
🚀 **PRICE ALERT** 🚀

{symbol}: ${current_price:,.2f}
Target: ${target:,.2f}
Status: 📈 ABOVE TARGET

Time: {datetime.now().strftime('%H:%M:%S')}

{alert.description}
"""
        
        elif alert.alert_type == AlertType.PRICE_BELOW:
            return f"""
📉 **PRICE ALERT** 📉

{symbol}: ${current_price:,.2f}
Target: ${target:,.2f}
Status: 📉 BELOW TARGET

Time: {datetime.now().strftime('%H:%M:%S')}

{alert.description}
"""
        
        elif alert.alert_type == AlertType.BREAKOUT:
            return f"""
🚀 **BREAKOUT ALERT** 🚀

{symbol}: ${current_price:,.2f}
Level: ${target:,.2f}
Status: ⚡ BREAKOUT

Time: {datetime.now().strftime('%H:%M:%S')}

{alert.description}
"""
        
        return f"Alert: {symbol} @ ${current_price:,.2f}"
    
    async def start_monitoring(self):
        """Start price monitoring"""
        if self.running:
            return
        
        self.running = True
        
        # Log system status
        redis_status = "✅ Connected" if self.redis_client else "❌ Not available"
        telegram_status = "✅ Configured" if (settings.TG_BOT_TOKEN and settings.TG_CHAT_ID) else "❌ Not configured"
        
        logger.info(f"🚀 Simple Alert System started")
        logger.info(f"   Redis: {redis_status}")
        logger.info(f"   Telegram: {telegram_status}")
        logger.info(f"   Check interval: {self.check_interval} seconds")
        
        while self.running:
            try:
                alerts = self.get_active_alerts()
                
                if alerts:
                    logger.info(f"🔍 Checking {len(alerts)} active alerts")
                    
                    # Group by symbol
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
                                logger.info(f"📊 {symbol}: ${current_price:.2f} (checking {len(alert_list)} alerts)")
                                self.price_cache[symbol] = current_price
                                
                                for alert in alert_list:
                                    try:
                                        if await self.check_alert(alert, current_price):
                                            logger.info(f"🚨 Alert triggered: {alert.id} for {symbol}")
                                    except Exception as e:
                                        logger.error(f"❌ Error checking alert {alert.id}: {e}")
                            else:
                                logger.warning(f"⚠️ Could not get price for {symbol}")
                        except Exception as e:
                            logger.error(f"❌ Error processing symbol {symbol}: {e}")
                else:
                    # Only log occasionally when no alerts
                    if hasattr(self, '_last_no_alerts_log'):
                        if (datetime.now() - self._last_no_alerts_log).total_seconds() > 300:  # 5 minutes
                            logger.info("💤 No active alerts to check")
                            self._last_no_alerts_log = datetime.now()
                    else:
                        logger.info("💤 No active alerts to check")
                        self._last_no_alerts_log = datetime.now()
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(30)
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        logger.info("⏹️ Alert monitoring stopped")
    
    def get_stats(self) -> Dict:
        """Get alert statistics"""
        active_alerts = self.get_active_alerts()
        return {
            "total_active": len(active_alerts),
            "by_symbol": {},
            "price_cache": self.price_cache
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
