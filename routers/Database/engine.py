# database/engine.py

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy engine — connection pool shared across all requests
engine = create_engine(
    settings.database_url,
    pool_size=5,          # maintain 5 connections in pool
    max_overflow=10,      # allow 10 extra connections under load
    pool_pre_ping=True,   # verify connections before using
    echo=False,           # set True to log all SQL (useful for debugging)
)

# Session factory — use this to create DB sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_db():
    """
    FastAPI dependency — yields a database session.
    Automatically closes the session when the request is done.

    Usage in a router:
        from database.engine import get_db
        from sqlalchemy.orm import Session
        from fastapi import Depends

        @router.get("/")
        def my_endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection() -> bool:
    """Verify database is reachable — used by /health endpoint."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False