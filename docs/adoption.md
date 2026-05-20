# Adoption: calibration, CI, and examples

This page complements [Reporting](reporting.md) and [Configuration](configuration.md) with a practical rollout path: measure first, tune thresholds, then enforce.

## Coding agent plugin

The [`configure-sqlfluff-complexity`](../plugins/sqlfluff-complexity/skills/configure-sqlfluff-complexity/SKILL.md) skill helps coding agents walk through presets, reports, nested config, and rollout. The [`analyze-complexity-report`](../plugins/sqlfluff-complexity/skills/analyze-complexity-report/SKILL.md) skill analyzes JSON report output (hotspot digest and threshold tuning): it reuses the user’s `--output` file when it is no older than five minutes, otherwise runs `sqlfluff-complexity report`. Keep that JSON local (for example `complexity.json`) and out of git—add it to `.gitignore` in the consumer project. Both skills ship in the **sqlfluff-complexity** agent plugin at [`plugins/sqlfluff-complexity/`](../plugins/sqlfluff-complexity/) (Claude Code, Cursor, and Codex manifests).

### Install

1. Install the Python package in the target project (`pip install sqlfluff-complexity` or `uv add --dev sqlfluff-complexity`).
2. Add the plugin from this repository:
   - **Claude Code:** register the repo marketplace (`.claude-plugin/marketplace.json`), install the `sqlfluff-complexity` plugin, and enable it in settings; or run with `claude --plugin-dir /path/to/sqlfluff-complexity/plugins/sqlfluff-complexity`.
   - **Cursor:** use `.cursor-plugin/marketplace.json` or install `plugins/sqlfluff-complexity` from a local checkout (see [Cursor plugins](https://cursor.com/docs/plugins)).
   - **Codex:** use `.codex-plugin/marketplace.json` or point Codex at the same plugin directory per [Codex plugins](https://developers.openai.com/codex/plugins).

Validate manifests locally from a checkout:

```bash
./scripts/validate-agent-plugin-manifests.sh
```

Invoke `configure-sqlfluff-complexity` when configuring CPX (for example `/configure-sqlfluff-complexity` in Claude Code). Invoke `analyze-complexity-report` when reviewing hotspots or tuning thresholds from a report (for example `/analyze-complexity-report`). Neither skill replaces `sqlfluff-complexity config preset` or `config-check`; they guide an agent through those commands.

## Calibration playbook

1. **Install** `sqlfluff-complexity` next to SQLFluff (see [Quick start](quickstart.md)).
2. **Run a repo-wide report** with your real dialect and `.sqlfluff`:

   ```bash
   sqlfluff-complexity report --dialect postgres --config .sqlfluff --format json --output complexity.json models/
   ```

3. **Inspect columns** in console output or JSON: `set_operation_count` counts `set_operator` parse segments (stacked `UNION` / `INTERSECT` / `EXCEPT`). `expression_depth` is **not** general expression-tree depth; it is the **maximum nesting depth of `case_expression` segments** (nested `CASE` inside `CASE`). `derived_tables` counts inline `from (select ...)` / `join (select ...)` relations **outside CTE query bodies** (inside a `WITH` CTE definition those are skipped so they are not double-counted with `ctes`).
4. **Set generous thresholds** in `[sqlfluff:rules:CPX_C108]`, `CPX_C109`, and `CPX_C110` (and existing CPX sections) so the first CI run is informative, not blocking.
5. **Tighten with `path_overrides`** on `[sqlfluff:rules:CPX_C201]` so staging vs marts get different budgets (see [Configuration](configuration.md)).
6. **Tune `complexity_weights` after baseline runs** if a metric is too noisy or too quiet for your
   project. Set weights as a **JSON object** string under `[sqlfluff:rules:CPX_C201]` (see [Aggregate score](configuration.md#aggregate-score)); omit keys to keep defaults. The defaults already include modest nonzero weights for `set_operation_count`,
   `expression_depth`, and `derived_tables`; teams can still lower them to `0` for an opt-in rollout.

## CI: HTML dashboard artifact

Upload a standalone HTML dashboard when reviewers need an interactive, browser-openable
view of complexity hotspots:

```yaml
# .github/workflows/complexity-report.yml (example)
name: complexity-report
on: [push, pull_request]
jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install sqlfluff sqlfluff-complexity
      - name: Generate HTML dashboard
        run: |
          sqlfluff-complexity report \
            --dialect postgres \
            --config .sqlfluff \
            --format html \
            --output complexity.html \
            models/
      - uses: actions/upload-artifact@v4
        with:
          name: complexity-html
          path: complexity.html
```

The uploaded `complexity.html` is self-contained. It can be opened without a server,
external assets, or network access, and it does not embed full SQL source by default.

## CI: SARIF artifact

Upload SARIF as a workflow artifact (and optionally feed GitHub code scanning if your org enables it for third-party tools):

```yaml
# .github/workflows/complexity-report.yml (example)
name: complexity-report
on: [push, pull_request]
jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install sqlfluff sqlfluff-complexity
      - name: Generate SARIF
        run: |
          sqlfluff-complexity report \
            --dialect postgres \
            --config .sqlfluff \
            --format sarif \
            --output complexity.sarif \
            models/
      - uses: actions/upload-artifact@v4
        with:
          name: complexity-sarif
          path: complexity.sarif
```

If the repository already uses `uv`, replace the `pip install` step with something like `uv sync --frozen` (or `uv pip install sqlfluff sqlfluff-complexity`) and invoke the CLI with `uv run sqlfluff-complexity report …` so the job uses the same resolver as local development.

Same flags work locally; see [Reporting](reporting.md) for JSON and `--fail-on-error`.

## CI: lint changed SQL only

GitHub Actions does not ship a single canonical “changed files” primitive; one pattern is `git diff` plus `xargs`:

```yaml
- name: Lint changed SQL
  run: |
    mapfile -t files < <(git diff --name-only --diff-filter=ACMRT ${{ github.event.pull_request.base.sha }} ${{ github.sha }} | grep -E '\.sql$' || true)
    if [ "${#files[@]}" -eq 0 ]; then echo "No SQL changes"; exit 0; fi
    sqlfluff lint "${files[@]}"
```

Adjust the revision range for your trigger (`push` vs `pull_request`). Keep a separate scheduled or manual job with `sqlfluff-complexity report` over the full tree for drift visibility.

## Before / after vignette

**Before:** one model stacks unions and nests business rules in `CASE`.

```sql
select id, 'a' as tier from customers where region = 'EMEA'
union all
select id, 'b' as tier from customers where region = 'APAC'
union all
select id,
  case when score > 90 then case when premium then 'p' else 'h' end else 's' end as tier
from customers where region = 'AMER';
```

A report might show elevated `set_operation_count` and `expression_depth`, and findings for `CPX_C109` / `CPX_C108` when thresholds are tight.

**After:** split regions into a staging model or seed, union once in a thin mart, and replace nested `CASE` with a mapping join or intermediate classification model. Re-run `sqlfluff-complexity report`: union arms and nested `CASE` depth should drop along with aggregate score because those metrics are weighted in `CPX_C201`.

## Positioning: agent harness

The narrative in [docs/assets/medium.md](assets/medium.md) matches the README positioning: structural complexity signals help humans and **coding agents** review SQL safely. You can republish or adapt that draft as an external article.

## See also

- [Rules reference](rules.md) for `CPX_C108` and `CPX_C109`
- [Reporting](reporting.md) for SARIF and JSON semantics
