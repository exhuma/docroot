# Background

## Why Docroot?

For years our team hosted internal documentation the simple
way: an Apache directory listing served over the network, with
uploads done via SCP.  It worked well for a small team.  It
required no infrastructure beyond a web server, and any static
documentation generator would do.

As the team and its documentation grew, limitations became
apparent.  There was no access control: anyone on the network
could read everything.  There was no way to delegate upload
access to a specific project without opening up the entire
server.  And there was no way to host documentation for
multiple teams with independent ownership.

Hosted services like Read the Docs were not an option —
our documentation must remain on-site and under our control.

We built a first internal version (the original "docroot") that
added a small Python API, a browsable index, and an
Elasticsearch-backed full-text search.  The search never worked
reliably, and the UI was difficult to navigate.  More
importantly, the lack of authentication and namespacing meant
other teams inside the organisation could not adopt it safely.

This project was built to close those gaps.

---

## Design Goals

**Modern, navigable UI** — A clean interface for browsing
across namespaces, projects, versions, and locales without
needing to know URLs in advance.

**Authentication and RBAC** — Every write operation requires
a valid token.  Each namespace carries an ACL that maps
identity-provider roles to read and write access.  The current
release targets Keycloak because that is what our team runs.
Local authentication was deliberately excluded: it would not
add value for us, and every additional authentication path
widens the attack surface.

**Namespacing** — Teams can own their own namespace with an
independent ACL.  One team's documentation is not visible to
another unless access is explicitly granted.

**Zero tool lock-in** — The only requirement for a
documentation archive is a ZIP file with an `index.html` at
its root.  Almost every static documentation generator already
produces exactly that: MkDocs, Sphinx, TypeDoc, JavaDoc,
VitePress, Pelican, Eleventy, and many others.  A single
Docroot instance can host JavaDoc for one project, Sphinx for
another, and hand-crafted HTML for a third — without caring
which tool produced it.

---

## MVP Status and Known Gaps

This release is an MVP.  It is in production use by our team
and stable enough for daily use, but several rough edges
remain:

- Some API error responses are not yet surfaced clearly in
  the UI.
- Some dialogs require a mouse click to confirm rather than
  pressing Enter.
- There is no lightweight full-text search across
  documentation content.
- Version lists are not yet sorted by semantic or calendar
  versioning rules.
- There is no visual indicator when you are reading an older
  version rather than `latest`.

Some of these will be addressed as they become a priority for
our team.  Others may never be implemented if they turn out
not to matter in practice.
