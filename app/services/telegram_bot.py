import httpx
import logging
from ..core.settings import settings

logger = logging.getLogger(__name__)

async def send(text: str):
    """Send message to Telegram with improved error handling"""
    if not (settings.TG_BOT_TOKEN and settings.TG_CHAT_ID):
        logger.warning("⚠️ Telegram not configured - skipping message")
        return False
    
    url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/sendMessage"
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, data={
                "chat_id": settings.TG_CHAT_ID, 
                "text": text,
                "parse_mode": "Markdown"
            })
            
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