"""Keycloak-compatible JWT role extractor.

Extracts both realm-level and client-level roles from Keycloak JWTs.

Realm roles are read from ``realm_access.roles`` and returned as-is.
Client roles are read from ``resource_access.<client_id>.roles``
and returned prefixed with the client ID and a slash, e.g.
``my-client/editor``, to preserve the client scope context.
"""


def extract_roles(
    payload: dict[str, object],
    context: dict[str, str],
) -> list[str]:
    """Extract Keycloak realm and client roles from JWT payload.

    Realm roles are taken from ``realm_access.roles`` and returned
    as-is.  Client roles are taken from every entry in
    ``resource_access`` and returned as ``<client_id>/<role>`` to
    preserve the client context and avoid name collisions.

    :param payload: Decoded JWT claims.
    :param context: Authentication context (unused by this
        extractor but required by the protocol).
    :returns: Deduplicated list of role strings.
    """
    roles: list[str] = []

    realm_access = payload.get("realm_access")
    if isinstance(realm_access, dict):
        realm_roles = realm_access.get("roles", [])
        if isinstance(realm_roles, list):
            roles.extend(str(r) for r in realm_roles)

    resource_access = payload.get("resource_access")
    if isinstance(resource_access, dict):
        for client_id, client_data in resource_access.items():
            if not isinstance(client_data, dict):
                continue
            client_roles = client_data.get("roles", [])
            if isinstance(client_roles, list):
                roles.extend(
                    f"{client_id}/{r}" for r in client_roles
                )

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for role in roles:
        if role not in seen:
            seen.add(role)
            unique.append(role)
    return unique
