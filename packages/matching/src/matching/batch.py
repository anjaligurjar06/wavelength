from dataclasses import dataclass

from compatibility_engine.service import recompute_compatibility_score
from shared.models import UserMusicProfile
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class BatchScoreResult:
    pairs_scored: int
    pairs_skipped: int


def mark_profile_stale(
    db: Session,
    user_id: str,
) -> UserMusicProfile:
    """Mark a user's music profile for compatibility-score refresh."""

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
    """Recompute compatibility scores for profile pairs."""

    profiles = db.query(UserMusicProfile).all()

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

            try:
                recompute_compatibility_score(
                    db,
                    profile_a.user_id,
                    profile_b.user_id,
                )
            except ValueError:
                pairs_skipped += 1
                continue

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