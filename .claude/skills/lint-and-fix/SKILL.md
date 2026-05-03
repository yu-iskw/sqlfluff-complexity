---
name: lint-and-fix
description: >
  Run linters and fix violations using Trunk when available; when Trunk is missing,
  run the equivalent tools from the dev environment (see .trunk/trunk.yaml and pyproject.toml)
  so agents still enforce Ruff, Pyright, Pylint, Bandit, and other enabled checks where possible.
---

# Lint and Fix Loop: Trunk + fallback

## Purpose

Identify, fix, and verify lint and format issues. **Prefer Trunk** (`make lint` / `make format`) for parity with CI. **If `trunk` is not installed or `make lint` fails because Trunk is absent**, do not stop: run the **fallback linter battery** below so the same categories of checks still run from the repo’s config files.

Authoritative Trunk configuration: **[`.trunk/trunk.yaml`](../../../.trunk/trunk.yaml)** (enabled linters and pinned versions).

## Loop Logic

1. **Identify**
   - Try **`make lint`** (runs `trunk check -a`).
   - If Trunk is missing or the command fails only because `trunk` is not on `PATH`, switch to **[Fallback: Trunk unavailable](#fallback-trunk-unavailable)** and continue the loop using those commands instead of aborting.

2. **Analyze**: Use file path, line number, and rule id from the active tool (Trunk, Ruff, Pyright, etc.).

3. **Fix**
   - With Trunk: **`make format`** (`trunk fmt -a`) for formatters; otherwise edit source.
   - Without Trunk: use **fallback format** commands (Ruff format, Prettier on docs—see below).
   - Resolve findings by changing code, types, imports, or structure—not with suppressions (see **Constraints**).

4. **Verify**
   - With Trunk: **`make lint`** until clean.
   - Without Trunk: re-run the **full fallback suite** you used in Identify until each configured tier passes or is explicitly **SKIPPED** with reason (missing binary).

## Fallback: Trunk unavailable

Run from the **repository root** after **`make setup`** / **`uv sync --all-extras`** (or equivalent) so `.venv` has dev dependencies.

Use **`uv run <tool>`** or **`.venv/bin/<tool>`** so versions match `uv.lock`. Prefer **`uv run`** when unsure.

### Tier 1 — Python package (must match Trunk’s Python linters)

These map to **enabled** entries under `lint.enabled` in `.trunk/trunk.yaml` that apply to `src/sqlfluff_complexity`:

| Trunk linter             | Fallback command (adjust paths if needed)                                                                                                 |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **ruff** (lint + format) | `uv run ruff format src/sqlfluff_complexity` then `uv run ruff check src/sqlfluff_complexity` — config: [`ruff.toml`](../../../ruff.toml) |
| **pyright**              | `uv run pyright src/sqlfluff_complexity` — config: [`pyproject.toml`](../../../pyproject.toml) `[tool.pyright]`                           |
| **pylint**               | `uv run pylint src/sqlfluff_complexity --score=no` — config: [`.pylintrc`](../../../.pylintrc)                                            |
| **bandit**               | `uv run bandit -r src/sqlfluff_complexity -c pyproject.toml -q` — config: [`pyproject.toml`](../../../pyproject.toml) `[tool.bandit]`     |

### Tier 2 — Optional / repo-native tools (run if present)

| Tool        | When to run                                                     | Command hint                                                                                                                                                                |
| ----------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **semgrep** | If `uv run semgrep` works or Semgrep is on `PATH`               | `uv run semgrep scan --config auto --quiet src/sqlfluff_complexity` (or project Semgrep config if added later)                                                              |
| **vulture** | Dead code (Makefile target)                                     | `make dead-code` or `uv run vulture` per [`pyproject.toml`](../../../pyproject.toml) `[tool.vulture]`                                                                       |
| **xenon**   | Cyclomatic complexity (not Trunk; useful parity with AGENTS.md) | Run on package sources only, e.g. `find src/sqlfluff_complexity -name '*.py' -not -path '*/tests/*' \| xargs uv run xenon --max-absolute B --max-modules B --max-average A` |

### Tier 3 — Markdown, YAML, TOML, Shell, GitHub Actions

Run **only if** the corresponding CLI is available (`command -v …`). Install via OS package manager or Trunk later if missing.

| Trunk linter            | Typical fallback                                                                                               |
| ----------------------- | -------------------------------------------------------------------------------------------------------------- |
| **prettier**            | `npx prettier@3.8.3 --check "**/*.{md,json,yml,yaml}"` or `--write` to fix — align globs with what you changed |
| **markdownlint**        | `npx markdownlint-cli2 "**/*.md"` or `markdownlint`                                                            |
| **yamllint**            | `yamllint .github .trunk` (or repo YAML dirs)                                                                  |
| **taplo**               | `taplo fmt --check .` or format `*.toml`                                                                       |
| **shellcheck**          | `shellcheck` on shell scripts under `dev/`, etc.                                                               |
| **shfmt**               | `shfmt -l -w` on shell scripts if installed                                                                    |
| **actionlint**          | `actionlint` on `.github/workflows` if installed                                                               |
| **markdown-link-check** | Run on docs if the CLI is installed                                                                            |

### Tier 4 — Security scanners (also in Trunk)

**trivy**, **osv-scanner**: use the **`security-scan`** skill / **`make scan-vulnerabilities`** when those binaries exist; they are not a substitute for Tier 1 Python lint but should run in full verifier flows.

### Fallback termination

- **PASS** when Tier 1 completes with no errors (required for a minimal “lint green” without Trunk).
- **PASS with notes** when Tier 1 passes and Tier 2–3 were skipped only because binaries were missing—list SKIPPED tools in the session summary.
- **Never** claim full Trunk parity without **`make lint`** succeeding; say explicitly that Markdown/Prettier/Semgrep/etc. were skipped if their CLIs were absent.

## Constraints

- Do not silence Trunk/Ruff/Pyright/Pylint/Bandit/Semgrep findings with inline suppressions (for example `# noqa`, `# type: ignore`, `# pylint: disable`, `ruff: noqa`, file-level `# ruff: noqa`, or Trunk inline disable comments).
- Do not broaden project configuration to hide violations (for example new `[tool.ruff.lint]` ignores, Pyright `report*` toggles, or Pylint disables) unless the user explicitly asked for that policy change.
- Prefer **`make format`** when Trunk is available; otherwise **`uv run ruff format`** for Python and Prettier for Markdown/JSON/YAML when running fallback.
- If fixes fail after genuine attempts, stop and surface the finding for a human—do not add suppressions to make CI green.

## Termination Criteria

- **`make lint`** succeeds (best), **or**
- **Fallback Tier 1** (Ruff + Pyright + Pylint + Bandit) succeeds with documented skips for optional tiers, **or**
- Max iteration limit (default: 5), or human escalation.

## Examples

### Trunk available

1. `make lint` reports issues.
2. `make format` or minimal code edits.
3. `make lint` passes.

### Trunk missing

1. `make lint` fails: `trunk: command not found` (or similar).
2. Run **Tier 1** fallback: `uv run ruff format …`, `uv run ruff check …`, `uv run pyright …`, `uv run pylint …`, `uv run bandit -r … -c pyproject.toml`.
3. Fix issues; re-run Tier 1 until clean.
4. Optionally run Tier 2–3 commands that exist on `PATH`.

## Resources

- [Trunk Documentation](https://docs.trunk.io/): Official Trunk CLI.
- Repo: **[`.trunk/trunk.yaml`](../../../.trunk/trunk.yaml)** — enabled linters and versions.
- Repo: **[AGENTS.md](../../../AGENTS.md)** — `make` targets and stack overview.
