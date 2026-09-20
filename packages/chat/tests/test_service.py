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

    Our own existence check genuinely finds nothing. Then, right as we
    attempt to commit our new thread, a second, independent session
    commits a conflicting thread first. Our commit then hits the real
    unique constraint, and create_thread_for_match should recover by
    reloading and returning the winning thread instead of propagating
    the error.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    db = Session(engine)
    match = make_match(db)

    original_commit = Session.commit
    call_count = {"n": 0}

    def commit_with_race(self):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # A concurrent request wins the race right before our commit.
            other_session = Session(engine)
            other_session.add(Thread(match_id=match.id))
            other_session.commit()
            other_session.close()
        return original_commit(self)

    with patch.object(Session, "commit", commit_with_race):
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
