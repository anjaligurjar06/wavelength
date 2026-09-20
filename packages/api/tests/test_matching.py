from unittest.mock import MagicMock

from api.jwt_utils import create_access_token
from api.main import app
from api.redis import get_redis
from fastapi.testclient import TestClient
from shared.models import CompatibilityScore, Thread, User

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
def test_like_candidate_without_mutual_like(db_session):
    user_a = User(
        email="like-a@example.com",
        display_name="Like A",
    )
    user_b = User(
        email="like-b@example.com",
        display_name="Like B",
    )

    db_session.add_all([user_a, user_b])
    db_session.commit()

    token_a = create_access_token(user_a.id)

    response = client.post(
        f"/matching/{user_b.id}/like",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["action"] == "like"
    assert data["matched"] is False
    assert data["match_id"] is None


def test_pass_candidate(db_session):
    user_a = User(
        email="pass-a@example.com",
        display_name="Pass A",
    )
    user_b = User(
        email="pass-b@example.com",
        display_name="Pass B",
    )

    db_session.add_all([user_a, user_b])
    db_session.commit()

    token_a = create_access_token(user_a.id)

    response = client.post(
        f"/matching/{user_b.id}/pass",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["action"] == "pass"
    assert data["matched"] is False
    assert data["match_id"] is None


def test_mutual_like_creates_match(db_session):
    user_a = User(
        email="mutual-a@example.com",
        display_name="Mutual A",
    )
    user_b = User(
        email="mutual-b@example.com",
        display_name="Mutual B",
    )

    db_session.add_all([user_a, user_b])
    db_session.commit()

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    first_response = client.post(
        f"/matching/{user_b.id}/like",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert first_response.status_code == 200
    assert first_response.json()["matched"] is False
    assert first_response.json()["match_id"] is None

    second_response = client.post(
        f"/matching/{user_a.id}/like",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert second_response.status_code == 200

    data = second_response.json()

    assert data["action"] == "like"
    assert data["matched"] is True
    assert data["match_id"] is not None

def test_mutual_like_creates_thread_for_chat(db_session):
    user_a = User(
        email="thread-a@example.com",
        display_name="Thread A",
    )
    user_b = User(
        email="thread-b@example.com",
        display_name="Thread B",
    )

    db_session.add_all([user_a, user_b])
    db_session.commit()

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    client.post(
        f"/matching/{user_b.id}/like",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    second_response = client.post(
        f"/matching/{user_a.id}/like",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    match_id = second_response.json()["match_id"]
    assert match_id is not None

    thread = (
        db_session.query(Thread)
        .filter_by(match_id=match_id)
        .one_or_none()
    )

    assert thread is not None