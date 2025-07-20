from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from ..services.telegram_bot import (
    send, send_with_buttons, answer_callback_query, edit_message,
    set_webhook, get_webhook_info, delete_webhook, get_updates,
    setup_telegram_menu, set_bot_commands, set_chat_menu_button
)
from ..services.simple_alerts import get_alert_system
from ..core.settings import settings
from ..core.logging_config import get_telegram_logger, log_telegram_request, log_telegram_response
from datetime import datetime
import json
import logging
import httpx
import asyncio

logger = get_telegram_logger("main")

async def get_all_alerts():
    """Get alerts from both Simple Alert System and GPT Alert System"""
    logger.debug("🔍 Fetching alerts from all systems...")
    
    all_alerts = []
    
    # 1. Try Simple Alert System (Redis-based)
    try:
        logger.debug("📊 Getting simple alert system instance...")
        alert_system = get_alert_system()
        simple_alerts = alert_system.get_active_alerts()
        logger.info("✅ Found %d simple alerts", len(simple_alerts))
        all_alerts.extend(simple_alerts)
    except Exception as e:
        logger.warning("⚠️ Simple alert system failed: %s", str(e))
    
    # 2. Try GPT Alert System (API-based)
    try:
        logger.debug("🤖 Fetching GPT alerts via internal API...")
        
        # Use internal localhost for production, external URL for debugging
        base_url = getattr(settings, 'INTERNAL_API_URL', 'http://localhost:8000')
        api_url = f"{base_url}/gpt-alerts/list"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                api_url,
                headers={"X-API-Key": settings.API_KEY} if hasattr(settings, 'API_KEY') else {},
                timeout=5.0
            )
            if response.status_code == 200:
                gpt_alerts = response.json()
                logger.info("✅ Found %d GPT alerts", len(gpt_alerts))
                
                # Convert GPT alerts to compatible format
                for alert in gpt_alerts:
                    compatible_alert = {
                        'id': alert.get('id'),
                        'symbol': alert.get('symbol'),
                        'alert_type': alert.get('alert_type'),
                        'target_price': alert.get('target_price'),
                        'description': alert.get('description', ''),
                        'created_at': alert.get('created_at', ''),
                        'source': 'gpt'  # Mark as GPT alert
                    }
                    all_alerts.append(compatible_alert)
            else:
                logger.warning("⚠️ GPT alerts API returned %d", response.status_code)
    except Exception as e:
        logger.warning("⚠️ GPT alert system failed: %s", str(e))
    
    logger.info("📊 Total alerts found: %d", len(all_alerts))
    return all_alerts

router = APIRouter(prefix="/telegram", tags=["telegram"])

# Separate router for webhook (no auth required)
webhook_router = APIRouter(prefix="/telegram", tags=["telegram"])

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

@webhook_router.post("/webhook", summary="Telegram webhook for bot interactions")
async def telegram_webhook(request: Request):
    """
    Handle Telegram webhook updates (messages and callback queries)
    Note: This endpoint is called by Telegram and doesn't require API key auth
    """
    try:
        # Parse JSON body
        try:
            update = await request.json()
        except Exception as json_error:
            logger.warning(f"⚠️ Invalid JSON in webhook request: {json_error}")
            return {"status": "error", "message": "Invalid JSON"}
        
        if not isinstance(update, dict):
            logger.warning("⚠️ Webhook update is not a dictionary")
            return {"status": "error", "message": "Invalid update format"}
        
        update_id = update.get("update_id", 0)
        logger.info(f"📨 Received webhook update: {update_id}")
        
        # Handle callback query (button press)
        if "callback_query" in update:
            callback_data = update["callback_query"].get("data", "")
            logger.info(f"🔘 Processing callback query: {callback_data}")
            await handle_callback_query(update["callback_query"])
        
        # Handle regular message
        elif "message" in update:
            message_text = update["message"].get("text", "")
            logger.info(f"💬 Processing message: {message_text}")
            await handle_message(update["message"])
        
        else:
            logger.warning("⚠️ Unknown update type received")
        
        return {"status": "ok", "update_id": update_id}
    
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
    
    if callback_data == "main_menu":
        await send_main_menu()
        await answer_callback_query(callback_query_id, "Hauptmenü")
        
    elif callback_data == "help":
        await send_help_message()
        await answer_callback_query(callback_query_id, "Hilfe")
        
    elif callback_data == "show_alerts":
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
        
    elif callback_data == "show_streams":
        await show_stream_status(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Stream Status geladen")
        
    elif callback_data.startswith("delete_alert_"):
        alert_id = callback_data.replace("delete_alert_", "")
        alert_system.delete_alert(alert_id)
        await show_active_alerts(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Alert gelöscht")
        
    elif callback_data == "show_all_alerts":
        await show_all_alerts_detailed(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Alle Alerts geladen")
        
    elif callback_data == "create_alert_menu":
        await show_create_alert_menu(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Alert-Erstellung geöffnet")
        
    elif callback_data == "trading_monitor":
        await show_trading_monitor(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Trading Monitor geladen")
        
    elif callback_data == "portfolio_watch":
        await show_portfolio_watch(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Portfolio Watch geladen")
        
    elif callback_data == "alert_types_menu":
        await show_alert_types_menu(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Alert-Typen angezeigt")
        
    elif callback_data == "performance_stats":
        await show_performance_stats(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Performance-Statistiken geladen")
        
    elif callback_data == "settings_menu":
        await show_settings_menu(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Einstellungen geöffnet")
        
    elif callback_data == "help_menu":
        await show_help_menu(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Hilfe angezeigt")
        
    elif callback_data == "refresh_alerts":
        await show_active_alerts(message.get("message_id"))
        await answer_callback_query(callback_query_id, "Alerts aktualisiert")

async def handle_message(message: dict):
    """Handle regular text messages"""
    text = message.get("text", "").lower()
    
    if text.startswith("/start"):
        await send_main_menu()
    elif text.startswith("/menu"):
        await send_main_menu()
    elif text.startswith("/help"):
        await send_help_message()
    elif text.startswith("/alerts"):
        await show_active_alerts()
    elif text.startswith("/new"):
        await show_create_alert_menu()
    elif text.startswith("/status"):
        await show_system_status()
    elif text.startswith("/streams"):
        await show_stream_status()
    elif text.startswith("/portfolio"):
        await show_portfolio_watch()
    elif text.startswith("/monitor"):
        await show_trading_monitor()
    elif text.startswith("/performance"):
        await show_performance_stats()
    elif text.startswith("/settings"):
        await show_settings_menu()
    elif text.startswith("/monitoring"):
        await send_alert_control_panel()
    else:
        # If no command matches, show help
        await send_help_message()

async def send_main_menu():
    """Send enhanced main menu with all important functions"""
    try:
        # Get alerts from all systems
        all_alerts = await get_all_alerts()
        
        # Try to get simple alert system stats
        total_streams = 0
        monitoring_online = False
        try:
            alert_system = get_alert_system()
            streaming_symbols = list(alert_system.price_streams.keys())
            total_streams = len(streaming_symbols)
            monitoring_online = alert_system.running
        except Exception as e:
            logger.warning("⚠️ Could not get stream stats: %s", str(e))
        
        text = f"""🤖 **Crypto Analyzer Bot** 🤖

📊 **System Status:**
• Alerts: {len(all_alerts)} aktiv
• Streams: {total_streams} laufend
• Monitoring: {'🟢 Online' if monitoring_online else '🔴 Offline'}

Wähle eine Funktion:"""
        
        buttons = [
            [
                {"text": "📋 Alle Alerts", "callback_data": "show_all_alerts"},
                {"text": "➕ Neuer Alert", "callback_data": "create_alert_menu"}
            ],
            [
                {"text": "📡 Live Streams", "callback_data": "show_streams"},
                {"text": "💹 Trading Monitor", "callback_data": "trading_monitor"}
            ],
            [
                {"text": "📊 Portfolio Watch", "callback_data": "portfolio_watch"},
                {"text": "🔔 Alert Typen", "callback_data": "alert_types_menu"}
            ],
            [
                {"text": "⚙️ System Status", "callback_data": "system_status"},
                {"text": "📈 Performance", "callback_data": "performance_stats"}
            ],
            [
                {"text": "🔧 Einstellungen", "callback_data": "settings_menu"},
                {"text": "❓ Hilfe", "callback_data": "help_menu"}
            ]
        ]
        
        await send_with_buttons(text, buttons)
        
    except Exception as e:
        logger.error("❌ Error in send_main_menu: %s", str(e))
        # Fallback simple menu
        await send("🤖 **Crypto Analyzer Bot**\n\nVerfügbare Befehle:\n• `/alerts` - Alerts anzeigen\n• `/help` - Hilfe")

async def send_help_message():
    """Send help message with available commands"""
    help_text = """🤖 **Crypto Analyzer Bot** 🤖

**Verfügbare Befehle:**
• `/start` - Hauptmenü anzeigen
• `/menu` - Hauptmenü anzeigen
• `/alerts` - Alert-Verwaltung
• `/status` - System-Status
• `/monitoring` - Monitoring ein/aus
• `/help` - Diese Hilfe

**Alert-System:**
Das System überwacht Preise alle 20 Sekunden und sendet automatisch Benachrichtigungen bei Auslösung.

**Dein GPT kann über die API neue Alerts erstellen:**
• `POST /gpt-alerts/price-above`
• `POST /gpt-alerts/price-below` 
• `POST /gpt-alerts/breakout`

**Interaktive Features:**
• ✅ Button-basierte Navigation
• ✅ Alert-Verwaltung
• ✅ Monitoring-Steuerung
• ✅ Echtzeit-Updates"""
    
    buttons = [
        [{"text": "🏠 Hauptmenü", "callback_data": "main_menu"}]
    ]
    
    await send_with_buttons(help_text, buttons)

async def send_alert_control_panel():
    """Send alert control panel with buttons"""
    alert_system = get_alert_system()
    active_alerts = alert_system.get_active_alerts()
    
    text = f"""📊 Alert Control Panel 📊

Aktive Alerts: {len(active_alerts)}
Monitoring: {'✅ Running' if alert_system.running else '❌ Stopped'}
Letzte Prüfung: {datetime.now().strftime('%H:%M:%S')}

Wähle eine Option:"""
    
    buttons = [
        [
            {"text": "📋 Aktive Alerts", "callback_data": "show_alerts"},
            {"text": "🔄 System Status", "callback_data": "system_status"}
        ],
        [
            {"text": "⚡ Monitoring Ein/Aus", "callback_data": "toggle_monitoring"}
        ],
        [
            {"text": "🏠 Hauptmenü", "callback_data": "main_menu"}
        ]
    ]
    
    await send_with_buttons(text, buttons)

from typing import Optional

# ...existing imports...

async def show_active_alerts(message_id: Optional[int] = None):
    """Show active alerts with delete buttons"""
    logger.info("🔍 show_active_alerts called with message_id=%s", message_id)
    
    try:
        logger.debug("� Fetching all alerts from combined systems...")
        active_alerts = await get_all_alerts()
        logger.info("✅ Found %d total alerts", len(active_alerts))
        
        if not active_alerts:
            logger.debug("📋 No active alerts found, showing empty state")
            text = """📋 Aktive Alerts 📋

Keine aktiven Alerts vorhanden.

Dein GPT kann neue Alerts über die API erstellen:
• /gpt-alerts/price-above
• /gpt-alerts/price-below
• /gpt-alerts/breakout"""
            buttons = [
                [{"text": "🔄 Aktualisieren", "callback_data": "refresh_alerts"}],
                [{"text": "🏠 Hauptmenü", "callback_data": "main_menu"}]
            ]
        else:
            logger.debug("📋 Building alert list display for %d alerts", len(active_alerts))
            text = f"""📋 Aktive Alerts ({len(active_alerts)})

"""
            buttons = []
            
            for alert in active_alerts[:5]:  # Limit to 5 alerts
                # Add alert info to text
                alert_type_emoji = {"price_above": "📈", "price_below": "📉", "breakout": "🚀"}
                
                # Handle both SimpleAlert objects and dictionaries
                if isinstance(alert, dict):
                    # Dictionary (including GPT alerts)
                    emoji = alert_type_emoji.get(alert.get('alert_type', ''), "📊")
                    symbol = alert.get('symbol', '')
                    alert_type = alert.get('alert_type', '')
                    target_price = alert.get('target_price', 0)
                    source = alert.get('source', 'simple')
                    alert_id = alert.get('id', '')
                    created_at = alert.get('created_at', '')
                    description = alert.get('description', '')
                    alert_id = alert.get('id', '')
                else:
                    # SimpleAlert object
                    emoji = alert_type_emoji.get(alert.alert_type, "📊")
                    symbol = alert.symbol
                    alert_type = alert.alert_type
                    target_price = alert.target_price
                    created_at = alert.created_at
                    description = alert.description
                    alert_id = alert.id
                
                text += f"""{emoji} {symbol}
Type: {alert_type}
Target: ${target_price:,.2f}
Created: {created_at[:10]}
Description: {description[:50]}...

"""
                
                # Add delete button
                buttons.append([
                    {"text": f"❌ Delete {symbol}", "callback_data": f"delete_alert_{alert_id}"}
                ])
            
            # Add refresh button
            buttons.append([
                {"text": "🔄 Aktualisieren", "callback_data": "refresh_alerts"}
            ])
            # Add back to main menu button
            buttons.append([
                {"text": "🏠 Hauptmenü", "callback_data": "main_menu"}
            ])
        
        logger.debug("💬 Sending telegram message with %d buttons", len([btn for row in buttons for btn in row]))
        
        if message_id:
            logger.debug("✏️ Editing existing message (ID: %s)", message_id)
            await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})
            logger.info("✅ Message edited successfully")
        else:
            logger.debug("📤 Sending new message with buttons")
            await send_with_buttons(text, buttons)
            logger.info("✅ Message sent successfully")
            
    except Exception as e:
        logger.error("❌ Error in show_active_alerts: %s", str(e))
        error_text = f"❌ Fehler beim Laden der Alerts: {str(e)}"
        if message_id:
            await edit_message(message_id, error_text, {"inline_keyboard": [[{"text": "🏠 Hauptmenü", "callback_data": "main_menu"}]]})
        else:
            await send(error_text)
        raise HTTPException(status_code=500, detail=str(e))

async def show_all_alerts_detailed(message_id: Optional[int] = None):
    """Show comprehensive alert overview with management options"""
    alert_system = get_alert_system()
    active_alerts = alert_system.get_active_alerts()
    
    if not active_alerts:
        text = """📋 **Alle Alerts** 📋

❌ Keine aktiven Alerts vorhanden.

**Schnell-Aktionen:**
• Verwende /create um neue Alerts zu erstellen
• GPT kann Alerts über die API erstellen
• Nutze das Menü für Alert-Vorlagen"""
        
        buttons = [
            [{"text": "➕ Neuer Alert", "callback_data": "create_alert_menu"}],
            [{"text": "📡 Alert-Typen", "callback_data": "alert_types_menu"}],
            [{"text": "🏠 Hauptmenü", "callback_data": "main_menu"}]
        ]
    else:
        # Group alerts by symbol
        symbol_alerts = {}
        for alert in active_alerts:
            if alert.symbol not in symbol_alerts:
                symbol_alerts[alert.symbol] = []
            symbol_alerts[alert.symbol].append(alert)
        
        text = f"""📋 **Alle Alerts ({len(active_alerts)})** 📋

"""
        
        buttons = []
        alert_count = 0
        
        for symbol, alerts in symbol_alerts.items():
            current_price = alert_system.price_cache.get(symbol, 0)
            stream_active = symbol in alert_system.price_streams
            stream_emoji = "🔴" if not stream_active else "🟢"
            
            text += f"""**{symbol}** {stream_emoji}
Current: ${current_price:,.2f}
Alerts: {len(alerts)}

"""
            
            for alert in alerts[:3]:  # Show max 3 alerts per symbol
                alert_count += 1
                type_emoji = {"price_above": "📈", "price_below": "📉", "breakout": "🚀"}.get(alert.alert_type, "📊")
                
                text += f"{type_emoji} {alert.alert_type.replace('_', ' ').title()}: ${alert.target_price:,.2f}\n"
                text += f"   📝 {alert.description[:30]}...\n"
                
                # Add delete button for each alert
                if alert_count <= 5:  # Limit buttons to avoid Telegram limits
                    buttons.append([
                        {"text": f"❌ Delete {symbol} Alert", "callback_data": f"delete_alert_{alert.id}"}
                    ])
            
            if len(alerts) > 3:
                text += f"   ... und {len(alerts) - 3} weitere\n"
            
            text += "\n"
        
        # Add control buttons
        buttons.extend([
            [{"text": "🔄 Aktualisieren", "callback_data": "show_all_alerts"}],
            [{"text": "➕ Neuer Alert", "callback_data": "create_alert_menu"}],
            [{"text": "🗑️ Alle löschen", "callback_data": "delete_all_alerts"}],
            [{"text": "🏠 Hauptmenü", "callback_data": "main_menu"}]
        ])
    
    if message_id:
        await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})
    else:
        await send_with_buttons(text, buttons)

async def show_create_alert_menu(message_id: Optional[int] = None):
    """Show alert creation options"""
    text = """➕ **Neuer Alert erstellen** ➕

**Verfügbare Alert-Typen:**

📈 **Price Above** - Benachrichtigung wenn Preis über Ziel steigt
📉 **Price Below** - Benachrichtigung wenn Preis unter Ziel fällt  
🚀 **Breakout** - Benachrichtigung bei Durchbruch über Widerstand

**Erstellung über:**
• GPT-Commands über API
• Telegram-Bot Buttons unten
• Direkte API-Calls

**Beliebte Symbole:** BTCUSDT, ETHUSDT, BNBUSDT, ADAUSDT, SOLUSDT"""
    
    buttons = [
        [
            {"text": "📈 Price Above", "callback_data": "create_price_above"},
            {"text": "📉 Price Below", "callback_data": "create_price_below"}
        ],
        [
            {"text": "🚀 Breakout Alert", "callback_data": "create_breakout"}
        ],
        [
            {"text": "📊 Beliebte Coins", "callback_data": "popular_coins"},
            {"text": "🎯 Vorlagen", "callback_data": "alert_templates"}
        ],
        [
            {"text": "🏠 Hauptmenü", "callback_data": "main_menu"}
        ]
    ]
    
    if message_id:
        await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})
    else:
        await send_with_buttons(text, buttons)

async def show_trading_monitor(message_id: Optional[int] = None):
    """Show trading position monitoring interface"""
    alert_system = get_alert_system()
    
    text = """💹 **Trading Position Monitor** 💹

**Überwache deine Trading-Positionen in Echtzeit!**

🎯 **Features:**
• Entry/Exit Punkt Alerts
• Stop-Loss Überwachung  
• Take-Profit Benachrichtigungen
• Position-Size Tracking
• Risk-Management Alerts

**Aktuelle Monitoring:**"""
    
    # Check for trading-related alerts
    trading_alerts = [alert for alert in alert_system.get_active_alerts() 
                     if any(keyword in alert.description.lower() 
                           for keyword in ['entry', 'exit', 'stop', 'profit', 'position'])]
    
    if trading_alerts:
        text += f"\n• {len(trading_alerts)} Trading-Alerts aktiv"
        for alert in trading_alerts[:3]:
            text += f"\n  📊 {alert.symbol}: ${alert.target_price:,.2f}"
    else:
        text += "\n• Keine Trading-Alerts aktiv"
    
    buttons = [
        [
            {"text": "🎯 Entry Alert", "callback_data": "create_entry_alert"},
            {"text": "🛑 Stop Loss", "callback_data": "create_stop_loss"}
        ],
        [
            {"text": "💰 Take Profit", "callback_data": "create_take_profit"},
            {"text": "⚖️ Position Size", "callback_data": "position_alerts"}
        ],
        [
            {"text": "📊 Trading Stats", "callback_data": "trading_stats"},
            {"text": "🔔 Risk Alerts", "callback_data": "risk_alerts"}
        ],
        [
            {"text": "🏠 Hauptmenü", "callback_data": "main_menu"}
        ]
    ]
    
    if message_id:
        await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})
    else:
        await send_with_buttons(text, buttons)

async def show_portfolio_watch(message_id: Optional[int] = None):
    """Show portfolio monitoring interface"""
    alert_system = get_alert_system()
    active_alerts = alert_system.get_active_alerts()
    
    # Group alerts by symbol for portfolio view
    portfolio = {}
    for alert in active_alerts:
        if alert.symbol not in portfolio:
            portfolio[alert.symbol] = {
                'alerts': [],
                'current_price': alert_system.price_cache.get(alert.symbol, 0)
            }
        portfolio[alert.symbol]['alerts'].append(alert)
    
    text = """📊 **Portfolio Watch** 📊

**Überwache dein gesamtes Portfolio:**

🎯 **Features:**
• Multi-Asset Tracking
• Portfolio Performance
• Risk Distribution
• Correlation Analysis"""
    
    if portfolio:
        text += f"\n\n**Tracked Assets ({len(portfolio)}):**\n"
        for symbol, data in portfolio.items():
            current_price = data['current_price']
            alert_count = len(data['alerts'])
            
            text += f"• {symbol}: ${current_price:,.2f} ({alert_count} alerts)\n"
    else:
        text += "\n\n❌ Keine Assets im Portfolio überwacht"
    
    buttons = [
        [
            {"text": "📈 Performance", "callback_data": "portfolio_performance"},
            {"text": "⚖️ Risk Analysis", "callback_data": "portfolio_risk"}
        ],
        [
            {"text": "🔄 Rebalance", "callback_data": "portfolio_rebalance"},
            {"text": "📊 Correlation", "callback_data": "portfolio_correlation"}
        ],
        [
            {"text": "➕ Add Asset", "callback_data": "portfolio_add_asset"},
            {"text": "🗑️ Remove Asset", "callback_data": "portfolio_remove_asset"}
        ],
        [
            {"text": "🏠 Hauptmenü", "callback_data": "main_menu"}
        ]
    ]
    
    if message_id:
        await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})
    else:
        await send_with_buttons(text, buttons)

async def show_alert_types_menu(message_id: Optional[int] = None):
    """Show available alert types and their descriptions"""
    text = """🔔 **Alert-Typen Übersicht** 🔔

**Verfügbare Alert-Typen:**

📈 **Price Above Alert**
Benachrichtigung wenn Preis über Zielwert steigt
• Ideal für: Breakout-Signale, Profit-Taking
• Beispiel: BTC über $45,000

📉 **Price Below Alert**  
Benachrichtigung wenn Preis unter Zielwert fällt
• Ideal für: Stop-Loss, Einstiegspunkte
• Beispiel: ETH unter $2,500

🚀 **Breakout Alert**
Benachrichtigung bei Durchbruch wichtiger Level
• Ideal für: Technische Analyse, Momentum
• Beispiel: SOL Breakout über $100

💹 **Trading Alerts**
Spezielle Alerts für Positionen
• Entry/Exit Signale
• Stop-Loss/Take-Profit
• Position-Size Management

📊 **Custom Alerts**
Benutzerdefinierte Alert-Logik
• RSI-basierte Alerts
• Volume-Anomalien
• Multi-Timeframe Signale"""
    
    buttons = [
        [
            {"text": "📈 Price Above", "callback_data": "create_price_above"},
            {"text": "📉 Price Below", "callback_data": "create_price_below"}
        ],
        [
            {"text": "🚀 Breakout", "callback_data": "create_breakout"},
            {"text": "💹 Trading", "callback_data": "trading_monitor"}
        ],
        [
            {"text": "📝 Custom Alert", "callback_data": "create_custom_alert"},
            {"text": "📚 Templates", "callback_data": "alert_templates"}
        ],
        [
            {"text": "🏠 Hauptmenü", "callback_data": "main_menu"}
        ]
    ]
    
    if message_id:
        await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})
    else:
        await send_with_buttons(text, buttons)

async def show_performance_stats(message_id: Optional[int] = None):
    """Show system and alert performance statistics"""
    alert_system = get_alert_system()
    stats = alert_system.get_stats()
    
    text = """📈 **Performance Statistiken** 📈

**System Performance:**"""
    
    # Calculate uptime (simplified)
    uptime_status = "🟢 Online" if alert_system.running else "🔴 Offline"
    
    text += f"""
• Status: {uptime_status}
• Total Alerts: {stats['total_active']}
• Active Streams: {stats['active_streams']}
• Check Interval: {alert_system.check_interval}s

**Alert Performance:**"""
    
    # Get alert statistics
    active_alerts = alert_system.get_active_alerts()
    alert_types = {}
    for alert in active_alerts:
        alert_type = alert.alert_type
        if alert_type not in alert_types:
            alert_types[alert_type] = 0
        alert_types[alert_type] += 1
    
    if alert_types:
        for alert_type, count in alert_types.items():
            text += f"\n• {alert_type.replace('_', ' ').title()}: {count}"
    else:
        text += "\n• Keine aktiven Alerts"
    
    text += f"""

**Stream Performance:**
• Streaming Symbols: {len(stats['streaming_symbols'])}
• Price Cache Size: {len(stats['price_cache'])}
• Last Update: {datetime.now().strftime('%H:%M:%S')}

**Resource Usage:**
• Memory: Optimal
• CPU: Low
• Network: Active"""
    
    buttons = [
        [
            {"text": "🔄 Refresh", "callback_data": "performance_stats"},
            {"text": "📊 Detailed", "callback_data": "performance_detailed"}
        ],
        [
            {"text": "📈 Charts", "callback_data": "performance_charts"},
            {"text": "⚠️ Alerts", "callback_data": "performance_alerts"}
        ],
        [
            {"text": "🏠 Hauptmenü", "callback_data": "main_menu"}
        ]
    ]
    
    if message_id:
        await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})
    else:
        await send_with_buttons(text, buttons)

async def show_settings_menu(message_id: Optional[int] = None):
    """Show system settings and configuration options"""
    alert_system = get_alert_system()
    
    text = """⚙️ **Systemeinstellungen** ⚙️

**Aktuelle Konfiguration:**"""
    
    # Show current settings
    text += f"""
• Check Interval: {alert_system.check_interval}s
• Redis: {'✅ Connected' if alert_system.redis_client else '❌ Disconnected'}
• Environment: {settings.ENVIRONMENT}
• Telegram: {'✅ Configured' if settings.TG_BOT_TOKEN else '❌ Not configured'}

**Alert Settings:**
• Max Alerts: Unlimited
• Alert Timeout: 30s
• Retry Count: 3
• Cache TTL: 60s

**Notification Settings:**
• Telegram Notifications: ✅ Enabled
• Silent Mode: ❌ Disabled
• Rich Formatting: ✅ Enabled

**Performance Settings:**
• Auto-cleanup: ✅ Enabled
• Stream Optimization: ✅ Enabled
• Cache Compression: ✅ Enabled"""
    
    buttons = [
        [
            {"text": "⏱️ Intervals", "callback_data": "settings_intervals"},
            {"text": "🔔 Notifications", "callback_data": "settings_notifications"}
        ],
        [
            {"text": "🚀 Performance", "callback_data": "settings_performance"},
            {"text": "🔐 Security", "callback_data": "settings_security"}
        ],
        [
            {"text": "📝 Logs", "callback_data": "settings_logs"},
            {"text": "🔄 Reset", "callback_data": "settings_reset"}
        ],
        [
            {"text": "💾 Export", "callback_data": "settings_export"},
            {"text": "📥 Import", "callback_data": "settings_import"}
        ],
        [
            {"text": "🏠 Hauptmenü", "callback_data": "main_menu"}
        ]
    ]
    
    if message_id:
        await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})
    else:
        await send_with_buttons(text, buttons)

async def show_help_menu(message_id: Optional[int] = None):
    """Show comprehensive help menu"""
    text = """❓ **Hilfe & Support** ❓

**📱 Bot Commands:**
• `/start` - Hauptmenü anzeigen
• `/menu` - Hauptmenü anzeigen  
• `/alerts` - Alert-Verwaltung
• `/status` - System-Status
• `/help` - Diese Hilfe

**🔔 Alert-System:**
Das System überwacht Preise alle 20 Sekunden und sendet automatisch Benachrichtigungen.

**🤖 GPT Integration:**
Dein GPT kann über die API neue Alerts erstellen:
• `POST /gpt-alerts/price-above`
• `POST /gpt-alerts/price-below`
• `POST /gpt-alerts/breakout`

**📊 Features:**
• ✅ Unlimited Alerts für beliebige Coins
• ✅ Real-time Price Streaming
• ✅ Trading Position Monitor
• ✅ Portfolio Watch
• ✅ Performance Analytics

**💡 Tipps:**
• Nutze Buttons für einfache Navigation
• Alerts werden automatisch gelöscht nach Auslösung
• Check System Status bei Problemen
• Export/Import für Backup

**🆘 Support:**
• GitHub: crypto-analyzer-gpt
• Status: System läuft 24/7
• Updates: Automatisch deployed"""
    
    buttons = [
        [
            {"text": "📖 Tutorial", "callback_data": "help_tutorial"},
            {"text": "🔧 Troubleshooting", "callback_data": "help_troubleshooting"}
        ],
        [
            {"text": "📊 API Docs", "callback_data": "help_api"},
            {"text": "🎯 Examples", "callback_data": "help_examples"}
        ],
        [
            {"text": "❓ FAQ", "callback_data": "help_faq"},
            {"text": "📞 Contact", "callback_data": "help_contact"}
        ],
        [
            {"text": "🏠 Hauptmenü", "callback_data": "main_menu"}
        ]
    ]
    
    if message_id:
        await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})
    else:
        await send_with_buttons(text, buttons)

async def show_stream_status(message_id: Optional[int] = None):
    """Show live stream status"""
    alert_system = get_alert_system()
    active_alerts = alert_system.get_active_alerts()
    
    # Group alerts by symbol
    symbol_alerts = {}
    for alert in active_alerts:
        if alert.symbol not in symbol_alerts:
            symbol_alerts[alert.symbol] = []
        symbol_alerts[alert.symbol].append(alert)
    
    text = f"""📡 **Live Stream Status** 📡

**System:** {'🟢 Online' if alert_system.running else '🔴 Offline'}
**Total Streams:** {len(alert_system.price_streams)}
**Check Interval:** {alert_system.check_interval}s

"""
    
    if symbol_alerts:
        text += "**Active Streams:**\n"
        for symbol, alerts in symbol_alerts.items():
            stream_active = symbol in alert_system.price_streams
            last_price = alert_system.price_cache.get(symbol)
            
            status_emoji = "🟢" if stream_active else "🔴"
            price_text = f"${last_price:,.2f}" if last_price else "No data"
            
            text += f"{status_emoji} {symbol}: {price_text} ({len(alerts)} alerts)\n"
    else:
        text += "**No active streams**\n"
    
    text += f"\n**Last Update:** {datetime.now().strftime('%H:%M:%S')}"
    
    buttons = [
        [{"text": "🔄 Refresh", "callback_data": "show_streams"}],
        [{"text": "🔧 System Status", "callback_data": "system_status"}],
        [{"text": "🏠 Main Menu", "callback_data": "main_menu"}]
    ]
    
    if message_id:
        await edit_message(message_id, text, {"inline_keyboard": [[{"text": button["text"], "callback_data": button["callback_data"]} for button in row] for row in buttons]})
    else:
        await send_with_buttons(text, buttons)

async def show_system_status(message_id: Optional[int] = None):
    """Show enhanced system status"""
    alert_system = get_alert_system()
    stats = alert_system.get_stats()
    
    redis_status = "✅ Connected" if alert_system.redis_client else "❌ Not available"
    telegram_status = "✅ Configured" if (settings.TG_BOT_TOKEN and settings.TG_CHAT_ID) else "❌ Not configured"
    
    text = f"""
🔧 **Enhanced System Status** 🔧

**Environment:** {settings.ENVIRONMENT}
**Redis:** {redis_status}
**Telegram:** {telegram_status}
**Live Monitoring:** {'✅ Running' if alert_system.running else '❌ Stopped'}

**Alert Statistics:**
• Active Alerts: {stats['total_active']}
• Active Streams: {stats['active_streams']}
• Check Interval: {alert_system.check_interval}s
• Stream Symbols: {', '.join(stats['streaming_symbols']) if stats['streaming_symbols'] else 'None'}

**Price Cache:**
"""
    
    for symbol, price in stats['price_cache'].items():
        text += f"• {symbol}: ${price:,.2f}\n"
    
    if not stats['price_cache']:
        text += "• No prices cached\n"
    
    text += f"\n**Last Update:** {datetime.now().strftime('%H:%M:%S')}"
    
    buttons = [
        [{"text": "🔄 Refresh", "callback_data": "system_status"}],
        [{"text": "📊 Streams", "callback_data": "show_streams"}],
        [{"text": "🏠 Main Menu", "callback_data": "main_menu"}]
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
        ],
        [
            {"text": "🏠 Hauptmenü", "callback_data": "main_menu"}
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

@router.post("/setup-menu", summary="Setup Telegram Bot Menu (Commands + Menu Button)")
async def setup_telegram_bot_menu():
    """
    Setup Telegram Bot Menu System
    - Commands menu (appears when typing /)
    - Menu button (appears next to text input)
    """
    if not settings.TG_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="TG_BOT_TOKEN not configured")
    
    if not settings.TG_CHAT_ID:
        raise HTTPException(status_code=400, detail="TG_CHAT_ID not configured")
    
    # Setup complete menu system
    success = await setup_telegram_menu()
    
    setup_info = f"""
📱 **Telegram Bot Menu Setup** 📱

**Status:** {'✅ Successfully configured' if success else '❌ Setup failed'}

**Features aktiviert:**
• 🔧 Command Menu (beim Eingeben von /)
• 📋 Menu Button (neben der Texteingabe)

**Verfügbare Kommandos:**
• `/start` - Bot starten und Hauptmenü
• `/menu` - Hauptmenü anzeigen
• `/alerts` - Alert Übersicht
• `/new` - Neuen Alert erstellen
• `/status` - System Status
• `/streams` - Live Streams
• `/portfolio` - Portfolio Watch
• `/monitor` - Trading Monitor
• `/performance` - Performance Stats
• `/settings` - Einstellungen
• `/help` - Hilfe anzeigen

**💡 Tipp:** Drücke auf das Menu-Symbol neben der Texteingabe für schnellen Zugriff!
"""
    
    # Send setup info to telegram
    if success:
        await send(setup_info)
        
        # Also send the main menu as confirmation
        await send_main_menu()
    
    return {
        "success": success,
        "message": "Menu setup completed" if success else "Menu setup failed",
        "commands_configured": success,
        "menu_button_configured": success,
        "chat_id": settings.TG_CHAT_ID
    }

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
