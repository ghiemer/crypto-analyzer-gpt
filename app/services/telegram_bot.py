import httpx
import logging
import json
from typing import Dict, Any, Optional
from ..core.settings import settings
from ..core.logging_config import get_telegram_logger, log_telegram_request, log_telegram_response

logger = get_telegram_logger("service")

async def send(text: str, reply_markup: Optional[Dict[str, Any]] = None):
    """Send message to Telegram with improved error handling and optional inline keyboard"""
    logger.debug("📤 send() called with text length=%d, has_markup=%s", len(text), reply_markup is not None)
    
    if not (settings.TG_BOT_TOKEN and settings.TG_CHAT_ID):
        logger.warning("⚠️ Telegram not configured - skipping message")
        return False
    
    url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/sendMessage"
    
    # Try with Markdown first
    payload = {
        "chat_id": settings.TG_CHAT_ID, 
        "text": text,
        "parse_mode": "Markdown"
    }
    
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
        logger.debug("📋 Added reply_markup with %d buttons", len(reply_markup.get('inline_keyboard', [])) if 'inline_keyboard' in reply_markup else 0)
    
    log_telegram_request(int(settings.TG_CHAT_ID), "send", payload)
    
    try:
        logger.debug("🌐 Making HTTP request to Telegram API...")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, data=payload)
            
            logger.debug("📊 Response status: %d", response.status_code)
            
            if response.status_code == 200:
                logger.info("✅ Telegram message sent successfully")
                log_telegram_response(True, {"status": "ok", "message": "sent"})
                return True
            elif response.status_code == 400 and "parse entities" in response.text:
                # Markdown parsing failed, try without parse_mode
                logger.warning("⚠️ Markdown parsing failed, retrying without formatting")
                del payload["parse_mode"]
                
                # Clean text from markdown
                clean_text = text.replace("**", "").replace("*", "").replace("_", "").replace("`", "")
                payload["text"] = clean_text
                
                logger.debug("🔄 Retrying with plain text...")
                response = await client.post(url, data=payload)
                
                if response.status_code == 200:
                    logger.info("✅ Telegram message sent successfully (plain text)")
                    log_telegram_response(True, {"status": "ok", "message": "sent_plain"})
                    return True
                else:
                    logger.error("❌ Telegram API error after retry: %d - %s", response.status_code, response.text[:200])
                    log_telegram_response(False, {"error": response.text[:200]})
                    return False
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

async def set_webhook(webhook_url: str):
    """Set webhook for Telegram bot"""
    if not settings.TG_BOT_TOKEN:
        return False
    
    url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/setWebhook"
    
    payload = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query"]
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, data=payload)
            if response.status_code == 200:
                logger.info(f"✅ Webhook set successfully: {webhook_url}")
                return True
            else:
                logger.error(f"❌ Webhook setup error: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logger.error(f"❌ Webhook setup error: {e}")
        return False

async def get_webhook_info():
    """Get current webhook info"""
    if not settings.TG_BOT_TOKEN:
        return None
    
    url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/getWebhookInfo"
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Get webhook info error: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"❌ Get webhook info error: {e}")
        return None

async def delete_webhook():
    """Delete webhook (switch to polling mode)"""
    if not settings.TG_BOT_TOKEN:
        return False
    
    url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/deleteWebhook"
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url)
            if response.status_code == 200:
                logger.info("✅ Webhook deleted successfully")
                return True
            else:
                logger.error(f"❌ Delete webhook error: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ Delete webhook error: {e}")
        return False

async def get_updates(offset: int = 0):
    """Get updates from Telegram (polling mode)"""
    if not settings.TG_BOT_TOKEN:
        return []
    
    url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/getUpdates"
    
    payload = {
        "offset": offset,
        "timeout": 1,
        "allowed_updates": ["message", "callback_query"]
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, data=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("result", [])
            else:
                logger.error(f"❌ Get updates error: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"❌ Get updates error: {e}")
        return []