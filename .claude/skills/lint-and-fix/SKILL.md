---
name: lint-and-fix
description: Run linters and fix violations, formatting errors, or style mismatches using Trunk. Use when code quality checks fail, before submitting PRs, or to repair "broken" linting states.
---

# Lint and Fix Loop: Trunk

## Purpose

An autonomous loop for the agent to identify, fix, and verify linting and formatting violations using [Trunk](https://trunk.io).

## GitHub CI parity (Trunk Check)

The **Trunk Check** workflow (`.github/workflows/trunk_check.yml`) runs the same tools as `make format` / `make lint` (Ruff format + lint, Prettier, Pylint, Bandit, etc.; see `.trunk/trunk.yaml`). Install the Trunk CLI so local `make format` and `make lint` match CI.

**If Trunk is not installed:** run formatters and linters in layers so results stay close to CI:

1. **`make format` equivalent (Python):** `uv run ruff format <paths>` (or `ruff format .` when appropriate).
2. **Markdown / other Prettier targets:** `npx prettier@<version> --write <files>` (match the Prettier version in `.trunk/trunk.yaml`, e.g. 3.8.3).
3. **Static checks without Trunk:** `uv run ruff check <paths>`, `uv run pyright`, `uv run pylint` on changed modules, `uv run bandit -r` on changed packages, and `uv run vulture` / `make dead-code` for dead code.

## Loop Logic

1. **Identify**: Run **`make format --dry-run`** (if available) or **`make lint`** (`trunk check -a`) to list violations. Format drift often shows as “unformatted file” (Ruff/Prettier) in Trunk’s output.
2. **Analyze**: Examine the output from Trunk, focusing on the file path, line number, and error message.
3. **Fix**:
   - For formatting issues, run **`make format`** (`trunk fmt -a`), or `uv run ruff format` + `npx prettier --write` as above when Trunk is missing.
   - For linting violations, apply the minimum necessary change to the source code to resolve the error.
   - Resolve findings by changing code, types, imports, or structure—not with blanket suppressions (see **Constraints**).
4. **Verify**:
   - Re-run **`make format`** then **`make lint`** (Ruff, **Pyright**, Pylint, security tools, Prettier via Trunk).
   - Run **`make dead-code`** (Vulture; reads `[tool.vulture]` in `pyproject.toml`) so unused code is caught alongside lint—fix findings by removing dead code or tightening tests/mocks, not by weakening Vulture.
   - For type-only triage, `uv run pyright` also reads `pyproject.toml` `[tool.pyright]`; prefer Trunk for CI parity when available.

## Constraints

- Do not silence Trunk/Ruff/Pyright/Pylint/Semgrep findings with blanket inline suppressions (`# noqa`, `# type: ignore`, `# pylint: disable`, file-wide `ruff: noqa`, Trunk inline disables).
- **Bandit** (`B404` / `B603`): Prefer refactoring so `subprocess` is unnecessary. When the design requires spawning a **trusted** helper resolved from `PATH` (for example `git` via `shutil.which`), narrow **`# nosec B404`** on the import and **`# nosec B603`** on the specific call—document why execution is bounded—rather than disabling Bandit project-wide.
- Do not broaden project configuration to hide violations (for example new `[tool.ruff.lint]` ignores, Pyright `report*` toggles, or Pylint disables) unless the user explicitly asked for that policy change.
- Prefer **`make format`** before **`make lint`** so formatting noise does not mask real issues.
- If fixes fail after genuine attempts, stop and surface the finding for a human to decide—do not add suppressions to make CI green.

## Termination Criteria

- No more errors reported by `make lint` after **`make format`** (or equivalent Ruff + Prettier passes).
- Reached max iteration limit (default: 5).

## Examples

### Scenario: Fixing a formatting violation

1. `make lint` reports formatting issues in `src/your_package/main.py`.
2. Agent runs `make format`.
3. `make lint` now passes.

## Resources

- [Trunk Documentation](https://docs.trunk.io/): Official documentation for the Trunk CLI.
