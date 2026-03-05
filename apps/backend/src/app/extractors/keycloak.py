"""Keycloak-compatible JWT role extractor.

Extracts both realm-level and client-level roles from Keycloak JWTs.

Realm roles are read from ``realm_access.roles``.
Client roles are read from ``resource_access.<client_id>.roles``
for every client present in ``resource_access``.
"""


def extract_roles(
    payload: dict[str, object],
    context: dict[str, str],
) -> list[str]:
    """Extract Keycloak realm and client roles from JWT payload.

    Realm roles are taken from ``realm_access.roles``.
    Client roles are taken from every entry in
    ``resource_access``.

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
        for client_data in resource_access.values():
            if not isinstance(client_data, dict):
                continue
            client_roles = client_data.get("roles", [])
            if isinstance(client_roles, list):
                roles.extend(str(r) for r in client_roles)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for role in roles:
        if role not in seen:
            seen.add(role)
            unique.append(role)
    return unique
