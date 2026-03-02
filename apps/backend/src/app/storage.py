import errno
import fcntl
import os
import shutil
import uuid
from pathlib import Path

import toml

DATA_ROOT = os.environ.get("DATA_ROOT", "/data")


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


class FilesystemStorage:
    def __init__(self, data_root: str | Path | None = None) -> None:
        if data_root is None:
            data_root = DATA_ROOT
        self.data_root = Path(data_root)

    # ------------------------------------------------------------------
    # Private path helpers
    # ------------------------------------------------------------------

    def _namespaces_dir(self) -> Path:
        return self.data_root / "namespaces"

    def _namespace_dir(self, namespace: str) -> Path:
        return self._namespaces_dir() / namespace

    def _projects_dir(self, namespace: str) -> Path:
        return self._namespace_dir(namespace) / "projects"

    def _project_dir(self, namespace: str, project: str) -> Path:
        return self._projects_dir(namespace) / project

    def _versions_dir(self, namespace: str, project: str) -> Path:
        return self._project_dir(namespace, project) / "versions"

    def _version_dir(
        self, namespace: str, project: str, version: str
    ) -> Path:
        return self._versions_dir(namespace, project) / version

    def _locale_path(
        self,
        namespace: str,
        project: str,
        version: str,
        locale: str,
    ) -> Path:
        return self._version_dir(namespace, project, version) / locale

    # ------------------------------------------------------------------
    # Public helpers for route-layer use
    # ------------------------------------------------------------------

    def namespace_dir(self, namespace: str) -> Path:
        return self._namespace_dir(namespace)

    def namespace_exists(self, namespace: str) -> bool:
        return self._namespace_dir(namespace).is_dir()

    def project_exists(self, namespace: str, project: str) -> bool:
        return self._project_dir(namespace, project).is_dir()

    def get_latest(
        self, namespace: str, project: str
    ) -> str | None:
        link = self._project_dir(namespace, project) / "latest"
        if link.is_symlink():
            return os.readlink(link)
        return None

    # ------------------------------------------------------------------
    # Namespace operations
    # ------------------------------------------------------------------

    def create_namespace(self, name: str) -> None:
        ns_dir = self._namespace_dir(name)
        ns_dir.mkdir(parents=True, exist_ok=True)
        (ns_dir / "projects").mkdir(exist_ok=True)
        toml_path = ns_dir / "namespace.toml"
        if not toml_path.exists():
            with open(toml_path, "w") as fh:
                toml.dump(
                    {
                        "access": {
                            "public_read": False,
                            "roles": [],
                        }
                    },
                    fh,
                )

    def delete_namespace(self, name: str) -> None:
        ns_dir = self._namespace_dir(name)
        if not ns_dir.exists():
            raise NamespaceNotFound(name)
        shutil.rmtree(ns_dir)

    def list_namespaces(self) -> list[str]:
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

    def create_project(self, namespace: str, project: str) -> None:
        ns_dir = self._namespace_dir(namespace)
        if not ns_dir.exists():
            raise NamespaceNotFound(namespace)
        proj_dir = self._project_dir(namespace, project)
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "versions").mkdir(exist_ok=True)

    def delete_project(self, namespace: str, project: str) -> None:
        proj_dir = self._project_dir(namespace, project)
        if not proj_dir.exists():
            raise ProjectNotFound(project)
        shutil.rmtree(proj_dir)

    def list_projects(self, namespace: str) -> list[str]:
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
        final_path = self._locale_path(
            namespace, project, version, locale
        )
        version_dir = self._version_dir(namespace, project, version)
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

                # Remove any uploaded metadata.toml;
                # the server generates it from form fields.
                uploaded_meta = source_dir / "metadata.toml"
                if uploaded_meta.exists():
                    uploaded_meta.unlink()

                with open(
                    source_dir / "metadata.toml", "w"
                ) as fh:
                    toml.dump(
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
                        fh,
                    )

                self._atomic_move(source_dir, final_path)
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

        if latest:
            self.set_latest(namespace, project, version)

    @staticmethod
    def _atomic_move(src: Path, dst: Path) -> None:
        """Move src to dst atomically when possible."""
        try:
            os.rename(src, dst)
        except OSError as exc:
            if exc.errno != errno.EXDEV:
                raise
            # Cross-device: copy then clean up source.
            shutil.copytree(src, dst)
            shutil.rmtree(src, ignore_errors=True)

    def delete_version(
        self,
        namespace: str,
        project: str,
        version: str,
        locale: str,
    ) -> None:
        locale_path = self._locale_path(
            namespace, project, version, locale
        )
        if not locale_path.exists():
            raise VersionNotFound(
                f"{namespace}/{project}/{version}/{locale}"
            )
        shutil.rmtree(locale_path)

    def list_versions(
        self, namespace: str, project: str
    ) -> list[str]:
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
        version_dir = self._version_dir(namespace, project, version)
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
        proj_dir = self._project_dir(namespace, project)
        tmp_name = f".latest_{os.getpid()}_{uuid.uuid4().hex}"
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
        if version_or_alias == "latest":
            link = self._project_dir(namespace, project) / "latest"
            if not link.is_symlink():
                raise VersionNotFound(
                    "latest symlink is not set"
                )
            version = os.readlink(link)
        else:
            version = version_or_alias

        version_dir = self._version_dir(namespace, project, version)
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
