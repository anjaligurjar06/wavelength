from api.jwt_utils import create_access_token
from api.main import app
from fastapi.testclient import TestClient
from shared.models import User

client = TestClient(app)


def test_report_user_success(db_session):
    reporter = User(email="reporter@example.com", display_name="Reporter")
    reported = User(email="reported@example.com", display_name="Reported")
    db_session.add_all([reporter, reported])
    db_session.commit()

    token = create_access_token(reporter.id)

    response = client.post(
        "/trust-safety/report",
        json={
            "reported_user_id": reported.id,
            "reason": "harassment",
            "details": "sent unwanted messages",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reason"] == "harassment"
    assert "id" in data


def test_report_user_invalid_reason_returns_400(db_session):
    reporter = User(email="reporter2@example.com", display_name="Reporter2")
    reported = User(email="reported2@example.com", display_name="Reported2")
    db_session.add_all([reporter, reported])
    db_session.commit()

    token = create_access_token(reporter.id)

    response = client.post(
        "/trust-safety/report",
        json={
            "reported_user_id": reported.id,
            "reason": "not_a_real_reason",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


def test_report_self_returns_400(db_session):
    user = User(email="selfreport@example.com", display_name="SelfReport")
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)

    response = client.post(
        "/trust-safety/report",
        json={
            "reported_user_id": user.id,
            "reason": "spam",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


def test_block_user_success(db_session):
    blocker = User(email="blocker@example.com", display_name="Blocker")
    blocked = User(email="blocked@example.com", display_name="Blocked")
    db_session.add_all([blocker, blocked])
    db_session.commit()

    token = create_access_token(blocker.id)

    response = client.post(
        "/trust-safety/block",
        json={"blocked_user_id": blocked.id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["blocked_user_id"] == blocked.id


def test_block_user_blocked_disappears_from_feed(db_session):
    """A blocked user should no longer show up in the blocker's feed,
    even though they'd otherwise be a valid, scoreable candidate."""
    from shared.models import UserMusicProfile

    blocker = User(
        email="blockerfeed@example.com",
        display_name="BlockerFeed",
        latitude=31.10,
        longitude=77.17,
        max_distance_km=100.0,
    )
    candidate = User(
        email="blockedcandidate@example.com",
        display_name="BlockedCandidate",
        latitude=31.11,
        longitude=77.18,
    )
    db_session.add_all([blocker, candidate])
    db_session.commit()

    db_session.add_all(
        [
            UserMusicProfile(
                user_id=blocker.id,
                top_artists={"items": [{"id": "artist_1", "name": "Artist 1", "genres": ["pop"]}]},
            ),
            UserMusicProfile(
                user_id=candidate.id,
                top_artists={"items": [{"id": "artist_1", "name": "Artist 1", "genres": ["pop"]}]},
            ),
        ]
    )
    db_session.commit()

    token = create_access_token(blocker.id)

    # Sanity check: before blocking, the candidate genuinely appears in the feed.
    feed_before = client.get(
        "/matching/feed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert feed_before.status_code == 200
    ids_before = [c["candidate_id"] for c in feed_before.json()]
    assert candidate.id in ids_before

    block_response = client.post(
        "/trust-safety/block",
        json={"blocked_user_id": candidate.id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert block_response.status_code == 200

    feed_after = client.get(
        "/matching/feed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert feed_after.status_code == 200
    ids_after = [c["candidate_id"] for c in feed_after.json()]
    assert candidate.id not in ids_after
