---
name: manage-adr
description: Manage Architecture Decision Records (ADRs). Use this to initialize, create, list, and link ADRs to document architectural evolution. Requires 'adr-tools' to be installed.
---

# Manage Architecture Decision Records (ADRs)

Architecture Decision Records (ADRs) are a lightweight way to document the "why" behind significant technical choices.

## Decision Significance Criteria

Use ADRs for decisions that meet one or more of the following criteria:

- **Architectural Impact**: Changes the fundamental structure or flow of the system.
- **Cross-module or cross-cutting**: Decisions that affect multiple subsystems or shared libraries.
- **Strategic Direction**: Significant choices that set a precedent for future development.
- **Non-Obvious Trade-offs**: Choosing between multiple valid approaches where the choice isn't purely technical or has long-term implications.

Do **NOT** use ADRs for:

- **Implementation Specifications**: Detailed API schemas, specific function signatures, or local implementation details (use design docs, README, or code instead).
- **Bug Fixes**: Unless the fix requires a significant architectural change.
- **Routine Changes**: Minor refactorings or style updates.

## ADR (Why) vs. Design Docs / Code (How)

A clear distinction must be maintained:

- **ADR**: Focuses on the **Why**. It documents the decision, the context, the alternatives considered, and the high-level architecture. It is the source of truth for architectural evolution.
- **Design docs, README, and code**: Focus on the **How**. Detailed proposal, technical specifications, design, and implementation tasks live in design docs, package READMEs, or code comments.

When an ADR requires implementation, link to design docs or relevant code in the `References` section.

## Content boundaries (required)

### Include in the ADR

- Context, **alternatives considered**, Decision, Consequences, **trade-offs**
- **Stable invariants** (rules that should survive refactors)
- Links to related ADRs

### Keep out of the ADR

Put these in `pyproject.toml`, Ruff/Pyright config, tests, or package README instead:

- Long file path lists and “directory listing” decisions
- Duplicated **threshold tables** from Ruff, Pyright, pytest, or coverage tools (link to the living config instead)
- Exhaustive filename or public-API inventories that belong in reference docs

### Pointers

- At most **one coarse pointer per concern** (package or subsystem), e.g. “error handling in `your_package.api`”—not five relative paths.

Granularity and anti-patterns: [references/adr-granularity.md](references/adr-granularity.md).

## Anti-patterns (do not)

- A Decision section that reads like a **folder tree** or file manifest
- An Amendment whose only purpose is to **update paths** after a move (intent unchanged)
- Mermaid diagrams that mirror **repository layout** instead of concepts, boundaries, or data flow—unless the ADR is literally about repository layout

## Relationship to `mend-adr`

- **`manage-adr`**: authoring and lifecycle (create, supersede, link, organize).
- **`mend-adr`**: drift workflow when behavior may no longer match an Accepted ADR—short, decision-level updates; keep volatile detail in code and config.

Command reference: [`.claude/commands/mend-adr.md`](../../../.claude/commands/mend-adr.md).

## Instructions

### 1. Initialization

If ADRs are not yet initialized in the project, run:

```bash
adr init docs/adr
```

This ensures records are created in `docs/adr`.

### 2. Creating a New ADR

To create a new ADR, use the provided script to ensure non-interactive creation:

```bash
.claude/skills/manage-adr/scripts/create-adr.sh "Title of the ADR"
```

After creation, the script will output the filename. You **MUST** then edit the file to fill in the Context, Decision, and Consequences.

### 3. Superseding an ADR

If a new decision replaces an old one, use the `-s` flag:

```bash
.claude/skills/manage-adr/scripts/create-adr.sh -s <old-adr-number> "New Decision Title"
```

### 4. Linking ADRs

To link two existing ADRs (e.g., ADR 12 amends ADR 10):

```bash
adr link 12 Amends 10 "Amended by"
```

### 5. Listing and Viewing

- List all ADRs: `adr list`
- Read a specific ADR: `read_file docs/adr/NNNN-title.md`

### 6. Generating Reports

- Generate a Table of Contents: `adr generate toc`
- Generate a dependency graph (requires Graphviz): `adr generate graph | dot -Tpng -o adr-graph.png`

### 7. Mermaid diagrams

Prefer **conceptual** diagrams (data flow, trust boundaries, user-visible behavior) over file-tree diagrams unless the ADR is about layout. Put diagrams in the Decision (or Architecture) section using a `mermaid` fenced block; add one short sentence of context before the block.

Examples and diagram types: [references/mermaid-diagrams.md](references/mermaid-diagrams.md).

## Best practices

- One decision per ADR; write for maintainers who lack your current context.
- Always include **alternatives considered** and **trade-offs**; focus rationale (**why**) not implementation dumps (**how**).
- Update status and links when decisions change.
- Philosophy and links: [references/adr-concepts.md](references/adr-concepts.md). New record shape: [`docs/adr/template.md`](../../../docs/adr/template.md).
