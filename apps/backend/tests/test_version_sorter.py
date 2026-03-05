"""Tests for the version_sorter module."""
import pytest

from app.version_sorter import sort_versions


def test_sort_semver():
    """Ensure semver sorting orders versions numerically."""
    versions = ["1.10.0", "1.2.0", "2.0.0", "1.2.1"]
    result = sort_versions(versions, "semver")
    assert result == ["1.2.0", "1.2.1", "1.10.0", "2.0.0"]


def test_sort_pep440():
    """Ensure pep440 sorting handles pre-releases correctly."""
    versions = ["1.0.0", "1.0.0a1", "2.0.0", "1.0.0b2"]
    result = sort_versions(versions, "pep440")
    assert result == [
        "1.0.0a1", "1.0.0b2", "1.0.0", "2.0.0"
    ]


def test_sort_unknown_scheme_returns_unchanged():
    """Ensure unknown scheme with bad regex returns list unchanged."""
    versions = ["v2", "v1", "v3"]
    result = sort_versions(versions, "")
    assert result == ["v2", "v1", "v3"]


def test_sort_calver():
    """Ensure calver sorting orders CalVer strings numerically."""
    versions = ["2024.1.0", "2023.12.0", "2024.10.0"]
    result = sort_versions(versions, "calver")
    assert result == [
        "2023.12.0", "2024.1.0", "2024.10.0"
    ]
