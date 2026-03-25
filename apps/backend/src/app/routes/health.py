"""Health check route.

Provides a lightweight liveness endpoint for container
orchestrators and Docker Compose healthcheck stanzas.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Return service health status.

    Always returns HTTP 200 with ``{"status": "ok"}`` when
    the process is running.  Requires no authentication.
    """
    return {"status": "ok"}
