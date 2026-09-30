from unittest.mock import MagicMock

from api.jwt_utils import create_access_token
from api.main import app
from api.redis import get_redis
from fastapi.testclient import TestClient
from shared.models import User

client = TestClient(app)


def test_full_happy_path_auth_to_feed_to_match_to_chat(db_session):
    """End-to-end: two users onboard via manual entry, one sees the other
    in their feed, they mutually like each other, a match and chat thread
    are created, and they exchange a message."""

    # --- Setup: two users close enough to match on distance ---
    user_a = User(
        email="happy-a@example.com",
        display_name="Happy A",
        latitude=31.10,
        longitude=77.17,
        max_distance_km=100.0,
    )
    user_b = User(
        email="happy-b@example.com",
        display_name="Happy B",
        latitude=31.11,
        longitude=77.18,
        max_distance_km=100.0,
    )
    db_session.add_all([user_a, user_b])
    db_session.commit()

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    # --- Step 1: both users complete onboarding via manual music entry ---
    for token in (token_a, token_b):
        response = client.post(
            "/music/manual-entry",
            json={
                "artists": ["Arijit Singh", "The Weeknd"],
                "genres": ["pop", "indian pop"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    # --- Step 2: user A sees user B in their ranked feed ---
    fake_redis = MagicMock()
    fake_redis.get.return_value = None
    app.dependency_overrides[get_redis] = lambda: fake_redis

    try:
        feed_response = client.get(
            "/matching/feed",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert feed_response.status_code == 200
        feed_ids = [c["candidate_id"] for c in feed_response.json()]
        assert user_b.id in feed_ids

        # --- Step 3: mutual like creates a match and a chat thread ---
        first_like = client.post(
            f"/matching/{user_b.id}/like",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert first_like.status_code == 200
        assert first_like.json()["matched"] is False

        second_like = client.post(
            f"/matching/{user_a.id}/like",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert second_like.status_code == 200
        match_data = second_like.json()
        assert match_data["matched"] is True
        assert match_data["match_id"] is not None
        assert match_data["thread_id"] is not None
    finally:
        app.dependency_overrides.pop(get_redis, None)

    thread_id = match_data["thread_id"]

    # --- Step 4: both users see the thread in their thread list ---
    threads_a = client.get(
        "/chat/threads",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert threads_a.status_code == 200
    assert any(t["id"] == thread_id for t in threads_a.json())

    threads_b = client.get(
        "/chat/threads",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert threads_b.status_code == 200
    assert any(t["id"] == thread_id for t in threads_b.json())

    # --- Step 5: user A sends a message, user B receives it ---
    fake_redis_chat = MagicMock()
    fake_redis_chat.incr.return_value = 1
    app.dependency_overrides[get_redis] = lambda: fake_redis_chat

    try:
        send_response = client.post(
            f"/chat/threads/{thread_id}/messages",
            json={"content": "Hey, loved your taste in music!"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert send_response.status_code == 200
    finally:
        app.dependency_overrides.pop(get_redis, None)

    messages_response = client.get(
        f"/chat/threads/{thread_id}/messages",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert len(messages) == 1
    assert messages[0]["content"] == "Hey, loved your taste in music!"
    assert messages[0]["sender_id"] == user_a.id
