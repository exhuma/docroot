# What is Docroot?

**Docroot** is a lightweight, self-hosted documentation server.
It stores versioned documentation archives (ZIP files containing an
`index.html`) and serves them through a web UI and a REST API.

## Core concepts

| Concept | Description |
|---|---|
| **Namespace** | A top-level grouping — usually matching an organisation or team. |
| **Project** | A single documentation source inside a namespace. |
| **Version** | A snapshot of the documentation for a specific release. |
| **Locale** | A language variant of a version (`en`, `fr`, `de`, …). |

## Getting started

1. **Browse** — the home page lists all namespaces you can access.
   Click a namespace → project → version to open the viewer.
2. **Authenticate** — click **Login** in the top-right corner.
   If OIDC is configured you will be redirected to your identity
   provider.  On return you are logged in automatically.
3. **Upload** — navigate to a project and click **Upload** (visible
   once logged in with write access).  The ZIP must contain an
   `index.html` at its root.
4. **Automate** — use the REST API with an OAuth2
   [client-credentials](https://oauth.net/2/grant-types/client-credentials/)
   token for CI/CD pipelines.  See the User Guide for curl examples.

For deployment instructions see the
[Operator Manual](https://docroot.readthedocs.io/en/latest/operator/).
