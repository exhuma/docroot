# Integrator Guide

This guide is for scripts, CI/CD pipelines, and other
programmatic consumers of the Docroot REST API.

---

## Authentication

### Client-credentials grant

Use the OAuth 2.0 client-credentials grant to obtain a token
without user interaction.

```bash
TOKEN=$(curl -s -X POST \
  "https://idp.example.com/realms/myrealm/\
protocol/openid-connect/token" \
  -d grant_type=client_credentials \
  -d client_id=my-ci-client \
  -d client_secret=MY_SECRET \
  | jq -r .access_token)
```

> **Known limitation:** With a client-credentials token the
> service account may not share roles with human users, so ACL
> entries created by that token may not grant access to
> end-users.  Use a device-code flow to act on behalf of a
> human user when you need cross-user role coverage.

---

## Common API Operations

### Create a namespace

```bash
curl -s -X POST \
  "https://docroot.example.com/api/namespaces" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "myns", "public_read": false}'
```

### Create a project

```bash
curl -s -X POST \
  "https://docroot.example.com/api/namespaces/myns/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "myproject"}'
```

### Upload documentation

```bash
curl -s -X POST \
  "https://docroot.example.com/api/namespaces/myns/\
projects/myproject/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@docs.zip" \
  -F "version=1.0.0" \
  -F "locale=en" \
  -F "latest=true"
```

The ZIP must satisfy:

- Contains `index.html` at the archive root.
- No path-traversal (`..`) entries, no symlinks.
- ≤ 500 files and ≤ 500 MB extracted.

---

## Access Control

ACL roles can be managed via the API or through the
**Manage Access** button (shield icon) on each namespace
in the UI.  Write access to the namespace is required.

```bash
# Read current ACL
curl -H "Authorization: Bearer $TOKEN" \
  https://docroot.example.com/api/namespaces/myns/acl

# Grant a role read access
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"read": true, "write": false}' \
  https://docroot.example.com/api/namespaces/myns/acl/roles/my-role

# Revoke a role
curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  https://docroot.example.com/api/namespaces/myns/acl/roles/my-role
```

> **Note:** With a client-credentials token the service account
> may not share roles with human users.  Use a device-code flow
> to act on behalf of a human user when you need cross-user role
> coverage.

---

## REST API Reference

The full API reference is available at `/api/docs` (Swagger UI)
when the backend is running.

### Key endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/namespaces` | List visible namespaces |
| `POST` | `/api/namespaces` | Create a namespace |
| `DELETE` | `/api/namespaces/{ns}` | Delete (creator only) |
| `GET` | `/api/namespaces/{ns}/acl` | Read ACL |
| `PUT` | `/api/namespaces/{ns}/acl/roles/{role}` | Add/update role |
| `DELETE` | `/api/namespaces/{ns}/acl/roles/{role}` | Remove role |
| `PATCH` | `/api/namespaces/{ns}/owner` | Transfer ownership |
| `GET` | `/api/namespaces/{ns}/projects` | List projects |
| `POST` | `/api/namespaces/{ns}/projects` | Create a project |
| `GET` | `/api/namespaces/{ns}/projects/{p}/versions` | List versions |
| `POST` | `/api/namespaces/{ns}/projects/{p}/upload` | Upload version |
| `GET` | `/api/namespaces/{ns}/projects/{p}/resolve/{v}/{l}` | Resolve |
| `GET` | `/api/oidc-config` | OIDC public client config |
