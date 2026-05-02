---
name: test-coverage
description: Run Python test coverage, inspect missing lines, enforce coverage thresholds, and guide targeted test additions for sqlfluff-complexity.
---

# Python Test Coverage

## Purpose

Measure Python test coverage for `sqlfluff-complexity`, identify untested branches or lines, and help add focused regression tests without broad or brittle rewrites.

Use this skill when the user asks to:

- Get Python test coverage.
- Run or inspect `make coverage` / `make test-coverage`.
- Generate an HTML coverage report.
- Enforce a coverage threshold locally or in CI.
- Add tests for uncovered critical paths.

## Prerequisites

- `uv` is available on `PATH`.
- The development environment has been set up with `make setup`, or `uv` can resolve the dev group on demand.
- The repository root is the current working directory.

## Commands

```bash
make coverage
```

Runs the default Python test suite with coverage and prints missing lines.

```bash
make test-coverage
```

Alias for `make coverage`.

```bash
COVERAGE_FAIL_UNDER=80 make coverage
```

Fails if total coverage is below the requested percentage.

```bash
make coverage-html
```

Generates an HTML report in `htmlcov/` after the terminal report succeeds.

```bash
PYTEST_PATH=src/sqlfluff_complexity/tests/test_rules.py make coverage
```

Scopes coverage to a test file or directory while still measuring `src/sqlfluff_complexity`.

## Workflow

1. **Run baseline coverage**
   - Execute `make coverage`.
   - Capture total coverage, files with the largest gaps, and any failing tests.

2. **Inspect missing lines**
   - Read the `coverage report --show-missing` output.
   - Prefer missing lines in production modules under `src/sqlfluff_complexity/` over test utilities.
   - For complex gaps, run `make coverage-html` and inspect `htmlcov/index.html` locally.

3. **Prioritize tests**
   - Start with uncovered behavior on public APIs, SQLFluff rule logic, CLI paths, and error handling.
   - Avoid tests that only execute lines without asserting behavior.
   - Keep tests colocated under `src/sqlfluff_complexity/tests/` and named `test_*.py`.

4. **Add focused tests**
   - Add the smallest test that proves the intended behavior.
   - Prefer parametrized pytest cases for similar SQL or rule scenarios.
   - Do not relax assertions just to increase coverage.

5. **Verify**
   - Re-run `make coverage`.
   - If code changed, also run `make test`.
   - If coverage is being enforced, re-run with the target threshold, for example `COVERAGE_FAIL_UNDER=80 make coverage`.

## Troubleshooting

- If xdist or subprocess coverage appears incomplete, the Makefile coverage target disables xdist with `PYTEST_XDIST_WORKERS=0` for deterministic local coverage.
- If optional marker suites are needed, override `PYTEST_MARKER`, for example:

  ```bash
  PYTEST_MARKER="dialect_extra" PYTEST_PATH=src/sqlfluff_complexity/tests make coverage
  ```

- If coverage output is stale or confusing, run:

  ```bash
  rm -rf .coverage htmlcov
  make coverage
  ```

## Guardrails

- Keep coverage changes behavior-driven; line coverage alone is not a sufficient reason for brittle tests.
- Do not lower or bypass `COVERAGE_FAIL_UNDER` when a threshold was explicitly requested.
- Do not include generated `htmlcov/` or `.coverage` files in commits.
- Follow repository guidance in `AGENTS.md` and Makefile targets as the source of truth.
