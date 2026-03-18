"""Tests for the GET /api/oidc-config endpoint.

Verifies that the endpoint correctly exposes OIDC configuration
from application settings.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings, get_settings


def _make_client(settings: Settings) -> TestClient:
    """Build a test client with given settings.

    :param settings: Application settings to use.
    :returns: Configured test client.
    """
    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app, raise_server_exceptions=True)


def test_oidc_config_returns_issuer_and_client_id(
    tmp_path: Path,
) -> None:
    """Ensure /api/oidc-config returns issuer and client_id."""
    settings = Settings(
        data_root=str(tmp_path),
        oidc_issuer="https://idp.example.com/realms/demo",
        oidc_client_id="docroot-ui",
    )
    client = _make_client(settings)

    response = client.get("/api/oidc-config")

    assert response.status_code == 200
    body = response.json()
    assert body["issuer"] == (
        "https://idp.example.com/realms/demo"
    )
    assert body["client_id"] == "docroot-ui"


def test_oidc_config_returns_null_when_not_configured(
    tmp_path: Path,
) -> None:
    """Ensure /api/oidc-config returns null values when unset."""
    settings = Settings(
        data_root=str(tmp_path),
        oidc_issuer="",
        oidc_client_id="",
    )
    client = _make_client(settings)

    response = client.get("/api/oidc-config")

    assert response.status_code == 200
    body = response.json()
    assert body["issuer"] is None
    assert body["client_id"] is None



def test_oidc_config_returns_issuer_and_client_id(
    tmp_path: Path,
) -> None:
    """Ensure /api/oidc-config returns issuer and client_id."""
    settings = Settings(
        data_root=str(tmp_path),
        oidc_issuer="https://idp.example.com/realms/demo",
        oidc_client_id="docroot-ui",
    )
    client = _make_client(settings)

    response = client.get("/api/oidc-config")

    assert response.status_code == 200
    body = response.json()
    assert body["issuer"] == (
        "https://idp.example.com/realms/demo"
    )
    assert body["client_id"] == "docroot-ui"


def test_oidc_config_returns_null_when_not_configured(
    tmp_path: Path,
) -> None:
    """Ensure /api/oidc-config returns null values when unset."""
    settings = Settings(
        data_root=str(tmp_path),
        oidc_issuer="",
        oidc_client_id="",
    )
    client = _make_client(settings)

    response = client.get("/api/oidc-config")

    assert response.status_code == 200
    body = response.json()
    assert body["issuer"] is None
    assert body["client_id"] is None
