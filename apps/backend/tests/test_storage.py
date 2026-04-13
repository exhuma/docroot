"""Tests for the FilesystemStorage class."""

from pathlib import Path

import pytest

from app.storage import (
    FilesystemStorage,
    RefNotFound,
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


def test_create_version_basic(storage: FilesystemStorage, tmp_path: Path):
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
        None,
        "user@test",
        "2024-01-01T00:00:00Z",
    )
    locales = storage.list_locales("ns", "proj", "1.0.0")
    assert "en" in locales


def test_create_version_conflict(storage: FilesystemStorage, tmp_path: Path):
    """Ensure creating a duplicate version+locale raises conflict."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src1 = make_source_dir(
        tmp_path / "src1",
        {"index.html": "<h1>v1</h1>"},
    )
    storage.create_version(
        "ns",
        "proj",
        "1.0.0",
        "en",
        src1,
        None,
        "user",
        "2024-01-01T00:00:00Z",
    )
    src2 = make_source_dir(
        tmp_path / "src2",
        {"index.html": "<h1>v2</h1>"},
    )
    with pytest.raises(VersionConflict):
        storage.create_version(
            "ns",
            "proj",
            "1.0.0",
            "en",
            src2,
            None,
            "user",
            "2024-01-01T00:00:00Z",
        )


def test_resolve_version_latest(storage: FilesystemStorage, tmp_path: Path):
    """Ensure resolve_version resolves the 'latest' ref alias."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src = make_source_dir(
        tmp_path / "src",
        {"index.html": "<h1>Hello</h1>"},
    )
    storage.create_version(
        "ns",
        "proj",
        "2.0",
        "en",
        src,
        "latest",
        "user",
        "2024-01-01T00:00:00Z",
    )
    version, locale = storage.resolve_version("ns", "proj", "latest", "en")
    assert version == "2.0"
    assert locale == "en"


def test_resolve_locale_fallback(storage: FilesystemStorage, tmp_path: Path):
    """Ensure locale fallback resolves to 'en' when available."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src = make_source_dir(
        tmp_path / "src",
        {"index.html": "<h1>Hello</h1>"},
    )
    storage.create_version(
        "ns",
        "proj",
        "1.0",
        "en",
        src,
        None,
        "user",
        "2024-01-01T00:00:00Z",
    )
    version, locale = storage.resolve_version("ns", "proj", "1.0", "fr")
    assert version == "1.0"
    assert locale == "en"


def test_resolve_version_latest_not_set(
    storage: FilesystemStorage,
):
    """Ensure resolving an unset ref raises VersionNotFound."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    with pytest.raises(VersionNotFound):
        storage.resolve_version("ns", "proj", "latest", "en")


def test_resolve_locale_not_found(storage: FilesystemStorage, tmp_path: Path):
    """Ensure locale fallback picks first available locale."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src = make_source_dir(
        tmp_path / "src",
        {"index.html": "<h1>Hello</h1>"},
    )
    storage.create_version(
        "ns",
        "proj",
        "1.0",
        "de",
        src,
        None,
        "user",
        "2024-01-01T00:00:00Z",
    )
    # "fr" not present, "en" not present; "de" is fallback
    version, locale = storage.resolve_version("ns", "proj", "1.0", "fr")
    assert version == "1.0"
    assert locale == "de"


def test_delete_version_ref_preserved(storage: FilesystemStorage, tmp_path: Path):
    """Ensure deleting a version preserves refs but breaks resolution."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src1 = make_source_dir(tmp_path / "src1", {"index.html": "<h1>v1</h1>"})
    storage.create_version(
        "ns",
        "proj",
        "1.0",
        "en",
        src1,
        "latest",
        "user",
        "2024-01-01T00:00:00Z",
    )
    src2 = make_source_dir(tmp_path / "src2", {"index.html": "<h1>v2</h1>"})
    storage.create_version(
        "ns",
        "proj",
        "2.0",
        "en",
        src2,
        None,
        "user",
        "2024-06-01T00:00:00Z",
    )
    storage.set_ref("ns", "proj", "latest", "2.0")
    refs = storage.list_refs("ns", "proj")
    assert refs.get("latest") == "2.0"
    storage.delete_version("ns", "proj", "2.0", "en")
    # Ref still exists after deletion.
    refs = storage.list_refs("ns", "proj")
    assert refs.get("latest") == "2.0"
    # But resolving it now raises VersionNotFound.
    with pytest.raises(VersionNotFound):
        storage.resolve_version("ns", "proj", "latest", "en")


def test_create_namespace_no_creator_role(
    storage: FilesystemStorage,
):
    """Ensure create_namespace does not add creator as a role entry."""
    import tomllib

    storage.create_namespace("ns-owner", creator="owner@example.com")
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

    storage.create_namespace("ns-transfer", creator="original@example.com")
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
    storage.transfer_ownership("ns-preserve", "new@example.com")
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


def test_create_namespace_stores_creator_display_name(
    storage: FilesystemStorage,
) -> None:
    """Ensure create_namespace persists creator_display_name."""
    import tomllib

    storage.create_namespace(
        "ns-dn",
        creator="uuid-1234",
        creator_display_name="Alice Example",
    )
    ns_dir = storage.namespace_dir("ns-dn")
    with open(ns_dir / "namespace.toml", "rb") as fh:
        data = tomllib.load(fh)
    assert data.get("creator") == "uuid-1234"
    assert data.get("creator_display_name") == "Alice Example"


def test_create_namespace_no_display_name_omitted(
    storage: FilesystemStorage,
) -> None:
    """Ensure creator_display_name is absent when not supplied."""
    import tomllib

    storage.create_namespace("ns-no-dn", creator="uuid-5678")
    ns_dir = storage.namespace_dir("ns-no-dn")
    with open(ns_dir / "namespace.toml", "rb") as fh:
        data = tomllib.load(fh)
    assert "creator_display_name" not in data


def test_transfer_ownership_stores_display_name(
    storage: FilesystemStorage,
) -> None:
    """Ensure transfer_ownership updates creator_display_name."""
    import tomllib

    storage.create_namespace(
        "ns-xfer-dn",
        creator="old-uuid",
        creator_display_name="Old Owner",
    )
    storage.transfer_ownership(
        "ns-xfer-dn",
        "new-uuid",
        new_owner_display_name="New Owner",
    )
    ns_dir = storage.namespace_dir("ns-xfer-dn")
    with open(ns_dir / "namespace.toml", "rb") as fh:
        data = tomllib.load(fh)
    assert data.get("creator") == "new-uuid"
    assert data.get("creator_display_name") == "New Owner"


def test_update_acl_preserves_creator_display_name(
    storage: FilesystemStorage,
) -> None:
    """Ensure update_namespace_acl preserves creator_display_name."""
    import tomllib

    storage.create_namespace(
        "ns-acl-dn",
        creator="uuid-acl",
        creator_display_name="ACL Owner",
    )
    storage.update_namespace_acl("ns-acl-dn", "editors", True, True)
    ns_dir = storage.namespace_dir("ns-acl-dn")
    with open(ns_dir / "namespace.toml", "rb") as fh:
        data = tomllib.load(fh)
    assert data.get("creator_display_name") == "ACL Owner"


def test_get_namespace_meta_returns_creator_display_name(
    storage: FilesystemStorage,
) -> None:
    """Ensure get_namespace_meta returns creator_display_name."""
    storage.create_namespace(
        "ns-meta-dn",
        creator="uuid-meta",
        creator_display_name="Meta Owner",
    )
    meta = storage.get_namespace_meta("ns-meta-dn")
    assert meta.get("creator_display_name") == "Meta Owner"


def test_create_namespace_stores_display_name(
    storage: FilesystemStorage,
) -> None:
    """Ensure create_namespace writes display_name to namespace.toml."""
    import tomllib

    storage.create_namespace(
        "my-ns",
        creator="user@example.com",
        display_name="My Namespace",
    )
    ns_dir = storage.namespace_dir("my-ns")
    with open(ns_dir / "namespace.toml", "rb") as fh:
        data = tomllib.load(fh)
    assert data.get("display_name") == "My Namespace"


def test_create_namespace_ns_display_name_omitted(
    storage: FilesystemStorage,
) -> None:
    """Ensure display_name is absent from toml when not supplied."""
    import tomllib

    storage.create_namespace("ns-no-disp", creator="user@example.com")
    ns_dir = storage.namespace_dir("ns-no-disp")
    with open(ns_dir / "namespace.toml", "rb") as fh:
        data = tomllib.load(fh)
    assert "display_name" not in data


def test_get_namespace_meta_returns_display_name(
    storage: FilesystemStorage,
) -> None:
    """Ensure get_namespace_meta returns the display_name field."""
    storage.create_namespace(
        "ns-disp",
        creator="user@example.com",
        display_name="Display Name",
    )
    meta = storage.get_namespace_meta("ns-disp")
    assert meta.get("display_name") == "Display Name"


def test_update_namespace_acl_preserves_display_name(
    storage: FilesystemStorage,
) -> None:
    """Ensure update_namespace_acl preserves display_name."""
    import tomllib

    storage.create_namespace(
        "ns-acl-disp",
        creator="user@example.com",
        display_name="ACL Namespace",
    )
    storage.update_namespace_acl("ns-acl-disp", "editors", True, True)
    ns_dir = storage.namespace_dir("ns-acl-disp")
    with open(ns_dir / "namespace.toml", "rb") as fh:
        data = tomllib.load(fh)
    assert data.get("display_name") == "ACL Namespace"


def test_transfer_ownership_preserves_namespace_display_name(
    storage: FilesystemStorage,
) -> None:
    """Ensure transfer_ownership preserves namespace display_name."""
    import tomllib

    storage.create_namespace(
        "ns-xfer-disp",
        creator="old-user",
        display_name="Xfer Namespace",
    )
    storage.transfer_ownership("ns-xfer-disp", "new-user")
    ns_dir = storage.namespace_dir("ns-xfer-disp")
    with open(ns_dir / "namespace.toml", "rb") as fh:
        data = tomllib.load(fh)
    assert data.get("display_name") == "Xfer Namespace"


def test_create_project_writes_project_toml(
    storage: FilesystemStorage,
) -> None:
    """Ensure create_project writes project.toml with display_name."""
    import tomllib

    storage.create_namespace("ns-proj-toml")
    storage.create_project("ns-proj-toml", "my-proj", display_name="My Project")
    proj_dir = storage.namespace_dir("ns-proj-toml") / "projects" / "my-proj"
    with open(proj_dir / "project.toml", "rb") as fh:
        data = tomllib.load(fh)
    assert data.get("display_name") == "My Project"


def test_create_project_no_display_name_uses_slug(
    storage: FilesystemStorage,
) -> None:
    """Ensure project.toml display_name defaults to the slug."""
    import tomllib

    storage.create_namespace("ns-slug-default")
    storage.create_project("ns-slug-default", "my-slug")
    proj_dir = storage.namespace_dir("ns-slug-default") / "projects" / "my-slug"
    with open(proj_dir / "project.toml", "rb") as fh:
        data = tomllib.load(fh)
    assert data.get("display_name") == "my-slug"


def test_get_project_meta_returns_display_name(
    storage: FilesystemStorage,
) -> None:
    """Ensure get_project_meta returns the display_name field."""
    storage.create_namespace("ns-pmeta")
    storage.create_project("ns-pmeta", "p-meta", display_name="Project Meta")
    meta = storage.get_project_meta("ns-pmeta", "p-meta")
    assert meta.get("display_name") == "Project Meta"


def test_get_project_meta_missing_toml_returns_empty(
    storage: FilesystemStorage,
) -> None:
    """Ensure get_project_meta returns empty dict for missing toml."""
    storage.create_namespace("ns-pmeta-missing")
    # Manually create directory without project.toml
    proj_dir = storage.namespace_dir("ns-pmeta-missing") / "projects" / "bare-proj"
    (proj_dir / "versions").mkdir(parents=True)
    meta = storage.get_project_meta("ns-pmeta-missing", "bare-proj")
    assert meta == {}


def test_disk_usage_empty_returns_empty(
    storage: FilesystemStorage,
) -> None:
    """Ensure disk_usage returns empty list when no namespaces exist."""
    result = storage.disk_usage()
    assert result == []


def test_disk_usage_single_namespace(
    storage: FilesystemStorage,
    tmp_path: Path,
) -> None:
    """Ensure disk_usage returns one group for one namespace."""
    storage.create_namespace("ns-du", display_name="DU Namespace")
    result = storage.disk_usage()
    assert len(result) == 1
    group = result[0]
    assert len(group.namespaces) == 1
    ns = group.namespaces[0]
    assert ns.name == "ns-du"
    assert ns.display_name == "DU Namespace"
    assert ns.size_bytes >= 0
    assert group.total_bytes >= 0
    assert group.free_bytes >= 0
    assert group.used_bytes >= 0
    assert len(group.mount_group) == 16


def test_disk_usage_namespaces_on_same_device_share_group(
    storage: FilesystemStorage,
) -> None:
    """Ensure namespaces on the same device appear in one group."""
    storage.create_namespace("ns-a")
    storage.create_namespace("ns-b")
    result = storage.disk_usage()
    # Both namespaces share the same tmp device.
    assert len(result) == 1
    names = {ns.name for ns in result[0].namespaces}
    assert names == {"ns-a", "ns-b"}


def test_disk_usage_mount_group_is_ephemeral(
    storage: FilesystemStorage,
) -> None:
    """Ensure mount_group hash differs between calls."""
    storage.create_namespace("ns-ephemeral")
    result1 = storage.disk_usage()
    result2 = storage.disk_usage()
    # Hashes are salted per-call so they must differ.
    assert result1[0].mount_group != result2[0].mount_group


def test_disk_usage_namespace_size_includes_files(
    storage: FilesystemStorage,
    tmp_path: Path,
) -> None:
    """Ensure namespace size_bytes reflects actual file content."""
    storage.create_namespace("ns-size")
    storage.create_project("ns-size", "p")
    src = make_source_dir(
        tmp_path / "src",
        {"index.html": "x" * 1000},
    )
    storage.create_version(
        "ns-size",
        "p",
        "1.0",
        "en",
        src,
        None,
        "user",
        "2024-01-01T00:00:00",
    )
    result = storage.disk_usage()
    assert len(result) == 1
    ns = result[0].namespaces[0]
    assert ns.size_bytes >= 1000


# ------------------------------------------------------------------
# Ref tests
# ------------------------------------------------------------------


def test_set_ref_creates_symlink(
    storage: FilesystemStorage,
    tmp_path: Path,
) -> None:
    """Ensure set_ref creates a symlink inside refs/."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src = make_source_dir(tmp_path / "src", {"index.html": "<h1/>"})
    storage.create_version("ns", "proj", "1.0", "en", src, None, "u", "")
    storage.set_ref("ns", "proj", "latest", "1.0")
    refs = storage.list_refs("ns", "proj")
    assert refs == {"latest": "1.0"}


def test_set_ref_updates_existing(
    storage: FilesystemStorage,
    tmp_path: Path,
) -> None:
    """Ensure set_ref atomically replaces an existing ref."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src1 = make_source_dir(tmp_path / "s1", {"index.html": ""})
    src2 = make_source_dir(tmp_path / "s2", {"index.html": ""})
    storage.create_version("ns", "proj", "1.0", "en", src1, None, "u", "")
    storage.create_version("ns", "proj", "2.0", "en", src2, None, "u", "")
    storage.set_ref("ns", "proj", "latest", "1.0")
    storage.set_ref("ns", "proj", "latest", "2.0")
    assert storage.list_refs("ns", "proj")["latest"] == "2.0"


def test_get_ref_not_found(storage: FilesystemStorage) -> None:
    """Ensure get_ref raises RefNotFound for a missing ref."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    with pytest.raises(RefNotFound):
        storage.get_ref("ns", "proj", "missing")


def test_list_refs_empty(storage: FilesystemStorage) -> None:
    """Ensure list_refs returns empty dict for a new project."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    assert storage.list_refs("ns", "proj") == {}


def test_list_refs_populated(
    storage: FilesystemStorage,
    tmp_path: Path,
) -> None:
    """Ensure list_refs returns the correct name-to-version map."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src1 = make_source_dir(tmp_path / "s1", {"index.html": ""})
    src2 = make_source_dir(tmp_path / "s2", {"index.html": ""})
    storage.create_version("ns", "proj", "1.0", "en", src1, None, "u", "")
    storage.create_version("ns", "proj", "2.0", "en", src2, None, "u", "")
    storage.set_ref("ns", "proj", "latest", "2.0")
    storage.set_ref("ns", "proj", "stable", "1.0")
    refs = storage.list_refs("ns", "proj")
    assert refs == {"latest": "2.0", "stable": "1.0"}


def test_delete_ref(
    storage: FilesystemStorage,
    tmp_path: Path,
) -> None:
    """Ensure delete_ref removes the ref symlink."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src = make_source_dir(tmp_path / "src", {"index.html": ""})
    storage.create_version("ns", "proj", "1.0", "en", src, None, "u", "")
    storage.set_ref("ns", "proj", "latest", "1.0")
    storage.delete_ref("ns", "proj", "latest")
    assert storage.list_refs("ns", "proj") == {}


def test_delete_ref_not_found(storage: FilesystemStorage) -> None:
    """Ensure delete_ref raises RefNotFound for a missing ref."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    with pytest.raises(RefNotFound):
        storage.delete_ref("ns", "proj", "no-such-ref")


def test_resolve_via_ref(
    storage: FilesystemStorage,
    tmp_path: Path,
) -> None:
    """Ensure resolve_version resolves any ref name, not just 'latest'."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src = make_source_dir(tmp_path / "src", {"index.html": ""})
    storage.create_version("ns", "proj", "3.0", "en", src, None, "u", "")
    storage.set_ref("ns", "proj", "stable", "3.0")
    version, locale = storage.resolve_version("ns", "proj", "stable", "en")
    assert version == "3.0"
    assert locale == "en"


def test_resolve_broken_ref(
    storage: FilesystemStorage,
    tmp_path: Path,
) -> None:
    """Ensure resolving a ref to a deleted version raises VersionNotFound."""
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    src = make_source_dir(tmp_path / "src", {"index.html": ""})
    storage.create_version("ns", "proj", "1.0", "en", src, "latest", "u", "")
    storage.delete_version("ns", "proj", "1.0", "en")
    with pytest.raises(VersionNotFound):
        storage.resolve_version("ns", "proj", "latest", "en")
