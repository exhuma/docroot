"""Health probe routes for /livez, /readyz, and /healthz.

Provides lightweight probes for container orchestrators and
monitoring systems.  /livez checks process liveness only;
/readyz checks required dependencies; /healthz summarises all
dependencies including optional ones.
"""

import os
import time
from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.settings import Settings, get_settings

router = APIRouter(tags=["health"])


class _Status(str, Enum):
    """Allowed status values for probes and components."""

    ok = "ok"
    degraded = "degraded"
    fail = "fail"
    unknown = "unknown"


class _Component(BaseModel):
    """Health status of a single tracked component."""

    name: str
    kind: str
    required: bool
    status: _Status
    reason_code: str
    latency_ms: int | None = None


class _Probe(BaseModel):
    """Health probe response payload."""

    probe: str
    status: _Status
    checked_at: str
    components: list[_Component]


def _now() -> str:
    """Return the current UTC time as an RFC 3339 string.

    :returns: Timestamp string, e.g. ``2026-01-01T12:00:00Z``.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_storage(data_root: str) -> _Component:
    """Probe the storage filesystem for accessibility.

    :param data_root: Path to the data directory.
    :returns: Component health record for the storage layer.
    """
    t0 = time.monotonic()
    try:
        accessible = os.path.isdir(data_root) and os.access(data_root, os.R_OK)
        latency_ms = round((time.monotonic() - t0) * 1000)
        if accessible:
            return _Component(
                name="storage",
                kind="storage",
                required=True,
                status=_Status.ok,
                reason_code="storage_ok",
                latency_ms=latency_ms,
            )
        return _Component(
            name="storage",
            kind="storage",
            required=True,
            status=_Status.fail,
            reason_code="storage_unavailable",
            latency_ms=latency_ms,
        )
    except OSError:
        latency_ms = round((time.monotonic() - t0) * 1000)
        return _Component(
            name="storage",
            kind="storage",
            required=True,
            status=_Status.fail,
            reason_code="storage_error",
            latency_ms=latency_ms,
        )


def _aggregate(components: list[_Component]) -> _Status:
    """Compute aggregate probe status from component statuses.

    :param components: List of component health records.
    :returns: Aggregated status per kit aggregation rules.
    """
    failing = {_Status.fail, _Status.unknown}
    required = [c for c in components if c.required]
    optional = [c for c in components if not c.required]
    if any(c.status in failing for c in required):
        return _Status.fail
    if any(c.status in failing for c in optional):
        return _Status.degraded
    return _Status.ok


def _make_response(body: _Probe) -> JSONResponse:
    """Build a JSONResponse with the correct HTTP status code.

    :param body: Probe result to serialise.
    :returns: JSONResponse with 503 for fail, 200 otherwise.
    """
    http_status = 503 if body.status == _Status.fail else 200
    return JSONResponse(
        content=body.model_dump(),
        status_code=http_status,
    )


@router.get("/livez")
async def livez() -> JSONResponse:
    """Return process liveness status.

    Always returns **200 ok** while the process can handle
    requests.  Performs no external dependency checks.

    ---
    Intended for liveness probes only.  Do not use this endpoint
    to gate traffic.
    """
    return _make_response(
        _Probe(
            probe="livez",
            status=_Status.ok,
            checked_at=_now(),
            components=[],
        )
    )


@router.get("/readyz")
async def readyz(
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Return service readiness status.

    Checks all **required** dependencies (currently: storage
    filesystem).  Returns **503** when any required dependency
    is unavailable.

    ---
    Intended for readiness probes.  Use this endpoint to gate
    incoming traffic until all dependencies are ready.
    """
    components = [_check_storage(settings.data_root)]
    return _make_response(
        _Probe(
            probe="readyz",
            status=_aggregate(components),
            checked_at=_now(),
            components=components,
        )
    )


@router.get("/healthz")
async def healthz(
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Return full operational health summary.

    Includes all required and optional dependencies.  Returns
    **200** with status `degraded` when only optional dependencies
    are failing, and **503** when any required dependency fails.

    ---
    Intended for monitoring dashboards and alert context.
    Not suitable as a traffic-gating probe.
    """
    components = [_check_storage(settings.data_root)]
    return _make_response(
        _Probe(
            probe="healthz",
            status=_aggregate(components),
            checked_at=_now(),
            components=components,
        )
    )
