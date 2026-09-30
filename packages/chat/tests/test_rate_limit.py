from unittest.mock import MagicMock

from chat.rate_limit import MAX_MESSAGES_PER_WINDOW, check_rate_limit


def test_allows_message_within_limit():
    redis_client = MagicMock()
    redis_client.incr.return_value = 1

    assert check_rate_limit(redis_client, "user_a") is True
    redis_client.expire.assert_called_once()


def test_blocks_message_over_limit():
    redis_client = MagicMock()
    redis_client.incr.return_value = MAX_MESSAGES_PER_WINDOW + 1

    assert check_rate_limit(redis_client, "user_a") is False


def test_allows_message_at_exact_limit():
    redis_client = MagicMock()
    redis_client.incr.return_value = MAX_MESSAGES_PER_WINDOW

    assert check_rate_limit(redis_client, "user_a") is True


def test_only_sets_expiry_on_first_message_in_window():
    redis_client = MagicMock()
    redis_client.incr.return_value = 5

    check_rate_limit(redis_client, "user_a")

    redis_client.expire.assert_not_called()


def test_uses_per_user_key():
    redis_client = MagicMock()
    redis_client.incr.return_value = 1

    check_rate_limit(redis_client, "user_a")
    key_used = redis_client.incr.call_args[0][0]

    assert "user_a" in key_used
    assert key_used.startswith("chat_rate_limit:")
