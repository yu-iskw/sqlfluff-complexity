---
name: configure-cpx
description: Guide users through configuring sqlfluff-complexity for a SQLFluff project by sampling reports, choosing a preset, explaining thresholds, validating config, and recommending gradual CI rollout.
---

# Configure CPX

This skill is for **consumer** SQLFluff projects (install by copying or linking into your agent tool’s skills directory, for example `.claude/skills/` or Cursor project skills).

Use this skill when a user asks to configure, tune, adopt, or roll out `sqlfluff-complexity` rules for a project.

## Workflow

1. Work from the repository root. Inspect `.sqlfluff`, `pyproject.toml`, and obvious SQL paths to infer dialect and target files before asking.
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
7. Suggest path overrides only when the report clearly shows different budgets for staging, intermediate, marts, or experimental SQL.
8. Validate the resulting config:

   ```bash
   sqlfluff-complexity config-check --dialect <dialect> --config .sqlfluff
   ```

9. Recommend rollout in this order: report mode baseline, individual high-signal rule enforcement, then `CPX_C201` once aggregate score is calibrated.

## Guardrails

- Do not invent hidden profile behavior; presets are plain generated SQLFluff config.
- Do not read dbt artifacts directly. Use SQLFluff parsing and the `sqlfluff-complexity report` command.
- Keep defaults conservative unless the user explicitly asks for strict enforcement.
