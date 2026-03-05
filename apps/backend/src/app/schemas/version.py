"""Version request and response schemas."""
from pydantic import BaseModel, Field


class VersionOut(BaseModel):
    """Version representation returned by the API.

    :param name: Version string.
    :param locales: Available locale codes for this version.
    :param is_latest: Whether this version is pointed to by
        latest.
    """

    name: str
    locales: list[str] = Field(default_factory=list)
    is_latest: bool = False


class ResolveOut(BaseModel):
    """Result of a version+locale resolution.

    :param version: Resolved version string.
    :param locale: Resolved locale code (may differ from
        requested if a fallback was applied).
    :param fallback_used: True when a locale fallback was
        applied.
    """

    version: str
    locale: str
    fallback_used: bool
