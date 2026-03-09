"""Tests for the AclCache class, focusing on creator-based access."""
from pathlib import Path

import pytest

from app.acl import AclCache


@pytest.fixture
def acl() -> AclCache:
    """Provide a fresh AclCache instance."""
    return AclCache()


def _write_toml(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_creator_has_read_access(
    acl: AclCache, tmp_path: Path
) -> None:
    """Ensure the namespace creator always has read access."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "user@example.com"\n'
        "\n[access]\npublic_read = false\n",
    )
    acl_data = acl.get(ns_dir)
    assert acl.can_read(
        acl_data, [], subject="user@example.com"
    )


def test_creator_has_write_access(
    acl: AclCache, tmp_path: Path
) -> None:
    """Ensure the namespace creator always has write access."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "user@example.com"\n'
        "\n[access]\npublic_read = false\n",
    )
    acl_data = acl.get(ns_dir)
    assert acl.can_write(
        acl_data, [], subject="user@example.com"
    )


def test_non_creator_denied_write_without_role(
    acl: AclCache, tmp_path: Path
) -> None:
    """Ensure a non-creator without a write role is denied."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n'
        "\n[access]\npublic_read = false\n",
    )
    acl_data = acl.get(ns_dir)
    assert not acl.can_write(
        acl_data, [], subject="other@example.com"
    )


def test_non_creator_denied_read_on_private(
    acl: AclCache, tmp_path: Path
) -> None:
    """Ensure a non-creator cannot read a private namespace."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n'
        "\n[access]\npublic_read = false\n",
    )
    acl_data = acl.get(ns_dir)
    assert not acl.can_read(
        acl_data, [], subject="other@example.com"
    )


def test_role_based_write_still_works(
    acl: AclCache, tmp_path: Path
) -> None:
    """Ensure role-based write access still works for non-creators."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n'
        "\n[access]\npublic_read = false\n\n"
        "[[access.roles]]\n"
        'role = "editor"\nread = true\nwrite = true\n',
    )
    acl_data = acl.get(ns_dir)
    assert acl.can_write(
        acl_data, ["editor"], subject="other@example.com"
    )


def test_public_read_allows_unauthenticated(
    acl: AclCache, tmp_path: Path
) -> None:
    """Ensure public_read=true allows unauthenticated read access."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n'
        "\n[access]\npublic_read = true\n",
    )
    acl_data = acl.get(ns_dir)
    assert acl.can_read(acl_data, [], subject="")


def test_creator_subject_mismatch_denied(
    acl: AclCache, tmp_path: Path
) -> None:
    """Ensure partial subject match does not grant access."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n'
        "\n[access]\npublic_read = false\n",
    )
    acl_data = acl.get(ns_dir)
    assert not acl.can_write(
        acl_data, [], subject="owner@example"
    )
    assert not acl.can_write(
        acl_data, [], subject="OWNER@EXAMPLE.COM"
    )
