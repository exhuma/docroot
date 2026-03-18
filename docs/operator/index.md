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
cp deploy/compose/.env.example deploy/compose/.env
# Edit deploy/compose/.env as needed
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
| `DOCROOT_OAUTH_JWKS_URL` | *(empty)* | JWKS endpoint URL for JWT validation. Supports `file://` for local dev. |
| `DOCROOT_OAUTH_AUDIENCE` | *(empty)* | Expected JWT audience. Empty disables audience validation. |
| `DOCROOT_OAUTH_ROLE_EXTRACTOR` | `keycloak` | Role extractor name. Currently `keycloak` only. |
| `DOCROOT_CORS_ORIGINS` | `*` | Comma-separated CORS origins, or `*` for any. |
| `DOCROOT_ZIP_MAX_FILES` | `500` | Maximum files in an uploaded ZIP. |
| `DOCROOT_ZIP_MAX_EXTRACTED_MB` | `500` | Maximum extracted ZIP size in MB. |
| `DOCROOT_LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `DOCROOT_COOKIE_SECURE` | `false` | Set `true` on HTTPS deployments. |
| `DOCROOT_OIDC_ISSUER` | *(empty)* | OIDC issuer URL served to the browser UI. Empty disables the OIDC login button. |
| `DOCROOT_OIDC_CLIENT_ID` | *(empty)* | OIDC **public** client ID for the browser authorization-code + PKCE flow. |

---

## Volumes

Mount one external volume at `/data`. All namespace, project,
and documentation data is stored there.

```yaml
volumes:
  - /your/host/path:/data
```

Restart the containers at any time without data loss.

---

## OIDC / OAuth2 Configuration

Docroot works with **any OIDC-compliant identity provider**.
It does not depend on Keycloak specifically.  The architecture
uses two clients:

1. **Confidential back-end client** — validates JWT Bearer tokens
   using JWKS (resource-server behaviour, no user redirect).
2. **Public front-end client** — drives the browser
   authorization-code + PKCE flow via `oidc-client-ts`.

### General setup pattern

For every OIDC-compliant IDP, apply the same two-step
configuration:

**Step 1 — back-end (resource server):**

```env
# Point to the IDP's JWKS endpoint
DOCROOT_OAUTH_JWKS_URL=https://<idp>/.well-known/jwks.json
# Audience value expected in every incoming JWT
DOCROOT_OAUTH_AUDIENCE=<your-api-audience>
```

**Step 2 — front-end (public client):**

```env
# OIDC issuer URL (same as the `iss` claim in your tokens)
DOCROOT_OIDC_ISSUER=https://<idp>
# Public client ID registered at the IDP
DOCROOT_OIDC_CLIENT_ID=<your-public-client-id>
```

Register `https://<your-host>/oidc-callback` as the allowed
redirect URI at your IDP.  No client secret is required for the
front-end client (PKCE only).

---

## Keycloak (self-hosted)

### 1. Create a realm

In the Keycloak admin console, create a realm (e.g. `docroot`).

### 2. Create a confidential back-end client

1. **Clients → Create client**
2. Client ID: `docroot-api`
3. Client authentication: **ON** (confidential)
4. Service accounts: **ON** (for client-credentials uploads)

Configure the API container:

```env
DOCROOT_OAUTH_JWKS_URL=https://keycloak.example.com/realms/\
docroot/protocol/openid-connect/certs
DOCROOT_OAUTH_AUDIENCE=docroot-api
```

### 3. Create a public front-end client

1. **Clients → Create client**
2. Client ID: `docroot-ui`
3. Client authentication: **OFF** (public)
4. Valid redirect URIs:
   `https://docroot.example.com/oidc-callback`
5. Web origins: `https://docroot.example.com`

Configure the API container:

```env
DOCROOT_OIDC_ISSUER=https://keycloak.example.com/realms/docroot
DOCROOT_OIDC_CLIENT_ID=docroot-ui
```

### 4. Create roles and assign them

1. Go to **Realm roles → Create role** (e.g. `docroot-editor`).
2. Assign the role to users via **Users → Role mappings**.
3. Reference the role name in `namespace.toml` ACL files.

The Keycloak role extractor reads:

- `realm_access.roles` — realm-level roles
- `resource_access.<client_id>.roles` — client-level roles

---

## Microsoft / Entra ID (Azure AD)

Microsoft Entra ID is a fully OIDC-compliant provider and can
be used directly without any intermediary.

### 1. Register an application

1. In the [Azure portal](https://portal.azure.com), go to
   **Azure Active Directory → App registrations →
   New registration**.
2. Supported account types: choose the appropriate scope
   (single tenant, multi-tenant, etc.).
3. Redirect URI: **Single-page application (SPA)**
   `https://docroot.example.com/oidc-callback`
4. Note the **Application (client) ID** (this is your
   `client_id`).
5. Note the **Directory (tenant) ID**.

### 2. Expose an API (back-end audience)

1. Under **Expose an API**, set the **Application ID URI**
   (e.g. `api://<client-id>`).
2. This value becomes your `DOCROOT_OAUTH_AUDIENCE`.

### 3. Configure Docroot

```env
DOCROOT_OAUTH_JWKS_URL=https://login.microsoftonline.com/\
<tenant-id>/discovery/v2.0/keys
DOCROOT_OAUTH_AUDIENCE=api://<client-id>
DOCROOT_OIDC_ISSUER=https://login.microsoftonline.com/\
<tenant-id>/v2.0
DOCROOT_OIDC_CLIENT_ID=<client-id>
```

---

## Google

Google Identity is fully OIDC-compliant and can be used
directly.

### 1. Create an OAuth2 client

1. In the [Google Cloud Console](https://console.cloud.google.com),
   go to **APIs & Services → Credentials → Create credentials
   → OAuth client ID**.
2. Application type: **Web application**.
3. Add an authorised redirect URI:
   `https://docroot.example.com/oidc-callback`
4. Note the **Client ID** (no secret needed; Docroot uses PKCE).

### 2. Configure Docroot

```env
DOCROOT_OAUTH_JWKS_URL=\
https://www.googleapis.com/oauth2/v3/certs
DOCROOT_OAUTH_AUDIENCE=<google-client-id>
DOCROOT_OIDC_ISSUER=https://accounts.google.com
DOCROOT_OIDC_CLIENT_ID=<google-client-id>
```

---

## GitHub

> **Note:** GitHub does **not** provide a standard OIDC
> authorization endpoint for browser user authentication.
> GitHub's OIDC provider (`token.actions.githubusercontent.com`)
> is intended for GitHub Actions workload identity only and
> cannot be used for interactive user logins via `oidc-client-ts`.
>
> To use GitHub as a login provider for Docroot, run an
> OIDC-compliant proxy in front of it.  Popular options include
> [Keycloak](https://www.keycloak.org/) (identity brokering),
> [Dex](https://dexidp.io/), or [Zitadel](https://zitadel.com/).
> Configure that proxy as the Docroot OIDC issuer.

---

## Facebook

> **Note:** Facebook Login uses OAuth 2.0 but its user access
> tokens are **not** JWTs and Facebook does not expose a
> standards-compliant OIDC discovery document suitable for
> browser authorization-code + PKCE flows with
> `oidc-client-ts`.
>
> To use Facebook as a login provider for Docroot, run an
> OIDC-compliant proxy in front of it (e.g. Keycloak, Dex, or
> Zitadel with Facebook federation enabled).  Configure that
> proxy as the Docroot OIDC issuer.

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
