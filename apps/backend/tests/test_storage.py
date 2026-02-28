from pathlib import Path

import pytest

from app.storage import (
    FilesystemStorage,
    LocaleNotFound,
    VersionConflict,
    VersionNotFound,
)


def make_source_dir(base: Path, files: dict) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (base / name).write_text(content)
    return base


def test_create_namespace(storage: FilesystemStorage):
    storage.create_namespace("myns")
    assert "myns" in storage.list_namespaces()


def test_create_project(storage: FilesystemStorage):
    storage.create_namespace("myns")
    storage.create_project("myns", "myproj")
    assert "myproj" in storage.list_projects("myns")


def test_list_namespaces(storage: FilesystemStorage):
    storage.create_namespace("ns1")
    storage.create_namespace("ns2")
    result = storage.list_namespaces()
    assert "ns1" in result
    assert "ns2" in result


def test_list_projects(storage: FilesystemStorage):
    storage.create_namespace("ns1")
    storage.create_project("ns1", "proj1")
    storage.create_project("ns1", "proj2")
    result = storage.list_projects("ns1")
    assert result == ["proj1", "proj2"]


def test_create_version_basic(
    storage: FilesystemStorage, tmp_path: Path
):
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
    storage.create_namespace("ns")
    storage.create_project("ns", "proj")
    with pytest.raises(VersionNotFound):
        storage.resolve_version("ns", "proj", "latest", "en")


def test_resolve_locale_not_found(
    storage: FilesystemStorage, tmp_path: Path
):
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
    # "fr" not present, "en" not present; "de" is returned as fallback
    version, locale = storage.resolve_version(
        "ns", "proj", "1.0", "fr"
    )
    assert version == "1.0"
    assert locale == "de"
