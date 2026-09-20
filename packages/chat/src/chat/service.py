from shared.models import Match, Thread
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def create_thread_for_match(db: Session, match: Match) -> Thread:
    """Ensure a Thread exists for a given Match. Idempotent and safe under
    concurrent calls — safe to call even if a thread already exists for
    this match."""
    existing = db.query(Thread).filter_by(match_id=match.id).one_or_none()
    if existing is not None:
        return existing

    thread = Thread(match_id=match.id)
    db.add(thread)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(Thread).filter_by(match_id=match.id).one_or_none()
        if existing is None:
            raise
        return existing

    db.refresh(thread)
    return thread