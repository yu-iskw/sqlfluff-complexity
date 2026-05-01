# P0 sqlfluff-complexity trust and reporting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship contributor explainability, deduplicated nested-select rule crawls, JSON report format, SARIF properties, `config-check` CLI, and minimal docs without new CPX codes or dbt artifacts.

**Architecture:** Single tree walk in `_MetricCounter` produces both `ComplexityMetrics` and `MetricContributor` rows; `collect_metrics` delegates to `analyze_segment_tree`. Rules skip nested `select_statement` via `is_nested_select_statement`. Report formats share `ReportEntry` data.

**Tech Stack:** Python 3.10+, SQLFluff, stdlib `json`, dataclasses.

---

### Task 1: Analysis API and segment tree

**Files:**

- Create: `src/sqlfluff_complexity/core/analysis.py`
- Modify: `src/sqlfluff_complexity/core/segment_tree.py`

- [x] Implement `MetricContributor`, `ComplexityAnalysis`, `analyze_segment_tree`, helpers; extend `_MetricCounter`; wire `collect_metrics` to analysis.

### Task 2: Rules and CPX_C201 messaging

**Files:**

- Modify: `src/sqlfluff_complexity/rules/base.py`, `c102`–`c106`, `c201_aggregate_score.py`

- [x] Add `skip_nested_select_statement`; C201 uses `format_contributor_examples`.

### Task 3: Report JSON, SARIF properties, config-check

**Files:**

- Modify: `src/sqlfluff_complexity/report.py`, `src/sqlfluff_complexity/cli.py`

- [x] `format_json_report`, SARIF `properties`, `load_fluff_config`, `validate_cpx_plugin_config`, `config-check` subcommand.

### Task 4: Tests and docs

**Files:**

- Tests under `src/sqlfluff_complexity/tests/`
- Docs: `docs/reporting.md`, `docs/configuration.md`, `README.md`

- [x] Unit and CLI tests; fixture SQL for nested join and CTE cases.

**Plan complete and saved to `docs/superpowers/plans/2026-05-01-p0-sqlfluff-complexity-trust.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks.

**2. Inline Execution** — execute tasks in this session using executing-plans with checkpoints.

**Which approach?** (Already executed inline in the agent session that produced this branch.)
