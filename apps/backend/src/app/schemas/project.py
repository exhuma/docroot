"""Project request and response schemas."""

from pydantic import BaseModel, Field


class ProjectIn(BaseModel):
    """Request body for project creation.

    :param name: Human-readable project name.  The server
        derives a URL-safe slug from this value, which is used
        as the filesystem directory name and URL path segment.
    """

    name: str = Field(
        min_length=1,
        max_length=200,
        description=(
            "Human-readable project name. "
            "The server slugifies this into a URL-safe identifier."
        ),
    )


class ProjectOut(BaseModel):
    """Project representation returned by the API.

    :param name: URL-safe slug used as the filesystem directory
        name and URL path segment.
    :param display_name: Original human-readable name supplied at
        creation time.  Falls back to ``name`` when not set.
    """

    name: str
    display_name: str = ""
