from redis import Redis

DEFAULT_SCORE_CACHE_TTL_SECONDS = 3600


def build_score_cache_key(
    user_a_id: str,
    user_b_id: str,
) -> str:
    """Build one stable cache key for a symmetric user pair."""

    first_user_id, second_user_id = sorted(
        [user_a_id, user_b_id]
    )

    return f"compatibility:{first_user_id}:{second_user_id}"


def get_cached_score(
    redis_client: Redis,
    user_a_id: str,
    user_b_id: str,
) -> float | None:
    """Return a cached compatibility score, if present."""

    key = build_score_cache_key(
        user_a_id,
        user_b_id,
    )

    value = redis_client.get(key)

    if value is None:
        return None

    return float(value)


def set_cached_score(
    redis_client: Redis,
    user_a_id: str,
    user_b_id: str,
    score: float,
    ttl_seconds: int = DEFAULT_SCORE_CACHE_TTL_SECONDS,
) -> None:
    """Cache a compatibility score for a limited time."""

    key = build_score_cache_key(
        user_a_id,
        user_b_id,
    )

    redis_client.set(key, score, ex=ttl_seconds)