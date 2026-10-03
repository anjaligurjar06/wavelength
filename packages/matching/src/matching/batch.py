from dataclasses import dataclass

from compatibility_engine.service import score_profiles
from shared.models import CompatibilityScore, UserMusicProfile
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class BatchScoreResult:
    pairs_scored: int
    pairs_skipped: int


def mark_profile_stale(
    db: Session,
    user_id: str,
) -> UserMusicProfile:
    """Mark a user's music profile for batch recomputation."""

    profile = (
        db.query(UserMusicProfile)
        .filter_by(user_id=user_id)
        .one_or_none()
    )

    if profile is None:
        raise ValueError("Music profile not found")

    profile.is_stale = True

    db.commit()
    db.refresh(profile)

    return profile


def run_batch_scorer(
    db: Session,
    stale_only: bool = False,
) -> BatchScoreResult:
    """Score unique profile pairs using already-loaded profiles."""

    profiles = db.query(UserMusicProfile).all()

    existing_scores = {
        (
            score.user_a_id,
            score.user_b_id,
        ): score
        for score in db.query(CompatibilityScore).all()
    }

    pairs_scored = 0
    pairs_skipped = 0

    for index, profile_a in enumerate(profiles):
        for profile_b in profiles[index + 1 :]:
            if (
                stale_only
                and not profile_a.is_stale
                and not profile_b.is_stale
            ):
                pairs_skipped += 1
                continue

            result = score_profiles(
                profile_a,
                profile_b,
            )

            first_user_id, second_user_id = sorted(
                [
                    profile_a.user_id,
                    profile_b.user_id,
                ]
            )

            pair_key = (
                first_user_id,
                second_user_id,
            )

            breakdown = {
                "artist_overlap": result.artist_overlap,
                "genre_similarity": result.genre_similarity,
                "shared_artists": result.shared_artists,
                "shared_genres": result.shared_genres,
                "low_confidence": result.low_confidence,
            }

            score_100 = round(
                result.score * 100,
                2,
            )

            score_record = existing_scores.get(
                pair_key
            )

            if score_record is None:
                score_record = CompatibilityScore(
                    user_a_id=first_user_id,
                    user_b_id=second_user_id,
                    score=score_100,
                    breakdown=breakdown,
                )

                db.add(score_record)

                existing_scores[pair_key] = (
                    score_record
                )

            else:
                score_record.score = score_100
                score_record.breakdown = breakdown

            pairs_scored += 1

    if stale_only:
        for profile in profiles:
            if profile.is_stale:
                profile.is_stale = False

    db.commit()

    return BatchScoreResult(
        pairs_scored=pairs_scored,
        pairs_skipped=pairs_skipped,
    )