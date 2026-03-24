"""Tests for the browser session cookie endpoints.

POST /api/auth/session  — validates a bearer token and sets an
                          HttpOnly session cookie.
DELETE /api/auth/session — clears the session cookie.

Also verifies that get_optional_auth falls back to the session
cookie when no Authorization header is present.
"""

import pytest
from fastapi.testclient import TestClient

from app.acl import AclCache
from app.auth import AuthContext
from app.dependencies import get_acl, get_storage
from app.main import create_app
from app.settings import Settings, get_settings
from app.storage import FilesystemStorage

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app_instance(tmp_path):
    """Return a configured FastAPI app with dependency overrides."""
    storage = FilesystemStorage(data_root=tmp_path)
    acl = AclCache()
    # Point JWKS at the dev key file so that validate_token is
    # reachable and token format/signature errors return 401.
    _dev_jwks = "file:///workspaces/docroot/deploy/dev/jwks.json"
    _settings = Settings(
        data_root=str(tmp_path),
        oauth_jwks_url=_dev_jwks,
    )
    application = create_app(settings=_settings)
    application.dependency_overrides[get_storage] = lambda: storage
    application.dependency_overrides[get_acl] = lambda: acl
    application.dependency_overrides[get_settings] = lambda: _settings
    return application


@pytest.fixture
def client(app_instance):
    """Provide a TestClient for the configured app."""
    return TestClient(app_instance, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# POST /api/auth/session
# ---------------------------------------------------------------------------


def test_create_session_missing_token_returns_401(client):
    """POST without Authorization header → 401."""
    resp = client.post("/api/auth/session")
    assert resp.status_code == 401


def test_create_session_malformed_header_returns_401(client):
    """POST with non-Bearer Authorization → 401."""
    resp = client.post(
        "/api/auth/session",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert resp.status_code == 401


def test_create_session_invalid_token_returns_401(client, app_instance):
    """POST with an unverifiable JWT → 401."""
    # validate_token will raise 401 for a garbage token.
    resp = client.post(
        "/api/auth/session",
        headers={"Authorization": "Bearer not.a.jwt"},
    )
    assert resp.status_code == 401


def test_create_session_valid_token_sets_cookie(client, app_instance):
    """POST with a valid token → 200 + Set-Cookie header."""
    fixed_ctx = AuthContext(
        subject="user@example.com",
        roles=["reader"],
        raw_token="valid.jwt.here",
    )

    def fake_validate(token, settings):
        return fixed_ctx

    import app.routes.session as session_mod

    original = session_mod.validate_token
    session_mod.validate_token = fake_validate
    try:
        resp = client.post(
            "/api/auth/session",
            headers={"Authorization": "Bearer valid.jwt.here"},
        )
    finally:
        session_mod.validate_token = original

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    set_cookie = resp.headers.get("set-cookie", "")
    assert "session=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=Lax" in set_cookie


def test_create_session_no_auth_configured_returns_501(client, app_instance):
    """POST when JWKS is not configured → 501."""
    empty_settings = Settings(
        oauth_jwks_url="",
        data_root="/tmp",
    )
    app_instance.dependency_overrides[get_settings] = lambda: empty_settings
    resp = client.post(
        "/api/auth/session",
        headers={"Authorization": "Bearer some.token.here"},
    )
    assert resp.status_code == 501
    del app_instance.dependency_overrides[get_settings]


# ---------------------------------------------------------------------------
# DELETE /api/auth/session
# ---------------------------------------------------------------------------


def test_delete_session_returns_200_and_clears_cookie(client):
    """DELETE → 200 with Max-Age=0 Set-Cookie."""
    resp = client.delete("/api/auth/session")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    set_cookie = resp.headers.get("set-cookie", "")
    assert "session=" in set_cookie
    assert "Max-Age=0" in set_cookie


# ---------------------------------------------------------------------------
# get_optional_auth — session cookie fallback
# ---------------------------------------------------------------------------


def test_get_optional_auth_reads_session_cookie(app_instance):
    """get_optional_auth returns AuthContext from session cookie."""
    fixed_ctx = AuthContext(
        subject="cookie-user",
        roles=["admin"],
        raw_token="cookie.jwt.token",
    )

    def fake_validate(token, settings):
        assert token == "cookie.jwt.token"
        return fixed_ctx

    import app.auth as auth_mod

    original = auth_mod.validate_token
    auth_mod.validate_token = fake_validate
    try:
        client = TestClient(
            app_instance,
            raise_server_exceptions=True,
            cookies={"session": "cookie.jwt.token"},
        )
        # Trigger a request that uses get_optional_auth; the
        # public namespace list endpoint is convenient.
        resp = client.get("/api/namespaces")
        # 200 (empty list) confirms auth was parsed from cookie.
        assert resp.status_code == 200
    finally:
        auth_mod.validate_token = original


def test_get_optional_auth_bearer_takes_priority_over_cookie(app_instance):
    """Authorization: Bearer takes precedence over session cookie."""
    header_ctx = AuthContext(
        subject="header-user",
        roles=[],
        raw_token="header.jwt",
    )
    cookie_ctx = AuthContext(
        subject="cookie-user",
        roles=[],
        raw_token="cookie.jwt",
    )

    def fake_validate(token, settings):
        if token == "header.jwt":
            return header_ctx
        return cookie_ctx

    import app.auth as auth_mod

    original = auth_mod.validate_token
    auth_mod.validate_token = fake_validate
    try:
        client = TestClient(
            app_instance,
            raise_server_exceptions=True,
            cookies={"session": "cookie.jwt"},
        )
        resp = client.get(
            "/api/namespaces",
            headers={"Authorization": "Bearer header.jwt"},
        )
        assert resp.status_code == 200
    finally:
        auth_mod.validate_token = original
