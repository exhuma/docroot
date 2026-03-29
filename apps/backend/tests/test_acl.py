"""Tests for the AclCache class, focusing on creator-based access."""

import shutil
from pathlib import Path

import pytest

from app.acl import AclCache

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def acl() -> AclCache:
    """Provide a fresh AclCache instance."""
    return AclCache()


def _write_toml(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_creator_has_read_access(acl: AclCache, tmp_path: Path) -> None:
    """Ensure the namespace creator always has read access."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "user@example.com"\n\n[access]\npublic_read = false\n',
    )
    acl_data = acl.get(ns_dir)
    assert acl.can_read(acl_data, [], subject="user@example.com")


def test_creator_has_write_access(acl: AclCache, tmp_path: Path) -> None:
    """Ensure the namespace creator always has write access."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "user@example.com"\n\n[access]\npublic_read = false\n',
    )
    acl_data = acl.get(ns_dir)
    assert acl.can_write(acl_data, [], subject="user@example.com")


def test_non_creator_denied_write_without_role(acl: AclCache, tmp_path: Path) -> None:
    """Ensure a non-creator without a write role is denied."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n\n[access]\npublic_read = false\n',
    )
    acl_data = acl.get(ns_dir)
    assert not acl.can_write(acl_data, [], subject="other@example.com")


def test_non_creator_denied_read_on_private(acl: AclCache, tmp_path: Path) -> None:
    """Ensure a non-creator cannot read a private namespace."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n\n[access]\npublic_read = false\n',
    )
    acl_data = acl.get(ns_dir)
    assert not acl.can_read(acl_data, [], subject="other@example.com")


def test_role_based_write_still_works(acl: AclCache, tmp_path: Path) -> None:
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
    assert acl.can_write(acl_data, ["editor"], subject="other@example.com")


def test_public_read_allows_unauthenticated(acl: AclCache, tmp_path: Path) -> None:
    """Ensure public_read=true allows unauthenticated read access."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n\n[access]\npublic_read = true\n',
    )
    acl_data = acl.get(ns_dir)
    assert acl.can_read(acl_data, [], subject="")


def test_creator_subject_mismatch_denied(acl: AclCache, tmp_path: Path) -> None:
    """Ensure partial subject match does not grant access."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n\n[access]\npublic_read = false\n',
    )
    acl_data = acl.get(ns_dir)
    assert not acl.can_write(acl_data, [], subject="owner@example")
    assert not acl.can_write(acl_data, [], subject="OWNER@EXAMPLE.COM")


def test_role_matching_is_case_insensitive(acl: AclCache, tmp_path: Path) -> None:
    """Ensure role comparison ignores case on both sides."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n'
        "\n[access]\npublic_read = false\n\n"
        "[[access.roles]]\n"
        'role = "Docroot-Editor"\nread = true\nwrite = true\n',
    )
    acl_data = acl.get(ns_dir)
    # JWT carries lowercase variant; TOML stores mixed-case.
    assert acl.can_read(acl_data, ["docroot-editor"], subject="other@example.com")
    assert acl.can_write(acl_data, ["docroot-editor"], subject="other@example.com")
    # TOML stores lowercase; JWT carries uppercase variant.
    ns_dir2 = tmp_path / "ns2"
    ns_dir2.mkdir()
    _write_toml(
        ns_dir2 / "namespace.toml",
        'creator = "owner@example.com"\n'
        "\n[access]\npublic_read = false\n\n"
        "[[access.roles]]\n"
        'role = "docroot-editor"\nread = true\nwrite = false\n',
    )
    acl_data2 = acl.get(ns_dir2)
    assert acl.can_read(acl_data2, ["DOCROOT-EDITOR"], subject="other@example.com")
    assert not acl.can_write(acl_data2, ["DOCROOT-EDITOR"], subject="other@example.com")


def test_can_browse_returns_true_when_browsable(acl: AclCache, tmp_path: Path) -> None:
    """Ensure can_browse returns True when browsable=true."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n'
        "\n[access]\npublic_read = false\nbrowsable = true\n",
    )
    acl_data = acl.get(ns_dir)
    assert acl.can_browse(acl_data, [], subject="")


def test_can_browse_false_when_not_browsable(acl: AclCache, tmp_path: Path) -> None:
    """Ensure can_browse returns False when browsable=false."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n'
        "\n[access]\npublic_read = false\nbrowsable = false\n",
    )
    acl_data = acl.get(ns_dir)
    assert not acl.can_browse(acl_data, [], subject="")


def test_can_browse_true_when_can_read(acl: AclCache, tmp_path: Path) -> None:
    """Ensure can_browse returns True whenever can_read is True."""
    ns_dir = tmp_path / "mynamespace"
    ns_dir.mkdir()
    # browsable=false but creator match → can_browse must still pass.
    _write_toml(
        ns_dir / "namespace.toml",
        'creator = "owner@example.com"\n'
        "\n[access]\npublic_read = false\nbrowsable = false\n",
    )
    acl_data = acl.get(ns_dir)
    assert acl.can_browse(acl_data, [], subject="owner@example.com")


def test_documented_example_fixture_is_valid(acl: AclCache, tmp_path: Path) -> None:
    """Ensure the documented namespace.toml example is parseable and correct.

    This test guards against the example fixture drifting out of sync
    with the implementation.
    """
    ns_dir = tmp_path / "example"
    ns_dir.mkdir()
    shutil.copy(FIXTURES / "namespace.toml", ns_dir / "namespace.toml")
    acl_data = acl.get(ns_dir)

    # Creator always has full access.
    assert acl.can_read(acl_data, [], subject="alice@example.com")
    assert acl.can_write(acl_data, [], subject="alice@example.com")

    # Role-based editor access.
    assert acl.can_read(acl_data, ["docroot-editor"], subject="bob@example.com")
    assert acl.can_write(acl_data, ["docroot-editor"], subject="bob@example.com")

    # Role-based reader access: read yes, write no.
    assert acl.can_read(acl_data, ["docroot-reader"], subject="carol@example.com")
    assert not acl.can_write(acl_data, ["docroot-reader"], subject="carol@example.com")

    # Namespace is browsable without authentication.
    assert acl.can_browse(acl_data, [], subject="")
