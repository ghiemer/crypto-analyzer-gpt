import httpx
import logging
import json
from typing import Dict, Any, Optional
from ..core.settings import settings

logger = logging.getLogger(__name__)

async def send(text: str, reply_markup: Optional[Dict[str, Any]] = None):
    """Send message to Telegram with improved error handling and optional inline keyboard"""
    if not (settings.TG_BOT_TOKEN and settings.TG_CHAT_ID):
        logger.warning("⚠️ Telegram not configured - skipping message")
        return False
    
    url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": settings.TG_CHAT_ID, 
        "text": text,
        "parse_mode": "Markdown"
    }
    
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, data=payload)
            
            if response.status_code == 200:
                logger.info("✅ Telegram message sent successfully")
                return True
            else:
                logger.error(f"❌ Telegram API error: {response.status_code} - {response.text}")
                return False
                
    except httpx.TimeoutException:
        logger.error("❌ Telegram timeout - message not sent")
        return False
    except Exception as e:
        logger.error(f"❌ Telegram error: {e}")
        return False

async def send_with_buttons(text: str, buttons: list):
    """Send message with inline keyboard buttons"""
    inline_keyboard = []
    
    # Convert button list to inline keyboard format
    for button_row in buttons:
        row = []
        for button in button_row:
            row.append({
                "text": button["text"],
                "callback_data": button["callback_data"]
            })
        inline_keyboard.append(row)
    
    reply_markup = {
        "inline_keyboard": inline_keyboard
    }
    
    return await send(text, reply_markup)

async def answer_callback_query(callback_query_id: str, text: str = ""):
    """Answer callback query from inline keyboard"""
    if not settings.TG_BOT_TOKEN:
        return False
    
    url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/answerCallbackQuery"
    
    payload = {
        "callback_query_id": callback_query_id,
        "text": text
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, data=payload)
            return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ Callback query error: {e}")
        return False

async def edit_message(message_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None):
    """Edit existing message"""
    if not (settings.TG_BOT_TOKEN and settings.TG_CHAT_ID):
        return False
    
    url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/editMessageText"
    
    payload = {
        "chat_id": settings.TG_CHAT_ID,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, data=payload)
            return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ Edit message error: {e}")
        return False