# mend-adr (drift check)

Use this command when **implementation or docs may have drifted** from an **Accepted** ADR’s intent.

## When to run

- After a large refactor that might affect an architectural decision.
- When someone asks whether the codebase still matches a documented decision.

## What to do

1. Load the relevant ADR from `docs/adr/` and extract **invariants** and **decision-level** claims (not file lists or volatile thresholds).
2. Compare against **living sources** (code, config, READMEs), not one-off comment threads.
3. If intent still matches, stop. If not, open a short **amendment** or a new ADR (supersede) per the `manage-adr` skill—avoid pasting large config dumps into the ADR.

## Relationship to `manage-adr`

- `manage-adr` — author and lifecycle (create, link, supersede).
- `mend-adr` (this) — read intent, audit drift, suggest ADR updates when behavior diverges.

See [`.claude/skills/manage-adr/SKILL.md`](../skills/manage-adr/SKILL.md) for authoring rules.
