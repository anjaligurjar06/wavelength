from api.jwt_utils import create_access_token
from api.main import app
from fastapi.testclient import TestClient
from shared.models import User, UserMusicProfile

client = TestClient(app)


def test_get_filters_defaults(db_session):
    user = User(email="filters1@example.com", display_name="F1")
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)
    response = client.get(
        "/matching/filters", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] is None
    assert data["longitude"] is None
    assert data["max_distance_km"] == 50.0


def test_put_filters_updates_values(db_session):
    user = User(email="filters2@example.com", display_name="F2")
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)
    response = client.put(
        "/matching/filters",
        json={"latitude": 40.7128, "longitude": -74.0060, "max_distance_km": 25.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 40.7128
    assert data["longitude"] == -74.0060
    assert data["max_distance_km"] == 25.0


def test_put_filters_partial_update(db_session):
    user = User(email="filters3@example.com", display_name="F3", max_distance_km=50.0)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)
    response = client.put(
        "/matching/filters",
        json={"max_distance_km": 10.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["max_distance_km"] == 10.0

def _make_user_with_location(db_session, email, lat, lon, artists):
    user = User(email=email, display_name=email, latitude=lat, longitude=lon)
    db_session.add(user)
    db_session.commit()

    profile = UserMusicProfile(user_id=user.id, top_artists={"items": artists})
    db_session.add(profile)
    db_session.commit()

    return user


def test_feed_excludes_candidates_outside_distance(db_session):
    user = _make_user_with_location(
        db_session,
        "feed-me@example.com",
        40.7128,
        -74.0060,
        [{"id": "artist_1", "name": "Artist 1", "genres": ["pop"]}],
    )
    user.max_distance_km = 10.0
    db_session.commit()

    _make_user_with_location(
        db_session,
        "feed-far@example.com",
        51.5074,
        -0.1278,  # London, way outside 10km
        [{"id": "artist_1", "name": "Artist 1", "genres": ["pop"]}],
    )

    token = create_access_token(user.id)
    response = client.get(
        "/matching/feed", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_feed_includes_and_sorts_candidates_by_score(db_session):
    user = _make_user_with_location(
        db_session,
        "feed-sorter@example.com",
        40.7128,
        -74.0060,
        [
            {"id": "artist_1", "name": "Artist 1", "genres": ["pop"]},
            {"id": "artist_2", "name": "Artist 2", "genres": ["rock"]},
        ],
    )
    user.max_distance_km = 100.0
    db_session.commit()

    high_match = _make_user_with_location(
        db_session,
        "feed-high@example.com",
        40.71,
        -74.00,
        [
            {"id": "artist_1", "name": "Artist 1", "genres": ["pop"]},
            {"id": "artist_2", "name": "Artist 2", "genres": ["rock"]},
        ],
    )
    low_match = _make_user_with_location(
        db_session,
        "feed-low@example.com",
        40.72,
        -74.01,
        [{"id": "artist_99", "name": "Unrelated Artist", "genres": ["jazz"]}],
    )

    token = create_access_token(user.id)
    response = client.get(
        "/matching/feed", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["candidate_id"] == high_match.id
    assert data[1]["candidate_id"] == low_match.id
    assert data[0]["score"] >= data[1]["score"]


def test_feed_skips_candidates_without_music_profile(db_session):
    user = _make_user_with_location(
        db_session,
        "feed-solo@example.com",
        40.7128,
        -74.0060,
        [{"id": "artist_1", "name": "Artist 1", "genres": ["pop"]}],
    )
    user.max_distance_km = 100.0
    db_session.commit()

    no_profile_user = User(
        email="feed-noprofile@example.com",
        display_name="No Profile",
        latitude=40.71,
        longitude=-74.00,
    )
    db_session.add(no_profile_user)
    db_session.commit()

    token = create_access_token(user.id)
    response = client.get(
        "/matching/feed", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == []
