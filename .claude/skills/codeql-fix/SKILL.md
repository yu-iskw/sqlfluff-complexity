---
name: codeql-fix
description: Run CodeQL security/quality analysis and fix findings. Use when the user asks to run CodeQL, security scan, static analysis, or fix CodeQL findings.
compatibility: Requires [CodeQL CLI](https://github.com/github/codeql-cli-binaries/releases) on PATH (e.g. brew install codeql). Python and [uv](https://github.com/astral-sh/uv) aligned with [`.python-version`](../../../.python-version) and [`pyproject.toml`](../../../pyproject.toml). Run `uv sync` or `make setup` before analysis when findings should reflect installed dependencies (matches [`.github/workflows/codeql.yml`](../../../.github/workflows/codeql.yml)).
---

# CodeQL Fix

Use when the user asks to run CodeQL or static analysis, or to fix CodeQL findings (see frontmatter `description`).

## Preconditions

- [CodeQL CLI](https://github.com/github/codeql-cli-binaries/releases) on `PATH` (e.g. `brew install codeql`).
- Install project deps before creating the database (`uv sync`, `make setup`, or CI-style `uv sync --frozen`) so results match installed dependencies.

## Run analysis (repository root)

All commands below assume `cd "$(git rev-parse --show-toplevel)"`.

Do not commit CodeQL databases or SARIF outputs (large, machine-specific). They belong in [`.gitignore`](../../../.gitignore) (for example `.codeql_db/`, `codeql-results.sarif`).

### 1. Preferred: Makefile (matches [`dev/codeql.sh`](../../../dev/codeql.sh))

```bash
make codeql
```

This creates **`.codeql_db`**, analyzes with **`codeql/python-queries:codeql-suites/python-security-and-quality.qls`**, writes **`codeql-results.sarif`**, and passes **`--download`** to resolve query packs.

### 2. Manual CLI (equivalent to the script)

Create the database (Python needs no build command for extraction):

```bash
codeql database create .codeql_db --language=python --source-root . --overwrite
```

Analyze and emit SARIF:

```bash
codeql database analyze .codeql_db \
  "codeql/python-queries:codeql-suites/python-security-and-quality.qls" \
  --format=sarif-latest \
  --output=codeql-results.sarif \
  --download
```

- For a narrower suite closer to default GitHub code scanning, use `codeql/python-queries:codeql-suites/python-code-scanning.qls` instead.
- If packs are missing and you are not using `--download`, run `codeql pack download codeql/python-queries` once.

View SARIF in the VS Code SARIF extension (or upload where your org uses code scanning).

### 3. Optional: code scanning config (`paths-ignore`)

Use the renderer when you want `paths-ignore` for large or generated trees, hand-edited query blocks, or parity with GitHub code scanning YAML.

```bash
REPO="$(git rev-parse --show-toplevel)"
"$REPO/.claude/skills/codeql-fix/scripts/render-code-scanning-config.sh" "$REPO" /tmp/codeql-config.yml
codeql database create .codeql_db --language=python --source-root . --codescanning-config=/tmp/codeql-config.yml --overwrite
```

Then run `codeql database analyze` as in section 2. See [references/code-scanning-config.md](references/code-scanning-config.md).

## Fixer loop

If the relevant SARIF has an empty `runs[].results` array, there are **no CodeQL alerts to fix** for that suite; stop unless the user wants a broader suite or diagnostic queries.

When SARIF findings remain:

1. **Identify:** Read the SARIF or CLI output for reported findings.
2. **Fix:** Apply the minimum necessary edit to resolve each finding.
3. **Verify:** From the repository root, run `make test`, then `make lint` (see [AGENTS.md](../../../AGENTS.md) and the [Makefile](../../../Makefile); `make lint` runs `trunk check -a`).
4. **Re-scan:** Run `make codeql` or repeat the manual create + analyze steps until clean or up to 3 iterations to avoid unbounded loops.

## Optional: code scanning config details

See [references/code-scanning-config.md](references/code-scanning-config.md) and the official [code scanning configuration](https://aka.ms/code-scanning-docs/config-file) reference.
