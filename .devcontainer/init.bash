#!/usr/bin/env bash
set -euo pipefail


echo "==> Installing Task (taskfile.dev) ..."
# Install into ~/.local/bin and ensure it is on the PATH for
# subsequent steps in this script and for the dev shell.
export PATH="${HOME}/.local/bin:${PATH}"
mkdir -p "${HOME}/.local/bin"
[ ! -f ${HOME}/.local/bin/task ] && sh -c "$(curl --location https://taskfile.dev/install.sh)" \
    -- -d -b "${HOME}/.local/bin"

echo "==> Installing backend dependencies (uv sync) ..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install CLI tools
uv tool install pre-commit
uv tool install ruff

# Install project dependencies
(cd apps/backend && uv sync --all-extras)
npm --prefix apps/frontend install

echo "==> Installing pre-commit hooks ..."
pre-commit install
