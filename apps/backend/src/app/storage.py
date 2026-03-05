"""Filesystem-backed storage for namespaces, projects and versions.

This module is the sole point of contact with the filesystem. All
other modules must call methods here; no direct filesystem I/O is
permitted outside this module.

Atomic renames (``os.replace``) guarantee that partial writes are
never visible. Per-locale ``fcntl.flock`` prevents duplicate
concurrent uploads to the same version+locale slot.
"""
import errno
import fcntl
import os
import shutil
import tomllib
import uuid
from pathlib import Path


class VersionConflict(Exception):
    """Raised when a version+locale artifact already exists."""


class VersionNotFound(Exception):
    """Raised when a version or alias cannot be resolved."""


class LocaleNotFound(Exception):
    """Raised when no locale can be resolved for a version."""


class NamespaceNotFound(Exception):
    """Raised when a namespace directory does not exist."""


class ProjectNotFound(Exception):
    """Raised when a project directory does not exist."""


def _write_toml_simple(
    path: Path,
    data: dict[str, object],
) -> None:
    """Write a simple flat TOML file (no nested tables).

    :param path: Destination path.
    :param data: Flat key-value pairs to serialise.
    """
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, bool):
            lines.append(f"{key} = {str(value).lower()}")
        elif isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace(
                '"', '\\"'
            )
            lines.append(f'{key} = "{escaped}"')
        elif isinstance(value, (int, float)):
            lines.append(f"{key} = {value}")
    path.write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_namespace_toml(
    path: Path,
    creator: str,
    public_read: bool,
    roles: list[dict[str, object]],
    versioning: str = "",
) -> None:
    """Write the namespace.toml access-control file.

    :param path: Destination path.
    :param creator: Subject of the user who created the namespace.
    :param public_read: Whether the namespace is publicly readable.
    :param roles: List of role dicts with 'role', 'read', 'write'.
    :param versioning: Optional versioning scheme name or regex.
    """
    lines: list[str] = []
    escaped_creator = creator.replace(
        "\\", "\\\\"
    ).replace('"', '\\"')
    lines.append(f'creator = "{escaped_creator}"')
    if versioning:
        escaped_v = versioning.replace(
            "\\", "\\\\"
        ).replace('"', '\\"')
        lines.append(f'versioning = "{escaped_v}"')
    lines.append("")
    lines.append("[access]")
    lines.append(
        f"public_read = {str(public_read).lower()}"
    )
    for role_entry in roles:
        lines.append("")
        lines.append("[[access.roles]]")
        role_name = str(role_entry.get("role", ""))
        escaped_role = role_name.replace(
            "\\", "\\\\"
        ).replace('"', '\\"')
        lines.append(f'role = "{escaped_role}"')
        lines.append(
            "read = "
            f"{str(bool(role_entry.get('read', False))).lower()}"
        )
        lines.append(
            "write = "
            f"{str(bool(role_entry.get('write', False))).lower()}"
        )
    path.write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


class FilesystemStorage:
    """Storage implementation backed by the local filesystem.

    :param data_root: Root directory for all namespace data.
        Defaults to ``/data``.
    """

    def __init__(
        self,
        data_root: str | Path | None = None,
    ) -> None:
        """Initialise storage with the given data root.

        :param data_root: Override the storage root path.
            If ``None``, falls back to the ``DOCROOT_DATA_ROOT``
            environment variable, then to ``/data``.
        """
        if data_root is None:
            data_root = os.environ.get(
                "DOCROOT_DATA_ROOT", "/data"
            )
        self.data_root = Path(data_root)

    # ------------------------------------------------------------------
    # Private path helpers
    # ------------------------------------------------------------------

    def _namespaces_dir(self) -> Path:
        """Return the path to the top-level namespaces directory."""
        return self.data_root / "namespaces"

    def _namespace_dir(self, namespace: str) -> Path:
        """Return the path for a specific namespace.

        :param namespace: Namespace name.
        """
        return self._namespaces_dir() / namespace

    def _projects_dir(self, namespace: str) -> Path:
        """Return the path to the projects directory.

        :param namespace: Namespace name.
        """
        return self._namespace_dir(namespace) / "projects"

    def _project_dir(
        self, namespace: str, project: str
    ) -> Path:
        """Return the path for a specific project.

        :param namespace: Namespace name.
        :param project: Project name.
        """
        return self._projects_dir(namespace) / project

    def _versions_dir(
        self, namespace: str, project: str
    ) -> Path:
        """Return the path to the versions directory.

        :param namespace: Namespace name.
        :param project: Project name.
        """
        return (
            self._project_dir(namespace, project) / "versions"
        )

    def _version_dir(
        self, namespace: str, project: str, version: str
    ) -> Path:
        """Return the path for a specific version.

        :param namespace: Namespace name.
        :param project: Project name.
        :param version: Version string.
        """
        return (
            self._versions_dir(namespace, project) / version
        )

    def _locale_path(
        self,
        namespace: str,
        project: str,
        version: str,
        locale: str,
    ) -> Path:
        """Return the path for a specific locale of a version.

        :param namespace: Namespace name.
        :param project: Project name.
        :param version: Version string.
        :param locale: Two-letter locale code.
        """
        return (
            self._version_dir(namespace, project, version)
            / locale
        )

    # ------------------------------------------------------------------
    # Public helpers for route-layer use
    # ------------------------------------------------------------------

    def namespace_dir(self, namespace: str) -> Path:
        """Return the directory path for a namespace.

        :param namespace: Namespace name.
        :returns: Path to the namespace directory.
        """
        return self._namespace_dir(namespace)

    def namespace_exists(self, namespace: str) -> bool:
        """Return True if the namespace directory exists.

        :param namespace: Namespace name.
        :returns: True if the namespace exists.
        """
        return self._namespace_dir(namespace).is_dir()

    def project_exists(
        self, namespace: str, project: str
    ) -> bool:
        """Return True if the project directory exists.

        :param namespace: Namespace name.
        :param project: Project name.
        :returns: True if the project exists.
        """
        return self._project_dir(namespace, project).is_dir()

    def get_latest(
        self, namespace: str, project: str
    ) -> str | None:
        """Return the version pointed to by the latest symlink.

        :param namespace: Namespace name.
        :param project: Project name.
        :returns: Version string or ``None`` if no symlink is set.
        """
        link = (
            self._project_dir(namespace, project) / "latest"
        )
        if link.is_symlink():
            return os.readlink(link)
        return None

    def get_namespace_meta(
        self, namespace: str
    ) -> dict[str, object]:
        """Return the raw parsed namespace.toml for a namespace.

        :param namespace: Namespace name.
        :returns: Parsed TOML data as a dict.
        """
        toml_path = (
            self._namespace_dir(namespace) / "namespace.toml"
        )
        if not toml_path.exists():
            return {}
        try:
            with open(toml_path, "rb") as fh:
                return tomllib.load(fh)
        except (tomllib.TOMLDecodeError, OSError):
            return {}

    # ------------------------------------------------------------------
    # Namespace operations
    # ------------------------------------------------------------------

    def create_namespace(
        self,
        name: str,
        creator: str = "",
        public_read: bool = False,
        roles: list[dict[str, object]] | None = None,
        versioning: str = "",
    ) -> None:
        """Create a namespace directory with a default ACL file.

        The creator is stored in namespace.toml and automatically
        granted write access (in addition to any supplied roles).

        :param name: Namespace name.
        :param creator: Subject of the creating user.
        :param public_read: Whether to allow public read access.
        :param roles: Additional ACL role entries.
        :param versioning: Versioning scheme name or regex string.
        """
        ns_dir = self._namespace_dir(name)
        ns_dir.mkdir(parents=True, exist_ok=True)
        (ns_dir / "projects").mkdir(exist_ok=True)
        toml_path = ns_dir / "namespace.toml"
        if not toml_path.exists():
            all_roles: list[dict[str, object]] = list(
                roles or []
            )
            if creator:
                creator_role = {
                    "role": creator,
                    "read": True,
                    "write": True,
                }
                if not any(
                    r.get("role") == creator
                    for r in all_roles
                ):
                    all_roles.insert(0, creator_role)
            _write_namespace_toml(
                toml_path,
                creator=creator,
                public_read=public_read,
                roles=all_roles,
                versioning=versioning,
            )

    def delete_namespace(self, name: str) -> None:
        """Delete a namespace and all its contents.

        :param name: Namespace name.
        :raises NamespaceNotFound: If the namespace does not exist.
        """
        ns_dir = self._namespace_dir(name)
        if not ns_dir.exists():
            raise NamespaceNotFound(name)
        shutil.rmtree(ns_dir)

    def list_namespaces(self) -> list[str]:
        """Return a sorted list of all namespace names.

        :returns: Sorted list of namespace directory names.
        """
        ns_dir = self._namespaces_dir()
        if not ns_dir.exists():
            return []
        return sorted(
            d.name
            for d in ns_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    # ------------------------------------------------------------------
    # Project operations
    # ------------------------------------------------------------------

    def create_project(
        self, namespace: str, project: str
    ) -> None:
        """Create a project directory within a namespace.

        :param namespace: Namespace name.
        :param project: Project name.
        :raises NamespaceNotFound: If the namespace does not exist.
        """
        ns_dir = self._namespace_dir(namespace)
        if not ns_dir.exists():
            raise NamespaceNotFound(namespace)
        proj_dir = self._project_dir(namespace, project)
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "versions").mkdir(exist_ok=True)

    def delete_project(
        self, namespace: str, project: str
    ) -> None:
        """Delete a project directory and all its versions.

        :param namespace: Namespace name.
        :param project: Project name.
        :raises ProjectNotFound: If the project does not exist.
        """
        proj_dir = self._project_dir(namespace, project)
        if not proj_dir.exists():
            raise ProjectNotFound(project)
        shutil.rmtree(proj_dir)

    def list_projects(self, namespace: str) -> list[str]:
        """Return a sorted list of project names in a namespace.

        :param namespace: Namespace name.
        :returns: Sorted list of project names.
        :raises NamespaceNotFound: If the namespace does not exist.
        """
        ns_dir = self._namespace_dir(namespace)
        if not ns_dir.exists():
            raise NamespaceNotFound(namespace)
        projects_dir = self._projects_dir(namespace)
        if not projects_dir.exists():
            return []
        return sorted(
            d.name
            for d in projects_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    # ------------------------------------------------------------------
    # Version operations
    # ------------------------------------------------------------------

    def create_version(
        self,
        namespace: str,
        project: str,
        version: str,
        locale: str,
        source_dir: Path,
        latest: bool,
        uploader_subject: str,
        upload_timestamp: str,
    ) -> None:
        """Extract and atomically install a version+locale artifact.

        Uses an exclusive file lock to prevent duplicate concurrent
        uploads to the same version+locale slot.

        :param namespace: Namespace name.
        :param project: Project name.
        :param version: Version string.
        :param locale: Two-letter locale code.
        :param source_dir: Directory with extracted ZIP content.
        :param latest: Whether to update the latest symlink.
        :param uploader_subject: JWT subject of the uploader.
        :param upload_timestamp: ISO 8601 timestamp string.
        :raises VersionConflict: If the version+locale already
            exists.
        """
        final_path = self._locale_path(
            namespace, project, version, locale
        )
        version_dir = self._version_dir(
            namespace, project, version
        )
        version_dir.mkdir(parents=True, exist_ok=True)

        lock_path = version_dir / f".lock_{locale}"
        with open(lock_path, "w") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                if final_path.exists():
                    raise VersionConflict(
                        f"{namespace}/{project}"
                        f"/{version}/{locale}"
                    )

                uploaded_meta = source_dir / "metadata.toml"
                if uploaded_meta.exists():
                    uploaded_meta.unlink()

                _write_toml_simple(
                    source_dir / "metadata.toml",
                    {
                        "upload_timestamp": (
                            upload_timestamp or ""
                        ),
                        "uploader_subject": (
                            uploader_subject or ""
                        ),
                        "latest": latest,
                        "locale": locale,
                    },
                )

                self._atomic_move(source_dir, final_path)
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

        if latest:
            self.set_latest(namespace, project, version)

    @staticmethod
    def _atomic_move(src: Path, dst: Path) -> None:
        """Move *src* to *dst* atomically when possible.

        Falls back to a copy-then-delete strategy for cross-device
        moves.

        :param src: Source path.
        :param dst: Destination path.
        """
        try:
            os.rename(src, dst)
        except OSError as exc:
            if exc.errno != errno.EXDEV:
                raise
            shutil.copytree(src, dst)
            shutil.rmtree(src, ignore_errors=True)

    def delete_version(
        self,
        namespace: str,
        project: str,
        version: str,
        locale: str,
    ) -> None:
        """Delete a specific version+locale artifact directory.

        If the deleted version was pointed to by the ``latest``
        symlink, the symlink is updated to point to the most
        recently uploaded remaining version, or removed if no
        versions remain.

        :param namespace: Namespace name.
        :param project: Project name.
        :param version: Version string.
        :param locale: Two-letter locale code.
        :raises VersionNotFound: If the version+locale does not
            exist.
        """
        locale_path = self._locale_path(
            namespace, project, version, locale
        )
        if not locale_path.exists():
            raise VersionNotFound(
                f"{namespace}/{project}/{version}/{locale}"
            )
        shutil.rmtree(locale_path)

        version_dir = self._version_dir(
            namespace, project, version
        )
        remaining_locales = [
            d for d in version_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
        version_deleted = not remaining_locales
        if version_deleted:
            shutil.rmtree(version_dir, ignore_errors=True)
            # Only update the latest symlink when the entire
            # version was removed and it was the current latest.
            # Skipping this check when no version was deleted
            # avoids an unnecessary filesystem read.
            current_latest = self.get_latest(
                namespace, project
            )
            if current_latest == version:
                self._update_latest_after_delete(
                    namespace, project
                )

    def _update_latest_after_delete(
        self, namespace: str, project: str
    ) -> None:
        """Update or remove the latest symlink after a delete.

        Picks the version with the most recent upload_timestamp
        from metadata.toml. If no versions remain, removes the
        symlink.

        :param namespace: Namespace name.
        :param project: Project name.
        """
        versions = self.list_versions(namespace, project)
        if not versions:
            link = (
                self._project_dir(namespace, project)
                / "latest"
            )
            try:
                link.unlink()
            except FileNotFoundError:
                pass
            return

        best_version: str | None = None
        best_ts = ""
        for ver in versions:
            locales = self.list_locales(
                namespace, project, ver
            )
            if not locales:
                continue
            meta_path = (
                self._locale_path(
                    namespace, project, ver, locales[0]
                )
                / "metadata.toml"
            )
            try:
                with open(meta_path, "rb") as fh:
                    meta = tomllib.load(fh)
                ts = str(meta.get("upload_timestamp", ""))
            except Exception:
                ts = ""
            if best_version is None or ts > best_ts:
                best_version = ver
                best_ts = ts

        if best_version:
            self.set_latest(namespace, project, best_version)
        else:
            link = (
                self._project_dir(namespace, project)
                / "latest"
            )
            try:
                link.unlink()
            except FileNotFoundError:
                pass

    def list_versions(
        self, namespace: str, project: str
    ) -> list[str]:
        """Return a sorted list of version names for a project.

        :param namespace: Namespace name.
        :param project: Project name.
        :returns: Sorted list of version strings.
        """
        versions_dir = self._versions_dir(namespace, project)
        if not versions_dir.exists():
            return []
        return sorted(
            d.name
            for d in versions_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    def list_locales(
        self, namespace: str, project: str, version: str
    ) -> list[str]:
        """Return a sorted list of available locales for a version.

        :param namespace: Namespace name.
        :param project: Project name.
        :param version: Version string.
        :returns: Sorted list of two-letter locale codes.
        """
        version_dir = self._version_dir(
            namespace, project, version
        )
        if not version_dir.exists():
            return []
        return sorted(
            d.name
            for d in version_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    def set_latest(
        self, namespace: str, project: str, version: str
    ) -> None:
        """Atomically update the latest symlink to *version*.

        :param namespace: Namespace name.
        :param project: Project name.
        :param version: Version string to set as latest.
        """
        proj_dir = self._project_dir(namespace, project)
        tmp_name = (
            f".latest_{os.getpid()}_{uuid.uuid4().hex}"
        )
        tmp_link = proj_dir / tmp_name
        os.symlink(version, tmp_link)
        os.replace(tmp_link, proj_dir / "latest")

    def resolve_version(
        self,
        namespace: str,
        project: str,
        version_or_alias: str,
        locale: str,
    ) -> tuple[str, str]:
        """Resolve a version alias and locale with fallback logic.

        Locale resolution order:

        1. Requested locale.
        2. ``en`` (if different and available).
        3. First alphabetically sorted available locale.
        4. :exc:`LocaleNotFound` if no locales exist.

        :param namespace: Namespace name.
        :param project: Project name.
        :param version_or_alias: Version string or ``"latest"``.
        :param locale: Requested locale code.
        :returns: Tuple of
            ``(resolved_version, resolved_locale)``.
        :raises VersionNotFound: If the version cannot be
            resolved.
        :raises LocaleNotFound: If no locale is available.
        """
        if version_or_alias == "latest":
            link = (
                self._project_dir(namespace, project)
                / "latest"
            )
            if not link.is_symlink():
                raise VersionNotFound(
                    "latest symlink is not set"
                )
            version = os.readlink(link)
        else:
            version = version_or_alias

        version_dir = self._version_dir(
            namespace, project, version
        )
        if not version_dir.exists():
            raise VersionNotFound(version)

        if (version_dir / locale).is_dir():
            return (version, locale)

        if locale != "en" and (version_dir / "en").is_dir():
            return (version, "en")

        available = sorted(
            d.name
            for d in version_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )
        if available:
            return (version, available[0])

        raise LocaleNotFound(
            f"No locale found for "
            f"{namespace}/{project}/{version}"
        )

    def update_namespace_acl(
        self,
        namespace: str,
        role: str,
        read: bool,
        write: bool,
    ) -> None:
        """Add or update a role entry in the namespace ACL.

        If a role with the given name already exists, updates its
        read/write flags. Otherwise appends a new entry.

        :param namespace: Namespace name.
        :param role: Role string to add or update.
        :param read: Whether to grant read access.
        :param write: Whether to grant write access.
        :raises NamespaceNotFound: If the namespace does not exist.
        """
        ns_dir = self._namespace_dir(namespace)
        if not ns_dir.exists():
            raise NamespaceNotFound(namespace)
        meta = self.get_namespace_meta(namespace)
        creator = str(meta.get("creator", ""))
        versioning = str(meta.get("versioning", ""))
        access = meta.get("access", {})
        if not isinstance(access, dict):
            access = {}
        public_read = bool(access.get("public_read", False))
        roles: list[dict[str, object]] = []
        for entry in access.get("roles", []):
            if not isinstance(entry, dict):
                continue
            if entry.get("role") == role:
                continue
            roles.append(dict(entry))
        roles.append(
            {"role": role, "read": read, "write": write}
        )
        _write_namespace_toml(
            ns_dir / "namespace.toml",
            creator=creator,
            public_read=public_read,
            roles=roles,
            versioning=versioning,
        )

    def remove_namespace_role(
        self, namespace: str, role: str
    ) -> None:
        """Remove a role entry from the namespace ACL.

        :param namespace: Namespace name.
        :param role: Role string to remove.
        :raises NamespaceNotFound: If the namespace does not exist.
        """
        ns_dir = self._namespace_dir(namespace)
        if not ns_dir.exists():
            raise NamespaceNotFound(namespace)
        meta = self.get_namespace_meta(namespace)
        creator = str(meta.get("creator", ""))
        versioning = str(meta.get("versioning", ""))
        access = meta.get("access", {})
        if not isinstance(access, dict):
            access = {}
        public_read = bool(access.get("public_read", False))
        roles: list[dict[str, object]] = [
            dict(e)
            for e in access.get("roles", [])
            if isinstance(e, dict)
            and e.get("role") != role
        ]
        _write_namespace_toml(
            ns_dir / "namespace.toml",
            creator=creator,
            public_read=public_read,
            roles=roles,
            versioning=versioning,
        )
