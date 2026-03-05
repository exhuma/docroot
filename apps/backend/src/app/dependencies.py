"""Shared FastAPI dependency callables.

Centralises storage, ACL, and authorisation dependencies so that
route modules stay thin and avoid repeating the same logic.
"""
from functools import lru_cache

from fastapi import HTTPException

from app.acl import AclCache
from app.auth import AuthContext
from app.settings import get_settings
from app.storage import FilesystemStorage


@lru_cache(maxsize=1)
def get_storage(
    data_root: str = "",
) -> FilesystemStorage:
    """Return the singleton :class:`FilesystemStorage` instance.

    :param data_root: Override the data root path. When empty the
        value is taken from application settings.
    :returns: Shared storage instance.
    """
    if data_root:
        return FilesystemStorage(data_root=data_root)
    settings = get_settings()
    return FilesystemStorage(data_root=settings.data_root)


@lru_cache(maxsize=1)
def get_acl() -> AclCache:
    """Return the singleton :class:`AclCache` instance.

    :returns: Shared ACL cache instance.
    """
    return AclCache()


def require_read(
    namespace: str,
    storage: FilesystemStorage,
    acl: AclCache,
    auth: AuthContext | None,
) -> None:
    """Assert that the caller has read access to *namespace*.

    :param namespace: Namespace name.
    :param storage: Storage instance.
    :param acl: ACL cache instance.
    :param auth: Optional authenticated principal.
    :raises HTTPException: 401 if unauthenticated and access
        denied; 403 if authenticated but access denied.
    """
    ns_dir = storage.namespace_dir(namespace)
    acl_data = acl.get(ns_dir)
    roles = auth.roles if auth else []
    if not acl.can_read(acl_data, roles):
        if auth is None:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
            )
        raise HTTPException(
            status_code=403,
            detail="Read permission denied",
        )


def require_write(
    namespace: str,
    storage: FilesystemStorage,
    acl: AclCache,
    auth: AuthContext | None,
) -> None:
    """Assert that the caller has write access to *namespace*.

    :param namespace: Namespace name.
    :param storage: Storage instance.
    :param acl: ACL cache instance.
    :param auth: Optional authenticated principal.
    :raises HTTPException: 401 if unauthenticated;
        403 if authenticated but access denied.
    """
    if auth is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )
    ns_dir = storage.namespace_dir(namespace)
    acl_data = acl.get(ns_dir)
    if not acl.can_write(acl_data, auth.roles):
        raise HTTPException(
            status_code=403,
            detail="Write permission denied",
        )
