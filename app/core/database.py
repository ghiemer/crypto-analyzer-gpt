from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker
import os

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL, echo=False, pool_pre_ping=True) if DB_URL else None

# Create session factory for SQLAlchemy (falls noch benötigt)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None

def init_db() -> None:
    """Initialize database - only if connection is available"""
    if not engine:
        print("ℹ️  Database not configured, skipping initialization")
        return                       # keine Postgres-Instanz hinterlegt
    try:
        import app.models.candle         # Model registrieren  # type: ignore
        SQLModel.metadata.create_all(engine)
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization failed (continuing anyway): {e}")
        pass  # Continue without database

def get_session():
    if not engine:
        raise RuntimeError("Database not configured")
    with Session(engine) as session:
        yield session

def get_db():
    """Get database session for SQLAlchemy (legacy - falls noch verwendet)"""
    if not engine or not SessionLocal:
        raise RuntimeError("Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()