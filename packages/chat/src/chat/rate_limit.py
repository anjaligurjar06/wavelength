import time

from redis import Redis

MAX_MESSAGES_PER_WINDOW = 12
WINDOW_SECONDS = 60


def check_rate_limit(redis_client: Redis, user_id: str) -> bool:
    """Return True if the user is within their message rate limit.

    Uses a fixed-window counter keyed per user per minute. Returns False
    (rate limited) if the user has already sent MAX_MESSAGES_PER_WINDOW
    messages within the current window.
    """
    window = int(time.time() // WINDOW_SECONDS)
    key = f"chat_rate_limit:{user_id}:{window}"

    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, WINDOW_SECONDS)

    return current <= MAX_MESSAGES_PER_WINDOW
