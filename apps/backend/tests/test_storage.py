"""Tests for the FilesystemStorage class."""
from pathlib import Path

import pytest

from app.storage import (
    FilesystemStorage,
    LocaleNotFound,
    VersionConflict,
    VersionNotFound,
)


def make_source_dir(base: Path, files: dict) -> Path:
    """Create a temporary source directory with given files."""
    base.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (base / name).write_text(content)
    return base


def test_create_namespace(storage: FilesystemStorage):
    """Ensure create_namespace creates the namespace directory."""
    storage.create_namespace("myns")
    assert "myns" in storage.list_namespaces()


def test_create_project(storage: FilesystemStorage):
    """Ensure create_project creates the project under the namespace."""
    storage.create_namespace("myns")
    storage.create_project("myns", "myproj")
    assert "myproj" in storage.list_projects("myns")


def test_list_namespaces(storage: FilesystemStorage):
    """Ensure list_namespaces returns all created namespaces."""
    storage.create_namespace("ns1")
    storage.create_namespace("ns2")
    result = storage.list_namespaces()
    assert "ns1" in result
    assert "ns2" in result


def test_list_projects(storage: FilesystemStorage):
    """Ensure list_projects returns all projects in a namespace."""
    storage.create_namespace("ns1")
    storage.create_project("ns1", "proj1")
    storage.create_project("ns1", "proj2")
    result = storage.list_projects("ns1")
    assert result == ["proj1", "proj2"]


def test_create_version_basic(
    storage: FilesystemStorage, tmp_path: Path
):
    """Ensure create_version stores the locale directory."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src = make_source_dir(
        tmp_path / "src",
        {"index.html": "<h1>Hello</h1>"},
    )
    storage.create_version(
        "ns",
        "proj",
        "1.0.0",
        "en",
        src,
        False,
        "user@test",
        "2024-01-01T00:00:00Z",
    )
    locales = storage.list_locales("ns", "proj", "1.0.0")
    assert "en" in locales


def test_create_version_conflict(
    storage: FilesystemStorage, tmp_path: Path
):
    """Ensure creating a duplicate version+locale raises conflict."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src1 = make_source_dir(
        tmp_path / "src1",
        {"index.html": "<h1>v1</h1>"},
    )
    storage.create_version(
        "ns", "proj", "1.0.0", "en",
        src1, False, "user", "2024-01-01T00:00:00Z",
    )
    src2 = make_source_dir(
        tmp_path / "src2",
        {"index.html": "<h1>v2</h1>"},
    )
    with pytest.raises(VersionConflict):
        storage.create_version(
            "ns", "proj", "1.0.0", "en",
            src2, False, "user", "2024-01-01T00:00:00Z",
        )


def test_resolve_version_latest(
    storage: FilesystemStorage, tmp_path: Path
):
    """Ensure resolve_version resolves the 'latest' alias."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src = make_source_dir(
        tmp_path / "src",
        {"index.html": "<h1>Hello</h1>"},
    )
    storage.create_version(
        "ns", "proj", "2.0", "en",
        src, True, "user", "2024-01-01T00:00:00Z",
    )
    version, locale = storage.resolve_version(
        "ns", "proj", "latest", "en"
    )
    assert version == "2.0"
    assert locale == "en"


def test_resolve_locale_fallback(
    storage: FilesystemStorage, tmp_path: Path
):
    """Ensure locale fallback resolves to 'en' when available."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src = make_source_dir(
        tmp_path / "src",
        {"index.html": "<h1>Hello</h1>"},
    )
    storage.create_version(
        "ns", "proj", "1.0", "en",
        src, False, "user", "2024-01-01T00:00:00Z",
    )
    version, locale = storage.resolve_version(
        "ns", "proj", "1.0", "fr"
    )
    assert version == "1.0"
    assert locale == "en"


def test_resolve_version_latest_not_set(
    storage: FilesystemStorage,
):
    """Ensure resolving 'latest' without a symlink raises error."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    with pytest.raises(VersionNotFound):
        storage.resolve_version("ns", "proj", "latest", "en")


def test_resolve_locale_not_found(
    storage: FilesystemStorage, tmp_path: Path
):
    """Ensure locale fallback picks first available locale."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src = make_source_dir(
        tmp_path / "src",
        {"index.html": "<h1>Hello</h1>"},
    )
    storage.create_version(
        "ns", "proj", "1.0", "de",
        src, False, "user", "2024-01-01T00:00:00Z",
    )
    # "fr" not present, "en" not present; "de" is fallback
    version, locale = storage.resolve_version(
        "ns", "proj", "1.0", "fr"
    )
    assert version == "1.0"
    assert locale == "de"


def test_delete_version_updates_latest(
    storage: FilesystemStorage, tmp_path: Path
):
    """Ensure deleting the latest version updates the symlink."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src1 = make_source_dir(
        tmp_path / "src1", {"index.html": "<h1>v1</h1>"}
    )
    storage.create_version(
        "ns", "proj", "1.0", "en",
        src1, True, "user", "2024-01-01T00:00:00Z",
    )
    src2 = make_source_dir(
        tmp_path / "src2", {"index.html": "<h1>v2</h1>"}
    )
    storage.create_version(
        "ns", "proj", "2.0", "en",
        src2, False, "user", "2024-06-01T00:00:00Z",
    )
    storage.set_latest("ns", "proj", "2.0")
    assert storage.get_latest("ns", "proj") == "2.0"
    storage.delete_version("ns", "proj", "2.0", "en")
    assert storage.get_latest("ns", "proj") == "1.0"


def test_create_namespace_no_creator_role(
    storage: FilesystemStorage,
):
    """Ensure create_namespace does not add creator as a role entry."""
    import tomllib
    storage.create_namespace(
        "ns-owner", creator="owner@example.com"
    )
    ns_dir = storage.namespace_dir("ns-owner")
    with open(ns_dir / "namespace.toml", "rb") as fh:
        data = tomllib.load(fh)
    roles = data.get("access", {}).get("roles", [])
    role_names = [r.get("role") for r in roles]
    assert "owner@example.com" not in role_names
    assert data.get("creator") == "owner@example.com"


def test_transfer_ownership(storage: FilesystemStorage):
    """Ensure transfer_ownership updates the creator field."""
    import tomllib
    storage.create_namespace(
        "ns-transfer", creator="original@example.com"
    )
    storage.transfer_ownership("ns-transfer", "new@example.com")
    ns_dir = storage.namespace_dir("ns-transfer")
    with open(ns_dir / "namespace.toml", "rb") as fh:
        data = tomllib.load(fh)
    assert data.get("creator") == "new@example.com"


def test_transfer_ownership_preserves_roles(
    storage: FilesystemStorage,
):
    """Ensure transfer_ownership preserves existing ACL roles."""
    import tomllib
    storage.create_namespace(
        "ns-preserve",
        creator="original@example.com",
        roles=[{"role": "editors", "read": True, "write": True}],
    )
    storage.transfer_ownership(
        "ns-preserve", "new@example.com"
    )
    ns_dir = storage.namespace_dir("ns-preserve")
    with open(ns_dir / "namespace.toml", "rb") as fh:
        data = tomllib.load(fh)
    assert data.get("creator") == "new@example.com"
    roles = data.get("access", {}).get("roles", [])
    assert any(r.get("role") == "editors" for r in roles)


def test_transfer_ownership_not_found(
    storage: FilesystemStorage,
):
    """Ensure transfer_ownership raises NamespaceNotFound."""
    from app.storage import NamespaceNotFound
    with pytest.raises(NamespaceNotFound):
        storage.transfer_ownership("no-such-ns", "x@example.com")
