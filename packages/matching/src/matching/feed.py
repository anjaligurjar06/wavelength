from dataclasses import dataclass

from compatibility_engine.service import (
    get_stored_compatibility_score,
    recompute_compatibility_score,
)
from redis import Redis
from shared.models import User
from sqlalchemy.orm import Session
from trust_safety.service import is_blocked

from matching.cache import get_cached_score, set_cached_score
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
    """Return a candidate score using Redis, DB, or recomputation."""

    cached_score = get_cached_score(
        redis_client,
        current_user_id,
        candidate_id,
    )

    if cached_score is not None:
        return cached_score

    try:
        score_record = get_stored_compatibility_score(
            db,
            current_user_id,
            candidate_id,
        )
    except ValueError:
        score_record = recompute_compatibility_score(
            db,
            current_user_id,
            candidate_id,
        )

    set_cached_score(
        redis_client,
        current_user_id,
        candidate_id,
        score_record.score,
    )

    return score_record.score


def build_ranked_feed(
    db: Session,
    redis_client: Redis,
    current_user: User,
    candidates: list[User],
) -> list[RankedCandidate]:
    """Filter candidates by distance and sort them by compatibility score."""

    ranked_candidates: list[RankedCandidate] = []

    for candidate in candidates:
        if candidate.id == current_user.id:
            continue

        if is_blocked(db, current_user.id, candidate.id):
            continue

        if not is_within_distance(
            current_user.latitude,
            current_user.longitude,
            candidate.latitude,
            candidate.longitude,
            current_user.max_distance_km,
        ):
            continue

        try:
            score = get_candidate_score(
                db,
                redis_client,
                current_user.id,
                candidate.id,
            )
        except ValueError:
            continue

        ranked_candidates.append(
            RankedCandidate(
                user_id=candidate.id,
                display_name=candidate.display_name,
                score=score,
            )
        )

    ranked_candidates.sort(
        key=lambda candidate: candidate.score,
        reverse=True,
    )

    return ranked_candidates
