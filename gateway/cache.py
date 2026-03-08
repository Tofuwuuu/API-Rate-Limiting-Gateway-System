"""Response caching using Redis."""
import hashlib
import json
from fastapi import Request
from fastapi.responses import Response

from .redis_client import get_redis
from .config import get_settings


def _cache_key(method: str, path: str, query: str) -> str:
    h = hashlib.sha256(f"{method}:{path}:{query}".encode()).hexdigest()
    return f"cache:{h}"


def get_cached_response(request: Request, api_key: str = "") -> Response | None:
    """Return cached response if exists."""
    r = get_redis()
    if not r:
        return None
    path = request.url.path
    query = request.url.query or ""
    key = _cache_key(request.method, path, query)
    data = r.get(key)
    if not data:
        return None
    try:
        stored = json.loads(data)
        return Response(
            content=stored["body"].encode("latin-1") if isinstance(stored["body"], str) else stored["body"],
            status_code=stored.get("status_code", 200),
            media_type=stored.get("content_type", "application/json"),
        )
    except (json.JSONDecodeError, KeyError):
        return None


def cache_response(request: Request, api_key: str, response: Response) -> None:
    """Cache response body for GET requests."""
    r = get_redis()
    if not r:
        return
    path = request.url.path
    query = request.url.query or ""
    key = _cache_key(request.method, path, query)
    body = getattr(response, "body", None) or getattr(response, "content", b"")
    if not isinstance(body, bytes):
        body = body.encode() if isinstance(body, str) else b""
    stored = {
        "body": body.decode("latin-1", errors="replace"),
        "status_code": response.status_code,
        "content_type": response.media_type or "application/json",
    }
    settings = get_settings()
    r.setex(key, settings.cache_ttl_seconds, json.dumps(stored))
