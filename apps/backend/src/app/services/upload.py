"""Upload service: ZIP extraction and version installation.

Orchestrates ZIP validation, extraction to a temporary directory,
metadata generation, and atomic installation via the storage layer.
"""
import shutil
import stat
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.storage import FilesystemStorage, VersionConflict
from app.zipvalidator import validate_zip


async def install_upload(
    file: UploadFile,
    namespace: str,
    project: str,
    version: str,
    locale: str,
    latest: bool,
    uploader_subject: str,
    upload_timestamp: str | None,
    storage: FilesystemStorage,
) -> None:
    """Validate, extract, and install a documentation ZIP upload.

    Extracts the ZIP to a temporary directory on the same
    filesystem as the data root (enabling atomic rename). Generates
    ``metadata.toml`` from the supplied form fields. Calls
    :meth:`FilesystemStorage.create_version` for the atomic
    install.

    :param file: Uploaded ZIP file.
    :param namespace: Target namespace name.
    :param project: Target project name.
    :param version: Target version string.
    :param locale: Target locale code.
    :param latest: Whether to update the latest symlink.
    :param uploader_subject: JWT subject of the uploader.
    :param upload_timestamp: ISO 8601 timestamp; defaults to now.
    :param storage: Storage instance.
    :raises HTTPException: 422 for invalid ZIP; 409 for conflicts.
    """
    if upload_timestamp is None:
        upload_timestamp = (
            datetime.now(timezone.utc).isoformat()
        )

    uploads_tmp = storage.data_root / ".uploads"
    uploads_tmp.mkdir(parents=True, exist_ok=True)
    tmpdir = Path(tempfile.mkdtemp(dir=uploads_tmp))
    try:
        zip_path = tmpdir / "upload.zip"
        zip_path.write_bytes(await file.read())

        try:
            validate_zip(zip_path)
        except ValueError as exc:
            raise HTTPException(
                status_code=422, detail=str(exc)
            ) from exc

        extract_dir = tmpdir / "content"
        extract_dir.mkdir()
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.infolist():
                if member.filename == "metadata.toml":
                    continue
                unix_mode = member.external_attr >> 16
                if stat.S_ISLNK(unix_mode):
                    continue
                zf.extract(member, extract_dir)

        try:
            storage.create_version(
                namespace,
                project,
                version,
                locale,
                extract_dir,
                latest,
                uploader_subject,
                upload_timestamp,
            )
        except VersionConflict:
            raise HTTPException(
                status_code=409,
                detail="Version+locale already exists",
            )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
