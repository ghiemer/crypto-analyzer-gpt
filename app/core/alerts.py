import asyncio
import pandas as pd
from redis import asyncio as aioredis
from typing import Dict, Any
from .settings import settings
from ..services.telegram_bot import send as tg_send

redis = aioredis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)

# CRUD ----------------------------------------------------------------------
async def add_alert(user: str, symbol: str, expr: str) -> None:
    await redis.hset(f"alert:{user}", symbol, expr)  # type: ignore

async def delete_alert(user: str, symbol: str) -> None:
    await redis.hdel(f"alert:{user}", symbol)  # type: ignore

async def list_alerts(user: str) -> Dict[str, str]:
    return await redis.hgetall(f"alert:{user}")  # type: ignore

# Spam-Lock (10 s) ----------------------------------------------------------
async def _spam_lock(lock_key: str) -> bool:
    ok = await redis.setnx(lock_key, 1)  # type: ignore
    if ok:
        await redis.expire(lock_key, 10)  # type: ignore
    return ok

# Background‑Worker ---------------------------------------------------------
async def alert_worker(fetch_df):
    """
    fetch_df(symbol:str)->DataFrame muss der Worker übergeben bekommen.
    Evaluiert jede Minute alle Regeln des Default‑Users.
    """
    while True:
        try:
            keys = await redis.keys("alert:*")  # type: ignore
            for key in keys:
                user = key.split(":", 1)[1]
                rules = await redis.hgetall(key)  # type: ignore
                for sym, expr in rules.items():
                    try:
                        df = await fetch_df(sym)
                        if not df.empty and eval(expr, {}, {"df": df}):
                            lock = f"lock:{user}:{sym}:{expr}"
                            if await _spam_lock(lock):
                                price = df.close.iloc[-1]
                                await tg_send(f"⚡ Alert: {sym} | {expr} @ {price:,.2f}")
                                await delete_alert(user, sym)  # one‑shot
                    except Exception:
                        pass                                 # silent fail
        except Exception:
            pass  # Redis connection error - continue trying
        await asyncio.sleep(60)