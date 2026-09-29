from shared.models import Block, Report
from sqlalchemy.orm import Session

VALID_REASONS = {"harassment", "spam", "inappropriate_content", "fake_profile", "other"}


def report_user(
    db: Session,
    reporter_id: str,
    reported_user_id: str,
    reason: str,
    details: str | None = None,
) -> Report:
    """Record a report against a user."""
    if reporter_id == reported_user_id:
        raise ValueError("A user cannot report themselves")

    if reason not in VALID_REASONS:
        raise ValueError(f"Invalid reason: {reason}")

    report = Report(
        reporter_id=reporter_id,
        reported_user_id=reported_user_id,
        reason=reason,
        details=details,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return report


def block_user(
    db: Session,
    blocker_id: str,
    blocked_user_id: str,
) -> Block:
    """Block a user. Idempotent — returns the existing block if one exists."""
    if blocker_id == blocked_user_id:
        raise ValueError("A user cannot block themselves")

    existing = (
        db.query(Block)
        .filter_by(blocker_id=blocker_id, blocked_user_id=blocked_user_id)
        .one_or_none()
    )
    if existing is not None:
        return existing

    block = Block(
        blocker_id=blocker_id,
        blocked_user_id=blocked_user_id,
    )
    db.add(block)
    db.commit()
    db.refresh(block)

    return block


def is_blocked(
    db: Session,
    user_a_id: str,
    user_b_id: str,
) -> bool:
    """Return True if either user has blocked the other."""
    block = (
        db.query(Block)
        .filter(
            (
                (Block.blocker_id == user_a_id)
                & (Block.blocked_user_id == user_b_id)
            )
            | (
                (Block.blocker_id == user_b_id)
                & (Block.blocked_user_id == user_a_id)
            )
        )
        .first()
    )
    return block is not None
