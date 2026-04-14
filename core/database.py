# core/database.py
"""
Database connection and session management.
SQLAlchemy setup for PostgreSQL.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings
import logging

logger = logging.getLogger(__name__)

# Database URL from environment or fallback
DATABASE_URL = settings.database_url or "sqlite:///./trading_analytics.db"

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=settings.debug,  # Log SQL queries if debug mode
    pool_size=20,         # Connection pool size
    max_overflow=40,      # Max overflow connections
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency injection for database session.
    Usage in routers:
        from fastapi import Depends
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database — create all tables.
    Call once on application startup.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def drop_db():
    """
    Drop all tables — use only in development/testing!
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")
