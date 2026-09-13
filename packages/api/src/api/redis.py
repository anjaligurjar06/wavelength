from redis import Redis


def get_redis() -> Redis:
    """Return the Redis client used by the API."""

    return Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )