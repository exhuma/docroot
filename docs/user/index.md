# User Guide

This guide covers how to browse and upload documentation using
the Docroot UI and REST API.

---

## Browsing Documentation

Open the application in a browser. The home page lists all
namespaces you have access to. Select a namespace to see its
projects, then select a project to see available versions.

Select a version and a locale to open the documentation in the
embedded viewer. If the exact locale you requested is unavailable,
Docroot will automatically fall back to English (`en`), then to
any available locale. A notice is shown when a fallback is used.

---

## Authentication

Protected operations (creating namespaces or projects, uploading
versions) require a Bearer token issued by the configured OIDC
provider.

### OIDC login (recommended for browser use)

1. Click the **Login** button in the top-right corner.
2. If OIDC is configured, click **Login with OIDC** to be
   redirected to the identity provider.
3. After authenticating, you are redirected back and logged in
   automatically.

### Manual token entry (development / CLI)

If OIDC is not configured, or for local development:

1. Click the **Login** button.
2. Paste your Bearer token into the text field.
3. Click **Set token**.

To log out, click the login icon and choose **Logout** (or
**Clear token**).

---

## Uploading Documentation

Navigate to a project's version list, then click **Upload**
(visible only when authenticated with write access).

Fill in:

- **Version** — version string for the upload
  (e.g. `1.0.0`, `2024.03.01`)
- **Locale** — two-letter locale code (e.g. `en`, `fr`, `de`)
- **ZIP file** — ZIP archive containing a top-level `index.html`
- **Set as latest** — check to make this version the default

The ZIP must satisfy the following constraints:

- Contains `index.html` at the archive root
- No path-traversal (`..`) entries
- No symlink entries
- No more than 500 files
- No more than 500 MB extracted size

---

## Automated Uploads via REST API (CI/CD)

For automated pipelines, use the OAuth2 client-credentials
grant to obtain a token and upload in a single script.

### Step 1 — Obtain a token

```bash
TOKEN=$(curl -s -X POST \
  "https://idp.example.com/realms/myrealm\
/protocol/openid-connect/token" \
  -d grant_type=client_credentials \
  -d client_id=my-ci-client \
  -d client_secret=MY_SECRET \
  | jq -r .access_token)
```

### Step 2 — Create a namespace (first time only)

```bash
curl -s -X POST \
  "https://docroot.example.com/api/namespaces" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "myns", "public_read": false}'
```

### Step 3 — Create a project (first time only)

```bash
curl -s -X POST \
  "https://docroot.example.com/api/namespaces/myns/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "myproject"}'
```

### Step 4 — Upload documentation

```bash
curl -s -X POST \
  "https://docroot.example.com/api/namespaces/myns\
/projects/myproject/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@docs.zip" \
  -F "version=1.0.0" \
  -F "locale=en" \
  -F "latest=true"
```

> **Known limitation (alpha):** When using a client-credentials
> flow, the service account may not have any roles matching the
> human users of the system.  ACL entries created via this flow
> may therefore grant access only to the service account's own
> roles, not to end-users.  Use a device-code flow to act on
> behalf of a human user if you need role-based access for other
> people.

---

## Access Control (ACL)

Access to each namespace is governed by a `namespace.toml` file
on the server. Roles in that file are matched exactly against the
roles present in your JWT.

> **Alpha limitation:** ACL roles cannot yet be granted or revoked
> via the API. Ask your operator to update `namespace.toml`
> directly if you need access changes.

Example `namespace.toml`:

```toml
creator = "alice"

[access]
public_read = false

[[access.roles]]
role = "docroot-editor"
read = true
write = true
```

---

## Using the REST API

The full API reference is available at `/api/docs` (Swagger UI)
when the backend is running.

All write endpoints require an `Authorization: Bearer <token>`
header. See the [operator guide](../operator/index.md) for
authentication setup.

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/namespaces` | List visible namespaces |
| `POST` | `/api/namespaces` | Create a namespace |
| `DELETE` | `/api/namespaces/{ns}` | Delete a namespace (creator only) |
| `PUT` | `/api/namespaces/{ns}/acl/roles/{role}` | Add/update ACL role |
| `DELETE` | `/api/namespaces/{ns}/acl/roles/{role}` | Remove ACL role |
| `GET` | `/api/namespaces/{ns}/projects` | List projects |
| `POST` | `/api/namespaces/{ns}/projects` | Create a project |
| `GET` | `/api/namespaces/{ns}/projects/{p}/versions` | List versions |
| `POST` | `/api/namespaces/{ns}/projects/{p}/upload` | Upload version |
| `GET` | `/api/namespaces/{ns}/projects/{p}/resolve/{v}/{l}` | Resolve version/locale |
| `GET` | `/api/oidc-config` | Get OIDC public client config |
