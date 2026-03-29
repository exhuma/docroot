# decision: route docstring separator — `---` vs bare `\r`

**Source kit:** `stack-fastapi-vuetify`

## Context

There is a direct conflict between the project's own style
guide and the `stack-fastapi-vuetify` kit on how to separate
user-facing API docs from internal developer notes inside
route handler docstrings.

## The conflict

**`docs/developer/code-style.md` (current project rule):**
> Separate internal developer notes with a line containing
> `---`.

**`stack-fastapi-vuetify` kit:**
> Route handler docstrings have two sections separated by
> a bare `\r` character (carriage return, not `---`).

All route files (`namespaces.py`, `projects.py`,
`versions.py`, `me.py`, etc.) currently use `---`.

## Why the `\r` separator matters

The kit uses a carriage-return as a machine-readable split
point. Sphinx autodoc tooling can strip everything after `\r`
before rendering public API reference, so internal
implementation notes never appear in published documentation.

The current `---` renders as a Markdown horizontal rule and
is visible in both the OpenAPI `/docs` page and in any
Sphinx autodoc output.

## Options

**A — Adopt the kit rule (`\r` separator)**
- Update `docs/developer/code-style.md`
- Update all route handler docstrings (≈ 30–40 docstrings)
- Configure autodoc post-processor to strip the section

Benefit: internal notes never appear in public API docs.

**B — Keep the project rule (`---`), document the deviation**
- Add a note to `docs/developer/code-style.md` recording the
  deliberate divergence from the kit
- Mitigate by not using `automodule` on route files, or by
  manually curating RST pages instead of using autodoc

Benefit: no change to existing code; `---` is more
human-readable in raw source.

**C — Hybrid: keep `---` as source, add autodoc filter**
- Write a custom Sphinx extension that strips content after
  `---` in route docstrings before autodoc renders it

## Decision needed

Choose option A, B, or C **before implementing**. Record the
decision in `contract.md` under `## Developer conventions`.
