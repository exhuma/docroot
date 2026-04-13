"""Tests for the refs management route endpoints."""

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

_WRITER = "test-writer"
_NS = "testns"
_PROJ = "testproj"
_VER = "1.0"


def _make_client(
    tmp_path: Path,
    *,
    authenticated: bool = True,
) -> tuple[TestClient, FilesystemStorage]:
    """Build a test client with a fresh temporary storage root.

    :param tmp_path: Pytest temporary directory fixture.
    :param authenticated: Inject a writer auth context when True.
    :returns: Tuple of ``(TestClient, FilesystemStorage)``.
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
        ctx = AuthContext(subject=_WRITER)
        app.dependency_overrides[get_optional_auth] = lambda: ctx
    return TestClient(app, raise_server_exceptions=True), storage


def _make_zip(files: dict[str, str]) -> bytes:
    """Build an in-memory ZIP from filename→content pairs.

    :param files: Mapping of archive member names to content.
    :returns: Raw ZIP archive bytes.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _setup(storage: FilesystemStorage) -> None:
    """Create namespace, project, and one version for route tests.

    :param storage: Storage instance to operate on.
    """
    storage.create_namespace(_NS, creator=_WRITER)
    storage.create_project(_NS, _PROJ)
    import tempfile
    import zipfile as _zf

    zip_bytes = _make_zip({"index.html": "<h1>hi</h1>"})
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        zpath = tdp / "up.zip"
        zpath.write_bytes(zip_bytes)
        with _zf.ZipFile(zpath) as z:
            z.extractall(tdp / "out")
        storage.create_version(
            _NS,
            _PROJ,
            _VER,
            "en",
            tdp / "out",
            None,
            _WRITER,
            "2024-01-01T00:00:00",
        )


# ------------------------------------------------------------------
# GET /api/namespaces/{ns}/projects/{proj}/refs
# ------------------------------------------------------------------


def test_list_refs_empty(tmp_path: Path) -> None:
    """Ensure list_refs returns an empty list for a new project."""
    client, storage = _make_client(tmp_path)
    _setup(storage)
    resp = client.get(f"/api/namespaces/{_NS}/projects/{_PROJ}/refs")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_refs_returns_entries(tmp_path: Path) -> None:
    """Ensure list_refs returns all set refs sorted by name."""
    client, storage = _make_client(tmp_path)
    _setup(storage)
    storage.set_ref(_NS, _PROJ, "latest", _VER)
    storage.set_ref(_NS, _PROJ, "stable", _VER)
    resp = client.get(f"/api/namespaces/{_NS}/projects/{_PROJ}/refs")
    assert resp.status_code == 200
    data = resp.json()
    names = [r["name"] for r in data]
    assert names == sorted(names)
    versions = {r["name"]: r["version"] for r in data}
    assert versions == {"latest": _VER, "stable": _VER}


def test_list_refs_namespace_not_found(tmp_path: Path) -> None:
    """Ensure list_refs returns 404 for an unknown namespace."""
    client, _ = _make_client(tmp_path)
    resp = client.get("/api/namespaces/ghost/projects/x/refs")
    assert resp.status_code == 404


def test_list_refs_project_not_found(tmp_path: Path) -> None:
    """Ensure list_refs returns 404 for an unknown project."""
    client, storage = _make_client(tmp_path)
    storage.create_namespace(_NS, creator=_WRITER)
    resp = client.get(f"/api/namespaces/{_NS}/projects/ghost/refs")
    assert resp.status_code == 404


# ------------------------------------------------------------------
# PUT /api/namespaces/{ns}/projects/{proj}/refs/{ref}
# ------------------------------------------------------------------


def test_set_ref_creates(tmp_path: Path) -> None:
    """Ensure PUT refs/{ref} creates a new ref and returns it."""
    client, storage = _make_client(tmp_path)
    _setup(storage)
    resp = client.put(
        f"/api/namespaces/{_NS}/projects/{_PROJ}/refs/latest",
        json={"version": _VER},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "latest"
    assert body["version"] == _VER


def test_set_ref_updates_existing(tmp_path: Path) -> None:
    """Ensure PUT refs/{ref} overwrites an existing ref."""
    client, storage = _make_client(tmp_path)
    _setup(storage)
    # Put a second version in storage so we can point at it.
    import tempfile

    zip2 = _make_zip({"index.html": "<h1>v2</h1>"})
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        zpath = tdp / "up.zip"
        zpath.write_bytes(zip2)
        import zipfile as _zf

        with _zf.ZipFile(zpath) as z:
            z.extractall(tdp / "out")
        storage.create_version(
            _NS,
            _PROJ,
            "2.0",
            "en",
            tdp / "out",
            None,
            _WRITER,
            "2024-01-02T00:00:00",
        )
    storage.set_ref(_NS, _PROJ, "latest", _VER)
    resp = client.put(
        f"/api/namespaces/{_NS}/projects/{_PROJ}/refs/latest",
        json={"version": "2.0"},
    )
    assert resp.status_code == 200
    assert resp.json()["version"] == "2.0"


def test_set_ref_version_not_found(tmp_path: Path) -> None:
    """Ensure PUT refs/{ref} returns 404 when the version is absent."""
    client, storage = _make_client(tmp_path)
    _setup(storage)
    resp = client.put(
        f"/api/namespaces/{_NS}/projects/{_PROJ}/refs/latest",
        json={"version": "9.9.9"},
    )
    assert resp.status_code == 404


def test_set_ref_unauthorized(tmp_path: Path) -> None:
    """Ensure PUT refs/{ref} returns 403 without write permission."""
    client, storage = _make_client(tmp_path, authenticated=False)
    _setup(storage)
    resp = client.put(
        f"/api/namespaces/{_NS}/projects/{_PROJ}/refs/latest",
        json={"version": _VER},
    )
    assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# DELETE /api/namespaces/{ns}/projects/{proj}/refs/{ref}
# ------------------------------------------------------------------


def test_delete_ref_success(tmp_path: Path) -> None:
    """Ensure DELETE refs/{ref} removes the ref and returns 204."""
    client, storage = _make_client(tmp_path)
    _setup(storage)
    storage.set_ref(_NS, _PROJ, "latest", _VER)
    resp = client.delete(f"/api/namespaces/{_NS}/projects/{_PROJ}/refs/latest")
    assert resp.status_code == 204
    assert storage.list_refs(_NS, _PROJ) == {}


def test_delete_ref_not_found(tmp_path: Path) -> None:
    """Ensure DELETE refs/{ref} returns 404 for a missing ref."""
    client, storage = _make_client(tmp_path)
    _setup(storage)
    resp = client.delete(f"/api/namespaces/{_NS}/projects/{_PROJ}/refs/no-such")
    assert resp.status_code == 404


def test_delete_ref_unauthorized(tmp_path: Path) -> None:
    """Ensure DELETE refs/{ref} returns 401 without write permission."""
    client, storage = _make_client(tmp_path, authenticated=False)
    _setup(storage)
    storage.set_ref(_NS, _PROJ, "latest", _VER)
    resp = client.delete(f"/api/namespaces/{_NS}/projects/{_PROJ}/refs/latest")
    assert resp.status_code in (401, 403)
