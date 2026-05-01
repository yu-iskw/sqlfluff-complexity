---
name: build-and-fix
description: Build the project and automatically fix packaging or build errors (for example Hatch failures) and related breakage. Use when the project fails to build, shows "broken" states, or after making significant changes.
---

# Build and Fix Loop

## Purpose

An autonomous loop for the agent to identify, analyze, and fix build errors using `make build`.

## Loop Logic

1. **Identify**: Run `make build` to identify build failures.
2. **Analyze**: Examine the build output to determine:
   - The failing component (e.g., `hatch` build error).
   - The specific error message (e.g., missing dependencies, syntax errors, packaging issues).
   - For `make` / `uv` commands, see the project root [CLAUDE.md](../../../CLAUDE.md).
3. **Fix**: Apply the minimum necessary change to resolve the error (e.g., updating `pyproject.toml`, fixing syntax, or adding missing files).
4. **Verify**: Re-run `make build`.
   - If passed: Finish.
   - If failed: Analyze the new failure and repeat the loop.

## Termination Criteria

- The project builds successfully (as reported by `make build`).
- Reached max iteration limit (default: 5).
- The error persists after multiple distinct fix attempts, indicating a need for human intervention.

## Examples

### Scenario: Fixing a packaging error

1. `make build` fails because of a missing dependency in `pyproject.toml`.
2. Agent analyzes the error, adds the dependency using `uv add`.
3. `make build` now passes.

## Resources

- [Hatch Documentation](https://hatch.pypa.io/): Official documentation for the Hatch build backend.
