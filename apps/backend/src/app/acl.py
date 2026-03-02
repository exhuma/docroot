import os
from pathlib import Path
from threading import Lock

import toml


class AclCache:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, dict]] = {}
        self._lock = Lock()

    def get(self, namespace_dir: Path) -> dict:
        toml_path = namespace_dir / "namespace.toml"
        try:
            mtime = os.path.getmtime(toml_path)
        except FileNotFoundError:
            return {"access": {"public_read": False, "roles": []}}

        key = str(toml_path)
        with self._lock:
            if key in self._cache:
                cached_mtime, cached_data = self._cache[key]
                if cached_mtime == mtime:
                    return cached_data
            try:
                data = toml.load(str(toml_path))
            except Exception:
                return {
                    "access": {"public_read": False, "roles": []}
                }
            self._cache[key] = (mtime, data)
            return data

    def can_read(self, acl: dict, roles: list[str]) -> bool:
        access = acl.get("access", {})
        if access.get("public_read", False):
            return True
        for entry in access.get("roles", []):
            if (
                entry.get("role") in roles
                and entry.get("read", False)
            ):
                return True
        return False

    def can_write(self, acl: dict, roles: list[str]) -> bool:
        access = acl.get("access", {})
        for entry in access.get("roles", []):
            if (
                entry.get("role") in roles
                and entry.get("write", False)
            ):
                return True
        return False
