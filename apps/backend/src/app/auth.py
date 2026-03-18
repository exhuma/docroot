"""JWT authentication helpers.

Validates Bearer tokens from the Authorization header using JWKS.
Supports HTTP and file:// JWKS endpoints for local development.

Provides :func:`get_optional_auth` (FastAPI dependency) and
:func:`get_auth` (FastAPI dependency that requires authentication).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, Request
from jwt import PyJWK, PyJWKClient

from app.logging import get_logger
from app.settings import Settings, get_settings

_log = get_logger(__name__)


@dataclass
class AuthContext:
    """Authenticated principal attached to a request.

    :param subject: JWT ``sub`` claim (unique user identifier).
    :param roles: Roles extracted by the configured role extractor.
    :param raw_token: The original encoded JWT string.
    """

    subject: str
    roles: list[str] = field(default_factory=list)
    raw_token: str = ""


@lru_cache(maxsize=1)
def _get_jwks_client(
    jwks_url: str,
) -> PyJWKClient | _FileJWKSClient:
    """Return a cached JWKS client for the given URL.

    :param jwks_url: JWKS endpoint URL. ``file://`` prefix is
        supported for local development.
    :returns: A JWKS client with ``get_signing_key_from_jwt``
        method.
    """
    if jwks_url.startswith("file://"):
        return _FileJWKSClient(jwks_url[len("file://"):])
    return PyJWKClient(jwks_url, cache_keys=True)


class _FileJWKSClient:
    """JWKS client that reads keys from a local JSON file.

    :param path: Filesystem path to the JWKS JSON file.
    """

    def __init__(self, path: str) -> None:
        """Initialise and load keys from *path*.

        :param path: Path to the JWKS JSON file.
        """
        with open(path) as fh:
            data: dict[str, object] = json.load(fh)
        keys_raw = data.get("keys", [])
        if not isinstance(keys_raw, list):
            keys_raw = []
        self._keys: dict[str, PyJWK] = {}
        for key_data in keys_raw:
            if not isinstance(key_data, dict):
                continue
            pyjwk = PyJWK(key_data)
            kid = key_data.get("kid")
            self._keys[
                str(kid) if kid else ""
            ] = pyjwk

    def get_signing_key_from_jwt(
        self, token: str
    ) -> PyJWK:
        """Return the signing key matching the JWT's ``kid``.

        :param token: Encoded JWT string.
        :returns: Matching :class:`jwt.PyJWK` instance.
        :raises HTTPException: 401 if no matching key is found.
        """
        header = jwt.get_unverified_header(token)
        kid = header.get("kid", "")
        if kid and kid in self._keys:
            return self._keys[kid]
        if not kid and self._keys:
            return next(iter(self._keys.values()))
        raise HTTPException(
            status_code=401,
            detail="Signing key not found",
        )


def _get_extractor(settings: Settings):
    """Return the configured role extractor callable.

    :param settings: Application settings.
    :returns: Role extractor function.
    :raises ValueError: If the configured extractor is unknown.
    """
    name = settings.oauth_role_extractor
    if name == "keycloak":
        from app.extractors.keycloak import extract_roles
        return extract_roles
    raise ValueError(f"Unknown role extractor: {name}")


def validate_token(
    token: str,
    settings: Settings,
) -> AuthContext:
    """Validate a JWT and return an :class:`AuthContext`.

    Verifies signature, expiration, and (if configured) audience.
    Extracts roles using the configured role extractor.

    :param token: Encoded JWT string.
    :param settings: Application settings.
    :returns: Validated :class:`AuthContext`.
    :raises HTTPException: 401 on any validation failure.
    """
    client = _get_jwks_client(settings.oauth_jwks_url)
    try:
        signing_key = client.get_signing_key_from_jwt(token)
    except jwt.exceptions.PyJWKClientError as exc:
        _log.error(
            "Signing key not found (JWKS: %s): %s",
            settings.oauth_jwks_url,
            exc,
        )
        raise HTTPException(
            status_code=401,
            detail="Signing key not found",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        _log.error(
            "Token key resolution failed (JWKS: %s): %s",
            settings.oauth_jwks_url,
            exc,
        )
        raise HTTPException(
            status_code=401,
            detail="Token key resolution failed",
        ) from exc

    header = jwt.get_unverified_header(token)
    alg = header.get("alg", "RS256")

    decode_options: dict[str, object] = {}
    audience: str | None = settings.oauth_audience or None
    if not audience:
        decode_options["verify_aud"] = False

    try:
        payload: dict[str, object] = jwt.decode(
            token,
            signing_key.key,
            algorithms=[alg],
            audience=audience,
            options=decode_options,
        )
    except jwt.ExpiredSignatureError as exc:
        _log.warning("Token rejected: expired")
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        _log.warning("Token rejected: %s", exc)
        raise HTTPException(
            status_code=401,
            detail="Token validation failed",
        ) from exc

    subject = str(payload.get("sub", ""))
    issuer = str(payload.get("iss", ""))
    extractor = _get_extractor(settings)
    roles = extractor(
        payload,
        {"issuer": issuer, "audience": settings.oauth_audience},
    )
    _log.debug(
        "Token validated: sub=%s roles=%s", subject, roles
    )
    return AuthContext(
        subject=subject,
        roles=roles,
        raw_token=token,
    )


async def get_optional_auth(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> AuthContext | None:
    """FastAPI dependency: optionally authenticate the request.

    Checks the ``Authorization`` header first.  When absent, falls
    back to the ``docroot_token`` cookie so that iframe navigation
    (which cannot attach custom headers) is also authenticated.
    Raises 401 if a token is present but invalid.

    :param request: Incoming HTTP request.
    :param settings: Application settings (injected).
    :returns: :class:`AuthContext` or ``None``.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            _log.warning(
                "Malformed Authorization header from %s",
                request.client.host if request.client else "unknown",
            )
            raise HTTPException(
                status_code=401,
                detail="Invalid Authorization header format",
            )
        return validate_token(parts[1], settings)

    session_token = request.cookies.get("session")
    if session_token:
        _log.debug(
            "Using session cookie for auth_request from %s",
            request.client.host if request.client else "unknown",
        )
        return validate_token(session_token, settings)

    return None


async def get_auth(
    auth: AuthContext | None = Depends(get_optional_auth),
) -> AuthContext:
    """FastAPI dependency: require authentication.

    Raises 401 if no valid ``Authorization`` header is present.

    :param auth: Optional auth context from
        :func:`get_optional_auth`.
    :returns: Validated :class:`AuthContext`.
    :raises HTTPException: 401 if not authenticated.
    """
    if auth is None:
        _log.warning("Request rejected: authentication required")
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )
    return auth
