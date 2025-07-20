"""
Universal Stream API
Advanced streaming service for multiple use cases
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..services.universal_stream import get_stream_service, StreamType

router = APIRouter(prefix="/stream", tags=["Universal Stream"])

class StreamSubscriptionRequest(BaseModel):
    symbol: str
    stream_type: str  # Will be converted to StreamType
    interval: int = 5
    metadata: Optional[Dict[str, Any]] = None

class StreamStats(BaseModel):
    running: bool
    total_subscriptions: int
    active_subscriptions: int
    active_streams: int
    symbols_monitored: List[str]

class SubscriptionInfo(BaseModel):
    id: str
    symbol: str
    stream_type: str
    interval: int
    active: bool
    created_at: str
    last_update: Optional[str]
    last_price: Optional[float]
    error_count: int

@router.get("/status", response_model=StreamStats)
async def get_stream_status():
    """Get universal stream service status"""
    stream_service = get_stream_service()
    stats = stream_service.get_stats()
    
    return StreamStats(
        running=stats["running"],
        total_subscriptions=stats["total_subscriptions"],
        active_subscriptions=stats["active_subscriptions"],
        active_streams=stats["active_streams"],
        symbols_monitored=stats["symbols_monitored"]
    )

@router.get("/subscriptions", response_model=List[SubscriptionInfo])
async def get_all_subscriptions():
    """Get all active subscriptions"""
    stream_service = get_stream_service()
    subscriptions = stream_service.get_subscriptions()
    
    return [
        SubscriptionInfo(
            id=sub.id,
            symbol=sub.symbol,
            stream_type=sub.stream_type.value,
            interval=sub.interval,
            active=sub.active,
            created_at=sub.created_at.isoformat(),
            last_update=sub.last_update.isoformat() if sub.last_update else None,
            last_price=sub.last_price,
            error_count=sub.error_count
        )
        for sub in subscriptions
    ]

@router.get("/subscriptions/{symbol}", response_model=List[SubscriptionInfo])
async def get_symbol_subscriptions(symbol: str):
    """Get subscriptions for a specific symbol"""
    stream_service = get_stream_service()
    subscriptions = stream_service.get_subscriptions(symbol=symbol)
    
    return [
        SubscriptionInfo(
            id=sub.id,
            symbol=sub.symbol,
            stream_type=sub.stream_type.value,
            interval=sub.interval,
            active=sub.active,
            created_at=sub.created_at.isoformat(),
            last_update=sub.last_update.isoformat() if sub.last_update else None,
            last_price=sub.last_price,
            error_count=sub.error_count
        )
        for sub in subscriptions
    ]

@router.get("/data/{symbol}")
async def get_current_data(symbol: str):
    """Get current cached data for a symbol"""
    stream_service = get_stream_service()
    data = await stream_service.get_current_data(symbol)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
    
    return data

@router.post("/start")
async def start_stream_service():
    """Start the universal stream service"""
    stream_service = get_stream_service()
    
    if stream_service.running:
        return {"status": "already_running", "message": "Stream service is already running"}
    
    await stream_service.start()
    return {"status": "started", "message": "Universal stream service started"}

@router.post("/stop")
async def stop_stream_service():
    """Stop the universal stream service"""
    stream_service = get_stream_service()
    
    if not stream_service.running:
        return {"status": "already_stopped", "message": "Stream service is not running"}
    
    await stream_service.stop()
    return {"status": "stopped", "message": "Universal stream service stopped"}

@router.get("/performance")
async def get_performance_stats():
    """Get detailed performance statistics"""
    stream_service = get_stream_service()
    stats = stream_service.get_stats()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "service": stats,
        "cache_efficiency": {
            "hits": stats["performance"]["cache_hits"],
            "misses": stats["performance"]["cache_misses"],
            "hit_ratio": (
                stats["performance"]["cache_hits"] / 
                (stats["performance"]["cache_hits"] + stats["performance"]["cache_misses"])
                if (stats["performance"]["cache_hits"] + stats["performance"]["cache_misses"]) > 0 else 0
            )
        }
    }

@router.delete("/subscription/{subscription_id}")
async def cancel_subscription(subscription_id: str):
    """Cancel a specific subscription"""
    stream_service = get_stream_service()
    
    # Check if subscription exists
    subscription = stream_service.subscriptions.get(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    await stream_service.unsubscribe(subscription_id)
    
    return {
        "status": "cancelled",
        "subscription_id": subscription_id,
        "symbol": subscription.symbol
    }

@router.get("/symbols")
async def get_monitored_symbols():
    """Get all currently monitored symbols with details"""
    stream_service = get_stream_service()
    stats = stream_service.get_stats()
    
    symbol_details = []
    for symbol, details in stats["symbol_details"].items():
        current_data = await stream_service.get_current_data(symbol)
        
        symbol_details.append({
            "symbol": symbol,
            "subscriptions": details["subscriptions"],
            "stream_active": details["stream_active"],
            "current_price": current_data["price"] if current_data else None,
            "last_update": current_data["timestamp"] if current_data else None,
            "change_percent": current_data.get("change_percent", 0) if current_data else 0
        })
    
    return {
        "total_symbols": len(symbol_details),
        "symbols": symbol_details,
        "timestamp": datetime.now().isoformat()
    }
