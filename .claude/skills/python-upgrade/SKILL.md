---
name: python-upgrade
description: Safely upgrade Python dependencies using uv. Use when asked to "upgrade dependencies", "update packages", "check for updates", or fix version mismatches in a Python project.
---

# Safe Python Dependency Upgrade

This skill provides a structured process for safely upgrading Python dependencies using `uv`, ensuring project stability through pre-upgrade health checks and post-upgrade validation.

## 1. Preparation & Health Check

Before making any changes, verify the current state of the project:

1. **Baseline Health Check**:
   - Run the test suite: `make test`.
   - _Constraint_: If the baseline tests fail, resolve those issues before proceeding with upgrades.
2. **Backup**:
   - Backup `uv.lock` and `pyproject.toml`: `cp uv.lock uv.lock.bak` and `cp pyproject.toml pyproject.toml.bak`.

## 2. Upgrade Execution

Choose the appropriate upgrade path based on the user's request. For common `uv` and `make` usage, see the project root [CLAUDE.md](../../../CLAUDE.md).

### Targeted Upgrade (Recommended)

Use this when the user specifies a package or a small set of packages.

1. **Upgrade**: Run `uv add <package>@latest` or `uv lock --upgrade-package <package>`.
2. **Verify**: Check `pyproject.toml` or `uv.lock` to ensure the version has been updated.

### Full Upgrade (Maintenance)

Use this for general dependency maintenance.

1. **Upgrade**: Run `uv lock --upgrade`.
2. **Check for Changes**: Review the `uv.lock` changes and check for major version bumps.

## 3. Validation & Verification

After the upgrade, ensure the project remains stable:

1. **Re-sync**: Run `uv sync --all-extras` to update the environment.
2. **Invoke Verifier**: Use the `verifier` subagent ([../../agents/verifier.md](../../agents/verifier.md)) to run the full build, lint, and test cycle (e.g., `make lint`, `make test`, `make build`).
3. **Handle Failure**: If any check reports persistent issues it cannot fix, analyze the breaking changes and apply manual fixes or roll back.

## 4. Finalization

1. **Commit**: Create a commit with the updated `pyproject.toml` and `uv.lock`.
   - _Message Suggestion_: `chore(deps): upgrade dependencies`
2. **Cleanup**: Remove backup files: `rm *.bak`.

## Rollback Plan

If validation fails and cannot be easily fixed:

1. **Restore**: `mv pyproject.toml.bak pyproject.toml` and `mv uv.lock.bak uv.lock`.
2. **Re-sync**: Run `uv sync --all-extras` to restore the environment.
3. **Report**: Notify the user of the failure and the reasons (e.g., specific breaking changes).
