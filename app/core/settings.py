from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os

# ENVIRONMENT DEBUG LOGGING
print(f"🔍 SETTINGS DEBUG: Loading settings...")
print(f"🔍 SETTINGS DEBUG: Environment = {os.getenv('ENVIRONMENT', 'NOT SET')}")
print(f"🔍 SETTINGS DEBUG: PORT = {os.getenv('PORT', 'NOT SET')}")
print(f"🔍 SETTINGS DEBUG: API_KEY = {'SET' if os.getenv('API_KEY') else 'NOT SET'}")
print(f"🔍 SETTINGS DEBUG: DATABASE_URL = {'SET' if os.getenv('DATABASE_URL') else 'NOT SET'}")
print(f"🔍 SETTINGS DEBUG: All env vars starting with API, PORT, DB:")
for key, value in os.environ.items():
    if any(prefix in key.upper() for prefix in ['API', 'PORT', 'DB', 'REDIS', 'TG_']):
        # Hide sensitive values but show if they're set
        display_value = f"SET({len(value)} chars)" if value else "NOT SET"
        print(f"   {key} = {display_value}")

class Settings(BaseSettings):
    # Required - loaded from environment variable
    # Must be set in production, no default value for security
    API_KEY: str = Field(default_factory=lambda: os.getenv("API_KEY", ""))
    
    @field_validator('API_KEY')
    @classmethod
    def validate_api_key(cls, v):
        print(f"🔍 API_KEY DEBUG: Validating API_KEY = '{v[:10]}...' (length: {len(v) if v else 0})")
        if not v or v.strip() == "":
            print(f"❌ API_KEY DEBUG: API_KEY is empty or not set!")
            print(f"🔍 API_KEY DEBUG: Environment API_KEY = {os.getenv('API_KEY', 'NOT SET')}")
            raise ValueError("API_KEY environment variable must be set for security reasons")
        if len(v) < 10:
            print(f"❌ API_KEY DEBUG: API_KEY too short: {len(v)} characters")
            raise ValueError("API_KEY must be at least 10 characters long for security")
        print(f"✅ API_KEY DEBUG: API_KEY validation successful")
        return v

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))  # Use Render's PORT env var

    # Logging
    LOG_LEVEL: str = "INFO"

    # Redis / Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 15                     # Seconds
    CACHE_ENABLED: bool = False             # Disabled by default for Render compatibility

    # Telegram
    TG_BOT_TOKEN: str | None = None
    TG_CHAT_ID:   str | None = None

    # News APIs
    NEWS_API_KEY: str | None = None
    CRYPTOPANIC_API_KEY: str | None = None

    # Postgres
    DATABASE_URL: str | None = None        # Render sets the value

    # Production Settings
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # Seconds
    
    # API Configuration
    API_TIMEOUT: int = 30
    MAX_INDICATORS: int = 10
    MAX_CANDLES: int = 1000
    
    # Internal API URL for self-referencing calls
    INTERNAL_API_URL: str = "http://localhost:8000"
    
    # Render Service Configuration
    RENDER_SERVICE_ID: str | None = None
    RENDER_SERVICE_NAME: str | None = None
    RENDER_SERVICE_URL: str | None = None
    
    # Telegram Webhook URL (auto-generated from RENDER_SERVICE_URL if not set)
    TELEGRAM_WEBHOOK_URL: str | None = None
    
    @property
    def webhook_url(self) -> str:
        """Get the Telegram webhook URL, auto-generated from RENDER_SERVICE_URL if not explicitly set"""
        if self.TELEGRAM_WEBHOOK_URL:
            return self.TELEGRAM_WEBHOOK_URL
        elif self.RENDER_SERVICE_URL:
            return f"{self.RENDER_SERVICE_URL}/telegram/webhook"
        else:
            return "https://your-app-name.onrender.com/telegram/webhook"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=True
    )

settings = Settings()
