# core/exceptions.py


class TradingPlatformError(Exception):
    """
    Base exception for all errors in this platform.
    Every custom exception inherits from this so you can catch
    all platform errors with a single except clause if needed.
    """
    def __init__(self, message: str, status_code: int = 500):
        self.message     = message
        self.status_code = status_code
        super().__init__(message)


class SymbolNotFoundError(TradingPlatformError):
    """Raised when yfinance returns no data for a symbol."""
    def __init__(self, symbol: str):
        super().__init__(
            message=f"No market data found for symbol '{symbol}'. "
                    f"Check the symbol is correct (e.g. ^NSEI, ^BSESN).",
            status_code=404,
        )
        self.symbol = symbol


class InsufficientDataError(TradingPlatformError):
    """Raised when there aren't enough candles to calculate an indicator."""
    def __init__(self, required: int, got: int, context: str = ""):
        msg = f"Not enough data. Need {required} candles, got {got}."
        if context:
            msg += f" Context: {context}"
        super().__init__(message=msg, status_code=422)
        self.required = required
        self.got      = got


class InvalidParameterError(TradingPlatformError):
    """Raised when a user passes an invalid parameter value."""
    def __init__(self, param: str, value, reason: str = ""):
        msg = f"Invalid value for '{param}': {value}."
        if reason:
            msg += f" {reason}"
        super().__init__(message=msg, status_code=400)
        self.param = param
        self.value = value


class DataFetchError(TradingPlatformError):
    """Raised when a data source (yfinance, NSE) fails to respond."""
    def __init__(self, source: str, reason: str = ""):
        msg = f"Failed to fetch data from {source}."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(message=msg, status_code=503)
        self.source = source