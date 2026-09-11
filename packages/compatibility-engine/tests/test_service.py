import pytest

from compatibility_engine.service import get_compatibility_score
from shared.models import User, UserMusicProfile


def test_get_compatibility_score(db_session):
    user_a = User(
        email="a@test.com",
        display_name="User A",
    )
    user_b = User(
        email="b@test.com",
        display_name="User B",
    )

    db_session.add_all([user_a, user_b])
    db_session.commit()

    profile_a = UserMusicProfile(
        user_id=user_a.id,
        top_artists={
            "items": [
                {
                    "id": "artist_1",
                    "name": "Artist 1",
                    "genres": ["pop"],
                },
                {
                    "id": "artist_2",
                    "name": "Artist 2",
                    "genres": ["rock"],
                },
            ]
        },
    )

    profile_b = UserMusicProfile(
        user_id=user_b.id,
        top_artists={
            "items": [
                {
                    "id": "artist_1",
                    "name": "Artist 1",
                    "genres": ["pop"],
                },
                {
                    "id": "artist_3",
                    "name": "Artist 3",
                    "genres": ["jazz"],
                },
            ]
        },
    )

    db_session.add_all([profile_a, profile_b])
    db_session.commit()

    result = get_compatibility_score(
        db_session,
        user_a.id,
        user_b.id,
    )

    assert result.artist_overlap == pytest.approx(1 / 3)
    assert 0.0 < result.genre_similarity < 1.0
    assert result.shared_artists == ["artist_1"]
    assert result.shared_genres == ["pop"]
    assert 0.0 < result.score < 1.0


def test_get_compatibility_score_missing_profile(db_session):
    user_a = User(
        email="a2@test.com",
        display_name="User A",
    )
    user_b = User(
        email="b2@test.com",
        display_name="User B",
    )

    db_session.add_all([user_a, user_b])
    db_session.commit()

    with pytest.raises(ValueError):
        get_compatibility_score(
            db_session,
            user_a.id,
            user_b.id,
        )