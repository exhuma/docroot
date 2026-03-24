"""Project request and response schemas."""

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


class ProjectIn(BaseModel):
    """Request body for project creation.

    :param name: Project identifier.
    """

    name: _NamePattern


class ProjectOut(BaseModel):
    """Project representation returned by the API.

    :param name: Project identifier.
    """

    name: str
