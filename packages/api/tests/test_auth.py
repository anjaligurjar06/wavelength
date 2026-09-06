from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app, follow_redirects=False)


def test_authorize_redirects_to_spotify() -> None:
    response = client.get("/auth/spotify/authorize")
    assert response.status_code == 307
    assert "accounts.spotify.com/authorize" in response.headers["location"]
