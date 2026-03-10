"""Namespace ACL management.

Reads and caches namespace ACL configuration from ``namespace.toml``
files stored in the namespace directory. The cache is invalidated
when the file's mtime changes, ensuring ACL changes are picked up
without restarting the service.
"""
import tomllib
from pathlib import Path
from threading import Lock


class AclCache:
    """Thread-safe cache for namespace ACL data.

    Reads ``namespace.toml`` from the namespace directory and caches
    the result keyed by the file path and its mtime. Automatically
    invalidates when the mtime changes.
    """

    def __init__(self) -> None:
        """Initialise the cache with an empty state."""
        self._cache: dict[
            str, tuple[float, dict[str, object]]
        ] = {}
        self._lock = Lock()

    def get(
        self, namespace_dir: Path
    ) -> dict[str, object]:
        """Return the parsed ACL data for a namespace directory.

        Returns a default (no-access) ACL if the file does not
        exist or cannot be parsed.

        :param namespace_dir: Path to the namespace directory.
        :returns: Parsed TOML data as a dict.
        """
        toml_path = namespace_dir / "namespace.toml"
        try:
            mtime = toml_path.stat().st_mtime
        except FileNotFoundError:
            return {
                "access": {"public_read": False, "roles": []}
            }

        key = str(toml_path)
        with self._lock:
            if key in self._cache:
                cached_mtime, cached_data = self._cache[key]
                if cached_mtime == mtime:
                    return cached_data
            try:
                with open(toml_path, "rb") as fh:
                    data: dict[str, object] = (
                        tomllib.load(fh)
                    )
            except Exception:
                return {
                    "access": {
                        "public_read": False,
                        "roles": [],
                    }
                }
            self._cache[key] = (mtime, data)
            return data

    def can_read(
        self,
        acl: dict[str, object],
        roles: list[str],
        subject: str = "",
    ) -> bool:
        """Return True if the given roles or subject grant read access.

        Public namespaces (``public_read = true``) are always
        readable. The namespace creator identified by *subject*
        is always granted read access.

        :param acl: Parsed ACL data from :meth:`get`.
        :param roles: Roles of the authenticated principal.
        :param subject: JWT subject of the authenticated principal.
        :returns: True if read is permitted.
        """
        access = acl.get("access")
        if not isinstance(access, dict):
            return False
        if access.get("public_read", False):
            return True
        creator = acl.get("creator")
        if subject and creator and subject == str(creator):
            return True
        for entry in access.get("roles", []):
            if not isinstance(entry, dict):
                continue
            if (
                entry.get("role") in roles
                and entry.get("read", False)
            ):
                return True
        return False

    def can_write(
        self,
        acl: dict[str, object],
        roles: list[str],
        subject: str = "",
    ) -> bool:
        """Return True if the given roles or subject grant write access.

        The namespace creator identified by *subject* is always
        granted write access.

        :param acl: Parsed ACL data from :meth:`get`.
        :param roles: Roles of the authenticated principal.
        :param subject: JWT subject of the authenticated principal.
        :returns: True if write is permitted.
        """
        access = acl.get("access")
        if not isinstance(access, dict):
            return False
        creator = acl.get("creator")
        if subject and creator and subject == str(creator):
            return True
        for entry in access.get("roles", []):
            if not isinstance(entry, dict):
                continue
            if (
                entry.get("role") in roles
                and entry.get("write", False)
            ):
                return True
        return False

    def get_creator(
        self, namespace_dir: Path
    ) -> str | None:
        """Return the creator subject stored in the namespace TOML.

        :param namespace_dir: Path to the namespace directory.
        :returns: Creator subject string, or None if not recorded.
        """
        data = self.get(namespace_dir)
        creator = data.get("creator")
        return str(creator) if creator else None
