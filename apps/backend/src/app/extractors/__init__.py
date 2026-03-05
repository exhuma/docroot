"""Role extractor plugins for JWT authentication.

Each extractor parses the decoded token payload to return a list of
roles for the authenticated principal. Extractors are IDP-specific.
"""
from typing import Protocol


class RoleExtractor(Protocol):
    """Protocol for role extractor callables."""

    def __call__(
        self,
        payload: dict[str, object],
        context: dict[str, str],
    ) -> list[str]:
        """Extract roles from a decoded JWT payload.

        :param payload: Decoded JWT claims.
        :param context: Authentication context with 'issuer' and
            'audience' keys.
        :returns: List of role strings.
        """
        ...
