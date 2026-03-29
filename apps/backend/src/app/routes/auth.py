"""Internal authorization check endpoint for nginx auth_request.

Nginx delegates authorization for static documentation requests to
this endpoint via the ``auth_request`` directive.  The response
status code instructs nginx whether to serve the file (2xx) or
deny access (401 / 403).

The endpoint reads the original request URI from the
``X-Original-URI`` header, extracts the namespace, and validates
the caller's read permission against the namespace ACL.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import Response

from app.acl import AclCache
from app.auth import AuthContext, get_optional_auth
from app.dependencies import get_acl, get_storage, require_read
from app.storage import FilesystemStorage

router = APIRouter(tags=["auth"])


def _extract_namespace(original_uri: str) -> str:
    """Extract the namespace segment from a static-doc URI.

    The static documentation route has the form::

        /{namespace}/{project}/{version}/{locale}/...

    :param original_uri: Value of the ``X-Original-URI`` header.
    :returns: Namespace string, or empty string when the URI
        cannot be parsed.
    """
    stripped = original_uri.lstrip("/")
    if not stripped:
        return ""
    return stripped.split("/")[0]


@router.get("/api/auth")
async def auth_check(
    x_original_uri: Annotated[str | None, Header(alias="X-Original-URI")] = None,
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)] = None,
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> Response:
    """Authorization gate for nginx ``auth_request``.

    nginx calls this endpoint before serving every static
    documentation file.  The response status code controls access:

    * **200** — caller is authorized; nginx serves the file.
    * **401** — no valid credentials; nginx returns 401.
    * **403** — credentials present but access denied; nginx
      returns 403.

    The ``X-Original-URI`` header must contain the original
    request path so that the correct namespace ACL can be
    evaluated.

    ---

    :param x_original_uri: Original request URI forwarded by
        nginx (injected from header).
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: Empty 200 response when access is granted.
    :raises HTTPException: 400 if the URI header is absent or
        cannot be parsed; 401 / 403 if access is denied.
    """
    if not x_original_uri:
        raise HTTPException(
            status_code=400,
            detail="X-Original-URI header is required",
        )

    namespace = _extract_namespace(x_original_uri)
    if not namespace:
        raise HTTPException(
            status_code=400,
            detail="Cannot determine namespace from URI",
        )

    if not storage.namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Namespace not found")

    require_read(namespace, storage, acl, auth)
    return Response(status_code=200)
