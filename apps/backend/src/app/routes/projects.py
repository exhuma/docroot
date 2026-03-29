"""Project management routes.

Provides CRUD operations for projects within a namespace.
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
from app.schemas import ProjectIn, ProjectOut
from app.slugify import slugify
from app.storage import (
    FilesystemStorage,
    NamespaceNotFound,
    ProjectNotFound,
)

router = APIRouter(tags=["projects"])


@router.get(
    "/api/namespaces/{namespace}/projects",
    response_model=list[ProjectOut],
)
async def list_projects(
    namespace: str,
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> list[ProjectOut]:
    """List all projects within a namespace.

    Requires read access to the namespace.

    ---

    :param namespace: Namespace name (path parameter).
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: List of project objects.
    :raises 404: If the namespace does not exist.
    :raises 401: If unauthenticated and namespace is private.
    :raises 403: If the caller lacks read access.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    require_browse(namespace, storage, acl, auth)
    try:
        names = storage.list_projects(namespace)
    except NamespaceNotFound:
        raise HTTPException(status_code=404, detail="Namespace not found")
    result: list[ProjectOut] = []
    for n in names:
        meta = storage.get_project_meta(namespace, n)
        display_name = str(meta.get("display_name", ""))
        result.append(ProjectOut(name=n, display_name=display_name))
    return result


@router.post(
    "/api/namespaces/{namespace}/projects",
    status_code=201,
    response_model=ProjectOut,
)
async def create_project(
    namespace: str,
    body: ProjectIn,
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> ProjectOut:
    """Create a new project within a namespace.

    Requires write access to the namespace.

    ---

    :param namespace: Namespace name (path parameter).
    :param body: Project creation request.
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: Created project object.
    :raises 404: If the namespace does not exist.
    :raises 401: If not authenticated.
    :raises 403: If the caller lacks write access.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    require_write(namespace, storage, acl, auth)
    slug = slugify(body.name)
    if not slug:
        raise HTTPException(
            status_code=400,
            detail=(
                "Name must contain at least one alphanumeric character "
                "so that a valid slug can be derived."
            ),
        )
    try:
        storage.create_project(namespace, slug, display_name=body.name)
    except NamespaceNotFound:
        raise HTTPException(status_code=404, detail="Namespace not found")
    return ProjectOut(name=slug, display_name=body.name)


@router.delete(
    "/api/namespaces/{namespace}/projects/{project}",
    status_code=204,
)
async def delete_project(
    namespace: str,
    project: str,
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> None:
    """Delete a project and all its versions.

    Requires write access to the namespace.

    ---

    :param namespace: Namespace name (path parameter).
    :param project: Project name (path parameter).
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :raises 404: If the namespace or project does not exist.
    :raises 401: If not authenticated.
    :raises 403: If the caller lacks write access.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    require_write(namespace, storage, acl, auth)
    try:
        storage.delete_project(namespace, project)
    except ProjectNotFound:
        raise HTTPException(status_code=404, detail="Project not found")
