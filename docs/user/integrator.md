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

### Setting up for unattended uploads

Before an unattended pipeline can upload, a human operator
must do the following once:

1. Create the namespace (via the UI or API with a human token).
2. In the namespace ACL, add the confidential client's role
   with write access.

Once a role that maps to the confidential client's token has
write access, uploads work without any further manual steps.
Projects are created automatically on first upload.

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

### Upload documentation

The project is created automatically on first upload.
The namespace must already exist.

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

The ZIP must contain `index.html` at the archive root.

---

## Access Control

ACL roles can be managed via the API or through the
**Manage Access** button (shield icon) on each namespace
in the UI.  Write access to the namespace is required.

```bash
# Read current ACL
curl -H "Authorization: Bearer $TOKEN" \
  https://docroot.example.com/api/namespaces/myns/acl

# Grant a role write access
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"read": true, "write": true}' \
  https://docroot.example.com/api/namespaces/myns/acl/roles/my-role

# Revoke a role
curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  https://docroot.example.com/api/namespaces/myns/acl/roles/my-role
```

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
