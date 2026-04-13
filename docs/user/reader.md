# Reader Guide

This guide covers browsing and reading documentation on a
Docroot instance.

---

## Browsing

The home page lists all namespaces you can access.  Click a
namespace to see its projects, then click a project to see its
versions.  Click a version to open the documentation viewer.

### Refs (named tags)

A project can have any number of named **refs** (tags) that
point to a specific version — similar to git tags or Docker
tags.  `latest` is a conventional ref name with no special
meaning beyond that convention.

To navigate directly to a ref, use the ref URL path:

```
/{namespace}/{project}/ref/{refname}/{locale}/
```

Refs are managed by authors via the **Manage refs** button
(tag icon) on the version list.

### Locale variants

If a version has been uploaded in multiple languages (e.g.
`en`, `fr`, `de`) the viewer picks the closest match to your
browser's preferred language.  If no match is found it falls
back to the first available locale.

---

## Authentication

Some namespaces are protected.  You must log in before their
content becomes visible.

### OIDC login

Click **Login** in the top-right toolbar.  You will be
redirected to the identity provider.  After authenticating
you are redirected back and logged in automatically.  Your
display name appears in the toolbar.  Click **Logout** to
end the session.

Silent refresh runs in the background; you will not be
interrupted during normal use.  If the session expires the UI
resets to the unauthenticated state automatically.
