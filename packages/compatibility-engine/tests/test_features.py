import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from compatibility_engine.features import (
    build_genre_vector,
    build_genre_vector_from_artists,
)
from shared.models import Base


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    return Session(engine)


def test_build_genre_vector_from_artists():
    session = make_session()

    calls = 0

    artist_genres = {
        "artist_1": ["pop", "dance"],
        "artist_2": ["rock"],
        "artist_3": ["pop", "indie"],
    }

    def fetch_genres(artist_id: str) -> list[str]:
        nonlocal calls
        calls += 1
        return artist_genres[artist_id]

    vector = build_genre_vector_from_artists(
        session,
        [
            "artist_1",
            "artist_2",
            "artist_3",
        ],
        fetch_genres,
    )

    assert sum(vector.values()) == pytest.approx(1.0)

    assert vector["pop"] > vector["indie"]
    assert vector["pop"] > vector["rock"]

    assert calls == 3


def test_build_genre_vector_from_artists_uses_cache():
    session = make_session()

    calls = 0

    artist_genres = {
        "artist_1": ["pop"],
        "artist_2": ["rock"],
    }

    def fetch_genres(artist_id: str) -> list[str]:
        nonlocal calls
        calls += 1
        return artist_genres[artist_id]

    first = build_genre_vector_from_artists(
        session,
        ["artist_1", "artist_2"],
        fetch_genres,
    )

    second = build_genre_vector_from_artists(
        session,
        ["artist_1", "artist_2"],
        fetch_genres,
    )

    assert first == second
    assert calls == 2


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