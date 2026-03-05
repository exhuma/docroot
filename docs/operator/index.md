# Operator / Maintainer Manual

Covers installation, deployment, OIDC configuration, and
namespace ACL management.

---

## Prerequisites

- Docker and Docker Compose
- An OIDC-compatible identity provider (e.g. Keycloak, Auth0,
  GitHub, GitLab)

---

## Quick Start

```bash
git clone https://github.com/exhuma/docroot.git
cd docroot
cp deploy/dev/.env.example deploy/dev/.env
# Edit deploy/dev/.env as needed
docker compose -f deploy/compose/docker-compose.yml up
```

The application is then available on port 80.

---

## Environment Variables

All variables use the `DOCROOT_` prefix. Set them in the
container environment or in a `.env` file loaded by the API
container.

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCROOT_DATA_ROOT` | `/data` | Filesystem path for stored data |
| `DOCROOT_OAUTH_JWKS_URL` | *(empty)* | JWKS endpoint URL. Required for JWT validation. Supports `file://` for local dev. |
| `DOCROOT_OAUTH_AUDIENCE` | *(empty)* | Expected JWT audience. Disable with empty string. |
| `DOCROOT_OAUTH_ROLE_EXTRACTOR` | `keycloak` | Role extractor name. Currently `keycloak` only. |
| `DOCROOT_CORS_ORIGINS` | `*` | Comma-separated CORS origins, or `*` for any. |
| `DOCROOT_ZIP_MAX_FILES` | `500` | Maximum files in an uploaded ZIP. |
| `DOCROOT_ZIP_MAX_EXTRACTED_MB` | `500` | Maximum extracted ZIP size in MB. |

---

## OIDC / OAuth2 Configuration

Docroot acts as an OAuth2 resource server. It validates JWT
Bearer tokens but does not perform the login flow itself.

1. Register Docroot as a resource server (audience) in your IDP.
2. Set `DOCROOT_OAUTH_JWKS_URL` to the JWKS endpoint of your
   IDP (e.g.
   `https://accounts.example.com/.well-known/jwks.json`).
3. Set `DOCROOT_OAUTH_AUDIENCE` to the audience value in your
   tokens.

### Keycloak-specific notes

The Keycloak extractor reads roles from:

- `realm_access.roles` — realm-level roles
- `resource_access.<client_id>.roles` — client-level roles

Assign roles in the Keycloak admin console and reference them
in namespace ACL files.

---

## Namespace ACL Format

Each namespace directory contains a `namespace.toml` file that
controls access. The file is read on each request and cached in
memory; changes take effect immediately on the next cache miss.

### Full Example

```toml
creator = "alice"
versioning = "semver"

[access]
public_read = false

[[access.roles]]
role = "docroot-editor"
read = true
write = true

[[access.roles]]
role = "docroot-reader"
read = true
write = false
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `creator` | string | Subject of the user who created the namespace. Only this user may delete the namespace. |
| `versioning` | string | Versioning scheme for display sorting. Values: `semver`, `calver`, `pep440`, or a regex pattern. |
| `access.public_read` | bool | Allow unauthenticated read access. |
| `access.roles[].role` | string | Role name from the JWT (exact match). |
| `access.roles[].read` | bool | Grant read access. |
| `access.roles[].write` | bool | Grant write (upload) access. |

### Managing Roles via API

Use the ACL endpoints instead of editing files directly:

```bash
# Grant editor role write access
curl -X PUT /api/namespaces/myns/acl/roles/editor \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"read": true, "write": true}'

# Revoke a role
curl -X DELETE /api/namespaces/myns/acl/roles/editor \
  -H "Authorization: Bearer $TOKEN"
```

---

## Volume and Data Layout

All data lives under `DOCROOT_DATA_ROOT`:

```
/data/
  namespaces/
    <namespace>/
      namespace.toml
      projects/
        <project>/
          versions/
            <version>/
              <locale>/
                index.html
                metadata.toml
                ...
          latest -> <version>  (symlink)
```

Restart the application at any time without data loss.
The filesystem is the source of truth.

---

## Development Mode

See the repository `README.md` and `Taskfile.yml` for local
development setup. Use `task gen-token` to generate a test JWT:

```bash
task gen-token -- --sub alice --roles editor
```
