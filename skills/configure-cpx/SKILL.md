---
name: configure-cpx
description: Guide users through configuring sqlfluff-complexity for a SQLFluff project by sampling reports, choosing a preset, explaining thresholds, per-directory strictness (nested .sqlfluff vs path_overrides), validating config, and recommending gradual CI rollout.
---

# Configure CPX

This skill is for **consumer** SQLFluff projects (install by copying or linking into your agent tool’s skills directory, for example `.claude/skills/` or Cursor project skills).

Use this skill when a user asks to configure, tune, adopt, or roll out `sqlfluff-complexity` rules for a project.

## Workflow

1. Work from the repository root. Inspect **root and nested** SQLFluff config: `.sqlfluff` at the repo root, `pyproject.toml` (`[tool.sqlfluff.*]` if present), and **nested** config files (for example `.sqlfluff` under `models/…` or other SQL directories). SQLFluff merges these along the path to each file. Scan obvious SQL paths to infer dialect and target files before asking.
2. If no dialect is discoverable, ask the user for the SQLFluff dialect.
3. Generate a starting config with one of:

   ```bash
   sqlfluff-complexity config preset report_only --dialect <dialect>
   sqlfluff-complexity config preset lenient --dialect <dialect>
   sqlfluff-complexity config preset recommended --dialect <dialect>
   sqlfluff-complexity config preset strict --dialect <dialect>
   ```

4. Run report mode on representative SQL files:

   ```bash
   sqlfluff-complexity report --dialect <dialect> --format json <paths>
   ```

5. Recommend a preset:
   - `report_only` for baselining or CI visibility without enforcement.
   - `lenient` when the first run produces too many findings.
   - `recommended` when findings are sparse and high-signal.
   - `strict` only for mature projects that already enforce SQL review budgets.

6. Explain any threshold changes in plain language, focusing on review risk rather than parser internals.
7. When the report clearly shows that staging, intermediate, marts, or experimental SQL need **different CPX budgets**, present **per-path strictness** using one or both of:
   - **SQLFluff nested configuration:** SQLFluff merges config along the directory chain toward each SQL file; values from files **closer to that file** override earlier ones. Authoritative behavior: [SQLFluff — Setting configuration — Nesting](https://docs.sqlfluff.com/en/stable/configuration/setting_configuration.html#nesting). CPX uses the same `[sqlfluff:rules:CPX_*]` sections as other rules.
   - **`path_overrides`:** Keep a **single** root config and add glob lines under `[sqlfluff:rules:CPX_C201]` for CPX-specific thresholds and `mode`. Full syntax and keys are in the sqlfluff-complexity **Configuration** user doc (`docs/configuration.md` when this repository is checked out).
   - If nested multi-file config produces surprising lint or report results, prefer **one root `.sqlfluff`** plus **`path_overrides`** instead of debugging merge order across many files.
8. Validate the resulting config:

   ```bash
   sqlfluff-complexity config-check --dialect <dialect> --config .sqlfluff
   ```

9. Recommend rollout in this order: report mode baseline, individual high-signal rule enforcement, then `CPX_C201` once aggregate score is calibrated.

## Guardrails

- Do not invent hidden profile behavior; presets are plain generated SQLFluff config.
- Do not read dbt artifacts directly. Use SQLFluff parsing and the `sqlfluff-complexity report` command.
- Keep defaults conservative unless the user explicitly asks for strict enforcement.
- Do **not** recommend setting `templater` only in a nested config under the working directory: SQLFluff does **not** allow `templater` in config files located in **subdirectories of the cwd** (same [nesting](https://docs.sqlfluff.com/en/stable/configuration/setting_configuration.html#nesting) documentation). Keep `templater` and dbt templater sections in project root or higher-level config.
- **Nested-file CPX** setups are not exhaustively validated in this plugin’s test matrix; run `config-check`, spot-check `sqlfluff lint` and `sqlfluff-complexity report` on real paths, and fall back to root config plus `path_overrides` if behavior is unclear—do not over-promise.
