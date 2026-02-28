from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.acl import AclCache
from app.auth import AuthContext, get_optional_auth
from app.models import NamespaceOut
from app.storage import FilesystemStorage, NamespaceNotFound
from app.validators import validate_namespace

router = APIRouter(prefix="/api/namespaces", tags=["namespaces"])

_storage = FilesystemStorage()
_acl = AclCache()


@router.get("", response_model=list[NamespaceOut])
async def list_namespaces(
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
) -> list[NamespaceOut]:
    return [
        NamespaceOut(name=n) for n in _storage.list_namespaces()
    ]


@router.post("", status_code=201, response_model=NamespaceOut)
async def create_namespace(
    body: NamespaceOut,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
) -> NamespaceOut:
    validate_namespace(body.name)
    if auth is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )
    _storage.create_namespace(body.name)
    return NamespaceOut(name=body.name)


@router.delete("/{namespace}", status_code=204)
async def delete_namespace(
    namespace: str,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
) -> None:
    validate_namespace(namespace)
    if auth is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )
    try:
        _storage.delete_namespace(namespace)
    except NamespaceNotFound:
        raise HTTPException(
            status_code=404, detail="Namespace not found"
        )
