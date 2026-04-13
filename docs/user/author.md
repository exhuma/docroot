# Author Guide

This guide is for people who want to publish documentation to a
Docroot instance via the web UI.

---

## Prerequisites

- An account with **write** access to the target namespace.
- A ZIP archive of your documentation.

---

## 1. Prepare Your Archive

The ZIP file must contain `index.html` at the **archive root**.
That is the only hard requirement.

A minimal archive:

```
docs.zip
└── index.html
```

---

## 2. Log In

Click **Login** in the top-right toolbar and authenticate with
your identity provider.  Write-access controls appear once you
are logged in.

---

## 3. Create a Namespace (first time only)

On the home page click **New namespace** and enter a name.

Two visibility flags control access:

- **Browsable** (default: on) — the namespace and its
  projects appear in the listing for everyone.  Visitors
  still need appropriate permission to open the
  documentation itself.
- **Public read** — anyone can browse, open, and read the
  documentation without logging in.  Enable this for fully
  public documentation.

---

## 4. Create a Project (first time only)

Navigate into the namespace and click **New project**.

---

## 5. Upload a Version

1. Navigate into the project.
2. Click **Upload**.
3. Select your ZIP file.
4. Enter the version string (e.g. `1.0.0` or `main`).
5. Select the locale (e.g. `en`).
6. Optionally enter a **Ref / tag** name (e.g. `latest`) to
   attach a named pointer to this version.  Leave the field
   blank to upload without any ref.
7. Click **Upload**.

The version appears in the list once processing completes.

---

## Refs (Tags)

A **ref** is a named pointer to a specific version, similar to
a git tag or a Docker tag.  Refs are stored in the project's
`refs/` directory as symlinks.

- Any ref name is valid.  `latest` is a conventional name
  with no special meaning beyond convention.
- Multiple refs can point to the same version.
- Refs can be created, updated, or deleted independently of
  the version through the **Manage refs** button (tag icon)
  on any version row.
- A visitor who navigates to a project using a ref URL
  (e.g. `.../ref/latest/en/`) is served the documentation
  for whichever version the ref currently points to.
- If a version is deleted while a ref still points to it,
  the ref is kept but returns a 404 until reassigned.
