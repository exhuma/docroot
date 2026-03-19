# Operator Manual

## Prerequisites

- Docker and Docker Compose
- An OIDC-compliant identity provider (Keycloak, Entra ID,
  Google, or any IDP that supports
  [Authorization Code + PKCE](https://oauth.net/2/pkce/))

---

## Quick Start

```bash
git clone https://github.com/exhuma/docroot.git
cd docroot
cp deploy/compose/.env.example deploy/compose/.env
# Edit deploy/compose/.env — see Environment Variables below
docker compose -f deploy/compose/docker-compose.yml up
```

Open `http://localhost` in a browser.

---

## Environment Variables

All variables use the `DOCROOT_` prefix.
Set them in `deploy/compose/.env` or pass them directly to the
container.

| Variable | Default | Description |
|---|---|---|
| `DOCROOT_DATA_ROOT` | `/data` | Filesystem path for stored data |
| `DOCROOT_OAUTH_JWKS_URL` | *(empty)* | JWKS endpoint for JWT validation (`https://…` or `file://…`) |
| `DOCROOT_OAUTH_AUDIENCE` | *(empty)* | Expected `aud` claim. Empty disables audience validation. |
| `DOCROOT_OAUTH_CA_BUNDLE` | *(empty)* | Path to a PEM CA cert/bundle for verifying the JWKS endpoint. Set when the IDP uses an internal or self-signed CA. |
| `DOCROOT_OAUTH_ROLE_EXTRACTOR` | `keycloak` | Role extractor. Only `keycloak` is shipped in this release. |
| `DOCROOT_CORS_ORIGINS` | `*` | Comma-separated allowed origins, or `*`. |
| `DOCROOT_OIDC_ISSUER` | *(empty)* | OIDC issuer URL served to the browser. Empty disables the Login button. |
| `DOCROOT_OIDC_CLIENT_ID` | *(empty)* | Public client ID for the browser authorization-code + PKCE flow. |
| `DOCROOT_COOKIE_SECURE` | `false` | Set `true` on HTTPS deployments. |
| `DOCROOT_LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `DOCROOT_ZIP_MAX_FILES` | `500` | Maximum files in an uploaded ZIP. |
| `DOCROOT_ZIP_MAX_EXTRACTED_MB` | `500` | Maximum extracted ZIP size in MB. |

---

## Volume

Mount a single host directory at `/data`.
All data is stored there; the container is stateless.

```yaml
volumes:
  - /your/host/path:/data
```

---

## Kubernetes

The nginx image accepts two environment variables to control where
it routes API requests.  This is needed when the container hostname
`api` is not resolvable (e.g. single-pod deployments where both
containers share a network namespace):

| Variable | Default | Description |
|---|---|---|
| `API_HOST` | `api` | Hostname or IP of the FastAPI container. Set to `localhost` for same-pod k8s deployments. |
| `API_PORT` | `8000` | TCP port of the FastAPI container. |

**Single-pod (sidecar) deployment:** Both containers share the pod
network namespace, so `localhost` resolves to the API container:

```yaml
containers:
  - name: accelerator
    image: ghcr.io/exhuma/docroot/nginx:latest
    env:
      - name: API_HOST
        value: localhost
  - name: api
    image: ghcr.io/exhuma/docroot/backend:latest
```

**Multi-pod deployment (separate Deployments + Service):** Set
`API_HOST` to the Kubernetes service name that fronts the API pods:

```yaml
env:
  - name: API_HOST
    value: docroot-api  # name of the k8s Service for the backend
```

---

## OIDC Authentication

Docroot uses a **two-client** architecture:

- **Back-end (resource server)** — validates Bearer tokens via
  JWKS.  No user redirect; pure JWT verification.
- **Front-end (public client)** — drives the browser
  [Authorization Code + PKCE](https://oauth.net/2/pkce/) flow
  via `oidc-client-ts`.

Configure both clients for every IDP:

```shell
# Back-end: where to fetch signing keys, and the expected audience
DOCROOT_OAUTH_JWKS_URL=https://<idp>/.well-known/jwks.json
DOCROOT_OAUTH_AUDIENCE=<api-audience>

# Front-end: issuer and public client id
DOCROOT_OIDC_ISSUER=https://<idp>
DOCROOT_OIDC_CLIENT_ID=<public-client-id>
```

Register `https://<your-host>/oidc-callback` as the redirect
URI at your IDP.  No client secret is needed (PKCE only).

### Audience validation

`DOCROOT_OAUTH_AUDIENCE` must match the `aud` claim in the
access token.  This is the trickiest part and differs between
IDPs — see the provider-specific sections below.

### JWKS key rotation

The backend fetches the JWKS endpoint automatically when an
unknown `kid` arrives.  Standard IDP key rotation needs no
operator action.

---

## Keycloak

### 1. Create a realm

In the Keycloak admin console, create a realm (e.g. `docroot`).

### 2. Back-end client (confidential)

1. **Clients → Create client**; Client ID: `docroot-api`
2. Client authentication: **ON**; Service accounts: **ON**

```shell
DOCROOT_OAUTH_JWKS_URL=https://keycloak.example.com/realms/docroot/protocol/openid-connect/certs
DOCROOT_OAUTH_AUDIENCE=docroot-api
```

### 3. Front-end client (public)

1. **Clients → Create client**; Client ID: `docroot-ui`
2. Client authentication: **OFF**
3. Valid redirect URIs: `https://docroot.example.com/oidc-callback`
4. Web origins: `https://docroot.example.com`

```shell
DOCROOT_OIDC_ISSUER=https://keycloak.example.com/realms/docroot
DOCROOT_OIDC_CLIENT_ID=docroot-ui
```

### 4. Roles

Create realm roles (e.g. `docroot-editor`) under
**Realm roles → Create role** and assign them to users via
**Users → Role mappings**.  Reference the exact role name in
`namespace.toml` ACL entries.

The Keycloak role extractor reads `realm_access.roles` and
`resource_access.<client_id>.roles` from the token.

### Getting the audience into the token

Keycloak does **not** add an `aud` claim for the back-end
client by default.  Two approaches:

**Transparent (role-based):** When a user is assigned a role
that is *scoped to* `docroot-api`, Keycloak automatically
includes `docroot-api` in the `aud` claim.  No mapper needed —
assigning the role is enough.  The trade-off is that audience
presence is tied to role assignment.

**Explicit (audience mapper):** Add a *Hardcoded audience*
mapper on the `docroot-ui` client:
`Clients → docroot-ui → Client scopes → dedicated →
Add mapper → Hardcoded audience → Included audience: docroot-api`.
This guarantees `aud` is always present regardless of roles.
The trade-off is a small amount of manual configuration.

---

## Microsoft Entra ID (Azure AD)

### 1. Register an application

1. **Azure AD → App registrations → New registration**
2. Redirect URI type: **Single-page application (SPA)**;
   value: `https://docroot.example.com/oidc-callback`
3. Note the **Application (client) ID** and **Directory
   (tenant) ID**.

### 2. Expose an API

Under **Expose an API**, set the **Application ID URI**
(e.g. `api://<client-id>`).
This becomes your `DOCROOT_OAUTH_AUDIENCE`.

> **Token version:** Entra ID issues v1 tokens by default.
> In the app **Manifest**, set
> `"accessTokenAcceptedVersion": 2` to get v2 tokens; the
> JWKS URL below only works with v2.

```shell
DOCROOT_OAUTH_JWKS_URL=https://login.microsoftonline.com/<tenant-id>/discovery/v2.0/keys
DOCROOT_OAUTH_AUDIENCE=api://<client-id>
DOCROOT_OIDC_ISSUER=https://login.microsoftonline.com/<tenant-id>/v2.0
DOCROOT_OIDC_CLIENT_ID=<client-id>
```

---

## Google

```shell
DOCROOT_OAUTH_JWKS_URL=https://www.googleapis.com/oauth2/v3/certs
DOCROOT_OAUTH_AUDIENCE=<google-client-id>
DOCROOT_OIDC_ISSUER=https://accounts.google.com
DOCROOT_OIDC_CLIENT_ID=<google-client-id>
```

In the [Google Cloud Console](https://console.cloud.google.com):
**APIs & Services → Credentials → OAuth client ID**;
application type **Web application**; add
`https://docroot.example.com/oidc-callback` as an authorised
redirect URI.

---

## Providers without native OIDC support

GitHub and Facebook do not expose a standards-compliant OIDC
endpoint for browser user logins.  To use them, run an
OIDC-compliant proxy such as
[Keycloak](https://www.keycloak.org/) (identity brokering),
[Dex](https://dexidp.io/), or
[Zitadel](https://zitadel.com/) in front of them and point
Docroot at the proxy.

---

## Namespace ACL

Each namespace stores a `namespace.toml` file:

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

| Field | Description |
|---|---|
| `creator` | `sub` claim of the creator. Only this user may delete the namespace. |
| `versioning` | Sort scheme: `semver`, `calver`, `pep440`, or a custom regex. |
| `access.public_read` | Allow unauthenticated read. |
| `access.roles[].role` | Exact role name from the JWT. |
| `access.roles[].read` / `.write` | Grant read / write access. |

> **Alpha limitation:** ACL roles cannot yet be managed via
> the API.  Edit `namespace.toml` directly on the host.

---

## Data Layout

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
                …
          latest -> <version>   (symlink)
```

---

## Development Setup

```bash
task gen-token -- --sub alice --roles editor
```

See `README.md` and `Taskfile.yml` for the full local dev
workflow.

### Local Keycloak overlay

```bash
docker compose \
  -f deploy/compose/docker-compose.yml \
  -f deploy/compose/docker-compose.dev.yml \
  up
```

Both the browser and the API container reach Keycloak at
`http://keycloak.127.0.0.1.nip.io:8080`.

Pre-loaded accounts:

| Username | Password | Role |
|---|---|---|
| `alice` | `alice` | `docroot-editor` |
| `bob` | `bob` | `docroot-reader` |

Admin: `http://keycloak.127.0.0.1.nip.io:8080/admin`
(admin / admin)

> **For local development only. Do not expose to the internet.**
