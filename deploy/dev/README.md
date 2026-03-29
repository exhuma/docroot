# Development Auth Files

This directory contains a pre-generated RSA keypair for local
development only. **Do not use these keys in production.**

## Files

- `dev_key.pem` — RSA private key (signs development JWTs)
- `jwks.json` — JWKS with the corresponding public key
  (used by the backend to verify tokens in dev)

## Usage

The Taskfile at the repository root provides a `gen-token` task
that generates a signed JWT for local development. See
`Taskfile.yml` for available tasks.

The backend reads the JWKS from a `file://` URL in dev mode:

```
OAUTH_JWKS_URL=file:///absolute/path/to/deploy/dev/jwks.json
```
