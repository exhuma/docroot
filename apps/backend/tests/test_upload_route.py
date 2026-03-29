"""Tests for the upload route endpoint behaviour."""

import io
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.acl import AclCache
from app.auth import AuthContext, get_optional_auth
from app.dependencies import get_acl, get_storage
from app.main import create_app
from app.settings import Settings
from app.storage import FilesystemStorage

_WRITER_SUBJECT = "test-writer"


def _make_client(
    tmp_path: Path,
    *,
    authenticated: bool = True,
) -> tuple[TestClient, FilesystemStorage]:
    """Build a test client with a fresh temporary storage root.

    :param tmp_path: Pytest temporary directory fixture.
    :param authenticated: When True, injects an AuthContext whose
        subject matches the namespace creator so that write access
        is granted.
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
    if authenticated:
        auth_ctx = AuthContext(subject=_WRITER_SUBJECT)
        app.dependency_overrides[get_optional_auth] = lambda: auth_ctx
    return TestClient(app, raise_server_exceptions=True), storage


def _make_zip_bytes(files: dict) -> bytes:
    """Build an in-memory ZIP archive from a dict of filename→content.

    :param files: Mapping of filename to content string.
    :returns: Raw ZIP bytes.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def test_upload_auto_creates_missing_project(tmp_path: Path) -> None:
    """Ensure uploading to a missing project auto-creates it."""
    client, storage = _make_client(tmp_path)
    storage.create_namespace(
        "myns",
        creator=_WRITER_SUBJECT,
        public_read=True,
    )

    zip_bytes = _make_zip_bytes({"index.html": "<h1>Hello</h1>"})
    response = client.post(
        "/api/namespaces/myns/projects/newproj/upload",
        files={"file": ("docs.zip", zip_bytes, "application/zip")},
        data={"version": "1.0.0", "locale": "en"},
    )

    assert response.status_code == 201
    assert storage.project_exists("myns", "newproj")


def test_upload_missing_namespace_returns_404(tmp_path: Path) -> None:
    """Ensure uploading to a missing namespace still returns 404."""
    client, _ = _make_client(tmp_path, authenticated=False)

    zip_bytes = _make_zip_bytes({"index.html": "<h1>Hello</h1>"})
    response = client.post(
        "/api/namespaces/noexist/projects/proj/upload",
        files={"file": ("docs.zip", zip_bytes, "application/zip")},
        data={"version": "1.0.0", "locale": "en"},
    )

    assert response.status_code == 404
