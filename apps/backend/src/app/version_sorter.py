"""Version sorting utilities.

Provides :func:`sort_versions` which orders version strings
according to the versioning scheme configured in the namespace.
Supported schemes: ``semver``, ``calver``, ``pep440``, or a
custom regex with named groups used to build a sort key tuple.

When sorting fails for a particular version (e.g. it does not
match the configured pattern), that version is placed at the end
of the list in its original position.
"""
from __future__ import annotations

import re


def _semver_key(
    version: str,
) -> tuple[int, ...]:
    """Return a numeric sort key for a semver-like string.

    :param version: Version string, e.g. ``"1.2.3"`` or
        ``"1.2.3-alpha.1"``.
    :returns: Tuple of ints for comparison.
    """
    base = version.split("-")[0].split("+")[0]
    parts = base.split(".")
    nums: list[int] = []
    for part in parts:
        try:
            nums.append(int(part))
        except ValueError:
            nums.append(0)
    return tuple(nums)


def _calver_key(version: str) -> tuple[int, ...]:
    """Return a numeric sort key for a CalVer string.

    Handles formats like ``YYYY.MM.DD``, ``YYYY.MM``, or
    ``YYYY.0M.DD.MICRO``.

    :param version: CalVer version string.
    :returns: Tuple of ints for comparison.
    """
    return _semver_key(version)


def _pep440_key(version: str) -> object:
    """Return a PEP-440-aware sort key via the packaging library.

    Falls back to the raw string if the packaging library is not
    installed or the version is not valid PEP-440.

    :param version: PEP-440 version string.
    :returns: A comparable key object.
    """
    try:
        from packaging.version import InvalidVersion, Version

        return Version(version)
    except (InvalidVersion, ImportError):
        return version


def _regex_key(
    version: str,
    pattern: re.Pattern[str],
) -> tuple[str, ...]:
    """Return a sort key tuple from named regex groups.

    :param version: Version string.
    :param pattern: Compiled regex with named groups.
    :returns: Tuple of matched group values as strings, or a
        tuple containing the original string on non-match.
    """
    match = pattern.fullmatch(version)
    if match is None:
        return (version,)
    return tuple(match.groupdict().values())


def sort_versions(
    versions: list[str],
    scheme: str,
) -> list[str]:
    """Sort *versions* according to *scheme*.

    :param versions: List of version strings to sort.
    :param scheme: Versioning scheme name (``semver``,
        ``calver``, ``pep440``) or a regex pattern string with
        named groups.
    :returns: New sorted list. Versions that fail to parse are
        placed at the end in their original relative order.
    """
    if scheme == "semver":
        try:
            return sorted(versions, key=_semver_key)
        except Exception:
            return list(versions)

    if scheme == "calver":
        try:
            return sorted(versions, key=_calver_key)
        except Exception:
            return list(versions)

    if scheme == "pep440":
        good: list[str] = []
        bad: list[str] = []
        for v in versions:
            try:
                from packaging.version import (
                    InvalidVersion,
                    Version,
                )
                Version(v)
                good.append(v)
            except (InvalidVersion, ImportError):
                bad.append(v)
        try:
            good.sort(key=_pep440_key)
        except Exception:
            pass
        return good + bad

    # Treat scheme as a regex
    try:
        pattern = re.compile(scheme)
        good_versions: list[str] = []
        bad_versions: list[str] = []
        for v in versions:
            if pattern.fullmatch(v):
                good_versions.append(v)
            else:
                bad_versions.append(v)
        good_versions.sort(
            key=lambda v: _regex_key(v, pattern)
        )
        return good_versions + bad_versions
    except re.error:
        return list(versions)
