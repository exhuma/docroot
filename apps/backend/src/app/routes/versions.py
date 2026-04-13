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
    "/api/namespaces/{namespace}/projects/{project}/versions",
    response_model=list[VersionOut],
)
async def list_versions(
    namespace: str,
    project: str,
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
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
        raise HTTPException(status_code=404, detail="Namespace not found")
    if not storage.project_exists(namespace, project):
        raise HTTPException(status_code=404, detail="Project not found")
    require_browse(namespace, storage, acl, auth)
    versions = storage.list_versions(namespace, project)
    proj_meta = storage.get_project_meta(namespace, project)
    versioning = str(proj_meta.get("versioning", ""))
    if not versioning:
        ns_meta = storage.get_namespace_meta(namespace)
        versioning = str(ns_meta.get("versioning", ""))
    if versioning:
        versions = reversed(sort_versions(versions, versioning))
    refs_map = storage.list_refs(namespace, project)
    # Invert: {ref_name: version} -> {version: [ref_names]}
    version_refs: dict[str, list[str]] = {}
    for ref_name, ver in refs_map.items():
        version_refs.setdefault(ver, []).append(ref_name)
    result: list[VersionOut] = []
    for v in versions:
        locales = storage.list_locales(namespace, project, v)
        result.append(
            VersionOut(
                name=v,
                locales=locales,
                refs=sorted(version_refs.get(v, [])),
            )
        )
    return result


@router.get(
    "/api/namespaces/{namespace}/projects/{project}/versions/{version}/locales",
    response_model=list[str],
)
async def list_locales(
    namespace: str,
    project: str,
    version: str,
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
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
        raise HTTPException(status_code=404, detail="Namespace not found")
    require_browse(namespace, storage, acl, auth)
    return storage.list_locales(namespace, project, version)


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
    ref: Annotated[str | None, Form()] = None,
    uploader_subject: Annotated[str | None, Form()] = None,
    upload_timestamp: Annotated[str | None, Form()] = None,
    versioning: Annotated[str | None, Form()] = None,
    force: Annotated[bool, Form()] = False,
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> dict[str, str]:
    """Upload a documentation ZIP for a specific version+locale.

    The ZIP must contain a top-level ``index.html``. The
    ``metadata.toml`` file in the archive (if present) is
    discarded; the server generates it from the supplied form
    fields.

    When the project does not yet exist it is created implicitly
    using the supplied ``versioning`` scheme (if any).

    When the project already exists and a ``versioning`` value is
    supplied that differs from the stored scheme, the upload is
    rejected with **409** unless ``force=true`` is also provided.

    Requires write access to the namespace.

    ---

    :param namespace: Namespace name.
    :param project: Project name.
    :param file: ZIP archive (multipart field ``file``).
    :param version: Target version string (form field).
    :param locale: Two-letter locale code (form field).
    :param ref: Optional ref name to assign after upload
        (form field, e.g. ``"latest"``).
    :param uploader_subject: Override uploader identity.
    :param upload_timestamp: ISO 8601 timestamp (form field).
    :param versioning: Versioning scheme for the project
        (form field).  Only used when the project does not yet
        exist, or to validate that the stored scheme has not
        changed.
    :param force: When ``true``, bypass a versioning-scheme
        mismatch and proceed with the upload (form field).
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: ``{"status": "created"}``.
    :raises 404: If the namespace does not exist.
    :raises 409: If the versioning scheme conflicts with the
        stored project scheme and ``force`` is not set.
    :raises 422: If the ZIP fails validation.
    :raises 409: If the version+locale already exists.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    require_write(namespace, storage, acl, auth)
    requested_versioning = versioning or ""
    if not storage.project_exists(namespace, project):
        storage.create_project(
            namespace,
            project,
            versioning=requested_versioning,
        )
    elif requested_versioning:
        proj_meta = storage.get_project_meta(namespace, project)
        stored_versioning = str(proj_meta.get("versioning", ""))
        if (
            stored_versioning
            and stored_versioning != requested_versioning
            and not force
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Versioning scheme mismatch: project uses "
                    f"'{stored_versioning}' but upload specifies "
                    f"'{requested_versioning}'. "
                    f"Pass force=true to override."
                ),
            )

    subject = uploader_subject or (auth.subject if auth else "")
    await install_upload(
        file=file,
        namespace=namespace,
        project=project,
        version=version,
        locale=locale,
        ref=ref,
        uploader_subject=subject,
        upload_timestamp=upload_timestamp,
        storage=storage,
    )
    return {"status": "created"}


@router.delete(
    "/api/namespaces/{namespace}/projects/{project}/versions/{version}/{locale}",
    status_code=204,
)
async def delete_version(
    namespace: str,
    project: str,
    version: str,
    locale: str,
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
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
        raise HTTPException(status_code=404, detail="Namespace not found")
    require_write(namespace, storage, acl, auth)
    try:
        storage.delete_version(namespace, project, version, locale)
    except VersionNotFound:
        raise HTTPException(
            status_code=404,
            detail="Version+locale not found",
        )


@router.get(
    "/api/namespaces/{namespace}/projects/{project}/resolve/{version}/{locale}",
    response_model=ResolveOut,
)
async def resolve_endpoint(
    namespace: str,
    project: str,
    version: str,
    locale: str,
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
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
        raise HTTPException(status_code=404, detail="Namespace not found")
    require_browse(namespace, storage, acl, auth)
    try:
        resolved_version, resolved_locale = storage.resolve_version(
            namespace, project, version, locale
        )
    except (VersionNotFound, LocaleNotFound) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ResolveOut(
        version=resolved_version,
        locale=resolved_locale,
        fallback_used=(resolved_locale != locale),
    )
