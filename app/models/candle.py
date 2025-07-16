from sqlmodel import SQLModel, Field
from datetime import datetime

class Candle(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    granularity: str
    ts: datetime = Field(index=True)
    open: float
    high: float
    low: float
    close: float
    vol_base: float