"""Version and locale management routes.

Handles version listing (with optional sorting by namespace
versioning config), documentation uploads, and version/locale
resolution with fallback logic.
"""
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
from app.dependencies import (
    get_acl,
    get_storage,
    require_browse,
    require_write,
)
from app.schemas import ResolveOut, VersionOut
from app.services.upload import install_upload
from app.storage import (
    FilesystemStorage,
    LocaleNotFound,
    VersionNotFound,
)
from app.version_sorter import sort_versions

router = APIRouter(tags=["versions"])


@router.get(
    "/api/namespaces/{namespace}/projects/{project}"
    "/versions",
    response_model=list[VersionOut],
)
async def list_versions(
    namespace: str,
    project: str,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> list[VersionOut]:
    """List all versions of a project.

    Versions are sorted according to the namespace versioning
    scheme (``semver``, ``calver``, ``pep440``, custom regex,
    or default lexicographic order).

    Requires read access to the namespace.

    ---

    :param namespace: Namespace name.
    :param project: Project name.
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: List of version objects ordered by versioning
        scheme.
    :raises 404: If the namespace or project does not exist.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    if not storage.project_exists(namespace, project):
        raise HTTPException(
            status_code=404, detail="Project not found"
        )
    require_browse(namespace, storage, acl, auth)
    versions = storage.list_versions(namespace, project)
    ns_meta = storage.get_namespace_meta(namespace)
    versioning = str(ns_meta.get("versioning", ""))
    if versioning:
        versions = sort_versions(versions, versioning)
    current_latest = storage.get_latest(namespace, project)
    result: list[VersionOut] = []
    for v in versions:
        locales = storage.list_locales(namespace, project, v)
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
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> list[str]:
    """List available locales for a specific version.

    Requires read access to the namespace.

    ---

    :param namespace: Namespace name.
    :param project: Project name.
    :param version: Version string.
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: Sorted list of locale codes.
    :raises 404: If the namespace does not exist.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    require_browse(namespace, storage, acl, auth)
    return storage.list_locales(namespace, project, version)


@router.post(
    "/api/namespaces/{namespace}/projects/{project}"
    "/upload",
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
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> dict[str, str]:
    """Upload a documentation ZIP for a specific version+locale.

    The ZIP must contain a top-level ``index.html``. The
    ``metadata.toml`` file in the archive (if present) is
    discarded; the server generates it from the supplied form
    fields.

    Requires write access to the namespace.

    ---

    :param namespace: Namespace name.
    :param project: Project name.
    :param file: ZIP archive (multipart field ``file``).
    :param version: Target version string (form field).
    :param locale: Two-letter locale code (form field).
    :param latest: Set as latest after upload (form field).
    :param uploader_subject: Override uploader identity.
    :param upload_timestamp: ISO 8601 timestamp (form field).
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: ``{"status": "created"}``.
    :raises 404: If the namespace or project does not exist.
    :raises 422: If the ZIP fails validation.
    :raises 409: If the version+locale already exists.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    if not storage.project_exists(namespace, project):
        raise HTTPException(
            status_code=404, detail="Project not found"
        )
    require_write(namespace, storage, acl, auth)

    subject = uploader_subject or (
        auth.subject if auth else ""
    )
    await install_upload(
        file=file,
        namespace=namespace,
        project=project,
        version=version,
        locale=locale,
        latest=latest,
        uploader_subject=subject,
        upload_timestamp=upload_timestamp,
        storage=storage,
    )
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
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> None:
    """Delete a specific version+locale artifact.

    If the deleted version was the latest, the latest symlink is
    updated to the most recently uploaded remaining version.

    Requires write access to the namespace.

    ---

    :param namespace: Namespace name.
    :param project: Project name.
    :param version: Version string.
    :param locale: Locale code.
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :raises 404: If the namespace or version+locale does not
        exist.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    require_write(namespace, storage, acl, auth)
    try:
        storage.delete_version(
            namespace, project, version, locale
        )
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
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> None:
    """Mark a version as the latest.

    Atomically updates the ``latest`` symlink for the project.

    Requires write access to the namespace.

    ---

    :param namespace: Namespace name.
    :param project: Project name.
    :param version: Version string to mark as latest.
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :raises 404: If the namespace, project, or version is not
        found.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    if not storage.project_exists(namespace, project):
        raise HTTPException(
            status_code=404, detail="Project not found"
        )
    require_write(namespace, storage, acl, auth)
    versions = storage.list_versions(namespace, project)
    if version not in versions:
        raise HTTPException(
            status_code=404, detail="Version not found"
        )
    storage.set_latest(namespace, project, version)


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
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> ResolveOut:
    """Resolve a version alias and locale with fallback logic.

    Returns the concrete version and locale that will be served.
    When a locale fallback is applied, ``fallback_used`` is
    ``true``.

    Requires read access to the namespace.

    ---

    :param namespace: Namespace name.
    :param project: Project name.
    :param version: Version string or ``"latest"``.
    :param locale: Requested locale code.
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: Resolved version and locale information.
    :raises 404: If the namespace, version, or locale cannot be
        resolved.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    require_browse(namespace, storage, acl, auth)
    try:
        resolved_version, resolved_locale = (
            storage.resolve_version(
                namespace, project, version, locale
            )
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
