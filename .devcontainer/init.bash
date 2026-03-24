#!/usr/bin/env bash
set -euo pipefail

# Install task runner
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d

# Install uv and make it available for the rest of this script
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Install CLI tools
uv tool install pre-commit
uv tool install ruff

# Install project dependencies
(cd apps/backend && uv sync --all-extras)
npm --prefix apps/frontend install

# Install git pre-commit hooks
pre-commit install
