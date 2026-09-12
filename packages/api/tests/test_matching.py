from api.jwt_utils import create_access_token
from api.main import app
from fastapi.testclient import TestClient
from shared.models import User

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
