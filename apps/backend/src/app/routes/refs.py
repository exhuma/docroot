"""Ref (tag) management routes.

Refs are named pointers to specific versions, stored as symlinks
inside the project's ``refs/`` directory. Any ref name is valid;
``latest`` is just a conventional name like a git tag.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.acl import AclCache
from app.auth import AuthContext, get_optional_auth
from app.dependencies import (
    get_acl,
    get_storage,
    require_browse,
    require_write,
)
from app.schemas import RefIn, RefOut
from app.storage import (
    FilesystemStorage,
    RefNotFound,
)

router = APIRouter(tags=["refs"])


@router.get(
    "/api/namespaces/{namespace}/projects/{project}/refs",
    response_model=list[RefOut],
)
async def list_refs(
    namespace: str,
    project: str,
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> list[RefOut]:
    """List all refs for a project.

    Returns each ref name and the version it points to.
    Requires read access to the namespace.

    ---

    :param namespace: Namespace name.
    :param project: Project name.
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: Sorted list of ref objects.
    :raises 404: If the namespace or project does not exist.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    if not storage.project_exists(namespace, project):
        raise HTTPException(status_code=404, detail="Project not found")
    require_browse(namespace, storage, acl, auth)
    refs = storage.list_refs(namespace, project)
    return sorted(
        [RefOut(name=n, version=v) for n, v in refs.items()],
        key=lambda r: r.name,
    )


@router.put(
    "/api/namespaces/{namespace}/projects/{project}/refs/{ref}",
    response_model=RefOut,
)
async def set_ref(
    namespace: str,
    project: str,
    ref: str,
    body: RefIn,
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> RefOut:
    """Create or update a ref to point to a version.

    If the ref already exists it is overwritten atomically.
    Requires write access to the namespace.

    ---

    :param namespace: Namespace name.
    :param project: Project name.
    :param ref: Ref name to create or update.
    :param body: Request body containing the target version.
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: The updated ref.
    :raises 404: If the namespace, project, or version is not
        found.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    if not storage.project_exists(namespace, project):
        raise HTTPException(status_code=404, detail="Project not found")
    require_write(namespace, storage, acl, auth)
    versions = storage.list_versions(namespace, project)
    if body.version not in versions:
        raise HTTPException(status_code=404, detail="Version not found")
    storage.set_ref(namespace, project, ref, body.version)
    return RefOut(name=ref, version=body.version)


@router.delete(
    "/api/namespaces/{namespace}/projects/{project}/refs/{ref}",
    status_code=204,
)
async def delete_ref(
    namespace: str,
    project: str,
    ref: str,
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> None:
    """Delete a named ref.

    The target version is not affected; only the ref pointer is
    removed. Requires write access to the namespace.

    ---

    :param namespace: Namespace name.
    :param project: Project name.
    :param ref: Ref name to delete.
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :raises 404: If the namespace, project, or ref is not found.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    if not storage.project_exists(namespace, project):
        raise HTTPException(status_code=404, detail="Project not found")
    require_write(namespace, storage, acl, auth)
    try:
        storage.delete_ref(namespace, project, ref)
    except RefNotFound:
        raise HTTPException(status_code=404, detail="Ref not found")
