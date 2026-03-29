"""ZIP archive validator for documentation uploads.

Enforces file-count and extracted-size limits, rejects
path-traversal and absolute-path entries, and requires a top-level
``index.html``. Limits are read from application settings and can
be overridden via environment variables.
"""

import stat
import zipfile
from pathlib import Path

from app.settings import get_settings


def validate_zip(zip_path: Path) -> None:
    """Validate a ZIP archive before extraction.

    Checks enforced:

    - File count does not exceed ``DOCROOT_API_ZIP_MAX_FILES``
    - Total extracted size does not exceed
      ``DOCROOT_API_ZIP_MAX_EXTRACTED_MB`` MB
    - No path-traversal (``..``) entries
    - No absolute-path entries
    - No symlink entries
    - Archive contains a top-level ``index.html``

    :param zip_path: Path to the ZIP file to validate.
    :raises ValueError: With a description of the violation.
    """
    settings = get_settings()
    max_files = settings.zip_max_files
    max_bytes = settings.zip_max_extracted_mb * 1024 * 1024

    with zipfile.ZipFile(zip_path) as zf:
        members = zf.infolist()

        if len(members) > max_files:
            raise ValueError(f"Archive exceeds max file count ({max_files})")

        total_size = sum(m.file_size for m in members)
        if total_size > max_bytes:
            raise ValueError(
                f"Archive exceeds max extracted size "
                f"({settings.zip_max_extracted_mb} MB)"
            )

        has_index = False
        for member in members:
            name = member.filename

            parts = name.rstrip("/").split("/")
            if ".." in parts:
                raise ValueError(f"Traversal path detected: {name}")
            if name.startswith("/"):
                raise ValueError(f"Absolute path detected: {name}")

            unix_mode = member.external_attr >> 16
            if stat.S_ISLNK(unix_mode):
                raise ValueError(f"Symlink entry detected: {name}")

            if name == "index.html":
                has_index = True

        if not has_index:
            raise ValueError("Archive must contain a top-level index.html")
