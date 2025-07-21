from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os

class Settings(BaseSettings):
    # Required - loaded from environment variable
    # Must be set in production, no default value for security
    API_KEY: str = Field(default_factory=lambda: os.getenv("API_KEY", ""))
    
    @field_validator('API_KEY')
    @classmethod
    def validate_api_key(cls, v):
        if not v or v.strip() == "":
            raise ValueError("API_KEY environment variable must be set for security reasons")
        if len(v) < 10:
            raise ValueError("API_KEY must be at least 10 characters long for security")
        return v

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

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
