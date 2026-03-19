# User Guide

## Browsing documentation

Open the application in a browser.  The home page lists all
namespaces you have read access to.  Select a namespace →
project → version to open the documentation in the embedded
viewer.

If the exact locale you requested is unavailable, Docroot falls
back to English (`en`) and then to any available locale.  A
notice is shown when a fallback is used.

---

## Authentication

Protected operations (creating namespaces, uploading versions)
require a Bearer token.

### OIDC login

When OIDC is configured, a **Login** button is visible in the
toolbar.  Click it to be redirected to the identity provider.
After authenticating you are redirected back and logged in
automatically.  Your display name and avatar appear in the
toolbar.  Click **Logout** to end the session.

Silent refresh runs in the background; you will not be
interrupted during normal use.  If the session expires the UI
resets to the unauthenticated state automatically.

### Manual token (development)

Click the **Set token** button (visible only in development
builds when OIDC is also enabled, or always when OIDC is
disabled), paste a Bearer token, and click **Set token**.

---

## Automated uploads (CI/CD)

Use the
[OAuth 2.0 client credentials grant](https://oauth.net/2/grant-types/client-credentials/)
to obtain a token without user interaction.

### 1. Obtain a token

```bash
TOKEN=$(curl -s -X POST \
  "https://idp.example.com/realms/myrealm/protocol/openid-connect/token" \
  -d grant_type=client_credentials \
  -d client_id=my-ci-client \
  -d client_secret=MY_SECRET \
  | jq -r .access_token)
```

### 2. Create a namespace (first time only)

```bash
curl -s -X POST \
  "https://docroot.example.com/api/namespaces" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "myns", "public_read": false}'
```

### 3. Create a project (first time only)

```bash
curl -s -X POST \
  "https://docroot.example.com/api/namespaces/myns/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "myproject"}'
```

### 4. Upload documentation

```bash
curl -s -X POST \
  "https://docroot.example.com/api/namespaces/myns/projects/myproject/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@docs.zip" \
  -F "version=1.0.0" \
  -F "locale=en" \
  -F "latest=true"
```

The ZIP must satisfy:

- Contains `index.html` at the archive root
- No path-traversal (`..`) entries, no symlinks
- ≤ 500 files and ≤ 500 MB extracted

> **Known limitation (alpha):** With a client-credentials
> token the service account may not share roles with human
> users, so ACL entries created by that token may not grant
> access to end-users.  Use a device-code flow to act on
> behalf of a human user when you need cross-user role
> coverage.

---

## Access control

Access is governed by `namespace.toml` on the server.  Roles
are matched exactly against the roles in your JWT.

> **Alpha limitation:** ACL roles cannot yet be managed via
> the API.  Ask your operator to update `namespace.toml`
> directly.

---

## REST API reference

The full API reference is available at `/api/docs` (Swagger UI)
when the backend is running.

### Key endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/namespaces` | List visible namespaces |
| `POST` | `/api/namespaces` | Create a namespace |
| `DELETE` | `/api/namespaces/{ns}` | Delete (creator only) |
| `PUT` | `/api/namespaces/{ns}/acl/roles/{role}` | Add/update ACL role |
| `DELETE` | `/api/namespaces/{ns}/acl/roles/{role}` | Remove ACL role |
| `GET` | `/api/namespaces/{ns}/projects` | List projects |
| `POST` | `/api/namespaces/{ns}/projects` | Create a project |
| `GET` | `/api/namespaces/{ns}/projects/{p}/versions` | List versions |
| `POST` | `/api/namespaces/{ns}/projects/{p}/upload` | Upload version |
| `GET` | `/api/namespaces/{ns}/projects/{p}/resolve/{v}/{l}` | Resolve version/locale |
| `GET` | `/api/oidc-config` | Get OIDC public client config |
