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

def get_cached_scores(
    redis_client: Redis,
    user_id: str,
    other_ids: list[str],
) -> dict[str, float]:
    """Fetch many pair scores with one MGET. Returns {other_id: score} for hits."""

    if not other_ids:
        return {}

    keys = [build_score_cache_key(user_id, other_id) for other_id in other_ids]
    values = redis_client.mget(keys)

    # An unexpected reply is treated as a full cache miss, never an error.
    if not isinstance(values, (list, tuple)) or len(values) != len(keys):
        return {}

    return {
        other_id: float(value)
        for other_id, value in zip(other_ids, values)
        if value is not None
    }


def set_cached_scores(
    redis_client: Redis,
    user_id: str,
    scores: dict[str, float],
    ttl_seconds: int = DEFAULT_SCORE_CACHE_TTL_SECONDS,
) -> None:
    """Cache many pair scores in a single pipelined round trip."""

    if not scores:
        return

    pipe = redis_client.pipeline()
    for other_id, score in scores.items():
        pipe.set(build_score_cache_key(user_id, other_id), score, ex=ttl_seconds)
    pipe.execute()