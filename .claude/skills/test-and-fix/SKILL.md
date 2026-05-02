---
name: test-and-fix
description: Run unit tests, coverage checks, and automatically fix code failures, regression bugs, or test mismatches. Use when tests are failing, after implementing new features, to repair "broken" tests, or to inspect Python coverage gaps.
---

# Test and Fix Loop

## Purpose

An autonomous loop for the agent to identify, analyze, and fix failing unit tests using `pytest`. This skill also covers Python test coverage checks so coverage gaps are handled as part of the normal test-and-fix workflow rather than as a separate skill.

Use this skill when the user asks to:

- Run or fix Python tests.
- Repair failing tests or regressions.
- Get Python test coverage.
- Run or inspect `make coverage` / `make test-coverage`.
- Generate an HTML coverage report.
- Enforce a coverage threshold locally or in CI.
- Add tests for uncovered critical paths.

## Commands

```bash
make test
```

Runs the default pytest suite.

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

## Loop Logic

1. **Identify**: Run `make test` to identify failing tests.
2. **Analyze**: Examine the `pytest` output to determine:
   - The failing test file and line number.
   - The expected vs actual values (assertion errors).
   - Tracebacks for runtime errors.
3. **Fix**: Apply the minimum necessary change to either the source code (if it's a bug) or the test code (if the test is outdated).
4. **Verify**: Re-run `make test` (or `uv run pytest path/to/failing_test.py` for speed).
   - If passed: Move to the next failing test or finish if all are resolved.
   - If failed: Analyze the new failure and repeat the loop.

## Coverage Workflow

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

5. **Verify coverage**
   - Re-run `make coverage`.
   - If code changed, also run `make test`.
   - If coverage is being enforced, re-run with the target threshold, for example `COVERAGE_FAIL_UNDER=80 make coverage`.

## Termination Criteria

- All tests pass (as reported by `make test`).
- Requested coverage threshold passes, when one was specified.
- Reached max iteration limit (default: 5).
- The error or coverage gap persists after multiple distinct fix attempts, indicating a need for human intervention.

## Troubleshooting

- `make coverage` runs `pytest` directly without Nox's xdist `-n` flags so local coverage collection is deterministic.
- If optional marker suites are needed, override `PYTEST_MARKER`, for example:

  ```bash
  PYTEST_MARKER="dialect_extra" PYTEST_PATH=src/sqlfluff_complexity/tests make coverage
  ```

- If coverage output is stale or confusing, run:

  ```bash
  rm -rf .coverage .coverage.* coverage.xml htmlcov
  make coverage
  ```

## Examples

### Scenario: Fixing a logic error

1. `make test` fails in `src/your_package/tests/test_dummy.py` due to an assertion or import error.
2. Agent inspects the failing test and the implementation under `src/your_package/`.
3. Agent applies the minimum fix in source or test so behavior matches the intended contract.
4. `make test` passes.

### Scenario: Closing a coverage gap

1. `make coverage` reports missing lines in `src/sqlfluff_complexity/example.py`.
2. Agent inspects the uncovered branch and determines the expected behavior.
3. Agent adds a focused test under `src/sqlfluff_complexity/tests/`.
4. `make coverage` passes with the requested threshold.

## Guardrails

- Keep coverage changes behavior-driven; line coverage alone is not a sufficient reason for brittle tests.
- Do not lower or bypass `COVERAGE_FAIL_UNDER` when a threshold was explicitly requested.
- Do not include generated `htmlcov/`, `.coverage`, `.coverage.*`, or `coverage.xml` files in commits.
- Apply the minimum fix necessary for failing tests.

## Resources

- [Pytest Documentation](https://docs.pytest.org/): Official documentation for the pytest framework.
- Testing conventions for this repo: [AGENTS.md](../../../AGENTS.md) (Testing section).
