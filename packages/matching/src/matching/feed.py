from dataclasses import dataclass

from compatibility_engine.service import (
    get_stored_compatibility_score,
    recompute_compatibility_score,
    score_profiles,
)
from redis import Redis
from shared.models import CompatibilityScore, User, UserMusicProfile
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from trust_safety.service import get_blocked_user_ids

from matching.cache import (
    get_cached_score,
    get_cached_scores,
    set_cached_score,
    set_cached_scores,
)
from matching.distance import is_within_distance


@dataclass(frozen=True)
class RankedCandidate:
    user_id: str
    display_name: str
    score: float


def get_candidate_score(
    db: Session,
    redis_client: Redis,
    current_user_id: str,
    candidate_id: str,
) -> float:
    """Return one candidate score using Redis, DB, or recomputation."""

    cached_score = get_cached_score(redis_client, current_user_id, candidate_id)

    if cached_score is not None:
        return cached_score

    try:
        score_record = get_stored_compatibility_score(
            db, current_user_id, candidate_id
        )
    except ValueError:
        score_record = recompute_compatibility_score(
            db, current_user_id, candidate_id
        )

    set_cached_score(
        redis_client, current_user_id, candidate_id, score_record.score
    )

    return score_record.score


def _load_stored_scores(
    db: Session,
    current_user_id: str,
    candidate_ids: list[str],
) -> dict[str, float]:
    """One query for every stored pair score involving the current user."""

    rows = (
        db.query(CompatibilityScore)
        .filter(
            or_(
                and_(
                    CompatibilityScore.user_a_id == current_user_id,
                    CompatibilityScore.user_b_id.in_(candidate_ids),
                ),
                and_(
                    CompatibilityScore.user_b_id == current_user_id,
                    CompatibilityScore.user_a_id.in_(candidate_ids),
                ),
            )
        )
        .all()
    )

    return {
        (row.user_b_id if row.user_a_id == current_user_id else row.user_a_id): row.score
        for row in rows
    }


def _compute_missing_scores(
    db: Session,
    current_user_id: str,
    candidate_ids: list[str],
) -> dict[str, float]:
    """Score pairs with no stored score, loading all profiles in one query.

    Candidates (or a current user) without a music profile are skipped,
    matching the old per-candidate behaviour.
    """

    profiles = {
        profile.user_id: profile
        for profile in db.query(UserMusicProfile)
        .filter(UserMusicProfile.user_id.in_([current_user_id, *candidate_ids]))
        .all()
    }

    mine = profiles.get(current_user_id)
    if mine is None:
        return {}

    computed: dict[str, float] = {}
    new_records: list[CompatibilityScore] = []

    for candidate_id in candidate_ids:
        theirs = profiles.get(candidate_id)
        if theirs is None:
            continue

        first_id, second_id = sorted([current_user_id, candidate_id])
        first, second = (mine, theirs) if first_id == current_user_id else (theirs, mine)

        result = score_profiles(first, second)
        score_100 = round(result.score * 100, 2)

        new_records.append(
            CompatibilityScore(
                user_a_id=first_id,
                user_b_id=second_id,
                score=score_100,
                breakdown={
                    "artist_overlap": result.artist_overlap,
                    "genre_similarity": result.genre_similarity,
                    "shared_artists": result.shared_artists,
                    "shared_genres": result.shared_genres,
                    "low_confidence": result.low_confidence,
                },
            )
        )
        computed[candidate_id] = score_100

    if new_records:
        db.add_all(new_records)
        try:
            db.commit()
        except IntegrityError:
            # A concurrent request stored the same pairs; our scores are still valid.
            db.rollback()

    return computed


def get_candidate_scores(
    db: Session,
    redis_client: Redis,
    current_user_id: str,
    candidate_ids: list[str],
) -> dict[str, float]:
    """Batched score lookup: Redis MGET, then one DB query, then bulk compute."""

    scores = get_cached_scores(redis_client, current_user_id, candidate_ids)

    missing = [cid for cid in candidate_ids if cid not in scores]
    if not missing:
        return scores

    stored = _load_stored_scores(db, current_user_id, missing)
    missing = [cid for cid in missing if cid not in stored]

    computed = _compute_missing_scores(db, current_user_id, missing) if missing else {}

    fresh = {**stored, **computed}
    scores.update(fresh)
    set_cached_scores(redis_client, current_user_id, fresh)

    return scores


def build_ranked_feed(
    db: Session,
    redis_client: Redis,
    current_user: User,
    candidates: list[User],
) -> list[RankedCandidate]:
    """Filter candidates by block and distance, then rank by compatibility."""

    blocked_ids = get_blocked_user_ids(db, current_user.id)

    eligible = [
        candidate
        for candidate in candidates
        if candidate.id != current_user.id
        and candidate.id not in blocked_ids
        and is_within_distance(
            current_user.latitude,
            current_user.longitude,
            candidate.latitude,
            candidate.longitude,
            current_user.max_distance_km,
        )
    ]

    scores = get_candidate_scores(
        db,
        redis_client,
        current_user.id,
        [candidate.id for candidate in eligible],
    )

    ranked_candidates = [
        RankedCandidate(
            user_id=candidate.id,
            display_name=candidate.display_name,
            score=scores[candidate.id],
        )
        for candidate in eligible
        if candidate.id in scores
    ]

    ranked_candidates.sort(key=lambda candidate: candidate.score, reverse=True)

    return ranked_candidates