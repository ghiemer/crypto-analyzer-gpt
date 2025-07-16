from sqlmodel import SQLModel, create_engine, Session
import os

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL, echo=False, pool_pre_ping=True) if DB_URL else None

def init_db() -> None:
    if not engine:
        return                       # keine Postgres-Instanz hinterlegt
    try:
        import app.models.candle         # Model registrieren  # type: ignore
        SQLModel.metadata.create_all(engine)
    except ImportError:
        pass  # Model nicht verfügbar

def get_session():
    if not engine:
        raise RuntimeError("Database not configured")
    with Session(engine) as session:
        yield session