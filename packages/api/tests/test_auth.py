from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

from api.config import settings
from api.main import app
from fastapi.testclient import TestClient


def test_authorize_sets_state_cookie() -> None:
    with TestClient(app, follow_redirects=False) as client:
        response = client.get("/auth/spotify/authorize")
        assert response.status_code == 307
        assert "accounts.spotify.com/authorize" in response.headers["location"]
        state = parse_qs(urlsplit(response.headers["location"]).query)["state"][0]
        assert state == client.cookies.get("spotify_oauth_state")
        assert "httponly" in response.headers["set-cookie"].lower()


def test_callback_rejects_missing_state() -> None:
    with TestClient(app, follow_redirects=False) as client:
        response = client.get("/auth/spotify/callback?code=fake-code&state=wrong")
        assert response.status_code == 400


def test_callback_rejects_mismatched_state() -> None:
    with TestClient(app, follow_redirects=False) as client:
        client.get("/auth/spotify/authorize")
        response = client.get("/auth/spotify/callback?code=fake-code&state=wrong")
        assert response.status_code == 400


def test_callback_uses_httponly_cookie(db_session) -> None:
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
    with TestClient(app, follow_redirects=False) as client:
        authorize_response = client.get("/auth/spotify/authorize")
        state = parse_qs(urlsplit(authorize_response.headers["location"]).query)["state"][0]
        with (
            patch("api.routes.auth.httpx.post", return_value=fake_token_response),
            patch("api.routes.auth.httpx.get", return_value=fake_profile_response),
        ):
            response = client.get(f"/auth/spotify/callback?code=fake-code&state={state}")
        assert response.status_code == 307
        assert response.headers["location"] == f"{settings.frontend_url}/auth/callback"
        assert "wavelength_session" in client.cookies
        assert "httponly" in response.headers["set-cookie"].lower()
