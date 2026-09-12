from api.jwt_utils import create_access_token
from api.main import app
from fastapi.testclient import TestClient
from shared.models import User, UserMusicProfile

client = TestClient(app)


def _make_user_with_profile(db_session, email, artists):
    user = User(email=email, display_name=email)
    db_session.add(user)
    db_session.commit()

    profile = UserMusicProfile(user_id=user.id, top_artists={"items": artists})
    db_session.add(profile)
    db_session.commit()

    return user


def test_get_score_computes_on_first_call(db_session):
    user_a = _make_user_with_profile(
        db_session,
        "compat-a@example.com",
        [{"id": "artist_1", "name": "Artist 1", "genres": ["pop"]}],
    )
    user_b = _make_user_with_profile(
        db_session,
        "compat-b@example.com",
        [{"id": "artist_1", "name": "Artist 1", "genres": ["pop"]}],
    )

    token = create_access_token(user_a.id)
    response = client.get(
        f"/compatibility/score/{user_b.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 100.0


def test_get_score_missing_profile_returns_404(db_session):
    user_a = _make_user_with_profile(
        db_session, "compat-c@example.com", [{"id": "artist_1", "name": "Artist 1"}]
    )
    user = User(email="compat-noprofile@example.com", display_name="No Profile")
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user_a.id)
    response = client.get(
        f"/compatibility/score/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_get_breakdown_after_score_computed(db_session):
    user_a = _make_user_with_profile(
        db_session,
        "compat-d@example.com",
        [{"id": "artist_1", "name": "Artist 1", "genres": ["pop"]}],
    )
    user_b = _make_user_with_profile(
        db_session,
        "compat-e@example.com",
        [{"id": "artist_1", "name": "Artist 1", "genres": ["pop"]}],
    )

    token = create_access_token(user_a.id)
    client.get(
        f"/compatibility/score/{user_b.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        f"/compatibility/score/{user_b.id}/breakdown",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["shared_artists"] == ["artist_1"]


def test_recompute_forces_fresh_calculation(db_session):
    user_a = _make_user_with_profile(
        db_session,
        "compat-f@example.com",
        [{"id": "artist_1", "name": "Artist 1", "genres": ["pop"]}],
    )
    user_b = _make_user_with_profile(
        db_session,
        "compat-g@example.com",
        [{"id": "artist_1", "name": "Artist 1", "genres": ["pop"]}],
    )

    token = create_access_token(user_a.id)
    response = client.post(
        f"/compatibility/recompute?candidate_id={user_b.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["score"] == 100.0
