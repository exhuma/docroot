"""Pytest configuration and shared fixtures for backend tests."""

import pytest

from app.storage import FilesystemStorage


@pytest.fixture
def storage(tmp_path):
    """Provide a FilesystemStorage instance backed by a temp dir."""
    return FilesystemStorage(data_root=tmp_path)
