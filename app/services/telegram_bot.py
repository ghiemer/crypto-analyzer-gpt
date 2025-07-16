import httpx
from ..core.settings import settings

async def send(text: str):
    if not (settings.TG_BOT_TOKEN and settings.TG_CHAT_ID):
        return
    url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as c:
        await c.post(url, data={"chat_id": settings.TG_CHAT_ID, "text": text})