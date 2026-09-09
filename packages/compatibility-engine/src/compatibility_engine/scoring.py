from dataclasses import dataclass

from compatibility_engine.similarity import cosine_similarity, jaccard_similarity

ARTIST_WEIGHT = 0.60
GENRE_WEIGHT = 0.40

# Provisional threshold.
# This can be tuned later using real Spotify/user data.
DEFAULT_MANUAL_FALLBACK_THRESHOLD = 0.30


@dataclass(frozen=True)
class ScoreBreakdown:
    score: float
    artist_overlap: float
    genre_similarity: float
    shared_artists: list[str]
    shared_genres: list[str]


def composite_score(
    artist_overlap: float,
    genre_similarity: float,
) -> float:
    """Combine artist and genre similarity into the MVP compatibility score."""

    return (
        ARTIST_WEIGHT * artist_overlap
        + GENRE_WEIGHT * genre_similarity
    )


def build_score_breakdown(
    artists_a: list[str],
    artists_b: list[str],
    genre_vector_a: dict[str, float],
    genre_vector_b: dict[str, float],
) -> ScoreBreakdown:
    """Build the standard MVP compatibility score and its components."""

    artist_score = jaccard_similarity(artists_a, artists_b)
    genre_score = cosine_similarity(
        genre_vector_a,
        genre_vector_b,
    )

    score = composite_score(
        artist_score,
        genre_score,
    )

    shared_artists = sorted(
        set(artists_a) & set(artists_b)
    )
    shared_genres = sorted(
        set(genre_vector_a) & set(genre_vector_b)
    )

    return ScoreBreakdown(
        score=score,
        artist_overlap=artist_score,
        genre_similarity=genre_score,
        shared_artists=shared_artists,
        shared_genres=shared_genres,
    )


def genre_coverage(top_artists: list[dict]) -> float:
    """Return the fraction of artists that have genre metadata."""

    if not top_artists:
        return 0.0

    artists_with_genres = sum(
        1
        for artist in top_artists
        if artist.get("genres")
    )

    return artists_with_genres / len(top_artists)


def adaptive_weights(
    coverage_a: float,
    coverage_b: float,
) -> tuple[float, float]:
    """Adjust artist and genre weights based on available genre data."""

    pair_coverage = min(
        coverage_a,
        coverage_b,
    )

    genre_weight = GENRE_WEIGHT * pair_coverage
    artist_weight = 1.0 - genre_weight

    return artist_weight, genre_weight


def adaptive_composite_score(
    artist_overlap: float,
    genre_similarity: float,
    coverage_a: float,
    coverage_b: float,
) -> float:
    """Calculate compatibility while accounting for missing genre metadata."""

    artist_weight, genre_weight = adaptive_weights(
        coverage_a,
        coverage_b,
    )

    return (
        artist_weight * artist_overlap
        + genre_weight * genre_similarity
    )


def needs_manual_genre_fallback(
    coverage_a: float,
    coverage_b: float,
    threshold: float = DEFAULT_MANUAL_FALLBACK_THRESHOLD,
) -> bool:
    """Return True when genre coverage is too low for reliable genre scoring."""

    pair_coverage = min(
        coverage_a,
        coverage_b,
    )

    return pair_coverage < threshold