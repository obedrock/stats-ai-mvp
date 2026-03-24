"""Redis cache helpers for data pipeline results.

Provides get/set operations with TTL support using source-appropriate expiry:
- FRED data: 86400 seconds (24 hours)
- Yahoo Finance data: 3600 seconds (1 hour)

Key format: {source}:{series_id}:{start}:{end}
"""
import redis as redis_lib

_redis = None


def get_redis() -> redis_lib.Redis:
    """Lazily initialize and return the Redis client."""
    global _redis
    if _redis is None:
        from app.config import settings
        _redis = redis_lib.Redis.from_url(settings.redis_url)
    return _redis


def init_redis(redis_client) -> None:
    """Inject a Redis client — used in tests to swap in fakeredis."""
    global _redis
    _redis = redis_client


def get_cached(key: str) -> str | None:
    """Retrieve a cached value by key.

    Args:
        key: Cache key in format {source}:{series_id}:{start}:{end}.

    Returns:
        Cached JSON string, or None if key not found or expired.
    """
    client = get_redis()
    value = client.get(key)
    if value is None:
        return None
    return value.decode()


def set_cached(key: str, value: str, ttl: int) -> None:
    """Store a value in cache with a TTL.

    Args:
        key: Cache key in format {source}:{series_id}:{start}:{end}.
        value: JSON-serialized string to cache.
        ttl: Time-to-live in seconds.
    """
    client = get_redis()
    client.setex(key, ttl, value)
