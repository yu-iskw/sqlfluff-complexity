---
name: complexity-check
description: Run Xenon cyclomatic complexity checks, analyze threshold failures, and guide refactors that keep sqlfluff-complexity maintainable.
---

# Complexity Check

## Purpose

Use Xenon to enforce maintainability guardrails for Python code in `sqlfluff-complexity`. This skill helps agents detect functions, classes, or modules whose cyclomatic complexity is too high and refactor them before changes land.

Use this skill when the user asks to:

- Run Xenon or check cyclomatic complexity.
- Diagnose `make complexity` / `make xenon` failures.
- Reduce complexity in a function, class, or module.
- Decide whether to adjust complexity thresholds.

## Prerequisites

- `uv` is available on `PATH`.
- Development dependencies are installed through `make setup`, or `uv` can resolve the dev group.
- The repository root is the current working directory.

## Commands

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

Scopes the check to a subpackage or file.

```bash
XENON_MAX_ABSOLUTE=A make complexity
```

Runs a stricter absolute threshold. Use this for exploratory tightening, not as a default unless the codebase is known to pass.

## Workflow

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

5. **Verify**
   - Re-run `make complexity`.
   - Re-run `make test` if source code changed.
   - Re-run `make lint` if signatures, imports, or structure changed.

## Threshold policy

Prefer refactoring over threshold relaxation. Adjust Xenon variables only when there is a documented reason, such as temporarily auditing legacy code or narrowing analysis to a known hotspot.

Do not raise repository defaults to make a new change pass unless the underlying complexity is intentionally unavoidable and documented in the PR.

## Guardrails

- Keep public behavior stable unless the user explicitly requested a behavior change.
- Avoid broad rewrites when a small extraction reduces complexity.
- Do not duplicate logic across helpers just to reduce a single reported score.
- Keep helper names domain-specific and readable.
- Follow `AGENTS.md`, `Makefile`, and existing tests as the source of truth.
