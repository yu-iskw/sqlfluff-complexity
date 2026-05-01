---
name: lint-and-fix
description: Run linters and fix violations, formatting errors, or style mismatches using Trunk. Use when code quality checks fail, before submitting PRs, or to repair "broken" linting states.
---

# Lint and Fix Loop: Trunk

## Purpose

An autonomous loop for the agent to identify, fix, and verify linting and formatting violations using [Trunk](https://trunk.io).

## Loop Logic

1. **Identify**: Run `make lint` (which executes `trunk check -a`) to list current violations.
2. **Analyze**: Examine the output from Trunk, focusing on the file path, line number, and error message.
3. **Fix**:
   - For formatting issues, run `make format` (which executes `trunk fmt -a`).
   - For linting violations, apply the minimum necessary change to the source code to resolve the error.
   - Resolve findings by changing code, types, imports, or structure—not with suppressions (see **Constraints**).
4. **Verify**: Re-run `make lint` (Ruff, **Pyright**, Pylint, and security tools via Trunk).
   - For type-only triage, `uv run pyright` also reads `pyproject.toml` `[tool.pyright]`; prefer Trunk for CI parity.
   - If passed: Move to the next issue or finish if all are resolved.
   - If failed: Analyze the new failure and repeat the loop.

## Constraints

- Do not silence Trunk/Ruff/Pyright/Pylint/Bandit/Semgrep findings with inline suppressions (for example `# noqa`, `# type: ignore`, `# pylint: disable`, `ruff: noqa`, file-level `# ruff: noqa`, or Trunk inline disable comments).
- Do not broaden project configuration to hide violations (for example new `[tool.ruff.lint]` ignores, Pyright `report*` toggles, or Pylint disables) unless the user explicitly asked for that policy change.
- Prefer `make format` for auto-fixable style; otherwise fix the underlying issue the linter reports.
- If fixes fail after genuine attempts, stop and surface the finding for a human to decide—do not add suppressions to make CI green.

## Termination Criteria

- No more errors reported by `make lint`.
- Reached max iteration limit (default: 5).

## Examples

### Scenario: Fixing a formatting violation

1. `make lint` reports formatting issues in `src/your_package/main.py`.
2. Agent runs `make format`.
3. `make lint` now passes.

## Resources

- [Trunk Documentation](https://docs.trunk.io/): Official documentation for the Trunk CLI.
