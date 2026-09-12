from shared.models import CompatibilityScore, UserMusicProfile
from sqlalchemy.orm import Session

from compatibility_engine.features import build_genre_vector
from compatibility_engine.scoring import (
    ScoreBreakdown,
    adaptive_composite_score,
    genre_coverage,
)
from compatibility_engine.similarity import cosine_similarity, jaccard_similarity


def get_compatibility_score(
    db: Session,
    user_a_id: str,
    user_b_id: str,
) -> ScoreBreakdown:
    """Calculate compatibility between two users from cached music profiles."""

    profile_a = (
        db.query(UserMusicProfile)
        .filter_by(user_id=user_a_id)
        .one_or_none()
    )
    profile_b = (
        db.query(UserMusicProfile)
        .filter_by(user_id=user_b_id)
        .one_or_none()
    )

    if profile_a is None or profile_b is None:
        raise ValueError("Music profile not found for one or both users")

    artists_a = profile_a.top_artists.get("items", [])
    artists_b = profile_b.top_artists.get("items", [])

    artist_ids_a = [
        artist["id"]
        for artist in artists_a
        if artist.get("id")
    ]
    artist_ids_b = [
        artist["id"]
        for artist in artists_b
        if artist.get("id")
    ]

    ranked_genres_a = [
        artist.get("genres", [])
        for artist in artists_a
    ]
    ranked_genres_b = [
        artist.get("genres", [])
        for artist in artists_b
    ]

    genre_vector_a = build_genre_vector(ranked_genres_a)
    genre_vector_b = build_genre_vector(ranked_genres_b)

    artist_overlap = jaccard_similarity(
        artist_ids_a,
        artist_ids_b,
    )

    genre_similarity = cosine_similarity(
        genre_vector_a,
        genre_vector_b,
    )

    coverage_a = genre_coverage(artists_a)
    coverage_b = genre_coverage(artists_b)

    score = adaptive_composite_score(
        artist_overlap,
        genre_similarity,
        coverage_a,
        coverage_b,
    )

    shared_artists = sorted(
        set(artist_ids_a) & set(artist_ids_b)
    )

    shared_genres = sorted(
        set(genre_vector_a) & set(genre_vector_b)
    )

    return ScoreBreakdown(
        score=score,
        artist_overlap=artist_overlap,
        genre_similarity=genre_similarity,
        shared_artists=shared_artists,
        shared_genres=shared_genres,
    )


def recompute_compatibility_score(
    db: Session,
    user_a_id: str,
    user_b_id: str,
) -> CompatibilityScore:
    """Recompute compatibility and save the latest result."""

    result = get_compatibility_score(
        db,
        user_a_id,
        user_b_id,
    )

    first_user_id, second_user_id = sorted(
        [user_a_id, user_b_id]
    )

    score_record = (
        db.query(CompatibilityScore)
        .filter_by(
            user_a_id=first_user_id,
            user_b_id=second_user_id,
        )
        .one_or_none()
    )

    breakdown = {
        "artist_overlap": result.artist_overlap,
        "genre_similarity": result.genre_similarity,
        "shared_artists": result.shared_artists,
        "shared_genres": result.shared_genres,
    }

    score_100 = round(result.score * 100, 2)

    if score_record is None:
        score_record = CompatibilityScore(
            user_a_id=first_user_id,
            user_b_id=second_user_id,
            score=score_100,
            breakdown=breakdown,
        )
        db.add(score_record)
    else:
        score_record.score = score_100
        score_record.breakdown = breakdown

    db.commit()
    db.refresh(score_record)

    return score_record


def get_stored_compatibility_score(
    db: Session,
    user_a_id: str,
    user_b_id: str,
) -> CompatibilityScore:
    """Return the latest stored compatibility score for a user pair."""

    first_user_id, second_user_id = sorted(
        [user_a_id, user_b_id]
    )

    score_record = (
        db.query(CompatibilityScore)
        .filter_by(
            user_a_id=first_user_id,
            user_b_id=second_user_id,
        )
        .one_or_none()
    )

    if score_record is None:
        raise ValueError("Compatibility score not found")

    return score_record


def get_score_breakdown(
    db: Session,
    user_a_id: str,
    user_b_id: str,
) -> dict:
    """Return the stored compatibility breakdown for a user pair."""

    score_record = get_stored_compatibility_score(
        db,
        user_a_id,
        user_b_id,
    )

    return score_record.breakdown