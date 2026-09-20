from unittest.mock import patch

from chat.service import create_thread_for_match
from shared.models import Base, Match, Thread, User
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def make_match(db: Session) -> Match:
    user_a = User(email="a@example.com", display_name="A")
    user_b = User(email="b@example.com", display_name="B")
    db.add_all([user_a, user_b])
    db.commit()

    match = Match(user_a_id=user_a.id, user_b_id=user_b.id)
    db.add(match)
    db.commit()

    return match


def test_creates_thread_when_none_exists():
    db = make_session()
    match = make_match(db)

    thread = create_thread_for_match(db, match)

    assert thread.match_id == match.id

    stored = db.scalar(select(Thread).where(Thread.match_id == match.id))
    assert stored is not None
    assert stored.id == thread.id


def test_returns_existing_thread_without_creating_duplicate():
    db = make_session()
    match = make_match(db)

    first = create_thread_for_match(db, match)
    second = create_thread_for_match(db, match)

    assert first.id == second.id

    all_threads = db.scalars(select(Thread).where(Thread.match_id == match.id)).all()
    assert len(all_threads) == 1


def test_concurrent_creation_recovers_from_integrity_error():
    """Simulate two requests racing to create a thread for the same match.

    The first request's session already committed a thread for this match
    (as if another concurrent request beat us to it), but our in-memory
    check hasn't seen it yet. The commit() call should raise IntegrityError
    on the unique constraint, and create_thread_for_match should recover by
    reloading and returning the existing thread instead of propagating the
    error.
    """
    db = make_session()
    match = make_match(db)

    # Simulate a concurrent request that already created the thread.
    winning_thread = Thread(match_id=match.id)
    db.add(winning_thread)
    db.commit()

    # Now call create_thread_for_match again as if it hadn't seen that
    # thread yet at the time of its initial SELECT, by forcing commit()
    # to raise IntegrityError on this attempt.
    with patch.object(
        Session, "commit", side_effect=IntegrityError("stmt", {}, Exception("unique violation"))
    ):
        result = create_thread_for_match(db, match)

    assert result.id == winning_thread.id

    all_threads = db.scalars(select(Thread).where(Thread.match_id == match.id)).all()
    assert len(all_threads) == 1


def test_reraises_integrity_error_when_no_existing_thread_found():
    """If commit() fails with IntegrityError but no existing thread can be
    found on reload, the original error must propagate rather than being
    silently swallowed."""
    db = make_session()
    match = make_match(db)

    with patch.object(
        Session, "commit", side_effect=IntegrityError("stmt", {}, Exception("unique violation"))
    ):
        try:
            create_thread_for_match(db, match)
            assert False, "expected IntegrityError to be raised"
        except IntegrityError:
            pass
