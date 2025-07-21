"""
GPT Alert API Endpoints
Flexible price alerts without fixed percentages
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..services.simple_alerts import get_alert_system, AlertType, SimpleAlert
from ..helpers.error_handlers import handle_api_errors
from ..helpers.response_helpers import ResponseHelper
from ..utils.validation import validate_symbol

router = APIRouter(prefix="/gpt-alerts", tags=["GPT Alerts"])

# Pydantic models
class CreateAlertRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    alert_type: AlertType = Field(..., description="Type of alert")
    target_price: float = Field(..., description="Target price to trigger alert")
    description: Optional[str] = Field("", description="Optional description")

class AlertResponse(BaseModel):
    id: str
    symbol: str
    alert_type: str
    target_price: float
    description: str
    created_at: str
    triggered: bool

class AlertStats(BaseModel):
    total_active: int
    by_symbol: Dict[str, Any]
    price_cache: Dict[str, float]

@router.post("/create", response_model=Dict[str, str])
@handle_api_errors("Failed to create alert")
async def create_alert(request: CreateAlertRequest):
    """
    Create a new price alert
    
    GPT can call this endpoint to set alerts for specific price targets:
    - PRICE_ABOVE: Alert when price goes above target
    - PRICE_BELOW: Alert when price goes below target  
    - BREAKOUT: Alert when price breaks above resistance level
    """
    alert_system = get_alert_system()
    
    # Validate symbol using utils
    validated_symbol = validate_symbol(request.symbol)
    
    alert_id = alert_system.create_alert(
        symbol=validated_symbol,
        alert_type=request.alert_type,
        target_price=request.target_price,
        description=request.description or ""
    )
    
    return ResponseHelper.success({
        "alert_id": alert_id,
        "message": f"Alert created for {validated_symbol} {request.alert_type.value} @ ${request.target_price}"
    })

@router.get("/list", response_model=List[AlertResponse])
@handle_api_errors("Failed to get alerts")
async def get_active_alerts():
    """Get all active alerts"""
    alert_system = get_alert_system()
    alerts = alert_system.get_active_alerts()
    
    return [
        AlertResponse(
            id=alert.id,
            symbol=alert.symbol,
            alert_type=alert.alert_type.value,
            target_price=alert.target_price,
            description=alert.description,
            created_at=alert.created_at,
            triggered=alert.triggered
        )
        for alert in alerts
    ]

@router.get("/stats", response_model=AlertStats)
@handle_api_errors("Failed to get stats")
async def get_alert_stats():
    """Get alert statistics"""
    alert_system = get_alert_system()
    stats = alert_system.get_stats()
    
    return AlertStats(
        total_active=stats["total_active"],
        by_symbol=stats["by_symbol"],
        price_cache=stats["price_cache"]
    )

@router.delete("/delete/{alert_id}")
@handle_api_errors("Failed to delete alert")
async def delete_alert(alert_id: str):
    """Delete an alert"""
    alert_system = get_alert_system()
    alert_system.delete_alert(alert_id)
    
    return ResponseHelper.success({
        "message": f"Alert {alert_id} deleted"
    })

@router.get("/alert/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str):
    """Get specific alert by ID"""
    try:
        alert_system = get_alert_system()
        alert = alert_system.get_alert(alert_id)
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return AlertResponse(
            id=alert.id,
            symbol=alert.symbol,
            alert_type=alert.alert_type.value,
            target_price=alert.target_price,
            description=alert.description,
            created_at=alert.created_at,
            triggered=alert.triggered
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert: {str(e)}")

# Convenience endpoints for GPT
@router.post("/price-above")
async def create_price_above_alert(
    symbol: str, 
    target_price: float, 
    description: str = ""
):
    """Create alert for price above target"""
    request = CreateAlertRequest(
        symbol=symbol,
        alert_type=AlertType.PRICE_ABOVE,
        target_price=target_price,
        description=description
    )
    return await create_alert(request)

@router.post("/price-below")
async def create_price_below_alert(
    symbol: str, 
    target_price: float, 
    description: str = ""
):
    """Create alert for price below target"""
    request = CreateAlertRequest(
        symbol=symbol,
        alert_type=AlertType.PRICE_BELOW,
        target_price=target_price,
        description=description
    )
    return await create_alert(request)

@router.post("/breakout")
async def create_breakout_alert(
    symbol: str, 
    resistance_level: float, 
    description: str = ""
):
    """Create alert for breakout above resistance"""
    request = CreateAlertRequest(
        symbol=symbol,
        alert_type=AlertType.BREAKOUT,
        target_price=resistance_level,
        description=description
    )
    return await create_alert(request)

@router.get("/")
async def alert_system_info():
    """Get basic info about the alert system"""
    return {
        "system": "GPT Flexible Alert System",
        "version": "1.0",
        "features": [
            "Price above target alerts",
            "Price below target alerts", 
            "Breakout alerts",
            "No fixed percentages - flexible pricing",
            "Telegram notifications",
            "Redis caching support"
        ],
        "endpoints": {
            "create_alert": "/gpt-alerts/create",
            "price_above": "/gpt-alerts/price-above",
            "price_below": "/gpt-alerts/price-below",
            "breakout": "/gpt-alerts/breakout",
            "list_alerts": "/gpt-alerts/list",
            "stats": "/gpt-alerts/stats"
        }
    }

@router.post("/test-system", response_model=Dict[str, Any])
async def test_system():
    """
    Test the alert system components on Render
    """
    from ..services.telegram_bot import send
    from ..services.bitget import candles
    from ..core.settings import settings
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "environment": settings.ENVIRONMENT,
        "tests": {}
    }
    
    # Test 1: Redis connection
    alert_system = get_alert_system()
    result["tests"]["redis"] = {
        "available": alert_system.redis_client is not None,
        "status": "✅ Connected" if alert_system.redis_client else "❌ Not available"
    }
    
    # Test 2: Telegram configuration
    telegram_configured = bool(settings.TG_BOT_TOKEN and settings.TG_CHAT_ID)
    result["tests"]["telegram"] = {
        "configured": telegram_configured,
        "status": "✅ Configured" if telegram_configured else "❌ Not configured"
    }
    
    # Test 3: Bitget API
    try:
        price_data = await candles("BTCUSDT", limit=1)
        current_price = float(price_data.iloc[-1]["close"]) if not price_data.empty else None
        result["tests"]["bitget"] = {
            "working": current_price is not None,
            "current_btc_price": current_price,
            "status": "✅ Working" if current_price else "❌ Failed"
        }
    except Exception as e:
        result["tests"]["bitget"] = {
            "working": False,
            "error": str(e),
            "status": "❌ Failed"
        }
    
    # Test 4: Send test Telegram message (only if configured)
    if telegram_configured:
        try:
            test_message = f"""
🧪 **TEST MESSAGE** 🧪

System Test: {datetime.now().strftime('%H:%M:%S')}
Environment: {settings.ENVIRONMENT}
Status: Alert system is running!

This is a test message from your crypto analyzer.
"""
            await send(test_message)
            result["tests"]["telegram_send"] = {
                "sent": True,
                "status": "✅ Test message sent"
            }
        except Exception as e:
            result["tests"]["telegram_send"] = {
                "sent": False,
                "error": str(e),
                "status": "❌ Failed to send"
            }
    
    # Test 5: Alert system monitoring status
    result["tests"]["monitoring"] = {
        "running": alert_system.running,
        "active_alerts": len(alert_system.get_active_alerts()),
        "status": "✅ Running" if alert_system.running else "❌ Not running"
    }
    
    return result
