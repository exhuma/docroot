from jose import jwt


def extract_roles(token: str, context: dict) -> list[str]:
    payload = jwt.get_unverified_claims(token)
    realm_access = payload.get("realm_access", {})
    return list(realm_access.get("roles", []))
