"""Namespace management routes.

Provides CRUD operations for namespaces, ACL management, and
namespace listing. Only the namespace creator may delete a namespace.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.acl import AclCache
from app.auth import AuthContext, get_auth, get_optional_auth
from app.dependencies import (
    get_acl,
    get_storage,
    require_write,
)
from app.schemas import (
    AclFlagsIn,
    AclOut,
    AclRoleIn,
    AclRoleOut,
    NamespaceIn,
    NamespaceOut,
)
from app.storage import FilesystemStorage, NamespaceNotFound

router = APIRouter(prefix="/api/namespaces", tags=["namespaces"])


@router.get("", response_model=list[NamespaceOut])
async def list_namespaces(
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> list[NamespaceOut]:
    """List all namespaces visible to the caller.

    Returns only namespaces that are either publicly readable or
    readable by the caller's roles.  Unauthenticated callers
    receive only publicly readable namespaces.

    ---

    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: List of namespace objects.
    """
    roles = auth.roles if auth else []
    subject = auth.subject if auth else ""
    result: list[NamespaceOut] = []
    for name in storage.list_namespaces():
        ns_dir = storage.namespace_dir(name)
        acl_data = acl.get(ns_dir)
        if acl.can_browse(acl_data, roles, subject):
            meta = storage.get_namespace_meta(name)
            access = meta.get("access", {})
            public_read = (
                bool(access.get("public_read", False))
                if isinstance(access, dict)
                else False
            )
            browsable = (
                bool(access.get("browsable", True))
                if isinstance(access, dict)
                else True
            )
            versioning = str(meta.get("versioning", ""))
            creator = str(meta.get("creator", ""))
            result.append(
                NamespaceOut(
                    name=name,
                    public_read=public_read,
                    browsable=browsable,
                    versioning=versioning,
                    creator=creator,
                )
            )
    return result


@router.post("", status_code=201, response_model=NamespaceOut)
async def create_namespace(
    body: NamespaceIn,
    auth: AuthContext = Depends(get_auth),
    storage: FilesystemStorage = Depends(get_storage),
) -> NamespaceOut:
    """Create a new namespace.

    The authenticated caller becomes the namespace creator and is
    automatically granted write (and read) access regardless of
    the supplied ``roles`` list.

    ---

    :param body: Namespace creation request.
    :param auth: Authenticated principal (required, injected).
    :param storage: Storage instance (injected).
    :returns: Created namespace object.
    """
    roles = [{"role": r.role, "read": r.read, "write": r.write} for r in body.roles]
    storage.create_namespace(
        body.name,
        creator=auth.subject,
        public_read=body.public_read,
        roles=roles,
        versioning=body.versioning,
        browsable=body.browsable,
    )
    return NamespaceOut(
        name=body.name,
        public_read=body.public_read,
        browsable=body.browsable,
        versioning=body.versioning,
        creator=auth.subject,
    )


@router.delete("/{namespace}", status_code=204)
async def delete_namespace(
    namespace: str,
    auth: AuthContext = Depends(get_auth),
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> None:
    """Delete a namespace and all its contents.

    Only the namespace creator may delete a namespace.

    ---

    :param namespace: Namespace name (path parameter).
    :param auth: Authenticated principal (required, injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :raises 404: If the namespace does not exist.
    :raises 403: If the caller is not the namespace creator.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    ns_dir = storage.namespace_dir(namespace)
    creator = acl.get_creator(ns_dir)
    if creator and auth.subject != creator:
        raise HTTPException(
            status_code=403,
            detail="Only the namespace creator may delete it",
        )
    try:
        storage.delete_namespace(namespace)
    except NamespaceNotFound:
        raise HTTPException(status_code=404, detail="Namespace not found")


@router.put("/{namespace}/acl/roles/{role}", status_code=204)
async def upsert_namespace_role(
    namespace: str,
    role: str,
    body: AclRoleIn,
    auth: AuthContext = Depends(get_auth),
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> None:
    """Add or update a role in the namespace ACL.

    Requires write access to the namespace.

    ---

    :param namespace: Namespace name (path parameter).
    :param role: Role name to add or update (path parameter).
    :param body: Read and write permission flags.
    :param auth: Authenticated principal (required, injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :raises 404: If the namespace does not exist.
    :raises 403: If the caller lacks write access.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    require_write(namespace, storage, acl, auth)
    try:
        storage.update_namespace_acl(namespace, role, body.read, body.write)
    except NamespaceNotFound:
        raise HTTPException(status_code=404, detail="Namespace not found")


@router.delete("/{namespace}/acl/roles/{role}", status_code=204)
async def remove_namespace_role(
    namespace: str,
    role: str,
    auth: AuthContext = Depends(get_auth),
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> None:
    """Remove a role from the namespace ACL.

    Requires write access to the namespace.

    ---

    :param namespace: Namespace name (path parameter).
    :param role: Role name to remove (path parameter).
    :param auth: Authenticated principal (required, injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :raises 404: If the namespace does not exist.
    :raises 403: If the caller lacks write access.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    require_write(namespace, storage, acl, auth)
    try:
        storage.remove_namespace_role(namespace, role)
    except NamespaceNotFound:
        raise HTTPException(status_code=404, detail="Namespace not found")


@router.get("/{namespace}/acl", response_model=AclOut)
async def get_namespace_acl(
    namespace: str,
    auth: AuthContext = Depends(get_auth),
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> AclOut:
    """Return the ACL for a namespace.

    Requires write access to the namespace.  Only principals
    that can already modify the ACL may read it, preventing
    role enumeration by read-only users.

    ---

    :param namespace: Namespace name (path parameter).
    :param auth: Authenticated principal (required, injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: Current ACL data including all role entries.
    :raises 404: If the namespace does not exist.
    :raises 401: If the caller is not authenticated.
    :raises 403: If the caller lacks write access.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    require_write(namespace, storage, acl, auth)
    meta = storage.get_namespace_meta(namespace)
    access = meta.get("access", {})
    if not isinstance(access, dict):
        access = {}
    public_read = bool(access.get("public_read", False))
    browsable = bool(access.get("browsable", True))
    roles = [
        AclRoleOut(
            role=str(e.get("role", "")),
            read=bool(e.get("read", False)),
            write=bool(e.get("write", False)),
        )
        for e in access.get("roles", [])
        if isinstance(e, dict)
    ]
    return AclOut(
        public_read=public_read,
        browsable=browsable,
        roles=roles,
    )


@router.patch("/{namespace}/acl", status_code=204)
async def update_namespace_acl_flags(
    namespace: str,
    body: AclFlagsIn,
    auth: AuthContext = Depends(get_auth),
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> None:
    """Update the public_read and browsable flags for a namespace.

    Requires write access to the namespace.

    ---

    :param namespace: Namespace name (path parameter).
    :param body: New flag values.
    :param auth: Authenticated principal (required, injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :raises 404: If the namespace does not exist.
    :raises 403: If the caller lacks write access.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    require_write(namespace, storage, acl, auth)
    try:
        storage.update_namespace_flags(namespace, body.public_read, body.browsable)
    except NamespaceNotFound:
        raise HTTPException(status_code=404, detail="Namespace not found")


@router.patch("/{namespace}/owner", status_code=204)
async def transfer_namespace_owner(
    namespace: str,
    auth: AuthContext = Depends(get_auth),
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> None:
    """Transfer namespace ownership to the authenticated caller.

    Any principal with write access to the namespace (including the
    current creator) may take ownership.  After this call, the caller
    becomes the new creator and inherits all creator privileges.

    ---

    :param namespace: Namespace name (path parameter).
    :param auth: Authenticated principal (required, injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :raises 404: If the namespace does not exist.
    :raises 403: If the caller lacks write access.
    """
    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")
    require_write(namespace, storage, acl, auth)
    try:
        storage.transfer_ownership(namespace, auth.subject)
    except NamespaceNotFound:
        raise HTTPException(status_code=404, detail="Namespace not found")
