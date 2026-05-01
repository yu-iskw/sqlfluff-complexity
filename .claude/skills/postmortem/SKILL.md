---
name: postmortem
description: At the end of a coding agent session (Cursor, Claude Code, Codex, Gemini CLI, or similar), summarize outcomes, failures, inefficiencies, and root causes, then output a concise postmortem with ranked Must/Should/Consider improvements. Chat-only output; do not edit project files unless the user explicitly asks. Skip nit-picks and one-off mistakes.
compatibility: Project-level Markdown skill; loadable from standard dirs such as `.cursor/skills/` and `.claude/skills/`. Tool-agnostic; produces a Markdown report in chat with no scripts or repo changes required.
---

# Session postmortem

## Trigger scenarios

Activate when the user says or implies:

- Postmortem, retrospective, session review, end of session
- What went wrong, why we failed, lessons learned, inefficiencies, wasted tokens/time

## Non-goals

- Do **not** edit `AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, `.cursor/skills`, `.claude/skills`, hooks, or subagent files unless the user **explicitly** asks for a follow-up change.
- Do **not** treat this skill as permission to refactor, fix tests, or run commands; stay analytical unless the user combines this with another task.

## Guardrails

1. **Signal only:** If a finding would not materially help a **similar** future session, omit it.
2. **Cap urgency:** At most **three** items under **Must** in "Changes for next session".
3. **Doc updates:** The section **Suggested documentation or skill updates** must be **"None warranted"** unless the issue is **recurring**, **high impact**, and plausibly preventable through focused workflow or verification guidance (e.g. repeated wrong quality gates, wrong tool assumptions, browser runtime drift that unit tests miss, systematic repo misunderstanding).

## Instructions

1. Briefly restate the **session goal** and whether it was **met**, **partially met**, or **not met** (one short paragraph).
2. Read [`references/postmortem-report-template.md`](references/postmortem-report-template.md) if needed, then fill every section it defines with concise bullets or short paragraphs. **Output contract:** emit one Markdown document using **exactly** the `###` sections under **Report body** in that file (same wording and heading level). **Do not** include the reference’s `## Report body` line in the report.
3. End with **Changes for next session** ranked **Must / Should / Consider**.
4. If **two or more** **Must**-level items are **mutually exclusive** or **order-ambiguous**, score those options in chat using [`references/solution-scorecard.md`](references/solution-scorecard.md) (read if not already in context). Output stays in the conversation; do not edit repo files.
5. If and only if guardrail (3) applies, add **Suggested documentation or skill updates** with **proposed wording** as copy-paste snippets (still do not apply edits yourself). Prefer targeted verifier/skill guidance when that would likely prevent the same failure mode in a future session.

## Example (illustrative fragment)

### Example: Changes for next session

- **Must:** Run `make lint` and `make test` from the repo root before claiming complete (per AGENTS.md).
- **Should:** Read `README.md` and the touched package under `src/your_package/` before large edits.
- **Consider:** Delegate broad codebase search when the question spans many directories.

### Example: Suggested documentation or skill updates

None warranted.

### Example: When doc or skill updates are warranted

- Repeated failures from claiming “green” without `make lint` / `make test` at the repo root.
- Repeated Trunk or `uv` version drift between local runs and CI.
- Repeated late discovery of Ruff complexity (`C901`) or type issues after large refactors.
