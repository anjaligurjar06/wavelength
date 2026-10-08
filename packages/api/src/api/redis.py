from functools import lru_cache

from redis import Redis

from api.config import settings


@lru_cache(maxsize=1)
def get_redis() -> Redis:
    """Return the shared Redis client used by the API."""

    return Redis.from_url(settings.redis_url, decode_responses=True)
