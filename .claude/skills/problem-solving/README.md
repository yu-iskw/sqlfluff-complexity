# Problem Solving

Companion README for [`SKILL.md`](SKILL.md). Load this skill when you want a **single-pass** XY-aware analysis: clarify stated problem vs underlying intent, compare **n** approaches (default 5) with **0–100** scores, and output using [`assets/templates/analysis-report.md`](assets/templates/analysis-report.md).

## Triggers (examples)

- “Analyze approaches for …”, “Compare options for …”, “What’s the best way to …?”

## Layout

```text
problem-solving/
├── SKILL.md
├── README.md
└── assets/templates/analysis-report.md
```

This repository may ship other skills under [`.claude/skills/`](..); pick the skill whose frontmatter **description** matches your task. Routing for decision-support variants is summarized in [AGENTS.md](../../../AGENTS.md) (Claude Code skills table).
