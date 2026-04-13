"""Disk usage response schemas."""

from pydantic import BaseModel, Field


class NamespaceUsageOut(BaseModel):
    """Disk usage for a single namespace.

    :param name: Namespace slug.
    :param display_name: Human-readable display name.
    :param size_bytes: Total byte size of the namespace directory.
    """

    name: str
    display_name: str = ""
    size_bytes: int = 0


class DiskUsageGroupOut(BaseModel):
    """Disk usage for a group of namespaces on a shared mount point.

    :param mount_group: Ephemeral opaque identifier for the mount
        point.  Changes between requests to avoid exposing
        system-level details.  Use only for grouping within a
        single response.
    :param free_bytes: Free bytes available on the device.
    :param total_bytes: Total capacity of the device in bytes.
    :param used_bytes: Used bytes on the device.
    :param low_space: ``True`` when free space is below the
        configured threshold.
    :param namespaces: Namespace entries belonging to this group.
    """

    mount_group: str
    free_bytes: int = 0
    total_bytes: int = 0
    used_bytes: int = 0
    low_space: bool = False
    namespaces: list[NamespaceUsageOut] = Field(default_factory=list)
