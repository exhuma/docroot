"""Internal nginx auth_request endpoint.

Provides ``GET /_internal/auth`` which nginx calls via
``auth_request`` before serving static documentation files.
The endpoint is marked ``internal`` in nginx so it is
unreachable by external clients; only nginx sub-requests can
trigger it.

The original request URI is passed in the ``X-Original-URI``
header.  The handler parses the namespace from the first path
segment, reads the namespace ACL, and returns:

* 200 — access granted.
* 401 — authentication required (public_read is false and no
  valid token was presented).
* 403 — authenticated but the caller's roles do not grant
  read access.
* 404 — namespace does not exist.
"""
import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app.acl import AclCache
from app.auth import AuthContext, get_optional_auth
from app.dependencies import get_acl, get_storage
from app.logging import get_logger
from app.storage import FilesystemStorage

_log = get_logger(__name__)

router = APIRouter(tags=["internal"])

# Matches the first path segment: /{namespace}/...
_NAMESPACE_RE = re.compile(r"^/([^/?#]+)")


@router.get("/_internal/auth", include_in_schema=False)
async def nginx_auth_check(
    request: Request,
    auth: Annotated[
        AuthContext | None, Depends(get_optional_auth)
    ] = None,
    storage: FilesystemStorage = Depends(get_storage),
    acl: AclCache = Depends(get_acl),
) -> Response:
    """Check whether the caller may read a static documentation file.

    nginx calls this endpoint via ``auth_request`` before serving
    any file from the ``/{namespace}/{project}/{version}/{locale}/``
    tree.  The original URI is taken from the ``X-Original-URI``
    request header set by nginx.

    Returns an empty 200 response when access is granted.  All
    other outcomes raise an HTTP exception whose status code nginx
    forwards to the original client.

    ---

    :param request: Incoming HTTP request (headers forwarded by
        nginx).
    :param auth: Optional authenticated principal (injected).
    :param storage: Storage instance (injected).
    :param acl: ACL cache instance (injected).
    :returns: Empty :class:`fastapi.responses.Response` with
        status 200.
    :raises HTTPException: 400 if the URI cannot be parsed, 404
        if the namespace does not exist, 401 if authentication is
        required but absent, 403 if the caller lacks read
        permission.
    """
    original_uri = request.headers.get("X-Original-URI", "")
    match = _NAMESPACE_RE.match(original_uri)
    if not match:
        _log.warning(
            "/_internal/auth: cannot parse namespace "
            "from URI %r",
            original_uri,
        )
        raise HTTPException(
            status_code=400,
            detail="Cannot parse namespace from URI",
        )

    namespace = match.group(1)

    if not storage.namespace_exists(namespace):
        _log.warning(
            "/_internal/auth: namespace %r not found",
            namespace,
        )
        raise HTTPException(
            status_code=404,
            detail="Namespace not found",
        )

    ns_dir = storage.namespace_dir(namespace)
    acl_data = acl.get(ns_dir)
    roles = auth.roles if auth else []
    subject = auth.subject if auth else ""

    if acl.can_read(acl_data, roles, subject):
        return Response(status_code=200)

    if auth is None:
        _log.warning(
            "/_internal/auth: read denied on '%s' "
            "(unauthenticated)",
            namespace,
        )
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    _log.warning(
        "/_internal/auth: read denied on '%s' "
        "(sub=%s roles=%s)",
        namespace,
        auth.subject,
        auth.roles,
    )
    raise HTTPException(
        status_code=403,
        detail="Read permission denied",
    )
