#!/usr/bin/env python3
"""Generate a development JWT for local testing.

Usage::

    python scripts/gen_dev_token.py [--sub NAME] [--roles ROLE,...]
        [--client CLIENT] [--client-roles ROLE,...]
        [--days N] [--audience AUD]

The token is signed with the dev RSA private key at
``deploy/dev/dev_key.pem`` and can be verified by the backend when
``DOCROOT_OAUTH_JWKS_URL`` points to ``deploy/dev/jwks.json``.
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent

try:
    import jwt
    from cryptography.hazmat.primitives.serialization import (
        load_pem_private_key,
    )
except ImportError:
    print(
        "Missing dependencies. Run:\n"
        "  uv sync\n"
        "from the apps/backend directory.",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    """Entry point: parse arguments and print the generated JWT."""
    parser = argparse.ArgumentParser(
        description="Generate a dev JWT token"
    )
    parser.add_argument(
        "--sub",
        default="dev-user",
        help="Subject (user identity). Default: dev-user",
    )
    parser.add_argument(
        "--roles",
        default="editor",
        help=(
            "Comma-separated Keycloak realm roles. "
            "Default: editor"
        ),
    )
    parser.add_argument(
        "--client",
        default="",
        help="Client ID for client-level roles.",
    )
    parser.add_argument(
        "--client-roles",
        default="",
        dest="client_roles",
        help="Comma-separated client-level roles.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Token validity in days. Default: 365",
    )
    parser.add_argument(
        "--audience",
        default="docroot-dev",
        help="Token audience. Default: docroot-dev",
    )
    args = parser.parse_args()

    key_path = ROOT / "deploy" / "dev" / "dev_key.pem"
    if not key_path.exists():
        print(
            f"Dev private key not found: {key_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    private_key = load_pem_private_key(
        key_path.read_bytes(), password=None
    )

    now = datetime.now(timezone.utc)
    roles = [
        r.strip()
        for r in args.roles.split(",")
        if r.strip()
    ]
    payload: dict[str, object] = {
        "sub": args.sub,
        "iss": "docroot-dev",
        "aud": args.audience,
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(days=args.days)).timestamp()
        ),
        "realm_access": {"roles": roles},
    }

    if args.client and args.client_roles:
        client_roles = [
            r.strip()
            for r in args.client_roles.split(",")
            if r.strip()
        ]
        payload["resource_access"] = {
            args.client: {"roles": client_roles}
        }

    token = jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": "dev-key-1"},
    )
    print(token)


if __name__ == "__main__":
    main()
