"""Utility for converting display names to URL-safe slugs.

A slug is a lowercase, hyphen-separated string containing only
ASCII alphanumeric characters and hyphens/underscores.  It is safe
to use as a filesystem directory name and as a URL path segment.
"""

import re
import unicodedata


def slugify(value: str) -> str:
    """Convert a display name to a URL-safe filesystem slug.

    Unicode characters are normalised to their closest ASCII
    equivalent (NFKD decomposition, then stripped of combining
    marks).  The result is lowercased, and any run of characters
    that is not ``[a-z0-9_]`` is replaced by a single hyphen.
    Leading and trailing hyphens are then stripped.

    :param value: Free-text display name to convert.
    :returns: Lowercase alphanumeric slug, or empty string if no
        alphanumeric characters remain after normalisation.

    Examples::

        >>> slugify("My Amazing Project")
        'my-amazing-project'
        >>> slugify("Hello World!")
        'hello-world'
        >>> slugify("café")
        'cafe'
        >>> slugify("my-project")
        'my-project'
    """
    normalised = unicodedata.normalize("NFKD", value)
    ascii_str = normalised.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_str.lower()
    slugged = re.sub(r"[^a-z0-9_]+", "-", lowered)
    return slugged.strip("-")
