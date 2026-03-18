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

Docroot uses two OIDC clients:

1. **Confidential back-end client** — validates JWT Bearer tokens
   using JWKS (resource-server behaviour, no redirect).
2. **Public front-end client** — drives the browser
   authorization-code + PKCE flow via `oidc-client-ts`.

### Back-end (resource server) setup

Set `DOCROOT_OAUTH_JWKS_URL` to the JWKS endpoint of your IDP
and `DOCROOT_OAUTH_AUDIENCE` to the audience value in your
tokens.

### Front-end (public client) setup

Set `DOCROOT_OIDC_ISSUER` to the OIDC issuer URL and
`DOCROOT_OIDC_CLIENT_ID` to the public client ID registered in
your IDP.  The front-end uses the authorization-code flow with
PKCE; no client secret is required.  Register
`https://<your-host>/oidc-callback` as the redirect URI.

---

## Keycloak Configuration

### 1. Create a realm

In the Keycloak admin console, create a realm (e.g. `docroot`).

### 2. Create a confidential back-end client

1. **Clients → Create client**
2. Client ID: `docroot-api`
3. Client authentication: **ON** (confidential)
4. Service accounts: **ON** (for client-credentials uploads)
5. Note the client secret from the **Credentials** tab.

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

## GitHub OAuth / OIDC

GitHub supports OIDC for Actions but not for browser logins.
For browser login, use GitHub as a social login provider via
Keycloak's identity brokering:

1. Register an OAuth App on GitHub
   (*Settings → Developer settings → OAuth Apps*).
2. Authorization callback URL:
   `https://keycloak.example.com/realms/docroot/broker/\
github/endpoint`
3. In Keycloak, add an **Identity Provider** of type **GitHub**
   and fill in the client ID and secret from step 1.

---

## Facebook Login

1. Create an app at
   [developers.facebook.com](https://developers.facebook.com).
2. Add the **Facebook Login** product.
3. Valid OAuth redirect URI:
   `https://keycloak.example.com/realms/docroot/broker/\
facebook/endpoint`
4. In Keycloak, add an Identity Provider of type **Facebook**
   with the App ID and App Secret.

---

## Microsoft / Entra ID (Azure AD)

1. Register an application in the
   [Azure portal](https://portal.azure.com) under
   **Azure Active Directory → App registrations**.
2. Add a redirect URI (Web):
   `https://keycloak.example.com/realms/docroot/broker/\
microsoft/endpoint`
3. Note the **Application (client) ID** and create a client
   secret.
4. In Keycloak, add an Identity Provider of type
   **Microsoft** with the client ID and secret.

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
