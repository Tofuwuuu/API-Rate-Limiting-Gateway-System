"""Rate limiting using Redis sliding window."""
import time
from fastapi import Request

from .redis_client import get_redis
from .config import get_settings


def check_rate_limit(api_key: str) -> tuple[bool, int, int]:
    """
    Check if request is within rate limit.
    Returns (allowed, current_count, limit).
    """
    r = get_redis()
    if not r:
        return True, 0, 999999  # Allow if Redis down
    settings = get_settings()
    key = f"ratelimit:{api_key}"
    window = settings.rate_limit_window_seconds
    limit = settings.rate_limit_requests
    now = time.time()
    window_start = now - window

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window + 1)
    results = pipe.execute()
    count = results[2]

    allowed = count <= limit
    return allowed, count, limit


async def rate_limit_middleware(request: Request, api_key: str) -> tuple[bool, int]:
    """
    Check rate limit. Returns (allowed, retry_after_seconds).
    """
    allowed, count, limit = check_rate_limit(api_key)
    retry_after = get_settings().rate_limit_window_seconds
    return allowed, retry_after
