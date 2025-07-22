import logging, asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.settings import settings
from .core.cache import init_cache, shutdown_cache, get_cache_worker_status
from .core.database import init_db
from .core.alerts import alert_worker, initialize_alert_system, start_alert_monitoring, stop_alert_monitoring, get_alert_system_status
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
    import os
    print(f"🔍 STARTUP DEBUG: App lifespan startup beginning")
    print(f"🔍 STARTUP DEBUG: PORT environment variable = {os.environ.get('PORT', 'NOT SET')}")
    print(f"🔍 STARTUP DEBUG: All PORT-related env vars:")
    for key, value in os.environ.items():
        if 'PORT' in key.upper():
            print(f"   {key} = {value}")
    
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
    
    # Initialize Enhanced Alert System
    try:
        await initialize_alert_system(lambda sym: candles(sym, limit=50))
        await start_alert_monitoring()
        print("✅ Enhanced Alert System initialized successfully")
    except Exception as e:
        print(f"⚠️ Enhanced Alert System initialization failed: {e}")
        print("🔄 Continuing with Simple Alert System...")
        
        # Fallback to simple alerts
        try:
            await start_alert_monitoring()
            print("✅ Simple Alert System started as fallback")
        except Exception as fallback_error:
            print(f"❌ Simple Alert System also failed: {fallback_error}")
    
    # Start Universal Stream Service
    try:
        await start_stream_service()
        print("✅ Universal Stream Service started")
    except Exception as e:
        print(f"⚠️ Universal Stream Service failed: {e}")
        print("🔄 Continuing without stream service...")
    
    print(f"🔍 STARTUP DEBUG: App startup completed, yielding control")
    yield  # Application is running
    
    print(f"🔍 SHUTDOWN DEBUG: App shutdown beginning")
    # Shutdown
    await shutdown_cache()
    
    # Stop Alert Monitoring
    try:
        await stop_alert_monitoring()
        print("✅ Alert monitoring stopped")
    except Exception as e:
        print(f"⚠️ Alert monitoring shutdown failed: {e}")
    
    # Stop Stream Service
    try:
        await stop_stream_service()
        print("✅ Stream service stopped")
    except Exception as e:
        print(f"⚠️ Stream service shutdown failed: {e}")
    
    print(f"🔍 SHUTDOWN DEBUG: App shutdown completed")

app = FastAPI(
    title="Crypto Signal API",
    version="2.0.0",
    description="API für Krypto-Trading-Signale mit technischen Indikatoren, Marktdaten und Alerts",
    lifespan=lifespan
)

# PORT BINDING DEBUG - Log the app creation
import os
print(f"🔍 APP DEBUG: FastAPI app created")
print(f"🔍 APP DEBUG: PORT environment at app creation = {os.environ.get('PORT', 'NOT SET')}")
print(f"🔍 APP DEBUG: settings.PORT = {getattr(settings, 'PORT', 'NOT AVAILABLE')}")

# Add CORS with more debug logging
cors_origins = [
    "https://chat.openai.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://crypto-analyzer-gpt.onrender.com",
    "https://custom-gpt.ai",
    "https://customgpt.ai",
    "https://api.openai.com",
]
print(f"🔍 CORS DEBUG: Adding CORS middleware with origins: {cors_origins}")

# CORS (CustomGPT + ChatGPT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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

# COMPREHENSIVE PORT BINDING DEBUGGING
if __name__ == "__main__":
    import uvicorn
    import os
    import socket
    
    # Get port from environment
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"  # Render requires binding to 0.0.0.0
    
    print(f"🔍 PORT DEBUG: Starting server configuration")
    print(f"🔍 PORT DEBUG: Environment PORT = {os.environ.get('PORT', 'NOT SET')}")
    print(f"🔍 PORT DEBUG: Calculated port = {port}")
    print(f"🔍 PORT DEBUG: Host = {host}")
    print(f"🔍 PORT DEBUG: settings.PORT = {getattr(settings, 'PORT', 'NOT SET')}")
    print(f"🔍 PORT DEBUG: All environment variables:")
    for key, value in os.environ.items():
        if 'PORT' in key.upper() or 'HOST' in key.upper():
            print(f"   {key} = {value}")
    
    # Test if port is available
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.close()
        print(f"🔍 PORT DEBUG: Port {port} on {host} is available")
    except Exception as e:
        print(f"❌ PORT DEBUG: Port {port} on {host} is NOT available: {e}")
    
    print(f"🚀 PORT DEBUG: Starting uvicorn server on {host}:{port}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )
else:
    # When running via uvicorn command, log the port info
    import os
    port = int(os.environ.get("PORT", 8000))
    print(f"🔍 PORT DEBUG: App loaded via uvicorn command, PORT env = {port}")
    print(f"🔍 PORT DEBUG: App should be accessible on 0.0.0.0:{port}")