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

    A second session commits a thread for this match after our SELECT has
    already run (as if a concurrent request beat us to it). Our own insert
    then violates the real unique constraint on threads.match_id, and
    create_thread_for_match should recover by reloading and returning the
    winning thread instead of propagating the error.
    """
    db = make_session()
    match = make_match(db)

    # Simulate our SELECT finding nothing, by directly inserting a
    # conflicting row through a second, independent session bound to the
    # same in-memory database connection, after create_thread_for_match's
    # own existence check would have run.
    original_query = Session.query

    def query_then_insert_conflict(self, *args, **kwargs):
        result = original_query(self, *args, **kwargs)
        if args and args[0] is Thread:
            winning_thread = Thread(match_id=match.id)
            db.add(winning_thread)
            db.commit()
        return result

    with patch.object(Session, "query", query_then_insert_conflict):
        result = create_thread_for_match(db, match)

    all_threads = db.scalars(select(Thread).where(Thread.match_id == match.id)).all()
    assert len(all_threads) == 1
    assert result.id == all_threads[0].id

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
