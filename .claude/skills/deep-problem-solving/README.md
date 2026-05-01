# Deep Problem Solving

Companion README for [`SKILL.md`](SKILL.md). Interactive decision support: deep framing, then **exactly ten** multiple-choice questions (one per turn), then a scored comparison and recommendation. Output uses [`references/full-report-template.md`](references/full-report-template.md).

## Triggers (examples)

- “Don’t jump to a solution—ask me questions first, then compare options with scores.”
- High-stakes architecture or strategy where priorities need to be elicited before scoring.

## Layout

```text
deep-problem-solving/
├── SKILL.md
├── README.md
└── references/full-report-template.md
```

This repository may ship other skills under [`.claude/skills/`](..); pick the skill whose frontmatter **description** matches your task. Routing for decision-support variants is summarized in [AGENTS.md](../../../AGENTS.md) (Claude Code skills table).
