
import logging
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_request_is_logged_and_has_request_id(caplog):
    with caplog.at_level(logging.INFO, logger="wavelength.access"):
        response = client.get("/users/me")

    assert response.headers["X-Request-ID"]
    assert any(
        "GET /users/me -> 401" in r.getMessage()
        for r in caplog.records
    )


def test_oauth_failure_is_logged_without_leaking_code(caplog):
    failed = Mock()
    failed.status_code = 400

    # Start OAuth to establish the expected state cookie.
    with TestClient(app, follow_redirects=False) as oauth_client:
        authorize_response = oauth_client.get("/auth/spotify/authorize")
        assert authorize_response.status_code == 307

        authorize_url = authorize_response.headers["location"]
        state = parse_qs(urlparse(authorize_url).query)["state"][0]

        with caplog.at_level(logging.WARNING), patch(
            "api.routes.auth.httpx.post",
            return_value=failed,
        ):
            response = oauth_client.get(
                "/auth/spotify/callback",
                params={
                    "code": "super-secret-code",
                    "state": state,
                },
            )

    assert response.status_code == 400
    assert any(
        "token exchange failed" in record.getMessage()
        and "upstream_status=400" in record.getMessage()
        for record in caplog.records
    )
    assert "super-secret-code" not in caplog.text
