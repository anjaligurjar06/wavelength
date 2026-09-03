import pytest

from compatibility_engine.features import build_genre_vector


def test_genre_vector_sums_to_one():
    genres = [
        ["pop", "dance"],
        ["rock"],
        ["pop", "indie"],
    ]

    vector = build_genre_vector(genres)

    assert sum(vector.values()) == pytest.approx(1.0)


def test_higher_rank_has_more_weight():
    genres = [
        ["pop"],
        ["rock"],
    ]

    vector = build_genre_vector(genres)

    assert vector["pop"] > vector["rock"]


def test_empty_input():
    assert build_genre_vector([]) == {}