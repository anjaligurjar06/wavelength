from unittest.mock import patch

from api.jwt_utils import create_access_token
from api.main import app
from fastapi.testclient import TestClient
from shared.models import User

client = TestClient(app)


def _make_user(db_session_factory, **overrides) -> User:
    user = User(
        email=overrides.get("email", "test@example.com"),
        display_name=overrides.get("display_name", "Test User"),
        spotify_id=overrides.get("spotify_id", "spotify-123"),
        spotify_access_token=overrides.get("spotify_access_token", "fake-token"),
    )
    return user


def test_sync_requires_spotify_token(db_session):
    user = User(email="a@example.com", display_name="A", spotify_access_token=None)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)
    response = client.post(
        "/music/sync", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


def test_sync_calls_spotify_and_persists_profile(db_session):
    user = User(
        email="b@example.com",
        display_name="B",
        spotify_access_token="fake-token",
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)

    fake_artists = {
        "items": [{"id": "a1", "name": "Artist One", "genres": ["pop"]}]
    }
    fake_tracks = {"items": []}
    fake_recently_played = {"items": []}
    with patch(
        "music_ingestion.spotify_client.SpotifyClient.get_top_artists",
        return_value=fake_artists,
    ), patch(
        "music_ingestion.spotify_client.SpotifyClient.get_top_tracks",
        return_value=fake_tracks,
    ), patch(
        "music_ingestion.spotify_client.SpotifyClient.get_recently_played",
        return_value=fake_recently_played,
    ):
        response = client.post(
            "/music/sync", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    assert response.json() == {"status": "synced"}

    profile_response = client.get(
        "/music/profile", headers={"Authorization": f"Bearer {token}"}
    )
    assert profile_response.status_code == 200
    data = profile_response.json()
    assert data["top_artists"]["items"][0]["name"] == "Artist One"
    assert data["top_genres"]["genres"] == ["pop"]


def test_profile_without_sync_returns_404(db_session):
    user = User(email="c@example.com", display_name="C", spotify_access_token="tok")
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)
    response = client.get(
        "/music/profile", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404

def test_manual_entry_saves_profile(db_session):
    user = User(email="d@example.com", display_name="D")
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)
    response = client.post(
        "/music/manual-entry",
        json={"artists": ["Radiohead", "Björk"], "genres": ["art rock", "experimental"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "saved"}

    profile_response = client.get(
        "/music/profile", headers={"Authorization": f"Bearer {token}"}
    )
    data = profile_response.json()
    assert data["time_window"] == "manual"
    assert data["top_genres"]["genres"] == ["art rock", "experimental"]
    artist_names = [a["name"] for a in data["top_artists"]["items"]]
    assert "Radiohead" in artist_names
    assert "Björk" in artist_names
