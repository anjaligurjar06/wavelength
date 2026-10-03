import pytest
from compatibility_engine.scoring import (
    adaptive_composite_score,
    adaptive_weights,
    build_score_breakdown,
    composite_score,
    genre_coverage,
    needs_manual_genre_fallback,
)


def test_composite_score():
    score = composite_score(
        artist_overlap=0.5,
        genre_similarity=0.75,
    )

    assert score == pytest.approx(0.60)


def test_identical_profiles():
    result = build_score_breakdown(
        artists_a=["artist_1", "artist_2"],
        artists_b=["artist_1", "artist_2"],
        genre_vector_a={"pop": 0.6, "rock": 0.4},
        genre_vector_b={"pop": 0.6, "rock": 0.4},
    )

    assert result.score == pytest.approx(1.0)
    assert result.artist_overlap == pytest.approx(1.0)
    assert result.genre_similarity == pytest.approx(1.0)
    assert result.shared_artists == ["artist_1", "artist_2"]
    assert result.shared_genres == ["pop", "rock"]


def test_completely_different_profiles():
    result = build_score_breakdown(
        artists_a=["artist_1", "artist_2"],
        artists_b=["artist_3", "artist_4"],
        genre_vector_a={"pop": 1.0},
        genre_vector_b={"jazz": 1.0},
    )

    assert result.score == pytest.approx(0.0)
    assert result.artist_overlap == pytest.approx(0.0)
    assert result.genre_similarity == pytest.approx(0.0)
    assert result.shared_artists == []
    assert result.shared_genres == []


def test_partial_profile_overlap():
    result = build_score_breakdown(
        artists_a=["artist_1", "artist_2", "artist_3"],
        artists_b=["artist_2", "artist_3", "artist_4"],
        genre_vector_a={"pop": 0.6, "rock": 0.4},
        genre_vector_b={"pop": 0.5, "jazz": 0.5},
    )

    assert result.artist_overlap == pytest.approx(0.5)
    assert 0.0 < result.genre_similarity < 1.0

    assert result.score == pytest.approx(
        0.60 * result.artist_overlap
        + 0.40 * result.genre_similarity
    )

    assert result.shared_artists == ["artist_2", "artist_3"]
    assert result.shared_genres == ["pop"]


def test_empty_profiles():
    result = build_score_breakdown(
        artists_a=[],
        artists_b=[],
        genre_vector_a={},
        genre_vector_b={},
    )

    assert result.score == pytest.approx(0.0)
    assert result.artist_overlap == pytest.approx(0.0)
    assert result.genre_similarity == pytest.approx(0.0)
    assert result.shared_artists == []
    assert result.shared_genres == []


def test_genre_coverage_complete():
    artists = [
        {"id": "1", "genres": ["pop"]},
        {"id": "2", "genres": ["rock"]},
    ]

    assert genre_coverage(artists) == pytest.approx(1.0)


def test_genre_coverage_partial():
    artists = [
        {"id": "1", "genres": ["pop"]},
        {"id": "2", "genres": []},
        {"id": "3", "genres": ["rock"]},
        {"id": "4", "genres": []},
    ]

    assert genre_coverage(artists) == pytest.approx(0.5)


def test_genre_coverage_empty():
    assert genre_coverage([]) == pytest.approx(0.0)


def test_adaptive_weights_full_coverage():
    artist_weight, genre_weight = adaptive_weights(
        1.0,
        1.0,
    )

    assert artist_weight == pytest.approx(0.60)
    assert genre_weight == pytest.approx(0.40)


def test_adaptive_weights_partial_coverage():
    artist_weight, genre_weight = adaptive_weights(
        0.5,
        0.8,
    )

    assert artist_weight == pytest.approx(0.80)
    assert genre_weight == pytest.approx(0.20)


def test_adaptive_weights_no_coverage():
    artist_weight, genre_weight = adaptive_weights(
        0.0,
        1.0,
    )

    assert artist_weight == pytest.approx(1.0)
    assert genre_weight == pytest.approx(0.0)


def test_adaptive_composite_score_full_coverage():
    score = adaptive_composite_score(
        artist_overlap=0.5,
        genre_similarity=0.75,
        coverage_a=1.0,
        coverage_b=1.0,
    )

    assert score == pytest.approx(0.60)


def test_adaptive_composite_score_partial_coverage():
    score = adaptive_composite_score(
        artist_overlap=0.7,
        genre_similarity=0.2,
        coverage_a=0.5,
        coverage_b=0.8,
    )

    assert score == pytest.approx(0.60)


def test_adaptive_composite_score_no_genre_data():
    score = adaptive_composite_score(
        artist_overlap=0.7,
        genre_similarity=0.0,
        coverage_a=0.0,
        coverage_b=1.0,
    )

    assert score == pytest.approx(0.70)


def test_manual_fallback_not_needed_with_good_coverage():
    assert needs_manual_genre_fallback(
        0.8,
        0.9,
    ) is False


def test_manual_fallback_needed_with_low_coverage():
    assert needs_manual_genre_fallback(
        0.2,
        0.8,
    ) is True


def test_manual_fallback_needed_with_no_genre_data():
    assert needs_manual_genre_fallback(
        0.0,
        1.0,
    ) is True


def test_manual_fallback_uses_custom_threshold():
    assert needs_manual_genre_fallback(
        0.4,
        0.8,
        threshold=0.5,
    ) is True
def test_artist_weight_is_stronger_than_genre_weight():
    artist_only_score = composite_score(
        artist_overlap=1.0,
        genre_similarity=0.0,
    )

    genre_only_score = composite_score(
        artist_overlap=0.0,
        genre_similarity=1.0,
    )

    assert artist_only_score == pytest.approx(0.60)
    assert genre_only_score == pytest.approx(0.40)
    assert artist_only_score > genre_only_score


def test_full_coverage_uses_60_40_weights():
    score = adaptive_composite_score(
        artist_overlap=0.8,
        genre_similarity=0.5,
        coverage_a=1.0,
        coverage_b=1.0,
    )

    expected = (0.60 * 0.8) + (0.40 * 0.5)

    assert score == pytest.approx(expected)


def test_missing_genres_shift_weight_to_artists():
    artist_weight, genre_weight = adaptive_weights(
        coverage_a=0.25,
        coverage_b=1.0,
    )

    assert artist_weight == pytest.approx(0.90)
    assert genre_weight == pytest.approx(0.10)


from compatibility_engine.scoring import (  # noqa: E402
    NO_OVERLAP_FLOOR,
    apply_score_floor,
    artist_key,
    is_sparse_profile,
)


def test_profile_with_two_artists_is_sparse():
    assert is_sparse_profile([{"id": "a"}, {"id": "b"}]) is True


def test_profile_with_zero_artists_is_sparse():
    assert is_sparse_profile([]) is True


def test_profile_with_enough_artists_is_not_sparse():
    artists = [{"id": str(i)} for i in range(5)]
    assert is_sparse_profile(artists) is False

def test_artist_key_uses_id_for_spotify_artist():
    assert artist_key({"id": "abc", "name": "Drake"}) == "abc"


def test_artist_key_uses_lowercase_name_when_no_id():
    assert artist_key({"id": None, "name": "  Drake "}) == "drake"


def test_artist_key_can_force_names():
    assert artist_key({"id": "abc", "name": "Drake"}, use_names=True) == "drake"


def test_artist_key_returns_none_for_empty_name():
    assert artist_key({"id": None, "name": "  "}) is None


def test_floor_applied_when_no_overlap():
    assert apply_score_floor(0.0, has_overlap=False) == NO_OVERLAP_FLOOR


def test_floor_never_lifts_a_real_score():
    assert apply_score_floor(0.4, has_overlap=True) == 0.4


def test_floor_does_not_lower_a_higher_score():
    assert apply_score_floor(0.5, has_overlap=False) == 0.5