# ADR Granularity Guide

This guide helps determine when a decision belongs in an ADR and when it belongs in design docs or code.

## The Rule of Thumb

- **ADR** = **The "Why"** (Architecture, Strategy, Trade-offs)
- **Design docs / Code** = **The "How"** (Design, API Spec, Tasks, Implementation)

---

## Examples

### Example 1: Introducing a new package

| Decision                                                       | Granularity         | Why?                                                                                                      |
| :------------------------------------------------------------- | :------------------ | :-------------------------------------------------------------------------------------------------------- |
| **"Create @lightdash-tools/mcp to expose Lightdash to LLMs"**  | **ADR**             | High-level architectural choice. Affects project structure and strategic capability.                      |
| **"Define `get_project` tool schema in @lightdash-tools/mcp"** | **Design doc/code** | Implementation detail. Specific schema and function signatures are better tracked in design docs or code. |

### Example 2: API Versioning

| Decision                                                          | Granularity         | Why?                                                                                         |
| :---------------------------------------------------------------- | :------------------ | :------------------------------------------------------------------------------------------- |
| **"Adopt versioned namespaces (v1/v2) for the Lightdash Client"** | **ADR**             | Strategic decision on how to handle breaking changes and project organization.               |
| **"Implement `client.v2.query.runMetricQuery` endpoint"**         | **Design doc/code** | Part of the implementation of the strategy. Detailed endpoint parameters and response types. |

### Example 3: Error Handling

| Decision                                                             | Granularity         | Why?                                              |
| :------------------------------------------------------------------- | :------------------ | :------------------------------------------------ |
| **"Use centralized error mapping from Lightdash API to MCP errors"** | **ADR**             | Standardizing a pattern across the codebase.      |
| **"Map 404 to `McpError.InvalidRequest`"**                           | **Design doc/code** | Specific mapping logic within the chosen pattern. |

---

## Checklist for ADRs

1. Does this decision affect more than one package?
2. Does this decision change how future code should be written?
3. Are there significant alternatives with different trade-offs?
4. If a developer joins the project in 6 months, would they ask "Why did we do it this way?"

If **YES** to any of these, it's an **ADR**.

## Checklist for Design Docs / Code

1. Does this involve specific API paths, schemas, or types?
2. Does this involve a list of specific implementation tasks?
3. Is this a feature implementation within an already decided architecture?

If **YES** to any of these, document in design docs, README, or code.

---

## This monorepo (`dbt-artifacts-parser-ts`)

### Timeline / Gantt focus edges

| In the ADR                                                                                                                                                     | Elsewhere                                                                                                                              |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------- |
| “Focus dependency edges are **ranked**, **capped**, and optionally **multi-hop**; defaults favor richer context with a user-visible way to reduce clutter.”    | Exact state field names (`dependencyDirection`, `dependencyDepthHops`), mapper functions, and filenames under `packages/dbt-tools/web` |
| Boundaries: edges only between rows on the **current filtered** timeline; adjacency comes from the **manifest graph / analysis snapshot**, not ad hoc UI graph | `packages/dbt-tools/core` analysis snapshot and graph build                                                                            |

Use at most one coarse pointer, e.g. “`@dbt-tools/web` timeline Gantt stack,” if disambiguation is needed.

### Lint, coverage, and agent gates

| In the ADR                                                                                                                                                     | Elsewhere                                                                                                                                         |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------ |
| “We enforce **minimum coverage** and **lint** for agent feedback; **complexity** is bounded (SonarJS + structural rules); tests/E2E may use **relaxed** caps.” | Per-rule and per-glob numbers in `eslint.config.mjs`; thresholds in `vitest.config.mjs` and `scripts/coverage-score.mjs`; commands in `AGENTS.md` |

### Theming / color

| In the ADR                                                                                                  | Elsewhere                                                                                                                        |
| :---------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------- |
| “We use **semantic roles**, separate **graph-local** tokens where needed, and a coherent light/dark story.” | Hex values and CSS custom properties in `packages/dbt-tools/web/src/styles/tokens.css` and mirrors in `constants/themeColors.ts` |

### Heuristic

If a sentence contains `packages/` **and** a file extension (`.ts`, `.tsx`, `.css`, `.mjs`),
it probably belongs in **code, README, or config**—not in the ADR body unless it is a
single intentional pointer.
