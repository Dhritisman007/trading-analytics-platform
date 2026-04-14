# repositories/user_repository.py
"""
Repository for user preference data access.
Handles all database operations for user settings and configurations.
"""

from sqlalchemy.orm import Session
from models.trade import UserPreference
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class UserPreferenceRepository:
    """
    Repository for UserPreference model operations.
    Handles all database queries for user settings.
    """

    @staticmethod
    def create_or_update(db: Session, user_id: str, **kwargs) -> UserPreference:
        """Create new user preference or update existing."""
        user_pref = db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()

        if user_pref:
            # Update existing
            for key, value in kwargs.items():
                if hasattr(user_pref, key):
                    setattr(user_pref, key, value)
            db.commit()
            db.refresh(user_pref)
            logger.info(f"User preference updated: {user_id}")
            return user_pref
        else:
            # Create new
            user_pref = UserPreference(user_id=user_id, **kwargs)
            db.add(user_pref)
            db.commit()
            db.refresh(user_pref)
            logger.info(f"User preference created: {user_id}")
            return user_pref

    @staticmethod
    def get_by_user_id(db: Session, user_id: str) -> Optional[UserPreference]:
        """Get user preferences by user ID."""
        return db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()

    @staticmethod
    def get_default_symbol(db: Session, user_id: str) -> str:
        """Get default symbol for user (fallback to ^NSEI)."""
        pref = UserPreferenceRepository.get_by_user_id(db, user_id)
        return pref.default_symbol if pref else "^NSEI"

    @staticmethod
    def get_default_capital(db: Session, user_id: str) -> Optional[float]:
        """Get default capital for user."""
        pref = UserPreferenceRepository.get_by_user_id(db, user_id)
        return pref.default_capital if pref else None

    @staticmethod
    def get_risk_preference(db: Session, user_id: str) -> float:
        """Get default risk percentage for user (fallback to 1%)."""
        pref = UserPreferenceRepository.get_by_user_id(db, user_id)
        return pref.default_risk_pct if pref else 1.0

    @staticmethod
    def update_preferences(db: Session, user_id: str, **kwargs) -> UserPreference:
        """Update specific preferences for a user."""
        pref = UserPreferenceRepository.get_by_user_id(db, user_id)
        if not pref:
            # Create with defaults
            pref = UserPreference(user_id=user_id)
            db.add(pref)
            db.flush()

        for key, value in kwargs.items():
            if hasattr(pref, key):
                setattr(pref, key, value)

        db.commit()
        db.refresh(pref)
        logger.info(f"User preferences updated: {user_id}")
        return pref

    @staticmethod
    def delete(db: Session, user_id: str) -> bool:
        """Delete user preferences."""
        pref = UserPreferenceRepository.get_by_user_id(db, user_id)
        if not pref:
            return False

        db.delete(pref)
        db.commit()
        logger.info(f"User preferences deleted: {user_id}")
        return True
