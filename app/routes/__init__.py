from fastapi import APIRouter
from .candles import router as candles
from .orderbook import router as orderbook
from .perp import router as perp
from .news import router as news
from .alerts import router as alerts
from .misc import router as misc

api_router = APIRouter()
for r in (candles, orderbook, perp, news, alerts, misc):
    api_router.include_router(r)