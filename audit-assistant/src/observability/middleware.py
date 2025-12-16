# src/observability/middleware.py

import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.observability.logger import get_logger

log = get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            status_code = getattr(response, "status_code", 500)

            log.info(
                "http_request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "elapsed_ms": round(elapsed_ms, 2),
                },
            )

            # também devolvemos o request_id ao cliente (útil para debugging)
            if response is not None:
                response.headers["x-request-id"] = request_id
