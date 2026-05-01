---
name: setup-dev-env
description: Set up the development environment for the project. Use when starting work on the project, when dependencies are out of sync, or to fix environment setup failures.
---

# Setup Development Environment

Ensure Python, `uv`, and `Trunk` match this template, then install dependencies.

## Workflow

1. **Validate tooling** — Read `.python-version` in the repo root; the active interpreter should match. Ensure `uv` and `trunk` are on `PATH` (on macOS: `brew install trunk-io uv` if missing).
2. **Install dependencies** — From the repo root, run `make setup` (see [CLAUDE.md](../../../CLAUDE.md) for `uv` / `make` conventions). This runs `dev/setup.sh`, which creates the venv and syncs dependencies.
3. **Trunk artifacts** — Run `trunk install` so managed linters and formatters are present.
4. **Optional verification** — Invoke the `verifier` subagent ([../../agents/verifier.md](../../agents/verifier.md)) if you need a full build, lint, and test pass after a broken or fresh environment.

## Success criteria

- Dependencies install without errors into the project virtual environment.
- `uv` and `trunk` are available; Python matches `.python-version`.
