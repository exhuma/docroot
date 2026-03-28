"""Keycloak-compatible JWT role extractor.

Extracts both realm-level and client-level roles from Keycloak JWTs.

Realm roles are read from ``realm_access.roles`` and returned as-is.
Client roles are read from ``resource_access.<client_id>.roles``
and returned prefixed with the client ID and a slash, e.g.
``my-client/editor``, to preserve the client scope context.

Client inclusion can be controlled via the ``client_allowlist`` and
``client_denylist`` keys in the *context* dict passed to
:func:`extract_roles`.  Both accept a list of client ID strings.
The allowlist is applied first: when non-empty, only the listed
clients are considered.  The denylist is then applied on top to
remove any explicitly blocked clients.  A client present in both
lists is therefore excluded.
"""


def _include_client(
    client_id: str,
    allowlist: list[str],
    denylist: list[str],
) -> bool:
    """Return True if *client_id* should have its roles extracted.

    The allowlist is processed first: when non-empty the client must
    be listed.  The denylist is then applied: even if a client passes
    the allowlist step, it is excluded when present in the denylist.
    A client in both lists is therefore excluded.

    :param client_id: Keycloak client identifier.
    :param allowlist: If non-empty, only these clients are considered.
    :param denylist: Clients to always exclude.
    :returns: True if the client's roles should be included.
    """
    if allowlist and client_id not in allowlist:
        return False
    return client_id not in denylist


def extract_roles(
    payload: dict[str, object],
    context: dict[str, object],
) -> list[str]:
    """Extract Keycloak realm and client roles from JWT payload.

    Realm roles are taken from ``realm_access.roles`` and returned
    as-is.  Client roles are taken from every entry in
    ``resource_access`` and returned as ``<client_id>/<role>`` to
    preserve the client context and avoid name collisions.

    Client extraction can be filtered using the optional
    ``client_allowlist`` and ``client_denylist`` keys in *context*.
    The allowlist is processed first, then the denylist is applied.
    A client in both lists is excluded.

    :param payload: Decoded JWT claims.
    :param context: Authentication context. Recognised keys:
        ``issuer`` (str), ``audience`` (str),
        ``client_allowlist`` (list[str]), ``client_denylist``
        (list[str]).
    :returns: Deduplicated list of role strings.
    """
    roles: list[str] = []

    allowlist_raw = context.get("client_allowlist", [])
    denylist_raw = context.get("client_denylist", [])
    allowlist: list[str] = (
        list(allowlist_raw) if isinstance(allowlist_raw, list) else []
    )
    denylist: list[str] = (
        list(denylist_raw) if isinstance(denylist_raw, list) else []
    )

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
            if not _include_client(client_id, allowlist, denylist):
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
