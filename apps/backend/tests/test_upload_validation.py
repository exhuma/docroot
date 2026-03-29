"""Tests for the ZIP upload validation logic."""

import io
import stat
import zipfile
from pathlib import Path

import pytest

from app.zipvalidator import validate_zip


def make_zip_bytes(
    files: dict,
    extra_attrs: dict | None = None,
) -> bytes:
    """Build an in-memory ZIP archive from a dict of filename→content."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_STORED
            if extra_attrs and name in extra_attrs:
                info.external_attr = extra_attrs[name]
            zf.writestr(info, content)
    return buf.getvalue()


def make_zip_file(
    tmp_path: Path,
    files: dict,
    extra_attrs: dict | None = None,
) -> Path:
    """Write a ZIP archive to a temp file and return its path."""
    zip_path = tmp_path / "test.zip"
    zip_path.write_bytes(make_zip_bytes(files, extra_attrs))
    return zip_path


def test_zip_traversal_rejected(tmp_path: Path):
    """Ensure path-traversal entries are rejected."""
    zip_path = make_zip_file(
        tmp_path,
        {
            "index.html": "<h1>Test</h1>",
            "../evil.txt": "evil",
        },
    )
    with pytest.raises(ValueError, match="[Tt]raversal"):
        validate_zip(zip_path)


def test_zip_symlink_rejected(tmp_path: Path):
    """Ensure symlink entries are rejected."""
    symlink_attr = stat.S_IFLNK << 16
    zip_path = make_zip_file(
        tmp_path,
        {
            "index.html": "<h1>Test</h1>",
            "link": "target",
        },
        extra_attrs={"link": symlink_attr},
    )
    with pytest.raises(ValueError, match="[Ss]ymlink"):
        validate_zip(zip_path)


def test_zip_missing_index_rejected(tmp_path: Path):
    """Ensure archives without index.html are rejected."""
    zip_path = make_zip_file(
        tmp_path,
        {"readme.txt": "hello"},
    )
    with pytest.raises(ValueError, match="index.html"):
        validate_zip(zip_path)


def test_valid_zip_accepted(tmp_path: Path):
    """Ensure a well-formed archive passes validation."""
    zip_path = make_zip_file(
        tmp_path,
        {
            "index.html": "<h1>Hello</h1>",
            "style.css": "body {}",
            "assets/logo.png": "fakepng",
        },
    )
    validate_zip(zip_path)


def test_zip_absolute_path_rejected(tmp_path: Path):
    """Ensure absolute-path entries are rejected."""
    zip_path = make_zip_file(
        tmp_path,
        {
            "index.html": "<h1>Test</h1>",
            "/etc/passwd": "root:x:0:0",
        },
    )
    with pytest.raises(ValueError, match="[Aa]bsolute"):
        validate_zip(zip_path)
