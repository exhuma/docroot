"""Browser session cookie endpoints.

Allows a browser holding an OIDC bearer token to exchange it for
a short-lived ``HttpOnly`` ``session`` cookie.  fastAPI validates
the token identically to the ``Authorization: Bearer`` path; no
server-side session state is created — the JWT itself travels in
the cookie.

POST /api/auth/session  — set cookie
DELETE /api/auth/session — clear cookie
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.auth import validate_token
from app.logging import get_logger
from app.settings import Settings, get_settings

_log = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

_SESSION_COOKIE = "session"
# Browsers reject SameSite=Strict cookies sent in the first
# cross-site navigation; Lax allows top-level navigations while
# still blocking CSRF on state-changing requests.
_COOKIE_ATTRS = "HttpOnly; SameSite=Lax; Path=/; Max-Age=86400"


@router.post("/session", status_code=200)
async def create_session(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Exchange a bearer token for an HttpOnly session cookie.

    Accepts the JWT in the ``Authorization: Bearer`` header.
    Validates the token using the standard path, then sets a
    ``session`` cookie that the browser will attach to all
    subsequent requests on the same origin — including iframe
    sub-resource requests that cannot carry custom headers.

    No server-side state is created; the cookie payload is the
    raw JWT.

    :param request: Incoming HTTP request.
    :param settings: Application settings (injected).
    :returns: JSON ``{"ok": true}`` with ``Set-Cookie`` header.
    :raises HTTPException: 401 if no valid bearer token is
        present.
    """
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        _log.warning(
            "Session exchange rejected: missing/malformed Authorization header"
        )
        raise HTTPException(
            status_code=401,
            detail="Bearer token required",
        )

    if not settings.oauth_jwks_url:
        raise HTTPException(
            status_code=501,
            detail="Authentication is not configured",
        )

    token = parts[1]
    ctx = validate_token(token, settings)
    _log.debug("Session cookie issued for sub=%s", ctx.subject)

    attrs = _COOKIE_ATTRS
    if settings.cookie_secure:
        attrs += "; Secure"

    response = JSONResponse({"ok": True})
    response.headers["Set-Cookie"] = f"{_SESSION_COOKIE}={token}; {attrs}"
    return response


@router.delete("/session", status_code=200)
async def delete_session(
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Clear the browser session cookie.

    Responds with a ``Set-Cookie`` header that instructs the
    browser to delete the ``session`` cookie immediately.

    :param settings: Application settings (injected).
    :returns: JSON ``{"ok": true}`` with cookie-clearing
        ``Set-Cookie`` header.
    """
    attrs = "HttpOnly; SameSite=Lax; Path=/; Max-Age=0"
    if settings.cookie_secure:
        attrs += "; Secure"

    response = JSONResponse({"ok": True})
    response.headers["Set-Cookie"] = f"{_SESSION_COOKIE}=; {attrs}"
    return response
