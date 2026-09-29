from unittest.mock import MagicMock

import pytest
from matching.cache import (
    build_score_cache_key,
    get_cached_score,
    set_cached_score,
)


def test_cache_key_is_symmetric():
    key_a = build_score_cache_key(
        "user_a",
        "user_b",
    )

    key_b = build_score_cache_key(
        "user_b",
        "user_a",
    )

    assert key_a == key_b


def test_get_cached_score_hit():
    redis_client = MagicMock()

    redis_client.get.return_value = b"84.5"

    score = get_cached_score(
        redis_client,
        "user_a",
        "user_b",
    )

    assert score == pytest.approx(84.5)


def test_get_cached_score_miss():
    redis_client = MagicMock()

    redis_client.get.return_value = None

    score = get_cached_score(
        redis_client,
        "user_a",
        "user_b",
    )

    assert score is None


def test_set_cached_score():
    redis_client = MagicMock()

    set_cached_score(
        redis_client,
        "user_a",
        "user_b",
        92.5,
    )

    redis_client.set.assert_called_once_with(
        "compatibility:user_a:user_b",
        92.5,
        ex=3600,
    )