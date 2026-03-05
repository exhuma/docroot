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

1. Click the **Login** button in the top-right corner of any page.
2. Paste your Bearer token.
3. Click **Login** to store the token for the current session.

The token is stored in the browser's `localStorage` and persists
across page refreshes.

To log out, click the key icon and choose **Logout**.

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
