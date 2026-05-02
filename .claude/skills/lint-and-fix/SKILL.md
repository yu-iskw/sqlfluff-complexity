---
name: lint-and-fix
description: Run linters, complexity checks, and fix violations, formatting errors, or style mismatches using Trunk and Xenon. Use when code quality checks fail, before submitting PRs, or to repair "broken" linting states.
---

# Lint and Fix Loop: Trunk and Xenon

## Purpose

An autonomous loop for the agent to identify, fix, and verify linting, formatting, and cyclomatic complexity violations using [Trunk](https://trunk.io) and Xenon.

Use this skill when the user asks to:

- Run or fix linting checks.
- Repair formatting or style violations.
- Run Xenon or check cyclomatic complexity.
- Diagnose `make complexity` / `make xenon` failures.
- Reduce complexity in a function, class, or module.

## Commands

```bash
make lint
```

Runs Trunk checks across the repository.

```bash
make format
```

Runs Trunk formatting across the repository.

```bash
make complexity
```

Runs Xenon against `src/sqlfluff_complexity` using the repository defaults:

- `XENON_MAX_ABSOLUTE=B`
- `XENON_MAX_MODULES=A`
- `XENON_MAX_AVERAGE=A`

```bash
make xenon
```

Alias for `make complexity`.

```bash
XENON_PATH=src/sqlfluff_complexity/rules make complexity
```

Scopes the complexity check to a subpackage or file.

```bash
XENON_MAX_ABSOLUTE=A make complexity
```

Runs a stricter absolute threshold. Use this for exploratory tightening, not as a default unless the codebase is known to pass.

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

## Complexity Workflow

1. **Run the check**
   - Execute `make complexity`.
   - Capture the failing file, object name, rank, and reported complexity.

2. **Classify the failure**
   - `A` is low complexity.
   - `B` is acceptable for this repo because the shared guardrail is max 10 per function.
   - `C` or worse means the function should usually be refactored before merging.

3. **Refactor first**
   - Split long decision trees into private helper functions.
   - Replace repeated conditionals with small lookup tables or strategy functions.
   - Extract SQLFluff rule-specific parsing, validation, and reporting into separate functions.
   - Preserve behavior with existing tests before making structural changes.

4. **Add or update tests when behavior moves**
   - If a refactor changes observable behavior or clarifies edge cases, add focused pytest coverage under `src/sqlfluff_complexity/tests/`.
   - Pair complexity refactors with `make test` and, when relevant, `make coverage`.

5. **Verify complexity**
   - Re-run `make complexity`.
   - Re-run `make test` if source code changed.
   - Re-run `make lint` if signatures, imports, or structure changed.

## Threshold policy

Prefer refactoring over threshold relaxation. Adjust Xenon variables only when there is a documented reason, such as temporarily auditing legacy code or narrowing analysis to a known hotspot.

Do not raise repository defaults to make a new change pass unless the underlying complexity is intentionally unavoidable and documented in the PR.

## Constraints

- Do not silence Trunk/Ruff/Pyright/Pylint/Bandit/Semgrep findings with inline suppressions (for example `# noqa`, `# type: ignore`, `# pylint: disable`, `ruff: noqa`, file-level `# ruff: noqa`, or Trunk inline disable comments).
- Do not broaden project configuration to hide violations (for example new `[tool.ruff.lint]` ignores, Pyright `report*` toggles, or Pylint disables) unless the user explicitly asked for that policy change.
- Do not raise Xenon thresholds to make a new change pass unless explicitly requested and documented.
- Prefer `make format` for auto-fixable style; otherwise fix the underlying issue the linter reports.
- If fixes fail after genuine attempts, stop and surface the finding for a human to decide—do not add suppressions to make CI green.

## Termination Criteria

- No more errors reported by `make lint`.
- `make complexity` passes when complexity checking was requested or relevant to the change.
- Reached max iteration limit (default: 5).

## Examples

### Scenario: Fixing a formatting violation

1. `make lint` reports formatting issues in `src/your_package/main.py`.
2. Agent runs `make format`.
3. `make lint` now passes.

### Scenario: Reducing complexity

1. `make complexity` reports a `C`-ranked function in `src/sqlfluff_complexity/example.py`.
2. Agent extracts cohesive private helpers while preserving behavior.
3. Agent runs `make test`, then `make complexity`, then `make lint`.

## Resources

- [Trunk Documentation](https://docs.trunk.io/): Official documentation for the Trunk CLI.
- Repository quality commands and guardrails: [AGENTS.md](../../../AGENTS.md).
