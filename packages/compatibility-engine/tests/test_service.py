import pytest
from compatibility_engine.service import (
    get_compatibility_score,
    get_score_breakdown,
    get_stored_compatibility_score,
    recompute_compatibility_score,
)
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


def test_recompute_compatibility_score(db_session):
    user_a = User(
        email="recompute-a@test.com",
        display_name="User A",
    )
    user_b = User(
        email="recompute-b@test.com",
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

    record = recompute_compatibility_score(
        db_session,
        user_a.id,
        user_b.id,
    )

    assert 0.0 < record.score < 100.0
    assert record.breakdown["artist_overlap"] == pytest.approx(1 / 3)
    assert record.breakdown["shared_artists"] == ["artist_1"]
    assert record.breakdown["shared_genres"] == ["pop"]


def test_recompute_updates_existing_score(db_session):
    user_a = User(
        email="update-a@test.com",
        display_name="User A",
    )
    user_b = User(
        email="update-b@test.com",
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
                }
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
                }
            ]
        },
    )

    db_session.add_all([profile_a, profile_b])
    db_session.commit()

    first_record = recompute_compatibility_score(
        db_session,
        user_a.id,
        user_b.id,
    )

    second_record = recompute_compatibility_score(
        db_session,
        user_a.id,
        user_b.id,
    )

    assert first_record.id == second_record.id
    assert second_record.score == pytest.approx(100.0)


def test_get_stored_compatibility_score(db_session):
    user_a = User(
        email="stored-a@test.com",
        display_name="User A",
    )
    user_b = User(
        email="stored-b@test.com",
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
                }
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
                }
            ]
        },
    )

    db_session.add_all([profile_a, profile_b])
    db_session.commit()

    recompute_compatibility_score(
        db_session,
        user_a.id,
        user_b.id,
    )

    record = get_stored_compatibility_score(
        db_session,
        user_a.id,
        user_b.id,
    )

    assert record.score == pytest.approx(100.0)


def test_get_score_breakdown(db_session):
    user_a = User(
        email="breakdown-a@test.com",
        display_name="User A",
    )
    user_b = User(
        email="breakdown-b@test.com",
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

    recompute_compatibility_score(
        db_session,
        user_a.id,
        user_b.id,
    )

    breakdown = get_score_breakdown(
        db_session,
        user_a.id,
        user_b.id,
    )

    assert breakdown["artist_overlap"] == pytest.approx(1 / 3)
    assert breakdown["shared_artists"] == ["artist_1"]
    assert breakdown["shared_genres"] == ["pop"]