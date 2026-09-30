from unittest.mock import MagicMock

from api.jwt_utils import create_access_token
from api.main import app
from api.redis import get_redis
from chat.rate_limit import MAX_MESSAGES_PER_WINDOW
from fastapi.testclient import TestClient
from shared.models import Match, Thread, User

client = TestClient(app)


def _make_matched_pair(db_session) -> tuple[User, User, Thread]:
    user_a = User(email="chat-a@example.com", display_name="Chat A")
    user_b = User(email="chat-b@example.com", display_name="Chat B")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    match = Match(user_a_id=user_a.id, user_b_id=user_b.id)
    db_session.add(match)
    db_session.commit()

    thread = Thread(match_id=match.id)
    db_session.add(thread)
    db_session.commit()

    return user_a, user_b, thread


def test_send_message_success(db_session):
    user_a, user_b, thread = _make_matched_pair(db_session)
    token = create_access_token(user_a.id)

    fake_redis = MagicMock()
    fake_redis.incr.return_value = 1
    app.dependency_overrides[get_redis] = lambda: fake_redis

    try:
        response = client.post(
            f"/chat/threads/{thread.id}/messages",
            json={"content": "hey!"},
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_redis, None)

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "hey!"
    assert data["sender_id"] == user_a.id


def test_send_message_non_participant_rejected(db_session):
    user_a, user_b, thread = _make_matched_pair(db_session)
    outsider = User(email="outsider@example.com", display_name="Outsider")
    db_session.add(outsider)
    db_session.commit()

    token = create_access_token(outsider.id)

    fake_redis = MagicMock()
    fake_redis.incr.return_value = 1
    app.dependency_overrides[get_redis] = lambda: fake_redis

    try:
        response = client.post(
            f"/chat/threads/{thread.id}/messages",
            json={"content": "hey!"},
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_redis, None)

    assert response.status_code == 403


def test_send_message_rate_limited(db_session):
    user_a, user_b, thread = _make_matched_pair(db_session)
    token = create_access_token(user_a.id)

    fake_redis = MagicMock()
    fake_redis.incr.return_value = MAX_MESSAGES_PER_WINDOW + 1
    app.dependency_overrides[get_redis] = lambda: fake_redis

    try:
        response = client.post(
            f"/chat/threads/{thread.id}/messages",
            json={"content": "spam"},
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_redis, None)

    assert response.status_code == 429


def test_get_messages_returns_sent_messages(db_session):
    user_a, user_b, thread = _make_matched_pair(db_session)
    token_a = create_access_token(user_a.id)

    fake_redis = MagicMock()
    fake_redis.incr.return_value = 1
    app.dependency_overrides[get_redis] = lambda: fake_redis

    try:
        client.post(
            f"/chat/threads/{thread.id}/messages",
            json={"content": "first message"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
    finally:
        app.dependency_overrides.pop(get_redis, None)

    response = client.get(
        f"/chat/threads/{thread.id}/messages",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 1
    assert messages[0]["content"] == "first message"


def test_list_threads_includes_thread_with_other_user_name(db_session):
    user_a, user_b, thread = _make_matched_pair(db_session)
    token_a = create_access_token(user_a.id)

    response = client.get(
        "/chat/threads",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert response.status_code == 200
    threads = response.json()
    assert len(threads) == 1
    assert threads[0]["other_user_id"] == user_b.id
    assert threads[0]["other_display_name"] == "Chat B"

