from unittest.mock import MagicMock, patch

from matching.feed import build_ranked_feed, get_candidate_score
from shared.models import User


def test_get_candidate_score_uses_cache():
    db = MagicMock()
    redis_client = MagicMock()

    with patch(
        "matching.feed.get_cached_score",
        return_value=88.0,
    ):
        score = get_candidate_score(
            db,
            redis_client,
            "user_a",
            "user_b",
        )

    assert score == 88.0


def test_get_candidate_score_uses_stored_score_on_cache_miss():
    db = MagicMock()
    redis_client = MagicMock()

    score_record = MagicMock()
    score_record.score = 76.0

    with (
        patch(
            "matching.feed.get_cached_score",
            return_value=None,
        ),
        patch(
            "matching.feed.get_stored_compatibility_score",
            return_value=score_record,
        ),
        patch(
            "matching.feed.set_cached_score",
        ) as cache_set,
    ):
        score = get_candidate_score(
            db,
            redis_client,
            "user_a",
            "user_b",
        )

    assert score == 76.0

    cache_set.assert_called_once_with(
        redis_client,
        "user_a",
        "user_b",
        76.0,
    )


def test_get_candidate_score_recomputes_when_missing():
    db = MagicMock()
    redis_client = MagicMock()

    score_record = MagicMock()
    score_record.score = 91.0

    with (
        patch(
            "matching.feed.get_cached_score",
            return_value=None,
        ),
        patch(
            "matching.feed.get_stored_compatibility_score",
            side_effect=ValueError,
        ),
        patch(
            "matching.feed.recompute_compatibility_score",
            return_value=score_record,
        ),
        patch(
            "matching.feed.set_cached_score",
        ),
    ):
        score = get_candidate_score(
            db,
            redis_client,
            "user_a",
            "user_b",
        )

    assert score == 91.0


def test_build_ranked_feed_sorts_descending():
    db = MagicMock()
    redis_client = MagicMock()

    current_user = User(
        id="current",
        latitude=31.10,
        longitude=77.17,
        max_distance_km=100.0,
    )

    candidate_a = User(
        id="candidate_a",
        latitude=31.11,
        longitude=77.18,
    )

    candidate_b = User(
        id="candidate_b",
        latitude=31.12,
        longitude=77.19,
    )

    candidate_c = User(
        id="candidate_c",
        latitude=31.13,
        longitude=77.20,
    )

    scores = {
        "candidate_a": 70.0,
        "candidate_b": 95.0,
        "candidate_c": 82.0,
    }

    def fake_score(
        db,
        redis_client,
        current_user_id,
        candidate_id,
    ):
        return scores[candidate_id]

    with patch(
        "matching.feed.get_candidate_score",
        side_effect=fake_score,
    ):
        feed = build_ranked_feed(
            db,
            redis_client,
            current_user,
            [
                candidate_a,
                candidate_b,
                candidate_c,
            ],
        )

    assert [candidate.user_id for candidate in feed] == [
        "candidate_b",
        "candidate_c",
        "candidate_a",
    ]


def test_build_ranked_feed_excludes_out_of_range_candidate():
    db = MagicMock()
    redis_client = MagicMock()

    current_user = User(
        id="current",
        latitude=31.10,
        longitude=77.17,
        max_distance_km=10.0,
    )

    candidate = User(
        id="far_user",
        latitude=28.61,
        longitude=77.20,
    )

    feed = build_ranked_feed(
        db,
        redis_client,
        current_user,
        [candidate],
    )

    assert feed == []


def test_build_ranked_feed_empty_candidates():
    db = MagicMock()
    redis_client = MagicMock()

    current_user = User(
        id="current",
        latitude=31.10,
        longitude=77.17,
        max_distance_km=100.0,
    )

    feed = build_ranked_feed(
        db,
        redis_client,
        current_user,
        [],
    )

    assert feed == []