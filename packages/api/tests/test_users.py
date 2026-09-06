from api.jwt_utils import create_access_token
from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_me_without_token_returns_401() -> None:
    response = client.get("/users/me")
    assert response.status_code == 401

def test_me_with_invalid_token_returns_401() -> None:
    response = client.get(
        "/users/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_me_with_valid_token_but_unknown_user_returns_401() -> None:
    token = create_access_token("nonexistent-user-id")
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
