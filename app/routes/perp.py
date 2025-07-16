from fastapi import APIRouter, Query
from ..services import bitget

router = APIRouter(prefix="/perp", tags=["futures"])

@router.get(
    "/funding",
    summary="Funding rate",
    description="""
    Retrieves current funding rate for a perpetual future.
    
    **Examples:**
    - `/perp/funding?symbol=BTCUSDT` - BTC funding rate
    """
)
async def funding(
    symbol: str = Query(..., description="Trading symbol (e.g. BTCUSDT)", example="BTCUSDT")
):
    return await bitget.funding(symbol)

@router.get(
    "/oi",
    summary="Open Interest",
    description="""
    Retrieves current open interest for a perpetual future.
    
    **Examples:**
    - `/perp/oi?symbol=BTCUSDT` - BTC open interest
    """
)
async def open_interest(
    symbol: str = Query(..., description="Trading symbol (e.g. BTCUSDT)", example="BTCUSDT")
):
    return await bitget.open_interest(symbol)