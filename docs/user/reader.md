# Reader Guide

This guide covers browsing and reading documentation on a
Docroot instance.

---

## Browsing

The home page lists all namespaces you can access.  Click a
namespace to see its projects, then click a project to see its
versions.  Click a version to open the documentation viewer.

### Latest version

Each project can mark one version as **latest**.  Navigating
to a project without specifying a version opens the one tagged
`latest`.

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
