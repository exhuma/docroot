"""Ref (tag) request and response schemas."""

from pydantic import BaseModel


class RefIn(BaseModel):
    """Request body for creating or updating a ref.

    :param version: Target version string.
    """

    version: str


class RefOut(BaseModel):
    """Ref representation returned by the API.

    :param name: Ref name (e.g. ``"latest"``).
    :param version: Version string the ref points to.
    """

    name: str
    version: str
