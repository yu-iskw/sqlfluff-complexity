# Code scanning config (template + renderer)

This skill ships a YAML template and a small shell renderer under the same directory as [`SKILL.md`](../SKILL.md).

- **Template:** [`assets/code-scanning-config.template.yml`](../assets/code-scanning-config.template.yml)
- **Renderer:** [`scripts/render-code-scanning-config.sh`](../scripts/render-code-scanning-config.sh)

Local CodeQL in this repository is **CLI-driven** for **Python**: primary extraction uses `codeql database create` with `--language=python` and `--source-root .` (no build command). See [`SKILL.md`](../SKILL.md) and [`dev/codeql.sh`](../../../../dev/codeql.sh) for the full `database create` / `database analyze` flow.

When `CODEQL_CONFIG_REPO_SCAN` is enabled (default), the renderer adds common noise paths if present (for example `.git`, `node_modules`, `.codeql_db`, virtualenvs, Python caches, coverage output). It intentionally stays minimal for this template; use comma-separated **`CODEQL_PATHS_IGNORE`** (and optional extra CLI arguments to the script) for monorepo build dirs, e2e artifacts, Terraform caches, or other repo-specific trees.

Pass the rendered file to `codeql database create --codescanning-config=<file>` when you need `paths-ignore` or other [code scanning configuration](https://aka.ms/code-scanning-docs/config-file) options beyond a bare `--source-root .` create.
