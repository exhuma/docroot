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
6. Tick **Set as latest** if this upload should become
   the default version.
7. Click **Upload**.

The version appears in the list once processing completes.

---

## Managing "Latest"

The version tagged **latest** is the one opened when a visitor
does not request a specific version.  Only one version per
namespace/project/locale combination can be `latest` at a time.
Uploading with **Set as latest** re-tags automatically.
