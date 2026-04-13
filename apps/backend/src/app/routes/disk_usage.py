"""Disk usage route.

Provides a single endpoint that returns disk usage per namespace
grouped by mount point.  Mount points are identified by an
ephemeral hash to avoid exposing system-level device details.
"""

from fastapi import APIRouter, Depends

from app.auth import AuthContext, get_auth
from app.dependencies import get_storage
from app.schemas.disk_usage import DiskUsageGroupOut, NamespaceUsageOut
from app.settings import get_settings
from app.storage import FilesystemStorage

router = APIRouter(prefix="/api/disk-usage", tags=["disk-usage"])


@router.get("", response_model=list[DiskUsageGroupOut])
async def get_disk_usage(
    auth: AuthContext = Depends(get_auth),
    storage: FilesystemStorage = Depends(get_storage),
) -> list[DiskUsageGroupOut]:
    """Return disk usage per namespace grouped by mount point.

    Each group represents one or more namespaces that share a
    common storage device.  The mount point is identified by an
    ephemeral opaque hash that changes between requests so that
    no system-level details are exposed.  Use the hash only for
    grouping within a single response.

    A group is flagged ``low_space`` when the free space on its
    device falls below the threshold configured by the
    ``DOCROOT_API_DISK_USAGE_LOW_SPACE_THRESHOLD_GB`` environment
    variable (default: 1 GB).

    Requires authentication.

    ---

    :param auth: Authenticated principal (required, injected).
    :param storage: Storage instance (injected).
    :returns: List of mount groups with namespace usage entries.
    """
    settings = get_settings()
    threshold_bytes = int(settings.disk_usage_low_space_threshold_gb * 1024**3)
    groups = storage.disk_usage()
    return [
        DiskUsageGroupOut(
            mount_group=g.mount_group,
            free_bytes=g.free_bytes,
            total_bytes=g.total_bytes,
            used_bytes=g.used_bytes,
            low_space=g.free_bytes < threshold_bytes,
            namespaces=[
                NamespaceUsageOut(
                    name=ns.name,
                    display_name=ns.display_name,
                    size_bytes=ns.size_bytes,
                )
                for ns in g.namespaces
            ],
        )
        for g in groups
    ]
