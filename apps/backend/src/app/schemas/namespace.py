"""Namespace request and response schemas."""
from typing import Annotated

from pydantic import BaseModel, Field


_NamePattern = Annotated[
    str,
    Field(
        pattern=r"^[a-z0-9][a-z0-9\-_]*$",
        description=(
            "Lowercase alphanumeric identifier. "
            "May contain hyphens and underscores."
        ),
    ),
]


class AclRoleIn(BaseModel):
    """A single ACL role entry.

    :param role: Role name as it appears in the JWT.
    :param read: Whether this role grants read access.
    :param write: Whether this role grants write access.
    """

    role: str = Field(
        description="Role name as it appears in the JWT."
    )
    read: bool = Field(
        default=False,
        description="Grant read access to this role.",
    )
    write: bool = Field(
        default=False,
        description="Grant write access to this role.",
    )


class NamespaceIn(BaseModel):
    """Request body for namespace creation.

    :param name: Namespace identifier.
    :param public_read: Allow unauthenticated read access.
    :param roles: Initial ACL role entries.
    :param versioning: Versioning scheme: ``semver``,
        ``calver``, a PEP-440 alias, or a custom regex pattern
        with named groups used for sort-tuple construction.
    """

    name: _NamePattern
    public_read: bool = Field(
        default=False,
        description=(
            "Allow unauthenticated read access to this "
            "namespace."
        ),
    )
    roles: list[AclRoleIn] = Field(
        default_factory=list,
        description="Initial ACL role entries.",
    )
    versioning: str = Field(
        default="",
        description=(
            "Versioning scheme. Supported values: "
            "``semver``, ``calver``, ``pep440``, "
            "or a custom regex with named groups."
        ),
    )


class NamespaceOut(BaseModel):
    """Namespace representation returned by the API.

    :param name: Namespace identifier.
    :param public_read: Whether the namespace is publicly
        readable.
    :param versioning: Configured versioning scheme.
    :param creator: Subject of the namespace creator.
    """

    name: str
    public_read: bool = False
    versioning: str = ""
    creator: str = ""
