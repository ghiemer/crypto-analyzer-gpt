from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services.telegram_bot import (
    send, send_with_buttons, answer_callback_query, edit_message,
    set_webhook, get_webhook_info, delete_webhook, get_updates
)
from ..services.simple_alerts import get_alert_system
from ..core.settings import settings
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

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

class TelegramUpdate(BaseModel):
    update_id: int
    message: dict = {}
    callback_query: dict = {}

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

@router.post("/webhook", summary="Telegram webhook for bot interactions")
async def telegram_webhook(update: TelegramUpdate):
    """
    Handle Telegram webhook updates (messages and callback queries)
    """
    try:
        logger.info(f"📨 Received webhook update: {update.update_id}")
        
        # Handle callback query (button press)
        if update.callback_query:
            logger.info(f"🔘 Processing callback query: {update.callback_query.get('data', '')}")
            await handle_callback_query(update.callback_query)
        
        # Handle regular message
        elif update.message:
            message_text = update.message.get("text", "")
            logger.info(f"💬 Processing message: {message_text}")
            await handle_message(update.message)
        
        else:
            logger.warning("⚠️ Unknown update type received")
        
        return {"status": "ok", "update_id": update.update_id}
    
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

async def handle_callback_query(callback_query: dict):
    """Handle button presses from inline keyboard"""
    callback_data = callback_query.get("data", "")
    callback_query_id = callback_query.get("id", "")
    message = callback_query.get("message", {})
    
    alert_system = get_alert_system()
    
    if callback_data == "show_alerts":
        await show_active_alerts(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Aktive Alerts geladen")
        
    elif callback_data == "toggle_monitoring":
        if alert_system.running:
            await alert_system.stop_monitoring()
            status = "❌ Monitoring gestoppt"
        else:
            # Start monitoring in background
            import asyncio
            asyncio.create_task(alert_system.start_monitoring())
            status = "✅ Monitoring gestartet"
        
        await update_control_panel(message.get("message_id"))
        await answer_callback_query(callback_query_id, status)
        
    elif callback_data == "system_status":
        await show_system_status(message.get("message_id"))
        await answer_callback_query(callback_query_id, "System Status geladen")
        
    elif callback_data.startswith("delete_alert_"):
        alert_id = callback_data.replace("delete_alert_", "")
        alert_system.delete_alert(alert_id)
        await show_active_alerts(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Alert gelöscht")
        
    elif callback_data == "refresh_alerts":
        await show_active_alerts(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Alerts aktualisiert")

async def handle_message(message: dict):
    """Handle regular text messages"""
    text = message.get("text", "").lower()
    
    if text.startswith("/start") or text.startswith("/help"):
        await send_help_message()
    elif text.startswith("/alerts"):
        await send_alert_control_panel()
    elif text.startswith("/status"):
        await send_alert_control_panel()
    elif text.startswith("/monitoring"):
        await send_alert_control_panel()

async def send_help_message():
    """Send help message with available commands"""
    help_text = """
🤖 **Crypto Analyzer Bot** 🤖

**Verfügbare Befehle:**
• `/alerts` - Alert-Verwaltung
• `/status` - System-Status
• `/monitoring` - Monitoring ein/aus
• `/help` - Diese Hilfe

**Alert-System:**
Das System überwacht Preise alle 20 Sekunden und sendet automatisch Benachrichtigungen bei Auslösung.

**Dein GPT kann über die API neue Alerts erstellen:**
`POST /gpt-alerts/price-above`
`POST /gpt-alerts/price-below`
`POST /gpt-alerts/breakout`
"""
    await send(help_text)

async def send_alert_control_panel():
    """Send alert control panel with buttons"""
    alert_system = get_alert_system()
    active_alerts = alert_system.get_active_alerts()
    
    text = f"""
📊 **Alert Control Panel** 📊

**Aktive Alerts:** {len(active_alerts)}
**Monitoring:** {'✅ Running' if alert_system.running else '❌ Stopped'}
**Letzte Prüfung:** {datetime.now().strftime('%H:%M:%S')}

Wähle eine Option:
"""
    
    buttons = [
        [
            {"text": "📋 Aktive Alerts", "callback_data": "show_alerts"},
            {"text": "🔄 System Status", "callback_data": "system_status"}
        ],
        [
            {"text": "⚡ Monitoring Ein/Aus", "callback_data": "toggle_monitoring"}
        ]
    ]
    
    await send_with_buttons(text, buttons)

from typing import Optional

# ...existing imports...

async def show_active_alerts(message_id: Optional[int] = None):
    """Show active alerts with delete buttons"""
    alert_system = get_alert_system()
    active_alerts = alert_system.get_active_alerts()
    
    if not active_alerts:
        text = """
📋 **Aktive Alerts** 📋

Keine aktiven Alerts vorhanden.

Dein GPT kann neue Alerts über die API erstellen:
• `/gpt-alerts/price-above`
• `/gpt-alerts/price-below`
• `/gpt-alerts/breakout`
"""
        buttons = [
            [{"text": "🔄 Aktualisieren", "callback_data": "refresh_alerts"}]
        ]
    else:
        text = f"""
📋 **Aktive Alerts** ({len(active_alerts)})

"""
        buttons = []
        
        for alert in active_alerts[:5]:  # Limit to 5 alerts
            # Add alert info to text
            alert_type_emoji = {"price_above": "📈", "price_below": "📉", "breakout": "🚀"}
            emoji = alert_type_emoji.get(alert.alert_type, "📊")
            
            text += f"""
{emoji} **{alert.symbol}**
Type: {alert.alert_type}
Target: ${alert.target_price:,.2f}
Created: {alert.created_at[:10]}
Description: {alert.description[:50]}...

"""
            
            # Add delete button
            buttons.append([
                {"text": f"❌ Delete {alert.symbol}", "callback_data": f"delete_alert_{alert.id}"}
            ])
        
        # Add refresh button
        buttons.append([
            {"text": "🔄 Aktualisieren", "callback_data": "refresh_alerts"}
        ])
    
    if message_id:
        await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})
    else:
        await send_with_buttons(text, buttons)

async def show_system_status(message_id: Optional[int] = None):
    """Show system status"""
    alert_system = get_alert_system()
    stats = alert_system.get_stats()
    
    redis_status = "✅ Connected" if alert_system.redis_client else "❌ Not available"
    telegram_status = "✅ Configured" if (settings.TG_BOT_TOKEN and settings.TG_CHAT_ID) else "❌ Not configured"
    
    text = f"""
🔧 **System Status** 🔧

**Environment:** {settings.ENVIRONMENT}
**Redis:** {redis_status}
**Telegram:** {telegram_status}
**Monitoring:** {'✅ Running' if alert_system.running else '❌ Stopped'}

**Alert Statistics:**
• Aktive Alerts: {stats['total_active']}
• Check Interval: {alert_system.check_interval}s

**Price Cache:**
"""
    
    for symbol, price in stats['price_cache'].items():
        text += f"• {symbol}: ${price:,.2f}\n"
    
    if not stats['price_cache']:
        text += "• Keine Preise gecacht\n"
    
    text += f"\n**Letzte Aktualisierung:** {datetime.now().strftime('%H:%M:%S')}"
    
    buttons = [
        [{"text": "🔄 Aktualisieren", "callback_data": "system_status"}]
    ]
    
    if message_id:
        await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})
    else:
        await send_with_buttons(text, buttons)

async def update_control_panel(message_id: int):
    """Update the control panel with current status"""
    alert_system = get_alert_system()
    active_alerts = alert_system.get_active_alerts()
    
    text = f"""
📊 **Alert Control Panel** 📊

**Aktive Alerts:** {len(active_alerts)}
**Monitoring:** {'✅ Running' if alert_system.running else '❌ Stopped'}
**Letzte Prüfung:** {datetime.now().strftime('%H:%M:%S')}

Wähle eine Option:
"""
    
    buttons = [
        [
            {"text": "📋 Aktive Alerts", "callback_data": "show_alerts"},
            {"text": "🔄 System Status", "callback_data": "system_status"}
        ],
        [
            {"text": "⚡ Monitoring Ein/Aus", "callback_data": "toggle_monitoring"}
        ]
    ]
    
    await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})

@router.post("/setup-bot", summary="Setup Telegram Bot Webhook")
async def setup_telegram_bot():
    """
    Setup Telegram Bot Webhook for interactive buttons
    Call this once to enable interactive bot features
    """
    if not settings.TG_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="TG_BOT_TOKEN not configured")
    
    # Set webhook URL
    webhook_url = f"https://crypto-analyzer-gpt.onrender.com/telegram/webhook"
    
    # Get current webhook info
    webhook_info = await get_webhook_info()
    current_webhook = webhook_info.get("result", {}).get("url", "") if webhook_info else ""
    
    setup_result = {}
    
    if current_webhook == webhook_url:
        setup_result["webhook_status"] = "✅ Already configured"
    else:
        # Set new webhook
        webhook_set = await set_webhook(webhook_url)
        if webhook_set:
            setup_result["webhook_status"] = "✅ Successfully configured"
        else:
            setup_result["webhook_status"] = "❌ Failed to configure"
    
    setup_info = f"""
🤖 **Telegram Bot Setup Complete** 🤖

**Webhook URL:** {webhook_url}
**Status:** {setup_result["webhook_status"]}

**Verfügbare Befehle:**
• `/alerts` - Alert Control Panel
• `/status` - System Status  
• `/help` - Hilfe anzeigen

**Interaktive Features:**
• ✅ Button-basierte Alert-Verwaltung
• ✅ Monitoring ein/ausschalten
• ✅ System-Status Dashboard
• ✅ Alerts direkt löschen

**Teste jetzt:**
Schreibe `/alerts` für das Control Panel!
"""
    
    # Send setup info to telegram
    await send(setup_info)
    
    return {
        "success": True,
        "webhook_url": webhook_url,
        "webhook_status": setup_result["webhook_status"],
        "current_webhook": current_webhook,
        "message": "Bot setup completed"
    }

@router.get("/webhook-info", summary="Get Telegram webhook info")
async def get_webhook_status():
    """Get current webhook configuration"""
    if not settings.TG_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="TG_BOT_TOKEN not configured")
    
    webhook_info = await get_webhook_info()
    
    if webhook_info:
        result = webhook_info.get("result", {})
        return {
            "webhook_url": result.get("url", ""),
            "has_custom_certificate": result.get("has_custom_certificate", False),
            "pending_update_count": result.get("pending_update_count", 0),
            "last_error_date": result.get("last_error_date", 0),
            "last_error_message": result.get("last_error_message", ""),
            "max_connections": result.get("max_connections", 0),
            "allowed_updates": result.get("allowed_updates", [])
        }
    else:
        return {"error": "Failed to get webhook info"}

@router.post("/test-polling", summary="Test Telegram polling mode")
async def test_polling():
    """Test polling mode for development"""
    if not settings.TG_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="TG_BOT_TOKEN not configured")
    
    # Delete webhook first
    await delete_webhook()
    
    # Get recent updates
    updates = await get_updates()
    
    # Process each update
    processed_updates = []
    for update in updates[-5:]:  # Only process last 5 updates
        update_info = {
            "update_id": update.get("update_id"),
            "type": "message" if "message" in update else "callback_query" if "callback_query" in update else "unknown"
        }
        
        # Process the update
        if "message" in update:
            await handle_message(update["message"])
            update_info["message"] = update["message"].get("text", "")
        elif "callback_query" in update:
            await handle_callback_query(update["callback_query"])
            update_info["callback_data"] = update["callback_query"].get("data", "")
        
        processed_updates.append(update_info)
    
    return {
        "success": True,
        "processed_updates": processed_updates,
        "total_updates": len(updates),
        "message": "Polling test completed"
    }
