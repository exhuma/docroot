# Release Process

Releases are version-controlled and tag-driven. A `v*` tag on `main`
is the single source of truth that triggers image publication. No
images are published from regular branch pushes.

## Versioning

This project follows [Semantic Versioning](https://semver.org/). All
version tokens must be kept consistent across both package manifests:

- `apps/backend/pyproject.toml` — `version` field under `[project]`
- `apps/frontend/package.json` — `version` field

Never bump one without the other.

## Cutting a Release

The `task release` command handles the full release flow in one step:
it validates the version string, bumps both manifests, commits, tags,
and pushes the tag to `origin`.

```console
task release VERSION=1.2.3
```

**Prerequisites:**

- Working tree must be clean (no staged or unstaged changes).
- You must be on the `main` branch.
- The version must be a valid semver string (e.g. `1.2.3` or
  `1.2.3-rc.1`).

The command will:

1. Validate the version format and branch state.
2. Rewrite the `version` field in `apps/backend/pyproject.toml`.
3. Rewrite the `version` field in `apps/frontend/package.json`.
4. Commit both changes as `chore: release <VERSION>`.
5. Create an annotated tag `v<VERSION>` on that commit.
6. Push `main` and the tag to `origin`.

Pushing the tag triggers the GitHub Actions release workflow, which
builds and publishes the Docker images.

### Bumping without pushing

If you only want to update the version strings locally (e.g. to review
the diff before committing), use:

```console
task release:bump VERSION=1.2.3
```

This writes the new version to both files but does not commit, tag,
or push anything.

## Docker Image Tags

The release workflow (`release.yml`) uses `docker/metadata-action`
to derive tags from the semver tag. A push of `v1.2.3` produces the
following image tags for both `backend` and `nginx`:

| Tag     | Description                        |
|---------|------------------------------------|
| `1.2.3` | Exact release version              |
| `1.2`   | Minor alias (stable patch updates) |
| `1`     | Major alias (stable minor updates) |

Pre-release tags (e.g. `v1.2.3-rc.1`) only produce the full version
tag (`1.2.3-rc.1`). The major and minor aliases are suppressed for
pre-releases to avoid misleading consumers of the `:1` or `:1.2`
aliases.

## Branch Protection

If `main` has branch-protection rules that prevent direct pushes,
`task release` will fail at the `git push origin main` step. In that
case, use the following manual flow:

1. Create a short-lived branch, run `task release:bump VERSION=x.y.z`,
   commit, and merge into `main` via a pull request.
2. Once merged, check out `main`, pull, and run:
   ```console
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

Only the tag push is required to trigger the image build; pushing
`main` is only needed to carry the version bump commit.

## GitHub Release Notes

After the images are published, the workflow automatically creates a
GitHub Release with auto-generated notes derived from the commits
since the previous tag. No manual release notes are required.
