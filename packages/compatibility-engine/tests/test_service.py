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




def _make_users(db_session):
    user_a = User(email="c6a@test.com", display_name="A")
    user_b = User(email="c6b@test.com", display_name="B")
    db_session.add_all([user_a, user_b])
    db_session.commit()
    return user_a, user_b


def _manual_profile(user, artists, genres):
    return UserMusicProfile(
        user_id=user.id,
        top_artists={
            "items": [{"id": None, "name": n, "genres": []} for n in artists]
        },
        top_genres={"genres": genres},
        time_window="manual",
    )


def _spotify_profile(user, count, name_prefix="Artist", genres=("pop",)):
    return UserMusicProfile(
        user_id=user.id,
        top_artists={
            "items": [
                {
                    "id": f"{name_prefix}_{i}",
                    "name": f"{name_prefix} {i}",
                    "genres": list(genres),
                }
                for i in range(count)
            ]
        },
    )



def test_sparse_user_is_flagged_low_confidence(db_session):
    a, b = _make_users(db_session)
    db_session.add_all([_spotify_profile(a, 2), _spotify_profile(b, 10)])
    db_session.commit()

    result = get_compatibility_score(db_session, a.id, b.id)

    assert result.low_confidence is True


def test_user_with_zero_artists_does_not_crash(db_session):
    a, b = _make_users(db_session)
    db_session.add_all([_spotify_profile(a, 0), _spotify_profile(b, 10)])
    db_session.commit()

    result = get_compatibility_score(db_session, a.id, b.id)

    assert result.low_confidence is True
    assert result.score >= 0


def test_two_full_profiles_are_not_low_confidence(db_session):
    a, b = _make_users(db_session)
    db_session.add_all([_spotify_profile(a, 8), _spotify_profile(b, 8)])
    db_session.commit()

    result = get_compatibility_score(db_session, a.id, b.id)

    assert result.low_confidence is False


def test_manual_users_with_same_artists_score_above_zero(db_session):
    a, b = _make_users(db_session)
    db_session.add_all(
        [
            _manual_profile(a, ["Drake", "Arijit Singh"], ["pop"]),
            _manual_profile(b, ["drake", "The Weeknd"], ["pop"]),
        ]
    )
    db_session.commit()

    result = get_compatibility_score(db_session, a.id, b.id)

    assert result.score > 0.05
    assert result.shared_artists == ["drake"]
    assert result.shared_genres == ["pop"]


def test_manual_typed_genres_create_genre_similarity(db_session):
    a, b = _make_users(db_session)
    db_session.add_all(
        [
            _manual_profile(a, ["X"], ["pop", "rock"]),
            _manual_profile(b, ["Y"], ["pop", "rock"]),
        ]
    )
    db_session.commit()

    result = get_compatibility_score(db_session, a.id, b.id)

    assert result.genre_similarity == pytest.approx(1.0)


def test_spotify_user_vs_manual_user_matches_by_name(db_session):
    a, b = _make_users(db_session)
    spotify = _spotify_profile(a, 6, name_prefix="Drake")
    manual = _manual_profile(b, ["drake 0", "Someone"], ["pop"])
    db_session.add_all([spotify, manual])
    db_session.commit()

    result = get_compatibility_score(db_session, a.id, b.id)

    assert "drake 0" in result.shared_artists
    assert result.score > 0.05


def test_no_overlap_pair_gets_the_floor(db_session):
    a, b = _make_users(db_session)
    db_session.add_all(
        [
            _spotify_profile(a, 6, "Alpha", genres=("pop",)),
            _spotify_profile(b, 6, "Beta", genres=("jazz",)),
        ]
    )
    db_session.commit()

    result = get_compatibility_score(db_session, a.id, b.id)

    assert result.score == pytest.approx(0.05)


def test_stored_floor_score_is_five_out_of_hundred(db_session):
    a, b = _make_users(db_session)
    db_session.add_all(
        [
            _spotify_profile(a, 6, "Alpha", genres=("pop",)),
            _spotify_profile(b, 6, "Beta", genres=("jazz",)),
        ]
    )
    db_session.commit()

    record = recompute_compatibility_score(db_session, a.id, b.id)

    assert record.score == pytest.approx(5.0)


def test_floor_does_not_change_real_overlap_score(db_session):
    a, b = _make_users(db_session)
    db_session.add_all([_spotify_profile(a, 6), _spotify_profile(b, 6)])
    db_session.commit()

    result = get_compatibility_score(db_session, a.id, b.id)

    assert result.score == pytest.approx(1.0)