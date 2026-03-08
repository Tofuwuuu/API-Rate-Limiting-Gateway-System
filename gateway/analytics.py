"""Analytics storage and aggregation for the gateway."""

from datetime import datetime, timedelta
from typing import Any

from .redis_client import get_redis


def log_request(
    api_key: str,
    path: str,
    method: str,
    status_code: int,
    response_time_ms: float,
    cached: bool = False,
) -> None:
    """Log a request for analytics."""
    redis = get_redis()
    if not redis:
        return

    timestamp = datetime.utcnow()
    key = f"req:{timestamp.strftime('%Y%m%d%H%M%S')}:{api_key[:8]}"
    data = {
        "api_key": api_key[:8] + "...",
        "path": path,
        "method": method,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "cached": cached,
        "timestamp": timestamp.isoformat(),
    }
    redis.hset(key, mapping={k: str(v) for k, v in data.items()})
    redis.expire(key, 86400 * 7)  # 7 days

    # Increment counters
    redis.incr("stats:total_requests")
    redis.incr(f"stats:by_path:{path}")
    redis.incr(f"stats:by_status:{status_code}")
    redis.incr(f"stats:by_key:{api_key[:8]}")
    if cached:
        redis.incr("stats:cache_hits")


def get_analytics_summary() -> dict[str, Any]:
    """Get aggregated analytics summary."""
    redis = get_redis()
    if not redis:
        return {"error": "Redis not available"}

    total = redis.get("stats:total_requests") or 0
    cache_hits = redis.get("stats:cache_hits") or 0

    # Get top paths
    path_keys = redis.keys("stats:by_path:*")
    by_path = {}
    for pk in path_keys[:20]:
        count = redis.get(pk)
        if count:
            by_path[pk.decode().replace("stats:by_path:", "")] = int(count)

    # Get by status
    status_keys = redis.keys("stats:by_status:*")
    by_status = {}
    for sk in status_keys:
        count = redis.get(sk)
        if count:
            by_status[sk.decode().replace("stats:by_status:", "")] = int(count)

    # Get recent requests (last 100)
    req_keys = sorted(redis.keys("req:*"), reverse=True)[:100]
    recent = []
    for rk in req_keys:
        data = redis.hgetall(rk)
        if data:
            recent.append({k.decode(): v.decode() for k, v in data.items()})

    return {
        "total_requests": int(total),
        "cache_hits": int(cache_hits),
        "cache_hit_rate": int(cache_hits) / int(total) * 100 if int(total) > 0 else 0,
        "by_path": dict(sorted(by_path.items(), key=lambda x: x[1], reverse=True)),
        "by_status": by_status,
        "recent_requests": recent,
    }
