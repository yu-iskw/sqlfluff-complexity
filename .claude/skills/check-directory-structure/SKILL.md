---
name: check-directory-structure
description: Inspect repository layout with tree and find, compare to AGENTS.md conventions, and fix misplaced or overly flat generated files. Use when auditing folder structure, after scaffolding or bulk file generation, when output looks flat, or when asked where code/tests/docs should live. Supports inspecting the repository root or a specified subdirectory.
compatibility: Unix-like shell. POSIX find required; optional tree for readability (install via OS package manager if missing). Run from inside the working tree; set TARGET to the directory to inspect (default `.` for the current directory, often the repo root after `cd`).
---

# Check directory structure

## Purpose

Ground work in the **actual** on-disk layout and catch **flat or misplaced** output (for example many new files at the repository root) before finishing a task.

## When to use

- After scaffolding, renaming the package, or generating several new files
- When imports or paths feel wrong compared to where files really live
- When the user asks where code, tests, or scripts should live
- When output looks like a **flat dump** instead of nested package layout

## How to run

Read **Architecture** and testing layout in [`AGENTS.md`](../../../AGENTS.md). This repository uses package **`sqlfluff_complexity`** under `src/sqlfluff_complexity/` (confirm with `pyproject.toml` and `src/` on disk if unsure).

**Target directory:** By default, inspect the **current directory** (after `cd` to the repository root, that is the whole repo). To inspect only a subtree—for example a package or feature folder—set `TARGET` to that path (repo-relative or absolute). Examples: `TARGET=.` (same as root after `cd` to repo root), `TARGET=src/sqlfluff_complexity`, `TARGET=dev`. Use the same `TARGET` in every command below.

```bash
# From repository root; inspect whole repo
TARGET=.

# Or inspect only a subtree (repo-relative or absolute path)
TARGET=src/sqlfluff_complexity
```

### 1. Snapshot layout

**Optional — readable tree** (skip if `tree` is not installed):

```bash
tree -L 3 -a -I '.git|__pycache__|.venv|node_modules|dist|build|.pytest_cache|.ruff_cache' "${TARGET:-.}"
```

**POSIX `find` — works without `tree`:** run from inside `TARGET` so skipping `.git`, `.venv`, and `__pycache__` works for both the repo root and a subdirectory.

```bash
# Immediate children of TARGET (plus `.` for the root of the scanned tree)
(cd "${TARGET:-.}" && find . \( -name '.git' -o -name '.venv' -o -name '__pycache__' \) -prune -o -maxdepth 1 -print)

# Sample of files under TARGET (cap output on large trees)
(cd "${TARGET:-.}" && find . \( -name '.git' -o -name '.venv' \) -prune -o \( -type d -name '__pycache__' \) -prune -o -type f -print | head -200)
```

**Optional — depth signal** (rough hint for flat vs nested paths under `TARGET`):

```bash
(cd "${TARGET:-.}" && find . -type f -print | awk -F/ '{ print NF-1 }' | sort -n | tail -5)
```

If `TARGET` is not the repository root, map what you see back to the **full** repo layout in [`AGENTS.md`](../../../AGENTS.md) (for example `src/sqlfluff_complexity/` vs `dev/`).

### 2. Compare to this repository

- **Package code** lives under `src/sqlfluff_complexity/`, not loose Python modules at the repository root.
- **Tests** live under `src/sqlfluff_complexity/tests/`; files match `test_*.py` (see [`AGENTS.md`](../../../AGENTS.md)).
- **Dev scripts:** `dev/`; **CI:** `.github/workflows/`; **ADRs:** `docs/adr/` when used.

For bootstrapping a **new** project from the Python template (rename package, clean docs), use [`initialize-project`](../../../.claude/skills/initialize-project/SKILL.md).

### 3. Fix loop

1. **Move** misplaced files to match the conventions above.
2. **Update** imports, packaging paths in `pyproject.toml`, and references in docs or CI if paths changed.
3. **Verify** with `make lint && make test` per [`AGENTS.md`](../../../AGENTS.md).

## Termination

- Layout matches documented conventions, or
- Remaining differences are **explicitly accepted** with a short rationale, or
- After **2** relocate/fix iterations, stop and list remaining items for the user.

## Related

- [`AGENTS.md`](../../../AGENTS.md) — Architecture, testing, quick commands
- [`CLAUDE.md`](../../../CLAUDE.md) — Claude Code entrypoint and `.claude/` layout
- [`initialize-project`](../../../.claude/skills/initialize-project/SKILL.md) — Rename template package and bootstrap
