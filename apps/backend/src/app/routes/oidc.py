"""OIDC configuration endpoint.

Exposes the OIDC issuer URL and public client ID to the frontend
so that the browser can perform the authorization-code + PKCE flow
without hard-coding those values into the static bundle.

GET /api/oidc-config
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.settings import Settings, get_settings

router = APIRouter(tags=["oidc"])


@router.get("/api/oidc-config")
async def get_oidc_config(
    settings: Settings = Depends(get_settings),
) -> dict[str, str | None]:
    """Return the OIDC public client configuration for the UI.

    The frontend uses these values to initialise ``oidc-client-ts``
    and redirect the user to the identity provider.  When
    ``oidc_issuer`` is empty, ``issuer`` is ``null`` and the UI
    should fall back to manual token entry.

    :param settings: Application settings (injected).
    :returns: ``{"issuer": str | null, "client_id": str | null}``
    """
    issuer: str | None = settings.oidc_issuer or None
    client_id: str | None = settings.oidc_client_id or None
    return {"issuer": issuer, "client_id": client_id}
