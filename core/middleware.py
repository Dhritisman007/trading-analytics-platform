# core/middleware.py

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every HTTP request automatically.
    You never have to add logging inside a router again.

    Output format:
    GET  /market/?symbol=^NSEI  →  200  in 1243ms
    GET  /indicators/           →  422  in 8ms
    """

    async def dispatch(self, request: Request, call_next):
        start   = time.perf_counter()
        method  = request.method
        path    = request.url.path
        query   = f"?{request.url.query}" if request.url.query else ""

        try:
            response = await call_next(request)
            duration = round((time.perf_counter() - start) * 1000)

            # Choose log level based on status code
            if response.status_code >= 500:
                log = logger.error
            elif response.status_code >= 400:
                log = logger.warning
            else:
                log = logger.info

            log(f"{method:<6} {path}{query}  →  {response.status_code}  in {duration}ms")
            return response

        except Exception as exc:
            duration = round((time.perf_counter() - start) * 1000)
            logger.error(f"{method:<6} {path}{query}  →  500  in {duration}ms  [{type(exc).__name__}]")
            raise