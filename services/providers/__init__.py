# services/providers/__init__.py

from core.config import settings


def get_provider():
    """Return the active OHLC data provider based on .env config."""
    if settings.data_provider == "upstox":
        if not settings.upstox_access_token:
            raise RuntimeError(
                "DATA_PROVIDER=upstox but UPSTOX_ACCESS_TOKEN is empty. "
                "Visit /auth/upstox/login to generate a token, "
                "or set DATA_PROVIDER=yfinance."
            )
        from services.providers.upstox_provider import fetch_ohlc
    else:
        from services.providers.yfinance_provider import fetch_ohlc

    return fetch_ohlc
