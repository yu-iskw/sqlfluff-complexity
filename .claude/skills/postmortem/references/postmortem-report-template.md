# Postmortem report template

Canonical headings for postmortem chat output; prefer changing guardrails in [`SKILL.md`](../SKILL.md) over tuning this file for nits.

## Report body

Include only the following sections in the chat postmortem. **Do not** include this `## Report body` heading in the report—only the `###` headings below.

### Session summary

- **Goal:**
- **Outcome:** (met / partial / not met)
- **Scope:** (files, packages, or areas touched)

### What went well

- (max 5 bullets)

### What did not go well

- (max 5 bullets)

### Root causes

- Distinguish **requirements ambiguity**, **tooling or environment**, **repo or convention misunderstanding**, and **execution mistakes** where relevant.

### Inefficiencies and token sinks

- Specific examples (e.g. wrong command, repeated search, missed `AGENTS.md` gate, false assumptions).

### Changes for next session

- **Must:** (max 3)
- **Should:**
- **Consider:**

### Suggested documentation or skill updates

- Either **None warranted** or, if guardrail (3) applies, **Target file** + **Proposed addition** (short snippet only).
