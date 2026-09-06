from music_ingestion.genre_cache import get_or_fetch_artist_genres
from shared.models import ArtistGenreCache, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    return Session(engine)


def test_cache_miss_fetches_and_stores_genres():
    session = make_session()

    calls = 0

    def fetch_genres(artist_id: str) -> list[str]:
        nonlocal calls
        calls += 1
        return ["pop", "dance"]

    genres = get_or_fetch_artist_genres(
        session,
        "artist_1",
        fetch_genres,
    )

    assert genres == ["pop", "dance"]
    assert calls == 1

    cached = session.get(ArtistGenreCache, "artist_1")

    assert cached is not None
    assert cached.genres == ["pop", "dance"]


def test_cache_hit_does_not_fetch_again():
    session = make_session()

    session.add(
        ArtistGenreCache(
            artist_id="artist_1",
            genres=["rock", "indie"],
        )
    )
    session.commit()

    calls = 0

    def fetch_genres(artist_id: str) -> list[str]:
        nonlocal calls
        calls += 1
        return ["pop"]

    genres = get_or_fetch_artist_genres(
        session,
        "artist_1",
        fetch_genres,
    )

    assert genres == ["rock", "indie"]
    assert calls == 0


def test_repeated_request_fetches_only_once():
    session = make_session()

    calls = 0

    def fetch_genres(artist_id: str) -> list[str]:
        nonlocal calls
        calls += 1
        return ["jazz"]

    first = get_or_fetch_artist_genres(
        session,
        "artist_2",
        fetch_genres,
    )

    second = get_or_fetch_artist_genres(
        session,
        "artist_2",
        fetch_genres,
    )

    assert first == ["jazz"]
    assert second == ["jazz"]
    assert calls == 1


def test_empty_genres_are_cached():
    session = make_session()

    calls = 0

    def fetch_genres(artist_id: str) -> list[str]:
        nonlocal calls
        calls += 1
        return []

    first = get_or_fetch_artist_genres(
        session,
        "artist_empty",
        fetch_genres,
    )

    second = get_or_fetch_artist_genres(
        session,
        "artist_empty",
        fetch_genres,
    )

    assert first == []
    assert second == []
    assert calls == 1