from collections import defaultdict
from collections.abc import Callable

from music_ingestion.genre_cache import get_or_fetch_artist_genres
from sqlalchemy.orm import Session


def build_genre_vector_from_artists(
    session: Session,
    ranked_artist_ids: list[str],
    fetch_genres: Callable[[str], list[str]],
) -> dict[str, float]:
    """Build a normalized genre vector from ranked artist IDs."""

    ranked_genres = [
        get_or_fetch_artist_genres(
            session,
            artist_id,
            fetch_genres,
        )
        for artist_id in ranked_artist_ids
    ]

    return build_genre_vector(ranked_genres)
def build_genre_vector(
    ranked_genres: list[list[str]],
) -> dict[str, float]:
    """Build an L1-normalized genre vector from ranked genre lists."""

    if not ranked_genres:
        return {}

    genre_weights: dict[str, float] = defaultdict(float)

    for rank, genres in enumerate(ranked_genres, start=1):
        if not genres:
            continue

        unique_genres = set(genres)

        rank_weight = 1.0 / rank
        weight_per_genre = rank_weight / len(unique_genres)

        for genre in unique_genres:
            genre_weights[genre] += weight_per_genre

    total_weight = sum(genre_weights.values())

    if total_weight == 0:
        return {}

    return {
        genre: weight / total_weight
        for genre, weight in genre_weights.items()
    }