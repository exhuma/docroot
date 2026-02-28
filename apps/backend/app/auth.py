import os
from dataclasses import dataclass, field

import httpx
from fastapi import HTTPException, Request
from jose import JWTError, jwt

JWKS_URL: str = os.environ.get("OAUTH_JWKS_URL", "")
AUDIENCE: str = os.environ.get("OAUTH_AUDIENCE", "")
ROLE_EXTRACTOR: str = os.environ.get(
    "OAUTH_ROLE_EXTRACTOR", "keycloak"
)

_jwks_cache: dict | None = None


@dataclass
class AuthContext:
    subject: str
    roles: list[str] = field(default_factory=list)
    raw_token: str = ""


def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    response = httpx.get(JWKS_URL, timeout=10)
    response.raise_for_status()
    _jwks_cache = response.json()
    return _jwks_cache


def _get_extractor():
    if ROLE_EXTRACTOR == "keycloak":
        from app.keycloak_extractor import extract_roles

        return extract_roles
    raise ValueError(
        f"Unknown role extractor: {ROLE_EXTRACTOR}"
    )


def validate_token(token: str) -> AuthContext:
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=401, detail="Invalid token header"
        ) from exc

    kid = header.get("kid")
    alg = header.get("alg", "RS256")
    jwks = _get_jwks()

    signing_key = None
    for key in jwks.get("keys", []):
        if kid is None or key.get("kid") == kid:
            signing_key = key
            break

    if signing_key is None:
        raise HTTPException(
            status_code=401, detail="Signing key not found"
        )

    decode_options: dict = {}
    if not AUDIENCE:
        decode_options["verify_aud"] = False

    try:
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[alg],
            audience=AUDIENCE if AUDIENCE else None,
            options=decode_options,
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=401, detail="Token validation failed"
        ) from exc

    subject: str = payload.get("sub", "")
    issuer: str = payload.get("iss", "")
    extractor = _get_extractor()
    roles = extractor(
        token, {"issuer": issuer, "audience": AUDIENCE}
    )
    return AuthContext(
        subject=subject,
        roles=roles,
        raw_token=token,
    )


async def get_optional_auth(
    request: Request,
) -> AuthContext | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format",
        )
    return validate_token(parts[1])
