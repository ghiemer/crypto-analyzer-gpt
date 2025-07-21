"""
Klassenbasierte Telegram Bot Service Implementation
Erweitert den bestehenden telegram_bot.py um eine strukturierte Klasse
Behält Backward Compatibility durch Wrapper-Funktionen
"""

import httpx
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.settings import settings
from ..core.logging_config import get_telegram_logger, log_telegram_request, log_telegram_response

logger = get_telegram_logger("service")


class TelegramBotService:
    """
    Klassenbasierte Service für Telegram Bot Integration
    
    Bietet strukturierte Methoden für:
    - Message Sending mit erweiterten Features
    - Inline Keyboards und Markup
    - File und Media Uploads
    - Webhook Management
    - Agent Framework Integration
    """
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None, timeout: int = 10):
        """
        Initialize Telegram Bot Service
        
        Args:
            bot_token: Telegram bot token (defaults to settings.TG_BOT_TOKEN)
            chat_id: Default chat ID (defaults to settings.TG_CHAT_ID)
            timeout: HTTP request timeout in seconds
        """
        self.bot_token = bot_token or settings.TG_BOT_TOKEN
        self.chat_id = chat_id or settings.TG_CHAT_ID
        self.timeout = timeout
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.session: Optional[httpx.AsyncClient] = None
        
        # Validate configuration
        if not self.bot_token or not self.chat_id:
            logger.warning("⚠️ Telegram not fully configured - some features may not work")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    def is_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return bool(self.bot_token and self.chat_id)
    
    async def _make_request(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to Telegram Bot API
        
        Args:
            method: API method name
            payload: Request payload
            
        Returns:
            API response data
            
        Raises:
            Exception: For API errors
        """
        if not self.is_configured():
            raise ValueError("Telegram bot not properly configured")
        
        if not self.session:
            self.session = httpx.AsyncClient(timeout=self.timeout)
        
        url = f"{self.base_url}/{method}"
        
        # Log request
        if self.chat_id:
            log_telegram_request(int(self.chat_id), method, payload)
        
        try:
            response = await self.session.post(url, data=payload)
            logger.debug(f"📊 {method} response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                log_telegram_response(True, {"status": "ok", "method": method})
                return result
            else:
                error_text = response.text
                log_telegram_response(False, {"error": error_text, "method": method})
                raise Exception(f"Telegram API error ({response.status_code}): {error_text}")
                
        except httpx.RequestError as e:
            logger.error(f"Telegram request failed: {e}")
            log_telegram_response(False, {"error": str(e), "method": method})
            raise
    
    async def send_message(
        self, 
        text: str, 
        chat_id: Optional[str] = None,
        parse_mode: Optional[str] = "Markdown",
        reply_markup: Optional[Dict[str, Any]] = None,
        disable_notification: bool = False
    ) -> bool:
        """
        Send a text message
        
        Args:
            text: Message text
            chat_id: Target chat ID (defaults to default chat)
            parse_mode: Parse mode ("Markdown", "HTML", or None)
            reply_markup: Inline keyboard markup
            disable_notification: Send silently
            
        Returns:
            bool: True if successful
        """
        logger.debug(f"📤 send_message() called with text length={len(text)}, parse_mode={parse_mode}")
        
        target_chat_id = chat_id or self.chat_id
        if not target_chat_id:
            logger.warning("⚠️ No chat ID specified")
            return False
        
        payload = {
            "chat_id": target_chat_id,
            "text": text[:4096],  # Telegram message limit
            "disable_notification": disable_notification
        }
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
            logger.debug(f"📋 Added reply_markup with {len(reply_markup.get('inline_keyboard', []))} buttons")
        
        try:
            await self._make_request("sendMessage", payload)
            logger.info("✅ Telegram message sent successfully")
            return True
            
        except Exception as e:
            # If Markdown parsing fails, try without formatting
            if parse_mode == "Markdown" and "parse entities" in str(e).lower():
                logger.warning("⚠️ Markdown parsing failed, retrying without formatting")
                payload.pop("parse_mode", None)
                
                # Clean text from markdown
                clean_text = text.replace("**", "").replace("*", "").replace("_", "").replace("`", "")
                payload["text"] = clean_text[:4096]
                
                try:
                    await self._make_request("sendMessage", payload)
                    logger.info("✅ Telegram message sent successfully (without formatting)")
                    return True
                except Exception as e2:
                    logger.error(f"❌ Telegram send failed even without formatting: {e2}")
                    return False
            else:
                logger.error(f"❌ Telegram send failed: {e}")
                return False
    
    async def send_photo(
        self,
        photo_url: str,
        caption: Optional[str] = None,
        chat_id: Optional[str] = None,
        parse_mode: Optional[str] = "Markdown"
    ) -> bool:
        """
        Send a photo from URL
        
        Args:
            photo_url: URL of the photo to send
            caption: Photo caption
            chat_id: Target chat ID
            parse_mode: Parse mode for caption
            
        Returns:
            bool: True if successful
        """
        target_chat_id = chat_id or self.chat_id
        if not target_chat_id:
            return False
        
        payload = {
            "chat_id": target_chat_id,
            "photo": photo_url
        }
        
        if caption:
            payload["caption"] = caption[:1024]  # Telegram caption limit
            if parse_mode:
                payload["parse_mode"] = parse_mode
        
        try:
            await self._make_request("sendPhoto", payload)
            logger.info("✅ Telegram photo sent successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Telegram photo send failed: {e}")
            return False
    
    async def send_document(
        self,
        document_url: str,
        caption: Optional[str] = None,
        chat_id: Optional[str] = None
    ) -> bool:
        """
        Send a document from URL
        
        Args:
            document_url: URL of the document to send
            caption: Document caption
            chat_id: Target chat ID
            
        Returns:
            bool: True if successful
        """
        target_chat_id = chat_id or self.chat_id
        if not target_chat_id:
            return False
        
        payload = {
            "chat_id": target_chat_id,
            "document": document_url
        }
        
        if caption:
            payload["caption"] = caption[:1024]
        
        try:
            await self._make_request("sendDocument", payload)
            logger.info("✅ Telegram document sent successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Telegram document send failed: {e}")
            return False
    
    def create_inline_keyboard(self, buttons: List[List[Dict[str, str]]]) -> Dict[str, Any]:
        """
        Create inline keyboard markup
        
        Args:
            buttons: List of button rows, each containing button dicts with 'text' and 'callback_data' or 'url'
            
        Returns:
            Dict: Inline keyboard markup
        """
        return {
            "inline_keyboard": buttons
        }
    
    def create_button(self, text: str, callback_data: Optional[str] = None, url: Optional[str] = None) -> Dict[str, str]:
        """
        Create a single inline button
        
        Args:
            text: Button text
            callback_data: Callback data for button press
            url: URL for button press
            
        Returns:
            Dict: Button definition
        """
        button = {"text": text}
        
        if callback_data:
            button["callback_data"] = callback_data
        elif url:
            button["url"] = url
        else:
            raise ValueError("Either callback_data or url must be provided")
        
        return button
    
    async def get_bot_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the bot
        
        Returns:
            Dict with bot information or None if failed
        """
        if not self.is_configured():
            return None
        
        try:
            response = await self._make_request("getMe", {})
            return response.get("result")
        except Exception as e:
            logger.error(f"Failed to get bot info: {e}")
            return None
    
    async def set_webhook(self, webhook_url: str) -> bool:
        """
        Set webhook URL
        
        Args:
            webhook_url: URL to set as webhook
            
        Returns:
            bool: True if successful
        """
        if not self.is_configured():
            return False
        
        payload = {"url": webhook_url}
        
        try:
            await self._make_request("setWebhook", payload)
            logger.info(f"✅ Webhook set successfully: {webhook_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            return False
    
    async def delete_webhook(self) -> bool:
        """
        Delete webhook
        
        Returns:
            bool: True if successful
        """
        if not self.is_configured():
            return False
        
        try:
            await self._make_request("deleteWebhook", {})
            logger.info("✅ Webhook deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return False
    
    async def get_webhook_info(self) -> Optional[Dict[str, Any]]:
        """
        Get webhook information
        
        Returns:
            Dict with webhook info or None if failed
        """
        if not self.is_configured():
            return None
        
        try:
            response = await self._make_request("getWebhookInfo", {})
            return response.get("result")
        except Exception as e:
            logger.error(f"Failed to get webhook info: {e}")
            return None
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for Agent Framework
        
        Returns:
            Dict with tool metadata and available methods
        """
        return {
            "name": "TelegramBotService",
            "description": "Telegram Bot service for sending messages and managing bot features",
            "methods": {
                "send_message": {
                    "description": "Send a text message",
                    "parameters": {
                        "text": {"type": "string", "required": True},
                        "chat_id": {"type": "string", "required": False},
                        "parse_mode": {"type": "string", "default": "Markdown"},
                        "disable_notification": {"type": "boolean", "default": False}
                    }
                },
                "send_photo": {
                    "description": "Send a photo from URL",
                    "parameters": {
                        "photo_url": {"type": "string", "required": True},
                        "caption": {"type": "string", "required": False}
                    }
                },
                "get_bot_info": {
                    "description": "Get information about the bot",
                    "parameters": {}
                },
                "create_inline_keyboard": {
                    "description": "Create inline keyboard markup",
                    "parameters": {
                        "buttons": {"type": "array", "required": True}
                    }
                }
            },
            "configuration": {
                "bot_token_configured": bool(self.bot_token),
                "chat_id_configured": bool(self.chat_id),
                "fully_configured": self.is_configured()
            }
        }


# Singleton instance for global access
_telegram_service_instance: Optional[TelegramBotService] = None

def get_telegram_service() -> TelegramBotService:
    """Get global TelegramBotService instance"""
    global _telegram_service_instance
    if _telegram_service_instance is None:
        _telegram_service_instance = TelegramBotService()
    return _telegram_service_instance


# Backward compatibility wrapper functions
async def send(text: str, reply_markup: Optional[Dict[str, Any]] = None):
    """Backward compatibility wrapper for send function"""
    service = get_telegram_service()
    return await service.send_message(text, reply_markup=reply_markup)
