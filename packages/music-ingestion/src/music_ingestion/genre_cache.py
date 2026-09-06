from collections.abc import Callable

from sqlalchemy.orm import Session

from shared.models import ArtistGenreCache


def get_or_fetch_artist_genres(
    session: Session,
    artist_id: str,
    fetch_genres: Callable[[str], list[str]],
) -> list[str]:
    """Return cached artist genres, or fetch and cache them if missing."""

    cached = session.get(ArtistGenreCache, artist_id)

    if cached is not None:
        return cached.genres

    genres = fetch_genres(artist_id)

    cache_entry = ArtistGenreCache(
        artist_id=artist_id,
        genres=genres,
    )

    session.add(cache_entry)
    session.commit()

    return genres