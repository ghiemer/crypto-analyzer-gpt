"""
Live Alert Streaming API
Enhanced real-time price monitoring with streaming capabilities
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..services.simple_alerts import get_alert_system

router = APIRouter(prefix="/live-alerts", tags=["Live Alerts"])

class StreamStatus(BaseModel):
    symbol: str
    active: bool
    alerts_count: int
    last_price: Optional[float] = None
    last_update: Optional[str] = None

class SystemStatus(BaseModel):
    monitoring_active: bool
    total_alerts: int
    active_streams: int
    check_interval: int
    spam_protection_active: int
    streaming_symbols: List[str]

@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get comprehensive system status"""
    alert_system = get_alert_system()
    stats = alert_system.get_stats()
    
    return SystemStatus(
        monitoring_active=alert_system.running,
        total_alerts=stats["total_active"],
        active_streams=stats["active_streams"],
        check_interval=stats["check_interval"],
        spam_protection_active=stats["spam_protection"],
        streaming_symbols=stats["streaming_symbols"]
    )

@router.get("/streams", response_model=List[StreamStatus])
async def get_active_streams():
    """Get status of all active price streams"""
    alert_system = get_alert_system()
    active_alerts = alert_system.get_active_alerts()
    
    # Group alerts by symbol
    symbol_alerts = {}
    for alert in active_alerts:
        if alert.symbol not in symbol_alerts:
            symbol_alerts[alert.symbol] = []
        symbol_alerts[alert.symbol].append(alert)
    
    streams = []
    for symbol, alerts in symbol_alerts.items():
        last_price = alert_system.price_cache.get(symbol)
        
        stream_status = StreamStatus(
            symbol=symbol,
            active=symbol in alert_system.price_streams,
            alerts_count=len(alerts),
            last_price=last_price,
            last_update=datetime.now().isoformat() if last_price else None
        )
        streams.append(stream_status)
    
    return streams

@router.post("/start-monitoring")
async def start_monitoring():
    """Start the live monitoring system"""
    alert_system = get_alert_system()
    
    if alert_system.running:
        return {"status": "already_running", "message": "Monitoring is already active"}
    
    # Start monitoring in background
    import asyncio
    asyncio.create_task(alert_system.start_monitoring())
    
    return {
        "status": "started",
        "message": "Live monitoring started",
        "check_interval": alert_system.check_interval
    }

@router.post("/stop-monitoring")
async def stop_monitoring():
    """Stop the live monitoring system"""
    alert_system = get_alert_system()
    
    if not alert_system.running:
        return {"status": "already_stopped", "message": "Monitoring is not active"}
    
    await alert_system.stop_monitoring()
    
    return {
        "status": "stopped",
        "message": "Live monitoring stopped",
        "streams_stopped": len(alert_system.price_streams)
    }

@router.post("/stream/{symbol}/start")
async def start_symbol_stream(symbol: str):
    """Manually start price stream for a specific symbol"""
    alert_system = get_alert_system()
    
    if not alert_system.running:
        raise HTTPException(status_code=400, detail="Monitoring system is not running")
    
    symbol = symbol.upper()
    
    if symbol in alert_system.price_streams:
        return {
            "status": "already_active",
            "message": f"Stream for {symbol} is already running"
        }
    
    await alert_system.start_price_stream(symbol)
    
    return {
        "status": "started",
        "message": f"Price stream started for {symbol}",
        "symbol": symbol
    }

@router.post("/stream/{symbol}/stop")
async def stop_symbol_stream(symbol: str):
    """Manually stop price stream for a specific symbol"""
    alert_system = get_alert_system()
    symbol = symbol.upper()
    
    if symbol not in alert_system.price_streams:
        return {
            "status": "not_active",
            "message": f"No active stream for {symbol}"
        }
    
    await alert_system.stop_price_stream(symbol)
    
    return {
        "status": "stopped",
        "message": f"Price stream stopped for {symbol}",
        "symbol": symbol
    }

@router.get("/performance")
async def get_performance_stats():
    """Get performance statistics"""
    alert_system = get_alert_system()
    stats = alert_system.get_stats()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "running": alert_system.running,
            "check_interval": alert_system.check_interval,
            "redis_connected": alert_system.redis_client is not None
        },
        "alerts": {
            "total_active": stats["total_active"],
            "by_symbol": stats["by_symbol"]
        },
        "streams": {
            "active_count": stats["active_streams"],
            "symbols": stats["streaming_symbols"]
        },
        "cache": {
            "price_cache_size": len(stats["price_cache"]),
            "cached_symbols": list(stats["price_cache"].keys())
        },
        "protection": {
            "spam_blocks_active": stats["spam_protection"]
        }
    }