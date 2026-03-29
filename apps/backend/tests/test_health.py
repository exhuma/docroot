"""Tests for /livez, /readyz, and /healthz health probe endpoints."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings, get_settings


def _client(data_root: str) -> TestClient:
    """Build a TestClient with the given data_root.

    :param data_root: Path passed as DOCROOT_API_DATA_ROOT.
    :returns: Configured test client.
    """
    settings = Settings(
        data_root=data_root,
        oauth_jwks_url="",
        oauth_audience="",
    )
    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


# ---------------------------------------------------------------------------
# /livez
# ---------------------------------------------------------------------------


def test_livez_returns_200(tmp_path: Path) -> None:
    """Ensure /livez returns 200 with status ok."""
    client = _client(str(tmp_path))
    resp = client.get("/livez")
    assert resp.status_code == 200
    body = resp.json()
    assert body["probe"] == "livez"
    assert body["status"] == "ok"
    assert body["components"] == []
    assert "checked_at" in body


def test_livez_storage_unavailable_still_ok(tmp_path: Path) -> None:
    """Ensure /livez ignores missing storage and returns ok."""
    client = _client("/nonexistent/path/that/does/not/exist")
    resp = client.get("/livez")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# /readyz
# ---------------------------------------------------------------------------


def test_readyz_accessible_storage_returns_200(tmp_path: Path) -> None:
    """Ensure /readyz returns 200 when storage is accessible."""
    client = _client(str(tmp_path))
    resp = client.get("/readyz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["probe"] == "readyz"
    assert body["status"] == "ok"
    storage = next(c for c in body["components"] if c["name"] == "storage")
    assert storage["status"] == "ok"
    assert storage["required"] is True


def test_readyz_missing_storage_returns_503(tmp_path: Path) -> None:
    """Ensure /readyz returns 503 when storage path is missing."""
    client = _client("/nonexistent/path/that/does/not/exist")
    resp = client.get("/readyz")
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "fail"
    storage = next(c for c in body["components"] if c["name"] == "storage")
    assert storage["status"] == "fail"
    assert storage["reason_code"] == "storage_unavailable"


# ---------------------------------------------------------------------------
# /healthz
# ---------------------------------------------------------------------------


def test_healthz_accessible_storage_returns_200(
    tmp_path: Path,
) -> None:
    """Ensure /healthz returns 200 when storage is accessible."""
    client = _client(str(tmp_path))
    resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["probe"] == "healthz"
    assert body["status"] == "ok"


def test_healthz_missing_storage_returns_503(tmp_path: Path) -> None:
    """Ensure /healthz returns 503 when storage path is missing."""
    client = _client("/nonexistent/path/that/does/not/exist")
    resp = client.get("/healthz")
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "fail"


def test_healthz_response_schema(tmp_path: Path) -> None:
    """Ensure /healthz response contains all required schema fields."""
    client = _client(str(tmp_path))
    body = client.get("/healthz").json()
    assert "probe" in body
    assert "status" in body
    assert "checked_at" in body
    assert "components" in body
    for comp in body["components"]:
        assert "name" in comp
        assert "kind" in comp
        assert "required" in comp
        assert "status" in comp
        assert "reason_code" in comp
