from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.telegram_bot import send
from ..core.settings import settings

router = APIRouter(prefix="/telegram", tags=["telegram"])

class TelegramMessage(BaseModel):
    message: str
    analysis_type: str = "general"
    symbol: str = ""
    signal: str = ""
    confidence: int = 0
    entry_price: float = 0
    target_price: float = 0
    stop_loss: float = 0

class TradingSignal(BaseModel):
    symbol: str
    signal: str  # BUY, SELL, HOLD
    confidence: int  # 0-100
    current_price: float
    entry_price: float
    target_1: float
    target_2: float
    stop_loss: float
    risk_reward: float
    analysis: str
    timestamp: str

class PriceAlert(BaseModel):
    symbol: str
    current_price: float
    alert_type: str  # "BREAKOUT", "SUPPORT", "RESISTANCE", "RSI_EXTREME", "PRICE_CHANGE"
    details: str = ""
    change_percentage: float = 0.0

@router.post("/send", summary="Send message to Telegram")
async def send_message(message: TelegramMessage):
    """
    Send a general message to the configured Telegram chat.
    """
    if not (settings.TG_BOT_TOKEN and settings.TG_CHAT_ID):
        raise HTTPException(status_code=400, detail="Telegram bot not configured")
    
    try:
        await send(message.message)
        return {"success": True, "message": "Message sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@router.post("/signal", summary="Send trading signal to Telegram")
async def send_trading_signal(signal: TradingSignal):
    """
    Send a formatted trading signal to Telegram.
    """
    if not (settings.TG_BOT_TOKEN and settings.TG_CHAT_ID):
        raise HTTPException(status_code=400, detail="Telegram bot not configured")
    
    # Format the trading signal message
    signal_message = f"""
🚨 **TRADING SIGNAL** 🚨

**Symbol**: {signal.symbol}
**Signal**: {signal.signal}
**Confidence**: {signal.confidence}%
**Current Price**: ${signal.current_price:,.2f}

📊 **Trading Plan**:
• Entry: ${signal.entry_price:,.2f}
• Target 1: ${signal.target_1:,.2f}
• Target 2: ${signal.target_2:,.2f}
• Stop Loss: ${signal.stop_loss:,.2f}
• Risk/Reward: 1:{signal.risk_reward:.1f}

📈 **Analysis**:
{signal.analysis}

⏰ **Time**: {signal.timestamp}

⚠️ **Risk Warning**: Trading involves risk. Always manage your position size appropriately.
"""
    
    try:
        await send(signal_message)
        return {"success": True, "message": "Trading signal sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send signal: {str(e)}")

@router.post("/alert", summary="Send price alert to Telegram")
async def send_price_alert(alert: PriceAlert):
    """
    Send a price alert to Telegram.
    """
    if not (settings.TG_BOT_TOKEN and settings.TG_CHAT_ID):
        raise HTTPException(status_code=400, detail="Telegram bot not configured")
    
    # Format change percentage if provided
    change_text = ""
    if alert.change_percentage != 0.0:
        direction = "📈" if alert.change_percentage > 0 else "📉"
        change_text = f"\n**Price Change**: {direction} {alert.change_percentage:+.2f}%"
    
    alert_message = f"""
🔔 **PRICE ALERT** 🔔

**{alert.symbol}**: ${alert.current_price:,.2f}
**Alert Type**: {alert.alert_type}{change_text}

{alert.details}

📊 Check your analysis for next steps!
"""
    
    try:
        await send(alert_message)
        return {"success": True, "message": "Price alert sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send alert: {str(e)}")
