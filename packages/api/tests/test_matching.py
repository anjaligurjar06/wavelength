from unittest.mock import MagicMock

from api.jwt_utils import create_access_token
from api.main import app
from api.redis import get_redis
from fastapi.testclient import TestClient
from shared.models import CompatibilityScore, User

client = TestClient(app)


def test_get_filters_defaults(db_session):
    user = User(email="filters1@example.com", display_name="F1")
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)
    response = client.get(
        "/matching/filters",
        headers={"Authorization": f"Bearer {token}"},
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
        json={
            "latitude": 40.7128,
            "longitude": -74.0060,
            "max_distance_km": 25.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["latitude"] == 40.7128
    assert data["longitude"] == -74.0060
    assert data["max_distance_km"] == 25.0


def test_put_filters_partial_update(db_session):
    user = User(
        email="filters3@example.com",
        display_name="F3",
        max_distance_km=50.0,
    )

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


def test_matching_feed_returns_candidates_sorted_by_score(db_session):
    current_user = User(
        email="feed-user@example.com",
        display_name="Feed User",
        latitude=31.10,
        longitude=77.17,
        max_distance_km=100.0,
    )

    candidate_a = User(
        email="candidate-a@example.com",
        display_name="Candidate A",
        latitude=31.11,
        longitude=77.18,
    )

    candidate_b = User(
        email="candidate-b@example.com",
        display_name="Candidate B",
        latitude=31.12,
        longitude=77.19,
    )

    candidate_c = User(
        email="candidate-c@example.com",
        display_name="Candidate C",
        latitude=31.13,
        longitude=77.20,
    )

    db_session.add_all(
        [
            current_user,
            candidate_a,
            candidate_b,
            candidate_c,
        ]
    )
    db_session.commit()

    for candidate, score in [
        (candidate_a, 70.0),
        (candidate_b, 95.0),
        (candidate_c, 82.0),
    ]:
        first_user_id, second_user_id = sorted(
            [current_user.id, candidate.id]
        )

        db_session.add(
            CompatibilityScore(
                user_a_id=first_user_id,
                user_b_id=second_user_id,
                score=score,
                breakdown={},
            )
        )

    db_session.commit()

    fake_redis = MagicMock()
    fake_redis.get.return_value = None

    app.dependency_overrides[get_redis] = lambda: fake_redis

    try:
        token = create_access_token(current_user.id)

        response = client.get(
            "/matching/feed",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_redis, None)

    assert response.status_code == 200

    data = response.json()

    assert [candidate["candidate_id"] for candidate in data] == [
        candidate_b.id,
        candidate_c.id,
        candidate_a.id,
    ]

    assert [candidate["score"] for candidate in data] == [
        95.0,
        82.0,
        70.0,
    ]
    assert [candidate["display_name"] for candidate in data] == [
        candidate_b.display_name,
        candidate_c.display_name,
        candidate_a.display_name,
    ]
