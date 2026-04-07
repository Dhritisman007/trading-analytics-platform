# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Trading Analytics Platform"
    debug: bool = True
    default_symbol: str = "^NSEI"
    default_period: str = "3mo"
    default_interval: str = "1d"
    secret_key: str = "change-this-before-production"
    database_url: str = ""
    redis_url: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"

# Single instance used everywhere in the project
settings = Settings()