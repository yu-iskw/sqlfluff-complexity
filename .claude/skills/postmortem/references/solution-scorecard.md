# Must-option solution scorecard

Use when **two or more** **Must**-level changes in a postmortem are **mutually exclusive** or **order-ambiguous**. Score each option **0–100** on every perspective below. **Higher is always better**, including **Risk** (higher score = **lower** operational risk: smaller blast radius, easier rollback).

## Default perspectives

### Feasibility

Can ship with available time, tools, and access.

### Impact

Addresses the real failure or goal (not a proxy).

### Maintainability

Low ongoing cost, clear ownership, no doc debt.

### Risk

Low blast radius and reversibility (**score higher = lower risk**).

### Alignment

Matches repo conventions, `AGENTS.md` gates, team constraints.

## Optional sixth perspective

**Token / efficiency** (vs maintainability trade-offs) only if the **user explicitly** asks; default remains **five**.

## Anti-pattern

Scores without evidence: add **at least one short clause** under the table for any cell that is not obvious—otherwise readers cannot audit the numbers.

## Calibration (anchors)

Use as a sanity check; interpolate between.

- **0–20:** Unacceptable for this context (blockers, wrong goal, or unacceptable risk).
- **25–40:** Weak; major gaps or heavy mitigation needed.
- **45–55:** Mixed; viable only with clear compensating controls.
- **60–75:** Solid; normal “good” range for a shippable option.
- **80–90:** Strong; few reservations.
- **95–100:** Rare; reserve for unusually clear wins (avoid grade inflation).

## Output rules

1. **Table first:** One row per **Must** option; columns **Feasibility**, **Impact**, **Maintainability**, **Risk**, **Alignment**, **Avg** (arithmetic mean of the five scores, one decimal if useful).
2. **Rationale:** Below the table, one short clause per non-obvious score.
3. **No empty scores:** Every option gets all five numbers.
4. **Pick one:** State which **Must** path to take and why.

## Tie-breaks

If **Avg** is within **3 points**, prefer:

1. Higher **Impact** (fixes the real goal).
2. Then higher **Alignment** (gates and conventions).
3. Then higher **Risk** score (safer).

If still tied, recommend the **smaller** change or the path that preserves more option value.
