"""
Enhanced Logging Configuration for Telegram Bot Debugging
"""
import logging
import sys
from datetime import datetime
from typing import Optional
from .settings import settings

class TelegramBotFormatter(logging.Formatter):
    """Custom formatter with enhanced context for Telegram bot debugging"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Add color for console output
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        colored_levelname = f"{color}{record.levelname}{reset}"
        
        # Enhanced format for different log types
        if hasattr(record, 'telegram_context'):
            # Special formatting for Telegram-related logs
            return (
                f"🤖 [{timestamp}] {colored_levelname:20} "
                f"TG:{getattr(record, 'telegram_context', 'unknown'):15} | {record.getMessage()}"
            )
        elif hasattr(record, 'api_context'):
            # Special formatting for API calls
            return (
                f"🌐 [{timestamp}] {colored_levelname:20} "
                f"API:{getattr(record, 'api_context', 'unknown'):15} | {record.getMessage()}"
            )
        else:
            # Standard format
            return (
                f"📊 [{timestamp}] {colored_levelname:20} "
                f"{record.name:25} | {record.getMessage()}"
            )

def setup_enhanced_logging():
    """Setup enhanced logging for debugging"""
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    console_handler.setFormatter(TelegramBotFormatter())
    
    root_logger.addHandler(console_handler)
    
    # Set specific loggers
    telegram_logger = logging.getLogger('telegram_bot')
    telegram_logger.setLevel(logging.DEBUG)
    
    api_logger = logging.getLogger('api_calls')
    api_logger.setLevel(logging.DEBUG)
    
    alerts_logger = logging.getLogger('alerts_system')
    alerts_logger.setLevel(logging.DEBUG)
    
    # Reduce noise from external libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    print("🔧 Enhanced logging system initialized")
    print(f"📊 Log Level: {settings.LOG_LEVEL}")
    print(f"🔍 Debug Mode: {settings.DEBUG}")
    
def get_telegram_logger(context: str = "general"):
    """Get a telegram-specific logger with context"""
    logger = logging.getLogger('telegram_bot')
    
    # Create a custom LoggerAdapter to add context
    class TelegramLoggerAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            # Add telegram context to the record
            extra = kwargs.get('extra', {})
            if self.extra:
                extra['telegram_context'] = self.extra.get('context', 'unknown')
            kwargs['extra'] = extra
            return msg, kwargs
    
    return TelegramLoggerAdapter(logger, {'context': context})

def get_api_logger(context: str = "general"):
    """Get an API-specific logger with context"""
    logger = logging.getLogger('api_calls')
    
    class APILoggerAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            extra = kwargs.get('extra', {})
            if self.extra:
                extra['api_context'] = self.extra.get('context', 'unknown')
            kwargs['extra'] = extra
            return msg, kwargs
    
    return APILoggerAdapter(logger, {'context': context})

def log_telegram_request(chat_id: Optional[int], message_type: str, data: dict):
    """Log telegram request with structured data"""
    logger = get_telegram_logger("request")
    logger.info(f"📨 {message_type} → Chat:{chat_id} | Data: {str(data)[:200]}...")

def log_telegram_response(success: bool, response_data: dict):
    """Log telegram response with structured data"""
    logger = get_telegram_logger("response")
    if success:
        logger.info(f"✅ Response OK | Data: {str(response_data)[:200]}...")
    else:
        logger.error(f"❌ Response FAILED | Error: {str(response_data)[:200]}...")

def log_alert_action(action: str, symbol: str, details: str):
    """Log alert system actions"""
    logger = logging.getLogger('alerts_system')
    logger.info(f"🚨 Alert {action} | {symbol} | {details}")

def log_api_call(endpoint: str, params: dict, duration_ms: float, success: bool):
    """Log API calls with performance metrics"""
    logger = get_api_logger("external")
    status = "✅ SUCCESS" if success else "❌ FAILED"
    logger.info(f"{status} {endpoint} | Params: {params} | {duration_ms:.1f}ms")
