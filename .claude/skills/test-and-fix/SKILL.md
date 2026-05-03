---
name: test-and-fix
description: Run unit tests and automatically fix code failures, regression bugs, or test mismatches. Use when tests are failing, after implementing new features, or to repair "broken" tests.
---

# Test and Fix Loop

## Purpose

An autonomous loop for the agent to identify, analyze, and fix failing unit tests using `pytest`.

## Loop Logic

1. **Identify**: Run `make test` to identify failing tests (pytest with **pytest-cov**; terminal shows coverage summary).
2. **Analyze**: Examine the `pytest` output to determine:
   - The failing test file and line number.
   - The expected vs actual values (assertion errors).
   - Tracebacks for runtime errors.
3. **Fix**: Apply the minimum necessary change to either the source code (if it's a bug) or the test code (if the test is outdated).
4. **Verify**: Re-run `make test` (or `uv run pytest path/to/failing_test.py` for speed).
   - If passed: Move to the next failing test or finish if all are resolved.
   - If failed: Analyze the new failure and repeat the loop.

## Termination Criteria

- All tests pass (as reported by `make test`).
- Reached max iteration limit (default: 5).
- The error persists after multiple distinct fix attempts, indicating a need for human intervention.

## Examples

### Scenario: Fixing a logic error

1. `make test` fails in `src/your_package/tests/test_dummy.py` due to an assertion or import error.
2. Agent inspects the failing test and the implementation under `src/your_package/`.
3. Agent applies the minimum fix in source or test so behavior matches the intended contract.
4. `make test` passes.

## Resources

- [Pytest Documentation](https://docs.pytest.org/): Official documentation for the pytest framework.
- Testing conventions for this repo: [AGENTS.md](../../../AGENTS.md) (Testing section).
