"""Pydantic request/response schemas for the Docroot API.

All schemas are Pydantic v2 BaseModels with field-level validation
via ``Annotated`` constraints. Validation errors produce HTTP 422
responses automatically via FastAPI.
"""

from app.schemas.namespace import (
    AclFlagsIn,
    AclOut,
    AclRoleIn,
    AclRoleOut,
    NamespaceIn,
    NamespaceOut,
)
from app.schemas.project import ProjectIn, ProjectOut
from app.schemas.version import ResolveOut, VersionOut

__all__ = [
    "AclFlagsIn",
    "AclOut",
    "AclRoleIn",
    "AclRoleOut",
    "NamespaceIn",
    "NamespaceOut",
    "ProjectIn",
    "ProjectOut",
    "ResolveOut",
    "VersionOut",
]
