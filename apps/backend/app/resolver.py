from app.storage import FilesystemStorage


def resolve_version(
    storage: FilesystemStorage,
    namespace: str,
    project: str,
    version_or_alias: str,
    locale: str,
) -> tuple[str, str]:
    return storage.resolve_version(
        namespace, project, version_or_alias, locale
    )
