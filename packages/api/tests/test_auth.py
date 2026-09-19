from unittest.mock import Mock, patch

from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app, follow_redirects=False)


def test_authorize_redirects_to_spotify() -> None:
    response = client.get("/auth/spotify/authorize")
    assert response.status_code == 307
    assert "accounts.spotify.com/authorize" in response.headers["location"]
def test_callback_redirects_to_frontend_with_token(db_session) -> None:
    fake_token_response = Mock()
    fake_token_response.status_code = 200
    fake_token_response.json.return_value = {
        "access_token": "fake-spotify-access-token",
        "refresh_token": "fake-spotify-refresh-token",
    }

    fake_profile_response = Mock()
    fake_profile_response.status_code = 200
    fake_profile_response.json.return_value = {
        "id": "spotify-user-1",
        "email": "callback-test@example.com",
        "display_name": "Callback Test User",
    }

    with (
        patch("api.routes.auth.httpx.post", return_value=fake_token_response),
        patch("api.routes.auth.httpx.get", return_value=fake_profile_response),
    ):
        response = client.get("/auth/spotify/callback?code=fake-code")

    assert response.status_code == 307
    location = response.headers["location"]
    assert location.startswith("http://localhost:3000/auth/callback?token=")
    assert "user_id=" in location
