from fastapi import APIRouter, Query
from ..services import bitget

router = APIRouter(prefix="/orderbook", tags=["market"])

@router.get(
    "", 
    summary="Order book data",
    description="""
    Retrieves current order book (bid/ask) for a symbol.
    
    **Examples:**
    - `/orderbook?symbol=BTCUSDT` - BTC order book
    - `/orderbook?symbol=BTCUSDT&limit=20` - Top 20 levels
    """
)
async def orderbook(
    symbol: str = Query(..., description="Trading symbol (e.g. BTCUSDT)", example="BTCUSDT"),
    limit: int = Query(5, le=20, description="Number of order book levels")
):
    return await bitget.orderbook(symbol, limit)