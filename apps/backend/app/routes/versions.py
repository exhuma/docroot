import shutil
import stat
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.acl import AclCache
from app.auth import AuthContext, get_optional_auth
from app.models import ResolveOut, VersionOut
from app.resolver import resolve_version
from app.storage import (
    FilesystemStorage,
    LocaleNotFound,
    VersionConflict,
    VersionNotFound,
)
from app.validators import (
    validate_locale,
    validate_namespace,
    validate_project,
    validate_version,
)
from app.zipvalidator import validate_zip

router = APIRouter(tags=["versions"])

_storage = FilesystemStorage()
_acl = AclCache()


def _require_read(
    namespace: str,
    auth: AuthContext | None,
) -> None:
    ns_dir = _storage.namespace_dir(namespace)
    acl = _acl.get(ns_dir)
    roles = auth.roles if auth else []
    if not _acl.can_read(acl, roles):
        if auth is None:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
            )
        raise HTTPException(
            status_code=403,
            detail="Read permission denied",
        )


def _require_write(
    namespace: str,
    auth: AuthContext | None,
) -> None:
    if auth is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )
    ns_dir = _storage.namespace_dir(namespace)
    acl = _acl.get(ns_dir)
    if not _acl.can_write(acl, auth.roles):
        raise HTTPException(
            status_code=403,
            detail="Write permission denied",
        )


@router.get(
    "/api/namespaces/{namespace}/projects/{project}/versions",
    response_model=list[VersionOut],
)
async def list_versions(
    namespace: str,
    project: str,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
) -> list[VersionOut]:
    validate_namespace(namespace)
    validate_project(project)
    if not _storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    if not _storage.project_exists(namespace, project):
        raise HTTPException(
            status_code=404, detail="Project not found"
        )
    _require_read(namespace, auth)
    versions = _storage.list_versions(namespace, project)
    current_latest = _storage.get_latest(namespace, project)
    result = []
    for v in versions:
        locales = _storage.list_locales(namespace, project, v)
        result.append(
            VersionOut(
                name=v,
                locales=locales,
                is_latest=(v == current_latest),
            )
        )
    return result


@router.get(
    "/api/namespaces/{namespace}/projects/{project}"
    "/versions/{version}/locales",
    response_model=list[str],
)
async def list_locales(
    namespace: str,
    project: str,
    version: str,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
) -> list[str]:
    validate_namespace(namespace)
    validate_project(project)
    if not _storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    _require_read(namespace, auth)
    return _storage.list_locales(namespace, project, version)


@router.post(
    "/api/namespaces/{namespace}/projects/{project}/upload",
    status_code=201,
)
async def upload_version(
    namespace: str,
    project: str,
    file: Annotated[UploadFile, File(...)],
    version: Annotated[str, Form(...)],
    locale: Annotated[str, Form(...)],
    latest: Annotated[bool, Form()] = False,
    uploader_subject: Annotated[
        str | None, Form()
    ] = None,
    upload_timestamp: Annotated[
        str | None, Form()
    ] = None,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
) -> dict:
    validate_namespace(namespace)
    validate_project(project)
    validate_version(version)
    validate_locale(locale)

    if not _storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    if not _storage.project_exists(namespace, project):
        raise HTTPException(
            status_code=404, detail="Project not found"
        )

    _require_write(namespace, auth)

    if upload_timestamp is None:
        upload_timestamp = (
            datetime.now(timezone.utc).isoformat()
        )
    if uploader_subject is None and auth is not None:
        uploader_subject = auth.subject
    uploader_subject = uploader_subject or ""

    # Create temp dir on the same filesystem as data root so
    # that atomic rename in storage works without a copy.
    uploads_tmp = _storage.data_root / ".uploads"
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
                # Server generates metadata.toml; ignore upload.
                if member.filename == "metadata.toml":
                    continue
                # Skip any symlink entries (defense-in-depth).
                unix_mode = member.external_attr >> 16
                if stat.S_ISLNK(unix_mode):
                    continue
                zf.extract(member, extract_dir)

        try:
            _storage.create_version(
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

    return {"status": "created"}


@router.delete(
    "/api/namespaces/{namespace}/projects/{project}"
    "/versions/{version}/{locale}",
    status_code=204,
)
async def delete_version(
    namespace: str,
    project: str,
    version: str,
    locale: str,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
) -> None:
    validate_namespace(namespace)
    validate_project(project)
    validate_version(version)
    validate_locale(locale)
    if not _storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    _require_write(namespace, auth)
    try:
        _storage.delete_version(namespace, project, version, locale)
    except VersionNotFound:
        raise HTTPException(
            status_code=404,
            detail="Version+locale not found",
        )


@router.put(
    "/api/namespaces/{namespace}/projects/{project}"
    "/versions/{version}/latest",
    status_code=204,
)
async def set_latest(
    namespace: str,
    project: str,
    version: str,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
) -> None:
    validate_namespace(namespace)
    validate_project(project)
    validate_version(version)
    if not _storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    if not _storage.project_exists(namespace, project):
        raise HTTPException(
            status_code=404, detail="Project not found"
        )
    _require_write(namespace, auth)
    versions = _storage.list_versions(namespace, project)
    if version not in versions:
        raise HTTPException(
            status_code=404, detail="Version not found"
        )
    _storage.set_latest(namespace, project, version)


@router.get(
    "/api/namespaces/{namespace}/projects/{project}"
    "/resolve/{version}/{locale}",
    response_model=ResolveOut,
)
async def resolve_endpoint(
    namespace: str,
    project: str,
    version: str,
    locale: str,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
) -> ResolveOut:
    validate_namespace(namespace)
    validate_project(project)
    validate_locale(locale)
    if not _storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    _require_read(namespace, auth)
    try:
        resolved_version, resolved_locale = resolve_version(
            _storage, namespace, project, version, locale
        )
    except (VersionNotFound, LocaleNotFound) as exc:
        raise HTTPException(
            status_code=404, detail=str(exc)
        ) from exc
    return ResolveOut(
        version=resolved_version,
        locale=resolved_locale,
        fallback_used=(resolved_locale != locale),
    )
