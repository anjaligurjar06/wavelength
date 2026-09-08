from api.jwt_utils import create_access_token
from api.main import app
from fastapi.testclient import TestClient
from shared.models import User

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

def test_patch_me_updates_display_name(db_session):
    user = User(email="patch@example.com", display_name="Old Name")
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)
    response = client.patch(
        "/users/me",
        json={"display_name": "New Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "New Name"
    assert response.json()["email"] == "patch@example.com"


def test_patch_me_partial_update_leaves_other_fields(db_session):
    user = User(email="keep@example.com", display_name="Keep Me")
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)
    response = client.patch(
        "/users/me",
        json={"email": "changed@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "changed@example.com"
    assert response.json()["display_name"] == "Keep Me"
