---
name: analyze-complexity-report
description: |
  Analyze sqlfluff-complexity JSON reports (hotspot digest and threshold tuning).
  Reuse --output when the file is no older than 5 minutes; otherwise run report.
  Scan paths and output path are always user-specified.
---

# Analyze complexity report

This skill is for **consumer** SQLFluff and dbt projects. Install it via the **sqlfluff-complexity** agent plugin (Claude Code, Cursor, or Codex) from this repository’s marketplace, or point your agent at `plugins/sqlfluff-complexity/` in a checkout. See [docs/adoption.md](https://github.com/yu-iskw/sqlfluff-complexity/blob/main/docs/adoption.md#coding-agent-plugin).

Use this skill when a user wants a **hotspot digest**, **threshold tuning ideas**, or a fast **measure → analyze → tune** loop on an existing or fresh JSON report—especially on large dbt projects where re-running `report` every turn is slow.

For first-time CPX adoption (presets, nested config, `config-check`, CI rollout), use **`configure-sqlfluff-complexity`** instead.

## When to use

- Rank files by complexity and explain review risk in plain language.
- Suggest presets, per-rule thresholds, or `path_overrides` from report data.
- Reuse a recent JSON report when the user’s `--output` file is still fresh (≤ 5 minutes).

Do **not** use this skill alone for greenfield CPX setup; prefer **`configure-sqlfluff-complexity`**.

## Required inputs

Ask for anything missing before running `report` or reading cache. **Do not assume default scan paths** (for example `models/`).

| Input                   | Required                   | Notes                                                                       |
| ----------------------- | -------------------------- | --------------------------------------------------------------------------- |
| SQL paths/globs to scan | **Yes**                    | User must specify every time                                                |
| `--output` JSON path    | **Yes**                    | Same file is cache and artifact (e.g. `complexity.json`)                    |
| `--dialect`             | If not discoverable        | Inspect `.sqlfluff` / `pyproject.toml` like `configure-sqlfluff-complexity` |
| `--config`              | If not default `.sqlfluff` | Optional                                                                    |
| Force refresh           | No                         | User says “refresh”, “force”, or “re-run report” → skip cache               |

## Cache policy

- **TTL:** 300 seconds (5 minutes) from the `--output` file’s modification time.
- **Invalidation:** Time only. Do **not** invalidate on `.sqlfluff`, git, or SQL changes within the TTL.
- **Force refresh:** Always run `report` when the user requests it, even if the file is fresh.
- **Git:** Do not commit the `--output` file. Suggest adding it to the consumer project’s `.gitignore` (only edit `.gitignore` if the user asks).
- **Disclaimer:** When reusing cache, tell the user once: results may be up to 5 minutes old; say **refresh** to regenerate.

### Cache check

Before running `report`, decide whether to read the existing `--output` file:

```bash
OUTPUT="<user-output-path>"
MAX_AGE_SEC=300

if [[ -f "$OUTPUT" ]]; then
  NOW=$(date +%s)
  # macOS: stat -f %m "$OUTPUT"
  # Linux: stat -c %Y "$OUTPUT"
  MTIME=$(stat -f %m "$OUTPUT" 2>/dev/null || stat -c %Y "$OUTPUT")
  AGE=$((NOW - MTIME))
  if [[ $AGE -le $MAX_AGE_SEC ]]; then
    echo "USE_CACHE (age ${AGE}s)"
  else
    echo "RUN_REPORT (stale, age ${AGE}s)"
  fi
else
  echo "RUN_REPORT (missing)"
fi
```

If the user requested force refresh, skip this and run `report`.

## Workflow

1. Work from the repository root. Collect **required inputs** (paths, `--output`, dialect/config).
2. Unless force refresh: run the **cache check** above.
3. **If USE_CACHE:** Read and parse the JSON at `--output`. Do not run `sqlfluff-complexity report`.
4. **If RUN_REPORT:** Run:

   ```bash
   sqlfluff-complexity report \
     --dialect <dialect> \
     --format json \
     --output <user-output-path> \
     <user-paths>
   ```

   Add `--config <path>` when not using the default `.sqlfluff`.

5. Parse JSON (see below) and produce **both** deliverables: hotspot digest and threshold tuning guide.

## JSON contract

See [Reporting: JSON](https://github.com/yu-iskw/sqlfluff-complexity/blob/main/docs/reporting.md#json-report).

- Top-level: `schema_version` (expect `1.1`), `entries`, `findings`
- Per **entry**: `path`, `score` (aggregate), `metrics`, errors / parse failures (`score` may be null)
- Per **finding**: `rule_id`, `metric`, `threshold`, `score`, `aggregate_score`, `remediation`, `contributors`

Do not read dbt artifacts (`manifest.json`, etc.).

## Hotspot digest

1. Sort `entries` by `score` descending. List entries with null `score` or parse errors separately.
2. Default **top 10** unless the user specifies another N.
3. For each hotspot: path, aggregate score, top 2–3 standout metrics, one plain-language review-risk line (from `findings` / `remediation`, not parser internals).
4. Do not embed full SQL unless the user asks.

### Sample hotspot digest

```markdown
## Hotspot digest

- Cache: reused `complexity.json` (age 2m) | regenerated report
- Scanned: `models/staging/` `models/marts/` (user-specified)

| Rank | Path                      | Score | Standout metrics                     |
| ---- | ------------------------- | ----- | ------------------------------------ |
| 1    | models/marts/orders.sql   | 42    | joins=4, ctes=2                      |
| 2    | models/staging/events.sql | 31    | subquery_depth=2, case_expressions=3 |

### Parse failures

- models/broken.sql — CPX_PARSE_ERROR (see findings)
```

## Threshold tuning guide

Ground suggestions in the report. Reuse preset heuristics from **`configure-sqlfluff-complexity`**:

- `report_only` — baselining or CI visibility without enforcement.
- `lenient` — many findings on first run.
- `recommended` — sparse, high-signal findings.
- `strict` — mature projects with existing SQL review budgets.

Include when relevant:

- Specific `CPX_*` threshold adjustments (cite `rule_id`, `metric`, current `threshold` vs actual `score`).
- **`path_overrides`** when scores clearly differ by folder (staging vs marts).
- Next commands:

  ```bash
  sqlfluff-complexity config preset <preset> --dialect <dialect>
  sqlfluff-complexity config-check --dialect <dialect> --config .sqlfluff
  ```

- Rollout order: report-only baseline → individual high-signal rules → `CPX_C201` after aggregate score is calibrated.

### Sample threshold tuning output

```markdown
## Threshold tuning

- Suggested preset: **lenient** (many CPX_C102 findings across hotspots)
- **CPX_C102:** consider raising `max_joins` from 2 → 4 where join fan-in drives scores
- **path_overrides:** stricter budget for `models/marts/**` if marts scores exceed staging
- Generate config: `sqlfluff-complexity config preset lenient --dialect <dialect>`
- Validate: `sqlfluff-complexity config-check --dialect <dialect> --config .sqlfluff`
```

## Guardrails

- Do not invent hidden preset behavior; presets are plain generated SQLFluff config.
- Do not read dbt artifacts directly. Use SQLFluff parsing and `sqlfluff-complexity report` only.
- Do not commit or version the `--output` JSON in git.
- Keep tuning suggestions conservative unless the user asks for strict enforcement.
- For full adoption workflow (nested `.sqlfluff`, `config-check`, CI), use **`configure-sqlfluff-complexity`**.

## Relationship to `configure-sqlfluff-complexity`

| Skill                           | Focus                                                          |
| ------------------------------- | -------------------------------------------------------------- |
| `configure-sqlfluff-complexity` | First-time setup, presets, nested config, validation, rollout  |
| `analyze-complexity-report`     | Cached JSON analysis, hotspots, tuning from an existing report |

After `configure-sqlfluff-complexity` has produced an initial report, use this skill for repeat analysis without re-scanning when the JSON is still fresh.
