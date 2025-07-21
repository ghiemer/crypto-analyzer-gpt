import logging, asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.settings import settings
from .core.cache import init_cache
from .core.database import init_db
from .core.alerts import alert_worker
from .core.logging_config import setup_enhanced_logging
from .core.agent_framework import get_agent_service_manager
from .services.bitget import candles          # fetch_df (backward compatibility)
from .routes import api_router, telegram, gpt_alerts, live_alerts, stream, agent_test
from .services.simple_alerts import start_alert_monitoring, stop_alert_monitoring
from .services.universal_stream import start_stream_service, stop_stream_service

# Setup enhanced logging first
setup_enhanced_logging()
log = logging.getLogger("uvicorn")
log.setLevel(settings.LOG_LEVEL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_cache()
    
    # Initialize database (with error handling)
    try:
        init_db()
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("🔄 Continuing without database...")
    
    # Initialize Agent Framework (new classbased system)
    try:
        agent_manager = get_agent_service_manager()
        await agent_manager.initialize_all_tools()
        print("✅ Agent Framework initialized successfully")
    except Exception as e:
        print(f"⚠️ Agent Framework initialization failed: {e}")
        print("🔄 Continuing with legacy system...")
    
    # Start old alert system
    alert_task = asyncio.create_task(alert_worker(lambda sym: candles(sym, limit=50)))
    
    # Start universal stream service
    await start_stream_service()
    
    # Start alert monitoring system
    monitoring_task = asyncio.create_task(start_alert_monitoring())
    
    yield
    
    # Shutdown
    alert_task.cancel()
    try:
        await alert_task
    except asyncio.CancelledError:
        pass
    
    # Stop alert monitoring
    await stop_alert_monitoring()
    
    # Stop universal stream service
    await stop_stream_service()
    
    # Shutdown Agent Framework
    try:
        agent_manager = get_agent_service_manager()
        await agent_manager.shutdown_all_tools()
        print("✅ Agent Framework shutdown completed")
    except Exception as e:
        print(f"⚠️ Agent Framework shutdown warning: {e}")

app = FastAPI(
    title="Crypto Signal API",
    version="2.0.0",
    description="API für Krypto-Trading-Signale mit technischen Indikatoren, Marktdaten und Alerts",
    lifespan=lifespan
)

# CORS (CustomGPT + ChatGPT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chat.openai.com",
        "https://chatgpt.com",
        "https://custom-gpt.ai",
        "https://customgpt.ai",
        "https://api.openai.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify(request: Request):
    # Accept both X-API-Key and x-api-key header variants
    api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="invalid key")

# Add public health endpoint (no auth required)
@app.get("/health")
async def public_health():
    """Public health check endpoint for load balancer and monitoring"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "message": "API is running"
    }

app.include_router(api_router, dependencies=[Depends(verify)])
app.include_router(telegram.router, dependencies=[Depends(verify)])
app.include_router(telegram.webhook_router)  # No auth for webhook
app.include_router(gpt_alerts.router, dependencies=[Depends(verify)])
app.include_router(live_alerts.router, dependencies=[Depends(verify)])
app.include_router(stream.router, dependencies=[Depends(verify)])
app.include_router(agent_test.router, dependencies=[Depends(verify)])  # New Agent Framework routes

# Global exception handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(f"Global exception: {type(exc).__name__}: {str(exc)}")
    log.error(f"Request: {request.method} {request.url}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error occurred",
                "details": str(exc) if settings.DEBUG else "Contact support"
            }
        }
    )