"""Tests for the /api/auth endpoint (nginx auth_request gate).

Verifies that the endpoint correctly enforces namespace ACL rules
when nginx delegates static-file authorization to FastAPI.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_acl, get_storage
from app.main import create_app
from app.settings import Settings
from app.storage import FilesystemStorage
from app.acl import AclCache


def _write_ns_toml(ns_dir: Path, content: str) -> None:
    """Write a namespace.toml file to *ns_dir*.

    :param ns_dir: Namespace directory path.
    :param content: TOML content to write.
    """
    (ns_dir / "namespace.toml").write_text(
        content, encoding="utf-8"
    )


def _make_client(
    tmp_path: Path,
) -> tuple[TestClient, FilesystemStorage]:
    """Build a test client with a fresh temporary storage root.

    :param tmp_path: Pytest temporary directory fixture.
    :returns: Tuple of test client and storage instance.
    """
    settings = Settings(
        data_root=str(tmp_path),
        oauth_jwks_url="",
        oauth_audience="",
    )
    storage = FilesystemStorage(data_root=str(tmp_path))
    acl = AclCache()
    app = create_app(settings=settings)
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_acl] = lambda: acl
    return TestClient(app, raise_server_exceptions=True), storage


def test_public_namespace_allows_unauthenticated(
    tmp_path: Path,
) -> None:
    """Ensure public namespaces return 200 without credentials."""
    client, storage = _make_client(tmp_path)
    storage.create_namespace(
        "pubns", public_read=True
    )
    ns_dir = storage.namespace_dir("pubns")
    _write_ns_toml(
        ns_dir,
        "[access]\npublic_read = true\n",
    )

    response = client.get(
        "/api/auth",
        headers={"X-Original-URI": "/pubns/proj/1.0/en/"},
    )
    assert response.status_code == 200


def test_private_namespace_unauthenticated_returns_401(
    tmp_path: Path,
) -> None:
    """Ensure private namespaces return 401 without credentials."""
    client, storage = _make_client(tmp_path)
    storage.create_namespace(
        "privns", public_read=False
    )
    ns_dir = storage.namespace_dir("privns")
    _write_ns_toml(
        ns_dir,
        "[access]\npublic_read = false\n",
    )

    response = client.get(
        "/api/auth",
        headers={"X-Original-URI": "/privns/proj/1.0/en/"},
    )
    assert response.status_code == 401


def test_missing_header_returns_400(tmp_path: Path) -> None:
    """Ensure missing X-Original-URI header returns 400."""
    client, _ = _make_client(tmp_path)

    response = client.get("/api/auth")
    assert response.status_code == 400


def test_empty_path_returns_400(tmp_path: Path) -> None:
    """Ensure an empty X-Original-URI returns 400."""
    client, _ = _make_client(tmp_path)

    response = client.get(
        "/api/auth",
        headers={"X-Original-URI": "/"},
    )
    assert response.status_code == 400


def test_spa_docs_path_extracts_correct_namespace(
    tmp_path: Path,
) -> None:
    """Ensure auth check works for the SPA docs-wrapper URL.

    The SPA wrapper URL has the form
    /{namespace}/{project}/docs/{version}/{locale}.  The 'docs'
    segment is a UI prefix, not a version.  The endpoint must
    extract the namespace from the first segment and evaluate the
    correct ACL.
    """
    client, storage = _make_client(tmp_path)
    storage.create_namespace(
        "myns", public_read=True
    )
    ns_dir = storage.namespace_dir("myns")
    _write_ns_toml(
        ns_dir,
        "[access]\npublic_read = true\n",
    )

    response = client.get(
        "/api/auth",
        headers={
            "X-Original-URI": "/myns/proj/docs/1.0/en"
        },
    )
    assert response.status_code == 200


def test_unknown_namespace_returns_404(tmp_path: Path) -> None:
    """Ensure a request for an unknown namespace returns 404."""
    client, _ = _make_client(tmp_path)

    response = client.get(
        "/api/auth",
        headers={
            "X-Original-URI": "/nosuchns/proj/1.0/en/"
        },
    )
    assert response.status_code == 404
