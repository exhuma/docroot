"""Namespace request and response schemas."""

from typing import Annotated

from pydantic import BaseModel, Field

_NamePattern = Annotated[
    str,
    Field(
        pattern=r"^[a-z0-9][a-z0-9\-_]*$",
        description=(
            "Lowercase alphanumeric identifier. May contain hyphens and underscores."
        ),
    ),
]


class AclRoleIn(BaseModel):
    """A single ACL role entry.

    :param role: Role name as it appears in the JWT.
    :param read: Whether this role grants read access.
    :param write: Whether this role grants write access.
    """

    role: str = Field(description="Role name as it appears in the JWT.")
    read: bool = Field(
        default=False,
        description="Grant read access to this role.",
    )
    write: bool = Field(
        default=False,
        description="Grant write access to this role.",
    )


class AclRoleOut(BaseModel):
    """A single ACL role entry in a read response.

    :param role: Role name as stored in the ACL.
    :param read: Whether this role grants read access.
    :param write: Whether this role grants write access.
    """

    role: str
    read: bool = False
    write: bool = False


class AclFlagsIn(BaseModel):
    """Request body for updating namespace-level ACL flags.

    :param public_read: Whether the namespace is publicly readable.
    :param browsable: Whether unauthenticated callers may list
        the namespace and its contents without gaining doc access.
    """

    public_read: bool = Field(description="Allow unauthenticated read access.")
    browsable: bool = Field(
        description=(
            "Allow unauthenticated listing without granting documentation access."
        )
    )


class AclOut(BaseModel):
    """ACL data returned by the read-ACL endpoint.

    :param public_read: Whether the namespace is publicly readable.
    :param browsable: Whether unauthenticated callers may list the
        namespace and its contents.
    :param roles: All role entries in the namespace ACL.
    """

    public_read: bool = False
    browsable: bool = True
    roles: list[AclRoleOut] = Field(default_factory=list)


class NamespaceIn(BaseModel):
    """Request body for namespace creation.

    :param name: Namespace identifier.
    :param public_read: Allow unauthenticated read access.
    :param browsable: Allow unauthenticated listing without
        granting documentation access.
    :param roles: Initial ACL role entries.
    :param versioning: Versioning scheme: ``semver``,
        ``calver``, a PEP-440 alias, or a custom regex pattern
        with named groups used for sort-tuple construction.
    """

    name: _NamePattern
    public_read: bool = Field(
        default=False,
        description=("Allow unauthenticated read access to this namespace."),
    )
    browsable: bool = Field(
        default=True,
        description=(
            "Allow unauthenticated callers to list this "
            "namespace and its contents without granting "
            "documentation access."
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
    :param browsable: Whether the namespace is publicly listable.
    :param versioning: Configured versioning scheme.
    :param creator: Subject of the namespace creator.
    """

    name: str
    public_read: bool = False
    browsable: bool = True
    versioning: str = ""
    creator: str = ""
