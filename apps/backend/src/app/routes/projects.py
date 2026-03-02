from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.acl import AclCache
from app.auth import AuthContext, get_optional_auth
from app.models import ProjectOut
from app.storage import (
    FilesystemStorage,
    NamespaceNotFound,
    ProjectNotFound,
)
from app.validators import validate_namespace, validate_project

router = APIRouter(tags=["projects"])

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
    "/api/namespaces/{namespace}/projects",
    response_model=list[ProjectOut],
)
async def list_projects(
    namespace: str,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
) -> list[ProjectOut]:
    validate_namespace(namespace)
    if not _storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    _require_read(namespace, auth)
    try:
        names = _storage.list_projects(namespace)
    except NamespaceNotFound:
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    return [ProjectOut(name=n) for n in names]


@router.post(
    "/api/namespaces/{namespace}/projects",
    status_code=201,
    response_model=ProjectOut,
)
async def create_project(
    namespace: str,
    body: ProjectOut,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
) -> ProjectOut:
    validate_namespace(namespace)
    validate_project(body.name)
    if not _storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    _require_write(namespace, auth)
    try:
        _storage.create_project(namespace, body.name)
    except NamespaceNotFound:
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    return ProjectOut(name=body.name)


@router.delete(
    "/api/namespaces/{namespace}/projects/{project}",
    status_code=204,
)
async def delete_project(
    namespace: str,
    project: str,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
) -> None:
    validate_namespace(namespace)
    validate_project(project)
    if not _storage.namespace_exists(namespace):
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
    _require_write(namespace, auth)
    try:
        _storage.delete_project(namespace, project)
    except ProjectNotFound:
        raise HTTPException(
            status_code=404, detail="Project not found"
        )
