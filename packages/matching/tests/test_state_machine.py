from matching.state_machine import record_interaction
from shared.models import Base, Match, User, UserInteraction
from sqlalchemy import create_engine, select
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


def add_users(db: Session) -> None:
    db.add_all(
        [
            User(
                id="user_a",
                email="a@example.com",
                display_name="User A",
            ),
            User(
                id="user_b",
                email="b@example.com",
                display_name="User B",
            ),
        ]
    )
    db.commit()


def test_like_without_reverse_like_does_not_match():
    db = make_session()
    add_users(db)

    result = record_interaction(
        db,
        "user_a",
        "user_b",
        "like",
    )

    interaction = db.scalar(
        select(UserInteraction).where(
            UserInteraction.user_id == "user_a",
            UserInteraction.target_user_id == "user_b",
        )
    )

    assert interaction is not None
    assert interaction.action == "like"
    assert result.matched is False
    assert result.match_id is None


def test_pass_does_not_create_match():
    db = make_session()
    add_users(db)

    result = record_interaction(
        db,
        "user_a",
        "user_b",
        "pass",
    )

    interaction = db.scalar(
        select(UserInteraction).where(
            UserInteraction.user_id == "user_a",
            UserInteraction.target_user_id == "user_b",
        )
    )

    assert interaction is not None
    assert interaction.action == "pass"
    assert result.matched is False
    assert result.match_id is None
    assert db.scalars(select(Match)).all() == []


def test_mutual_like_creates_match():
    db = make_session()
    add_users(db)

    first_result = record_interaction(
        db,
        "user_a",
        "user_b",
        "like",
    )

    second_result = record_interaction(
        db,
        "user_b",
        "user_a",
        "like",
    )

    matches = db.scalars(select(Match)).all()

    assert first_result.matched is False
    assert second_result.matched is True
    assert second_result.match_id is not None
    assert len(matches) == 1

    assert matches[0].user_a_id == "user_a"
    assert matches[0].user_b_id == "user_b"


def test_repeated_like_does_not_duplicate_match():
    db = make_session()
    add_users(db)

    record_interaction(
        db,
        "user_a",
        "user_b",
        "like",
    )

    first_match = record_interaction(
        db,
        "user_b",
        "user_a",
        "like",
    )

    repeated = record_interaction(
        db,
        "user_b",
        "user_a",
        "like",
    )

    matches = db.scalars(select(Match)).all()

    assert first_match.matched is True
    assert repeated.matched is True
    assert repeated.match_id == first_match.match_id
    assert len(matches) == 1