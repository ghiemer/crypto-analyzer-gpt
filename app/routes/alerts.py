from fastapi import APIRouter, Body
from ..core.alerts import add_alert, delete_alert, list_alerts
from ..core.errors import BAD_ARGUMENT

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.post("")
async def create(alerts: list[dict] = Body(..., example=[
    {"symbol": "BTCUSDT", "expr": "df.rsi14.iloc[-1] < 30"}])):
    for a in alerts:
        if "symbol" not in a or "expr" not in a:
            raise BAD_ARGUMENT("symbol and expr required")
        await add_alert("default", a["symbol"], a["expr"])
    return {"status": "ok", "count": len(alerts)}

@router.get("")
async def read():
    return await list_alerts("default")

@router.delete("/{symbol}")
async def delete(symbol: str):
    await delete_alert("default", symbol)
    return {"status": "deleted", "symbol": symbol}