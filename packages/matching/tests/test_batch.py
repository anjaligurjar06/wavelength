from matching.batch import mark_profile_stale, run_batch_scorer
from shared.models import Base, CompatibilityScore, User, UserMusicProfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def make_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine)

    return session_factory()


def add_user_with_profile(
    db,
    email,
    artist_id,
    genres,
):
    user = User(
        email=email,
        display_name=email,
    )

    db.add(user)
    db.flush()

    profile = UserMusicProfile(
        user_id=user.id,
        top_artists={
            "items": [
                {
                    "id": artist_id,
                    "name": artist_id,
                    "genres": genres,
                }
            ]
        },
    )

    db.add(profile)
    db.commit()

    return user


def test_batch_scorer_scores_every_unique_pair():
    db = make_session()

    add_user_with_profile(
        db,
        "a@example.com",
        "artist-a",
        ["pop"],
    )

    add_user_with_profile(
        db,
        "b@example.com",
        "artist-b",
        ["pop"],
    )

    add_user_with_profile(
        db,
        "c@example.com",
        "artist-c",
        ["rock"],
    )

    result = run_batch_scorer(db)

    scores = db.query(CompatibilityScore).all()

    assert result.pairs_scored == 3
    assert result.pairs_skipped == 0
    assert len(scores) == 3


def test_batch_scorer_does_not_create_duplicate_pairs():
    db = make_session()

    add_user_with_profile(
        db,
        "a@example.com",
        "artist-a",
        ["pop"],
    )

    add_user_with_profile(
        db,
        "b@example.com",
        "artist-b",
        ["rock"],
    )

    first_result = run_batch_scorer(db)
    second_result = run_batch_scorer(db)

    scores = db.query(CompatibilityScore).all()

    assert first_result.pairs_scored == 1
    assert second_result.pairs_scored == 1
    assert len(scores) == 1


def test_batch_scorer_with_one_profile_scores_nothing():
    db = make_session()

    add_user_with_profile(
        db,
        "a@example.com",
        "artist-a",
        ["pop"],
    )

    result = run_batch_scorer(db)

    assert result.pairs_scored == 0
    assert result.pairs_skipped == 0
    assert db.query(CompatibilityScore).count() == 0


def test_mark_profile_stale():
    db = make_session()

    user = add_user_with_profile(
        db,
        "a@example.com",
        "artist-a",
        ["pop"],
    )

    profile = mark_profile_stale(
        db,
        user.id,
    )

    assert profile.is_stale is True


def test_stale_batch_only_scores_affected_pairs():
    db = make_session()

    user_a = add_user_with_profile(
        db,
        "a@example.com",
        "artist-a",
        ["pop"],
    )

    add_user_with_profile(
        db,
        "b@example.com",
        "artist-b",
        ["rock"],
    )

    add_user_with_profile(
        db,
        "c@example.com",
        "artist-c",
        ["jazz"],
    )

    mark_profile_stale(
        db,
        user_a.id,
    )

    result = run_batch_scorer(
        db,
        stale_only=True,
    )

    assert result.pairs_scored == 2
    assert result.pairs_skipped == 1

    profile = (
        db.query(UserMusicProfile)
        .filter_by(user_id=user_a.id)
        .one()
    )

    assert profile.is_stale is False


def test_stale_batch_with_no_stale_profiles_scores_nothing():
    db = make_session()

    add_user_with_profile(
        db,
        "a@example.com",
        "artist-a",
        ["pop"],
    )

    add_user_with_profile(
        db,
        "b@example.com",
        "artist-b",
        ["rock"],
    )

    result = run_batch_scorer(
        db,
        stale_only=True,
    )

    assert result.pairs_scored == 0
    assert result.pairs_skipped == 1