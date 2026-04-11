# core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="Trading Analytics Platform", alias="APP_NAME")
    debug: bool = Field(default=True, alias="DEBUG")
    default_symbol: str = Field(default="^NSEI", alias="DEFAULT_SYMBOL")
    default_period: str = Field(default="3mo", alias="DEFAULT_PERIOD")
    default_interval: str = Field(default="1d", alias="DEFAULT_INTERVAL")
    secret_key: str = Field(default="change-this-before-production", alias="SECRET_KEY")
    database_url: str = Field(default="", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")

    # Provider switch
    data_provider: str = Field(default="yfinance", alias="DATA_PROVIDER")

    # Upstox
    upstox_api_key: str = Field(default="", alias="UPSTOX_API_KEY")
    upstox_api_secret: str = Field(default="", alias="UPSTOX_API_SECRET")
    upstox_redirect_uri: str = Field(
        default="http://127.0.0.1:8000/auth/upstox/callback",
        alias="UPSTOX_REDIRECT_URI",
    )
    upstox_access_token: str = Field(default="", alias="UPSTOX_ACCESS_TOKEN")

    class Config:
        env_file = ".env"
        case_sensitive = False
        populate_by_name = True


settings = Settings()
