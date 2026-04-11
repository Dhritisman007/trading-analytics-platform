# core/error_handlers.py

import logging
import traceback
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.exceptions import TradingPlatformError

logger = logging.getLogger(__name__)


def _error_response(
    status_code: int,
    error_type: str,
    message: str,
    path: str,
    details: dict | None = None,
) -> JSONResponse:
    """
    Build a consistent error JSON response.
    Every single error from this API looks exactly like this — no exceptions.
    """
    body = {
        "error": error_type,
        "message": message,
        "status_code": status_code,
        "path": path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if details:
        body["details"] = details

    return JSONResponse(status_code=status_code, content=body)


def register_error_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers on the FastAPI app.
    Call this once in main.py after creating the app instance.
    """

    @app.exception_handler(TradingPlatformError)
    async def trading_error_handler(
        request: Request, exc: TradingPlatformError
    ) -> JSONResponse:
        """Handles all our custom exceptions — SymbolNotFoundError, etc."""
        logger.warning(
            f"{type(exc).__name__} | {request.method} {request.url.path} | {exc.message}"
        )
        return _error_response(
            status_code=exc.status_code,
            error_type=type(exc).__name__,
            message=exc.message,
            path=str(request.url.path),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handles Pydantic/FastAPI validation errors (422).
        Reformats them into a clean, readable structure instead of
        FastAPI's default nested 'detail' array.
        """
        # Extract just the field name and message from each error
        errors = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            errors.append(
                {
                    "field": field,
                    "message": error["msg"],
                    "value": error.get("input"),
                }
            )

        logger.warning(
            f"ValidationError | {request.method} {request.url.path} | "
            f"{len(errors)} field(s) failed"
        )
        return _error_response(
            status_code=422,
            error_type="ValidationError",
            message=f"{len(errors)} validation error(s). Check the 'details' field.",
            path=str(request.url.path),
            details={"errors": errors},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handles standard HTTP errors (404 Not Found, 405 Method Not Allowed, etc.)"""
        logger.warning(
            f"HTTPException {exc.status_code} | "
            f"{request.method} {request.url.path} | {exc.detail}"
        )
        return _error_response(
            status_code=exc.status_code,
            error_type="HTTPException",
            message=str(exc.detail),
            path=str(request.url.path),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Catch-all for any exception that wasn't handled above.
        Logs the full traceback so you can debug it, but only returns
        a generic message to the client — never expose internal details.
        """
        logger.error(
            f"Unhandled {type(exc).__name__} | "
            f"{request.method} {request.url.path}\n"
            f"{traceback.format_exc()}"
        )
        return _error_response(
            status_code=500,
            error_type="InternalServerError",
            message="An unexpected error occurred. Please try again later.",
            path=str(request.url.path),
        )
