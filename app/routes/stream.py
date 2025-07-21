"""
Universal Stream API
Advanced streaming service for multiple use cases
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..services.universal_stream import get_stream_service, StreamType
from ..helpers.error_handlers import handle_api_errors
from ..helpers.response_helpers import ResponseHelper
from ..utils.validation import validate_symbol

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
@handle_api_errors("Failed to get stream status")
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

@router.get("/data/{symbol}")
@handle_api_errors("Failed to get stream data")
async def get_stream_data(symbol: str):
    """Get current cached data for a symbol"""
    validated_symbol = validate_symbol(symbol)
    stream_service = get_stream_service()
    data = await stream_service.get_current_data(validated_symbol)
    
    if not data:
        return ResponseHelper.not_found(f"No data available for {validated_symbol}")
    
    return ResponseHelper.success(data)

@router.delete("/subscription/{subscription_id}")
@handle_api_errors("Failed to cancel subscription")  
async def cancel_subscription(subscription_id: str):
    """Cancel a specific subscription"""
    stream_service = get_stream_service()
    
    # Check if subscription exists
    subscription = stream_service.subscriptions.get(subscription_id)
    if not subscription:
        return ResponseHelper.not_found("Subscription not found")
    
    await stream_service.unsubscribe(subscription_id)
    
    return ResponseHelper.success({
        "subscription_id": subscription_id,
        "symbol": subscription.symbol,
        "message": "Subscription cancelled successfully"
    })
