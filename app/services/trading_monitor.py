"""
Trading Position Monitor
Advanced position tracking with entry/exit alerts and risk management
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid

from ..core.settings import settings
from ..services.telegram_bot import send
from ..services.universal_stream import get_stream_service, StreamType

logger = logging.getLogger(__name__)

class PositionType(str, Enum):
    LONG = "long"
    SHORT = "short"

class PositionStatus(str, Enum):
    PLANNED = "planned"           # Position geplant, warte auf Entry
    ENTERED = "entered"           # Position eröffnet
    PARTIAL_PROFIT = "partial_profit"  # Teilgewinn realisiert
    CLOSED_PROFIT = "closed_profit"    # Position mit Gewinn geschlossen
    CLOSED_LOSS = "closed_loss"        # Position mit Verlust geschlossen
    STOPPED_OUT = "stopped_out"        # Stop-Loss ausgelöst

class TradingPosition:
    """A trading position with comprehensive monitoring"""
    
    def __init__(
        self,
        symbol: str,
        position_type: PositionType,
        entry_price: float,
        position_size: float,
        stop_loss: Optional[float] = None,
        take_profit_1: Optional[float] = None,
        take_profit_2: Optional[float] = None,
        description: str = ""
    ):
        self.id = str(uuid.uuid4())
        self.symbol = symbol.upper()
        self.position_type = position_type
        self.entry_price = entry_price
        self.position_size = position_size
        self.stop_loss = stop_loss
        self.take_profit_1 = take_profit_1
        self.take_profit_2 = take_profit_2
        self.description = description
        
        self.status = PositionStatus.PLANNED
        self.created_at = datetime.now()
        self.entry_time: Optional[datetime] = None
        self.exit_time: Optional[datetime] = None
        
        self.current_price: Optional[float] = None
        self.unrealized_pnl: float = 0.0
        self.realized_pnl: float = 0.0
        
        # Monitoring
        self.subscription_id: Optional[str] = None
        self.alerts_triggered: List[str] = []
        
        # Partial close tracking
        self.remaining_size: float = position_size
        self.avg_exit_price: float = 0.0

    def calculate_pnl(self, current_price: float) -> Dict[str, float]:
        """Calculate current P&L for the position"""
        if self.status == PositionStatus.PLANNED:
            return {"unrealized": 0.0, "realized": self.realized_pnl, "total": self.realized_pnl}
        
        if self.position_type == PositionType.LONG:
            price_diff = current_price - self.entry_price
        else:  # SHORT
            price_diff = self.entry_price - current_price
        
        unrealized = price_diff * self.remaining_size
        total = unrealized + self.realized_pnl
        
        return {
            "unrealized": unrealized,
            "realized": self.realized_pnl,
            "total": total,
            "percentage": (price_diff / self.entry_price) * 100 if self.entry_price > 0 else 0
        }

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "position_type": self.position_type.value,
            "entry_price": self.entry_price,
            "position_size": self.position_size,
            "remaining_size": self.remaining_size,
            "stop_loss": self.stop_loss,
            "take_profit_1": self.take_profit_1,
            "take_profit_2": self.take_profit_2,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "current_price": self.current_price,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "alerts_triggered": self.alerts_triggered
        }

class TradingPositionMonitor:
    """Monitor trading positions with real-time alerts"""
    
    def __init__(self):
        self.positions: Dict[str, TradingPosition] = {}
        self.running = False
        
        # Redis for persistence
        self.redis_client = None
        try:
            import redis
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Trading Monitor: Redis available")
        except Exception as e:
            logger.info(f"ℹ️ Trading Monitor: Redis not available: {e}")

    async def create_position(
        self,
        symbol: str,
        position_type: PositionType,
        entry_price: float,
        position_size: float,
        stop_loss: Optional[float] = None,
        take_profit_1: Optional[float] = None,
        take_profit_2: Optional[float] = None,
        description: str = ""
    ) -> str:
        """Create a new trading position to monitor"""
        
        position = TradingPosition(
            symbol, position_type, entry_price, position_size,
            stop_loss, take_profit_1, take_profit_2, description
        )
        
        self.positions[position.id] = position
        
        # Save to Redis
        await self._save_position(position)
        
        # Start monitoring
        await self._start_position_monitoring(position)
        
        logger.info(f"📈 Created {position_type.value} position: {symbol} @ ${entry_price}")
        
        # Send Telegram notification
        await self._send_position_notification(position, "CREATED")
        
        return position.id

    async def _start_position_monitoring(self, position: TradingPosition):
        """Start monitoring a position via universal stream"""
        try:
            stream_service = get_stream_service()
            
            async def position_callback(subscription, price_data):
                await self._handle_position_update(position, price_data)
            
            subscription_id = await stream_service.subscribe(
                symbol=position.symbol,
                stream_type=StreamType.TRADING_POSITION,
                callback=position_callback,
                interval=5,
                metadata={
                    "position_id": position.id,
                    "position_type": position.position_type.value,
                    "entry_price": position.entry_price
                }
            )
            
            position.subscription_id = subscription_id
            logger.info(f"📡 Started monitoring position {position.id} for {position.symbol}")
            
        except Exception as e:
            logger.error(f"❌ Failed to start monitoring position {position.id}: {e}")

    async def _handle_position_update(self, position: TradingPosition, price_data: Dict):
        """Handle price update for a position"""
        try:
            current_price = price_data["price"]
            position.current_price = current_price
            
            # Calculate P&L
            pnl = position.calculate_pnl(current_price)
            position.unrealized_pnl = pnl["unrealized"]
            
            # Check for alerts
            await self._check_position_alerts(position, current_price, price_data)
            
            # Save updated position
            await self._save_position(position)
            
        except Exception as e:
            logger.error(f"❌ Error handling position update for {position.id}: {e}")

    async def _check_position_alerts(self, position: TradingPosition, current_price: float, price_data: Dict):
        """Check if any alerts should trigger for this position"""
        
        # Entry alert (if position is planned)
        if position.status == PositionStatus.PLANNED:
            await self._check_entry_alert(position, current_price, price_data)
        
        # Exit alerts (if position is entered)
        elif position.status == PositionStatus.ENTERED:
            await self._check_exit_alerts(position, current_price, price_data)

    async def _check_entry_alert(self, position: TradingPosition, current_price: float, price_data: Dict):
        """Check entry conditions for planned position"""
        entry_triggered = False
        
        if position.position_type == PositionType.LONG:
            # For long: trigger when price reaches or goes below entry
            if current_price <= position.entry_price:
                entry_triggered = True
        else:  # SHORT
            # For short: trigger when price reaches or goes above entry
            if current_price >= position.entry_price:
                entry_triggered = True
        
        if entry_triggered and "entry" not in position.alerts_triggered:
            position.status = PositionStatus.ENTERED
            position.entry_time = datetime.now()
            position.alerts_triggered.append("entry")
            
            await self._send_position_notification(position, "ENTRY", current_price, price_data)
            logger.info(f"🎯 Entry triggered for position {position.id}: {position.symbol} @ ${current_price}")

    async def _check_exit_alerts(self, position: TradingPosition, current_price: float, price_data: Dict):
        """Check exit conditions for entered position"""
        
        # Stop Loss check
        if position.stop_loss and "stop_loss" not in position.alerts_triggered:
            stop_triggered = False
            
            if position.position_type == PositionType.LONG:
                if current_price <= position.stop_loss:
                    stop_triggered = True
            else:  # SHORT
                if current_price >= position.stop_loss:
                    stop_triggered = True
            
            if stop_triggered:
                position.status = PositionStatus.STOPPED_OUT
                position.exit_time = datetime.now()
                position.alerts_triggered.append("stop_loss")
                
                # Calculate final P&L
                pnl = position.calculate_pnl(current_price)
                position.realized_pnl = pnl["total"]
                position.remaining_size = 0
                
                await self._send_position_notification(position, "STOP_LOSS", current_price, price_data)
                await self._stop_position_monitoring(position)
                return
        
        # Take Profit 1 check
        if position.take_profit_1 and "take_profit_1" not in position.alerts_triggered:
            tp1_triggered = False
            
            if position.position_type == PositionType.LONG:
                if current_price >= position.take_profit_1:
                    tp1_triggered = True
            else:  # SHORT
                if current_price <= position.take_profit_1:
                    tp1_triggered = True
            
            if tp1_triggered:
                position.alerts_triggered.append("take_profit_1")
                await self._send_position_notification(position, "TAKE_PROFIT_1", current_price, price_data)
        
        # Take Profit 2 check
        if position.take_profit_2 and "take_profit_2" not in position.alerts_triggered:
            tp2_triggered = False
            
            if position.position_type == PositionType.LONG:
                if current_price >= position.take_profit_2:
                    tp2_triggered = True
            else:  # SHORT
                if current_price <= position.take_profit_2:
                    tp2_triggered = True
            
            if tp2_triggered:
                position.alerts_triggered.append("take_profit_2")
                await self._send_position_notification(position, "TAKE_PROFIT_2", current_price, price_data)

    async def _send_position_notification(self, position: TradingPosition, alert_type: str, current_price: Optional[float] = None, price_data: Optional[Dict] = None):
        """Send Telegram notification for position events"""
        try:
            symbol = position.symbol
            pos_type = position.position_type.value.upper()
            
            if alert_type == "CREATED":
                message = f"""🎯 **NEUE POSITION ERSTELLT** 🎯

**{symbol}** - {pos_type}
📊 Entry: ${position.entry_price:,.2f}
📏 Size: {position.position_size:,.4f}
🛑 Stop Loss: ${position.stop_loss:,.2f}
💰 Take Profit 1: ${position.take_profit_1:,.2f}
💰 Take Profit 2: ${position.take_profit_2:,.2f}

📝 {position.description}

🔔 Monitoring gestartet!"""

            elif alert_type == "ENTRY":
                if current_price is not None:
                    pnl = position.calculate_pnl(current_price)
                    message = f"""🎯 **ENTRY SIGNAL** 🎯

**{symbol}** - {pos_type} POSITION
📊 Entry Price: ${position.entry_price:,.2f}
💰 Current: ${current_price:,.2f}
📈 P&L: ${pnl['total']:,.2f} ({pnl['percentage']:+.2f}%)

⏰ Zeit für Einstieg!"""
                else:
                    message = f"🎯 Entry Signal for {symbol} - {pos_type}"

            elif alert_type == "STOP_LOSS":
                if current_price is not None:
                    pnl = position.calculate_pnl(current_price)
                    message = f"""🛑 **STOP LOSS TRIGGERED** 🛑

**{symbol}** - {pos_type}
📊 Entry: ${position.entry_price:,.2f}
🛑 Stop: ${position.stop_loss:,.2f}
💰 Current: ${current_price:,.2f}
📉 Final P&L: ${pnl['total']:,.2f} ({pnl['percentage']:+.2f}%)

Position geschlossen!"""
                else:
                    message = f"🛑 Stop Loss triggered for {symbol}"

            elif alert_type == "TAKE_PROFIT_1":
                if current_price is not None:
                    pnl = position.calculate_pnl(current_price)
                    message = f"""💰 **TAKE PROFIT 1 REACHED** 💰

**{symbol}** - {pos_type}
📊 Entry: ${position.entry_price:,.2f}
🎯 TP1: ${position.take_profit_1:,.2f}
💰 Current: ${current_price:,.2f}
📈 P&L: ${pnl['total']:,.2f} ({pnl['percentage']:+.2f}%)

Zeit für Teilgewinn!"""
                else:
                    message = f"💰 Take Profit 1 reached for {symbol}"

            elif alert_type == "TAKE_PROFIT_2":
                if current_price is not None:
                    pnl = position.calculate_pnl(current_price)
                    message = f"""🚀 **TAKE PROFIT 2 REACHED** 🚀

**{symbol}** - {pos_type}
📊 Entry: ${position.entry_price:,.2f}
🎯 TP2: ${position.take_profit_2:,.2f}
💰 Current: ${current_price:,.2f}
📈 P&L: ${pnl['total']:,.2f} ({pnl['percentage']:+.2f}%)

Vollständiger Gewinn erreicht!"""
                else:
                    message = f"🚀 Take Profit 2 reached for {symbol}"

            else:
                message = f"Trading Alert: {alert_type} for {symbol}"

            await send(message)
            
        except Exception as e:
            logger.error(f"❌ Failed to send position notification: {e}")

    async def _save_position(self, position: TradingPosition):
        """Save position to Redis"""
        if self.redis_client:
            try:
                self.redis_client.set(
                    f"trading_position:{position.id}", 
                    json.dumps(position.to_dict())
                )
                self.redis_client.sadd("active_trading_positions", position.id)
            except Exception as e:
                logger.warning(f"Failed to save position to Redis: {e}")

    async def _stop_position_monitoring(self, position: TradingPosition):
        """Stop monitoring a position"""
        if position.subscription_id:
            try:
                stream_service = get_stream_service()
                await stream_service.unsubscribe(position.subscription_id)
                position.subscription_id = None
                logger.info(f"📴 Stopped monitoring position {position.id}")
            except Exception as e:
                logger.error(f"❌ Failed to stop monitoring position {position.id}: {e}")

    async def close_position(self, position_id: str, close_price: float, partial_size: Optional[float] = None) -> bool:
        """Manually close a position"""
        if position_id not in self.positions:
            return False
        
        position = self.positions[position_id]
        
        if partial_size:
            # Partial close
            if partial_size >= position.remaining_size:
                partial_size = position.remaining_size
            
            # Calculate partial P&L
            if position.position_type == PositionType.LONG:
                price_diff = close_price - position.entry_price
            else:
                price_diff = position.entry_price - close_price
            
            partial_pnl = price_diff * partial_size
            position.realized_pnl += partial_pnl
            position.remaining_size -= partial_size
            
            if position.remaining_size <= 0:
                position.status = PositionStatus.CLOSED_PROFIT if partial_pnl > 0 else PositionStatus.CLOSED_LOSS
                position.exit_time = datetime.now()
                await self._stop_position_monitoring(position)
            else:
                position.status = PositionStatus.PARTIAL_PROFIT
        
        else:
            # Full close
            pnl = position.calculate_pnl(close_price)
            position.realized_pnl = pnl["total"]
            position.remaining_size = 0
            position.status = PositionStatus.CLOSED_PROFIT if pnl["total"] > 0 else PositionStatus.CLOSED_LOSS
            position.exit_time = datetime.now()
            await self._stop_position_monitoring(position)
        
        await self._save_position(position)
        await self._send_position_notification(position, "MANUAL_CLOSE", close_price)
        
        return True

    def get_active_positions(self) -> List[TradingPosition]:
        """Get all active positions"""
        return [
            pos for pos in self.positions.values() 
            if pos.status in [PositionStatus.PLANNED, PositionStatus.ENTERED, PositionStatus.PARTIAL_PROFIT]
        ]

    def get_position_stats(self) -> Dict:
        """Get position statistics"""
        active_positions = self.get_active_positions()
        
        total_unrealized = sum(pos.unrealized_pnl for pos in active_positions)
        total_realized = sum(pos.realized_pnl for pos in self.positions.values())
        
        return {
            "total_positions": len(self.positions),
            "active_positions": len(active_positions),
            "total_unrealized_pnl": total_unrealized,
            "total_realized_pnl": total_realized,
            "symbols_traded": list(set(pos.symbol for pos in self.positions.values()))
        }

# Global instance
trading_monitor = TradingPositionMonitor()

def get_trading_monitor() -> TradingPositionMonitor:
    """Get the trading monitor instance"""
    return trading_monitor
