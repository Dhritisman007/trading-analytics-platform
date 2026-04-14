"""
Repository pattern implementation for Trade Analytics Platform.
All database operations are encapsulated in repository classes.
This ensures clean separation between business logic (services) and data persistence.
"""

from repositories.trade_repository import (
    TradeRepository,
    PredictionRepository,
    BacktestResultRepository,
)
from repositories.news_repository import NewsArticleRepository
from repositories.fiidii_repository import FiidiiFlowRepository
from repositories.user_repository import UserPreferenceRepository

__all__ = [
    "TradeRepository",
    "PredictionRepository",
    "BacktestResultRepository",
    "NewsArticleRepository",
    "FiidiiFlowRepository",
    "UserPreferenceRepository",
]
