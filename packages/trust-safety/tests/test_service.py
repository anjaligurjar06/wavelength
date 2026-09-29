import pytest
from shared.models import Base, Block, Report, User
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from trust_safety.service import block_user, is_blocked, report_user


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def add_users(db: Session) -> tuple[User, User]:
    user_a = User(email="a@example.com", display_name="A")
    user_b = User(email="b@example.com", display_name="B")
    db.add_all([user_a, user_b])
    db.commit()
    return user_a, user_b


def test_report_user_creates_record():
    db = make_session()
    user_a, user_b = add_users(db)

    report = report_user(db, user_a.id, user_b.id, "harassment", "was rude")

    assert report.reporter_id == user_a.id
    assert report.reported_user_id == user_b.id
    assert report.reason == "harassment"
    assert report.details == "was rude"

    stored = db.scalar(select(Report).where(Report.id == report.id))
    assert stored is not None


def test_report_user_rejects_self_report():
    db = make_session()
    user_a, _ = add_users(db)

    with pytest.raises(ValueError, match="cannot report themselves"):
        report_user(db, user_a.id, user_a.id, "spam")


def test_report_user_rejects_invalid_reason():
    db = make_session()
    user_a, user_b = add_users(db)

    with pytest.raises(ValueError, match="Invalid reason"):
        report_user(db, user_a.id, user_b.id, "made_up_reason")


def test_block_user_creates_record():
    db = make_session()
    user_a, user_b = add_users(db)

    block = block_user(db, user_a.id, user_b.id)

    assert block.blocker_id == user_a.id
    assert block.blocked_user_id == user_b.id

    stored = db.scalar(select(Block).where(Block.id == block.id))
    assert stored is not None


def test_block_user_rejects_self_block():
    db = make_session()
    user_a, _ = add_users(db)

    with pytest.raises(ValueError, match="cannot block themselves"):
        block_user(db, user_a.id, user_a.id)


def test_block_user_is_idempotent():
    db = make_session()
    user_a, user_b = add_users(db)

    first = block_user(db, user_a.id, user_b.id)
    second = block_user(db, user_a.id, user_b.id)

    assert first.id == second.id

    all_blocks = db.scalars(select(Block)).all()
    assert len(all_blocks) == 1


def test_is_blocked_true_when_blocker_checks():
    db = make_session()
    user_a, user_b = add_users(db)
    block_user(db, user_a.id, user_b.id)

    assert is_blocked(db, user_a.id, user_b.id) is True


def test_is_blocked_true_in_reverse_direction():
    """If A blocked B, B should also be considered blocked relative to A
    for feed-filtering purposes, even though the Block row is directional."""
    db = make_session()
    user_a, user_b = add_users(db)
    block_user(db, user_a.id, user_b.id)

    assert is_blocked(db, user_b.id, user_a.id) is True


def test_is_blocked_false_when_no_block_exists():
    db = make_session()
    user_a, user_b = add_users(db)

    assert is_blocked(db, user_a.id, user_b.id) is False
