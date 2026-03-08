"""API Gateway - Lightweight Kong-like gateway with rate limiting, auth, and caching."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .auth import verify_api_key
from .rate_limit import rate_limit_middleware
from .cache import get_cached_response, cache_response
from .logging_middleware import RequestLoggingMiddleware
from .proxy import proxy_request


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    yield
    # Cleanup if needed


app = FastAPI(
    title="API Gateway",
    description="Lightweight API gateway with rate limiting, auth, caching, and analytics",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)


@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    """Main gateway middleware: auth -> rate limit -> cache -> proxy."""
    # Skip for health and internal routes
    if request.url.path in ["/health", "/metrics", "/api/analytics"]:
        return await call_next(request)

    # API key authentication
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Rate limiting
    rate_ok, retry_after = await rate_limit_middleware(request, api_key)
    if not rate_ok:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

    # Check cache for GET requests
    if request.method == "GET":
        cached = get_cached_response(request, api_key)
        if cached:
            return cached

    # Proxy to backend
    response = await proxy_request(request, request.url.path)

    # Cache GET responses
    if request.method == "GET" and response.status_code == 200:
        cache_response(request, api_key, response)

    return response


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    """Basic metrics for monitoring."""
    from .redis_client import get_redis

    redis = get_redis()
    if not redis:
        return {"redis": "disconnected", "status": "degraded"}

    total = redis.get("gateway:stats:total_requests") or 0
    return {
        "redis": "connected",
        "status": "healthy",
        "total_requests": int(total),
    }


# Analytics API for the dashboard
@app.get("/api/analytics")
async def analytics():
    """Analytics data for the dashboard."""
    from .redis_client import get_redis
    import json

    redis = get_redis()
    if not redis:
        return {"error": "Redis not available", "logs": [], "stats": {}}

    # Get recent logs
    raw_logs = redis.lrange("gateway:logs", 0, 99)
    logs = [json.loads(log) for log in (raw_logs or [])]

    # Get stats
    total = redis.get("gateway:stats:total_requests") or 0
    by_status = redis.hgetall("gateway:stats:by_status") or {}
    by_path = redis.hgetall("gateway:stats:by_path") or {}

    return {
        "total_requests": int(total),
        "by_status": {str(k) if isinstance(k, bytes) else k: int(v) for k, v in by_status.items()},
        "by_path": {str(k) if isinstance(k, bytes) else k: int(v) for k, v in by_path.items()},
        "recent_logs": logs,
    }
