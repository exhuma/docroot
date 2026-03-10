"""Tests for the /_internal/auth endpoint.

Verifies that the nginx auth_request handler correctly grants or
denies access based on namespace ACL and the caller's JWT roles.
"""
import pytest
from fastapi.testclient import TestClient

from app.acl import AclCache
from app.auth import AuthContext
from app.dependencies import get_acl, get_storage
from app.main import create_app
from app.storage import FilesystemStorage


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def data_dir(tmp_path):
    """Provide a temporary data directory."""
    return tmp_path


@pytest.fixture
def client(data_dir):
    """Provide a TestClient wired to a temp data directory."""
    storage = FilesystemStorage(data_root=data_dir)
    acl = AclCache()
    app = create_app()
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_acl] = lambda: acl
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_public_namespace(data_dir, name: str) -> None:
    """Create a namespace with public_read = true."""
    ns_dir = data_dir / "namespaces" / name
    ns_dir.mkdir(parents=True)
    (ns_dir / "namespace.toml").write_text(
        '[access]\npublic_read = true\n', encoding="utf-8"
    )


def _make_private_namespace(
    data_dir, name: str, role: str = "reader"
) -> None:
    """Create a private namespace with a read role."""
    ns_dir = data_dir / "namespaces" / name
    ns_dir.mkdir(parents=True)
    (ns_dir / "namespace.toml").write_text(
        "[access]\npublic_read = false\n\n"
        "[[access.roles]]\n"
        f'role = "{role}"\nread = true\nwrite = false\n',
        encoding="utf-8",
    )


def _auth_headers(client: TestClient) -> dict:
    """Override auth dependency to return a fixed AuthContext."""
    return {}


# ---------------------------------------------------------------------------
# Tests — public namespace
# ---------------------------------------------------------------------------


def test_public_namespace_no_token(client, data_dir):
    """Ensure a public namespace is readable without a token."""
    _make_public_namespace(data_dir, "public-ns")
    resp = client.get(
        "/_internal/auth",
        headers={"X-Original-URI": "/public-ns/proj/1.0/en/"},
    )
    assert resp.status_code == 200


def test_public_namespace_with_token(client, data_dir):
    """Ensure a public namespace is readable with any valid token."""
    _make_public_namespace(data_dir, "public-ns2")
    app = client.app
    from app.auth import get_optional_auth

    app.dependency_overrides[get_optional_auth] = (
        lambda: AuthContext(
            subject="user@example.com", roles=[]
        )
    )
    resp = client.get(
        "/_internal/auth",
        headers={
            "X-Original-URI": "/public-ns2/proj/1.0/en/"
        },
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Tests — private namespace
# ---------------------------------------------------------------------------


def test_private_namespace_no_token_returns_401(
    client, data_dir
):
    """Ensure a private namespace returns 401 without a token."""
    _make_private_namespace(data_dir, "private-ns")
    resp = client.get(
        "/_internal/auth",
        headers={
            "X-Original-URI": "/private-ns/proj/1.0/en/"
        },
    )
    assert resp.status_code == 401


def test_private_namespace_wrong_role_returns_403(
    client, data_dir
):
    """Ensure wrong roles result in 403 for a private namespace."""
    _make_private_namespace(data_dir, "private-ns2")
    app = client.app
    from app.auth import get_optional_auth

    app.dependency_overrides[get_optional_auth] = (
        lambda: AuthContext(
            subject="user@example.com", roles=["other-role"]
        )
    )
    resp = client.get(
        "/_internal/auth",
        headers={
            "X-Original-URI": "/private-ns2/proj/1.0/en/"
        },
    )
    assert resp.status_code == 403


def test_private_namespace_correct_role_returns_200(
    client, data_dir
):
    """Ensure correct read role grants access to a private namespace."""
    _make_private_namespace(
        data_dir, "private-ns3", role="reader"
    )
    app = client.app
    from app.auth import get_optional_auth

    app.dependency_overrides[get_optional_auth] = (
        lambda: AuthContext(
            subject="user@example.com", roles=["reader"]
        )
    )
    resp = client.get(
        "/_internal/auth",
        headers={
            "X-Original-URI": "/private-ns3/proj/1.0/en/"
        },
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Tests — edge cases
# ---------------------------------------------------------------------------


def test_missing_namespace_returns_404(client, data_dir):
    """Ensure a 404 is returned when the namespace does not exist."""
    resp = client.get(
        "/_internal/auth",
        headers={
            "X-Original-URI": "/nonexistent/proj/1.0/en/"
        },
    )
    assert resp.status_code == 404


def test_missing_x_original_uri_returns_400(client):
    """Ensure a 400 is returned when X-Original-URI is absent."""
    resp = client.get("/_internal/auth")
    assert resp.status_code == 400


def test_malformed_x_original_uri_returns_400(client):
    """Ensure a 400 is returned for a URI with no path segment."""
    resp = client.get(
        "/_internal/auth",
        headers={"X-Original-URI": ""},
    )
    assert resp.status_code == 400


def test_creator_has_read_access(client, data_dir):
    """Ensure the namespace creator can always read the namespace."""
    ns_dir = data_dir / "namespaces" / "owned-ns"
    ns_dir.mkdir(parents=True)
    (ns_dir / "namespace.toml").write_text(
        'creator = "owner@example.com"\n'
        "[access]\npublic_read = false\n",
        encoding="utf-8",
    )
    app = client.app
    from app.auth import get_optional_auth

    app.dependency_overrides[get_optional_auth] = (
        lambda: AuthContext(
            subject="owner@example.com", roles=[]
        )
    )
    resp = client.get(
        "/_internal/auth",
        headers={"X-Original-URI": "/owned-ns/proj/1.0/en/"},
    )
    assert resp.status_code == 200
