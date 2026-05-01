# ADR concepts (this repository)

Architecture Decision Records document **why** a significant choice was made, not a
mirror of implementation files.

## Canonical in-repo entry

- [ADR 0001 — Record architecture decisions](../../../../docs/adr/0001-record-architecture-decisions.md) — adopts ADRs for this project.

## External background

- [Documenting architecture decisions (Michael Nygard)](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions)
- [adr-tools](https://github.com/npryce/adr-tools) — CLI for numbering, linking, and TOC

## Local policy

Decision-first authoring and drift handling are defined in:

- [`.claude/skills/manage-adr/SKILL.md`](../SKILL.md) — what belongs in an ADR
- [`references/adr-granularity.md`](adr-granularity.md) — examples and heuristics
- [`.claude/commands/mend-adr.md`](../../../commands/mend-adr.md) — intent-first drift checks
