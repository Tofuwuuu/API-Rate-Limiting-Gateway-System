"""Request logging middleware for the API gateway."""

import time
import json
from datetime import datetime
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .redis_client import get_redis


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs all requests to Redis for analytics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key", "anonymous")
        path = str(request.url.path)
        method = request.method

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "api_key": api_key[:8] + "..." if len(api_key) > 8 else api_key,
        }

        try:
            r = get_redis()
            if r:
                r.lpush("gateway:logs", json.dumps(log_entry))
                r.ltrim("gateway:logs", 0, 9999)  # Keep last 10k logs
                r.incr("gateway:stats:total_requests")
                r.hincrby("gateway:stats:by_status", str(status_code), 1)
                r.hincrby("gateway:stats:by_path", path, 1)
        except Exception:
            pass  # Don't fail requests if logging fails

        return response
