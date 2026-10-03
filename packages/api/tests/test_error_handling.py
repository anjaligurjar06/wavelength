from api.errors import register_exception_handlers
from api.jwt_utils import create_access_token
from api.main import app
from fastapi import FastAPI
from fastapi.testclient import TestClient
from shared.models import User

client = TestClient(app)


def test_unknown_route_returns_problem_json():
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 404
    assert body["title"] == "Not Found"
    assert body["instance"] == "/does-not-exist"


def test_auth_failure_keeps_detail_and_problem_shape():
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 401
    assert "detail" in body


def test_validation_error_includes_errors_list(db_session):

    user = User(email="problem422@example.com", display_name="P422")
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user.id)

    response = client.post(
        "/trust-safety/report",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["detail"] == "Request validation failed"
    assert isinstance(body["errors"], list) and body["errors"]


def test_unhandled_exception_returns_500_without_leaking_details():
    isolated = FastAPI()
    register_exception_handlers(isolated)

    @isolated.get("/boom")
    def boom():
        raise RuntimeError("secret internal detail")

    safe_client = TestClient(isolated, raise_server_exceptions=False)
    response = safe_client.get("/boom")

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "secret internal detail" not in response.text
    assert response.json()["detail"] == "Internal server error"