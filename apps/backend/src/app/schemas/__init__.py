"""Pydantic request/response schemas for the Docroot API.

All schemas are Pydantic v2 BaseModels with field-level validation
via ``Annotated`` constraints. Validation errors produce HTTP 422
responses automatically via FastAPI.
"""

from app.schemas.disk_usage import DiskUsageGroupOut, NamespaceUsageOut
from app.schemas.namespace import (
    AclFlagsIn,
    AclOut,
    AclRoleIn,
    AclRoleOut,
    NamespaceIn,
    NamespaceOut,
)
from app.schemas.project import ProjectIn, ProjectOut
from app.schemas.refs import RefIn, RefOut
from app.schemas.version import ResolveOut, VersionOut

__all__ = [
    "AclFlagsIn",
    "AclOut",
    "AclRoleIn",
    "AclRoleOut",
    "DiskUsageGroupOut",
    "NamespaceIn",
    "NamespaceOut",
    "NamespaceUsageOut",
    "ProjectIn",
    "ProjectOut",
    "RefIn",
    "RefOut",
    "ResolveOut",
    "VersionOut",
]
