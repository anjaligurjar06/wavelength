from shared.models import CompatibilityScore, UserMusicProfile
from sqlalchemy.orm import Session

from compatibility_engine.explanations import render_score_breakdown
from compatibility_engine.features import (
    build_genre_vector,
    build_manual_genre_vector,
)
from compatibility_engine.scoring import (
    ScoreBreakdown,
    adaptive_composite_score,
    apply_score_floor,
    artist_key,
    genre_coverage,
    is_manual_profile,
    is_sparse_profile,
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

    return score_profiles(profile_a, profile_b)


def score_profiles(
    profile_a: UserMusicProfile,
    profile_b: UserMusicProfile,
) -> ScoreBreakdown:
    """Calculate compatibility between two already-loaded music profiles."""

    artists_a = (profile_a.top_artists or {}).get("items", [])
    artists_b = (profile_b.top_artists or {}).get("items", [])

    # If either user entered music manually, compare artists by name.
    use_names = is_manual_profile(
        profile_a.time_window
    ) or is_manual_profile(
        profile_b.time_window
    )

    artist_ids_a = [
        key
        for artist in artists_a
        if (key := artist_key(artist, use_names))
    ]

    artist_ids_b = [
        key
        for artist in artists_b
        if (key := artist_key(artist, use_names))
    ]

    genre_vector_a, coverage_a = _genre_data(
        profile_a,
        artists_a,
    )

    genre_vector_b, coverage_b = _genre_data(
        profile_b,
        artists_b,
    )

    artist_overlap = jaccard_similarity(
        artist_ids_a,
        artist_ids_b,
    )

    genre_similarity = cosine_similarity(
        genre_vector_a,
        genre_vector_b,
    )

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

    has_overlap = bool(
        shared_artists or shared_genres
    )

    score = apply_score_floor(
        score,
        has_overlap,
    )

    low_confidence = (
        is_sparse_profile(artists_a)
        or is_sparse_profile(artists_b)
    )

    return ScoreBreakdown(
        score=score,
        artist_overlap=artist_overlap,
        genre_similarity=genre_similarity,
        shared_artists=shared_artists,
        shared_genres=shared_genres,
        low_confidence=low_confidence,
    )


def _genre_data(
    profile: UserMusicProfile,
    artists: list[dict],
) -> tuple[dict[str, float], float]:
    """Return (genre_vector, coverage) for one user.

    Spotify users: genres come from their artists.
    Manual users: genres come from the list they typed in.
    """

    typed_genres = (profile.top_genres or {}).get("genres", [])

    if is_manual_profile(profile.time_window) and typed_genres:
        return build_manual_genre_vector(typed_genres), 1.0

    ranked_genres = [
        artist.get("genres", [])
        for artist in artists
    ]

    return build_genre_vector(ranked_genres), genre_coverage(artists)


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
        "low_confidence": result.low_confidence,
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


def get_shared_artist_names(
    db: Session,
    user_a_id: str,
    user_b_id: str,
    shared_artist_ids: list[str],
) -> list[str]:
    """Return readable artist names for shared Spotify artist IDs."""

    if not shared_artist_ids:
        return []

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
        return []

    artists_a = (profile_a.top_artists or {}).get("items", [])
    artists_b = (profile_b.top_artists or {}).get("items", [])

    artist_names = {}

    for artist in artists_a + artists_b:
        artist_id = artist.get("id")
        artist_name = artist.get("name")

        if artist_id and artist_name:
            artist_names[artist_id] = artist_name

        if artist_name:
            artist_names[
                artist_name.strip().lower()
            ] = artist_name

    return [
        artist_names[artist_id]
        for artist_id in shared_artist_ids
        if artist_id in artist_names
    ]


def get_score_breakdown_explanation(
    db: Session,
    user_a_id: str,
    user_b_id: str,
) -> dict:
    """Return a frontend-readable explanation of the compatibility breakdown."""

    breakdown = get_score_breakdown(
        db,
        user_a_id,
        user_b_id,
    )

    shared_artist_ids = breakdown.get(
        "shared_artists",
        [],
    )

    artist_names = get_shared_artist_names(
        db,
        user_a_id,
        user_b_id,
        shared_artist_ids,
    )

    explanation = render_score_breakdown(
        breakdown,
        artist_names=artist_names,
    )

    return {
        **explanation,
        "artist_overlap": breakdown.get(
            "artist_overlap",
            0.0,
        ),
        "genre_similarity": breakdown.get(
            "genre_similarity",
            0.0,
        ),
        "low_confidence": breakdown.get(
            "low_confidence",
            False,
        ),
    }


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