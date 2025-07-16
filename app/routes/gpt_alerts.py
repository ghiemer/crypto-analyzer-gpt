"""
GPT Alert API Endpoints
Flexible price alerts without fixed percentages
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..services.simple_alerts import get_alert_system, AlertType, SimpleAlert

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
async def create_alert(request: CreateAlertRequest):
    """
    Create a new price alert
    
    GPT can call this endpoint to set alerts for specific price targets:
    - PRICE_ABOVE: Alert when price goes above target
    - PRICE_BELOW: Alert when price goes below target  
    - BREAKOUT: Alert when price breaks above resistance level
    """
    try:
        alert_system = get_alert_system()
        
        alert_id = alert_system.create_alert(
            symbol=request.symbol.upper(),
            alert_type=request.alert_type,
            target_price=request.target_price,
            description=request.description or ""
        )
        
        return {
            "status": "success",
            "alert_id": alert_id,
            "message": f"Alert created for {request.symbol} {request.alert_type.value} @ ${request.target_price}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")

@router.get("/list", response_model=List[AlertResponse])
async def get_active_alerts():
    """Get all active alerts"""
    try:
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.get("/stats", response_model=AlertStats)
async def get_alert_stats():
    """Get alert statistics"""
    try:
        alert_system = get_alert_system()
        stats = alert_system.get_stats()
        
        return AlertStats(
            total_active=stats["total_active"],
            by_symbol=stats["by_symbol"],
            price_cache=stats["price_cache"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.delete("/delete/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert"""
    try:
        alert_system = get_alert_system()
        alert_system.delete_alert(alert_id)
        
        return {
            "status": "success",
            "message": f"Alert {alert_id} deleted"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete alert: {str(e)}")

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
