"""Redis client for rate limiting and caching."""
import redis
from .config import get_settings


_redis: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    """Get Redis connection (sync). Returns None if Redis is unavailable."""
    global _redis
    try:
        if _redis is None:
            settings = get_settings()
            _redis = redis.from_url(settings.redis_url, decode_responses=True)
        _redis.ping()
        return _redis
    except Exception:
        return None
