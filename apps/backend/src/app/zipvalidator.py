import stat
import zipfile
from pathlib import Path

MAX_FILES = 500
MAX_EXTRACTED_BYTES = 500 * 1024 * 1024  # 500 MB


def validate_zip(zip_path: Path) -> None:
    """Validate a ZIP archive before extraction.

    Raises ValueError describing the violation on failure.
    """
    with zipfile.ZipFile(zip_path) as zf:
        members = zf.infolist()

        if len(members) > MAX_FILES:
            raise ValueError(
                f"Archive exceeds max file count ({MAX_FILES})"
            )

        total_size = sum(m.file_size for m in members)
        if total_size > MAX_EXTRACTED_BYTES:
            raise ValueError(
                "Archive exceeds max extracted size (500 MB)"
            )

        has_index = False
        for member in members:
            name = member.filename

            parts = name.rstrip("/").split("/")
            if ".." in parts:
                raise ValueError(
                    f"Traversal path detected: {name}"
                )
            if name.startswith("/"):
                raise ValueError(
                    f"Absolute path detected: {name}"
                )

            unix_mode = member.external_attr >> 16
            if stat.S_ISLNK(unix_mode):
                raise ValueError(
                    f"Symlink entry detected: {name}"
                )

            if name == "index.html":
                has_index = True

        if not has_index:
            raise ValueError(
                "Archive must contain a top-level index.html"
            )
