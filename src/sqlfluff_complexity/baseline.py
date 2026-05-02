"""Baseline JSON format and serialization for sqlfluff-complexity."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlfluff_complexity.report import ComplexityReport, ReportEntry


BASELINE_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class BaselineEntry:
    """One file entry in a complexity baseline."""

    score: int | None
    metrics: dict[str, int] | None
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class Baseline:
    """Saved baseline snapshot keyed by normalized relative paths."""

    entries: dict[str, BaselineEntry]
    schema_version: str = BASELINE_SCHEMA_VERSION


def _metrics_from_report_entry(entry: ReportEntry) -> dict[str, int] | None:
    if entry.metrics is None:
        return None
    m = entry.metrics
    return {
        "boolean_operators": m.boolean_operators,
        "case_expressions": m.case_expressions,
        "ctes": m.ctes,
        "joins": m.joins,
        "subqueries": m.subqueries,
        "subquery_depth": m.subquery_depth,
        "window_functions": m.window_functions,
    }


def baseline_from_report(
    report: ComplexityReport,
    *,
    path_key: Mapping[Path, str],
) -> Baseline:
    """Build a baseline from an analyzed report using precomputed path keys."""
    entries: dict[str, BaselineEntry] = {}
    for entry in report.entries:
        key = path_key[entry.path]
        entries[key] = BaselineEntry(
            score=entry.score,
            metrics=_metrics_from_report_entry(entry),
            errors=tuple(entry.errors),
        )
    return Baseline(entries=dict(sorted(entries.items())))


def format_baseline_json(baseline: Baseline) -> str:
    """Serialize baseline to stable JSON (sorted keys, minimal whitespace off)."""
    payload = _baseline_to_dict(baseline)
    return json.dumps(payload, indent=2, sort_keys=True)


def _baseline_to_dict(baseline: Baseline) -> dict[str, object]:
    entries_out: dict[str, object] = {}
    for path, ent in sorted(baseline.entries.items()):
        row: dict[str, object] = {"errors": list(ent.errors)}
        if ent.score is not None:
            row["score"] = ent.score
        if ent.metrics is not None:
            row["metrics"] = dict(sorted(ent.metrics.items()))
        entries_out[path] = row
    return {
        "entries": entries_out,
        "schema_version": baseline.schema_version,
        "tool": "sqlfluff-complexity",
    }


def load_baseline(path: Path) -> Baseline:
    """Load baseline JSON from disk."""
    text = path.read_text(encoding="utf-8")
    return load_baseline_from_string(text)


def _validate_baseline_root(data: object) -> dict[str, Any]:
    if not isinstance(data, dict):
        message = "Baseline root must be a JSON object."
        raise TypeError(message)
    return data


def _parse_entry_raw(path_key: str, raw: object) -> BaselineEntry:
    if not isinstance(raw, dict):
        message = f"Baseline entry for {path_key!r} must be an object."
        raise TypeError(message)
    errors_raw = raw.get("errors", [])
    if not isinstance(errors_raw, list) or not all(isinstance(x, str) for x in errors_raw):
        message = f"Baseline entry for {path_key!r} must have errors: [str, ...]."
        raise TypeError(message)
    score: int | None
    if "score" in raw:
        s = raw["score"]
        if not isinstance(s, int):
            message = f"Baseline score for {path_key!r} must be an integer."
            raise TypeError(message)
        score = s
    else:
        score = None
    metrics: dict[str, int] | None
    if "metrics" in raw:
        m = raw["metrics"]
        if not isinstance(m, dict):
            message = f"Baseline metrics for {path_key!r} must be an object."
            raise TypeError(message)
        metrics = {}
        for mk, mv in m.items():
            if not isinstance(mk, str) or not isinstance(mv, int):
                message = f"Baseline metrics for {path_key!r} must map strings to integers."
                raise TypeError(message)
            metrics[mk] = mv
    else:
        metrics = None
    return BaselineEntry(score=score, metrics=metrics, errors=tuple(errors_raw))


def load_baseline_from_string(text: str) -> Baseline:
    """Parse baseline JSON from a string."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        message = f"Invalid baseline JSON: {exc}"
        raise ValueError(message) from exc
    root = _validate_baseline_root(data)
    schema = root.get("schema_version")
    if schema != BASELINE_SCHEMA_VERSION:
        message = f"Unsupported baseline schema_version: {schema!r} (expected {BASELINE_SCHEMA_VERSION})."
        raise ValueError(message)
    if root.get("tool") != "sqlfluff-complexity":
        message = "Baseline tool field must be 'sqlfluff-complexity'."
        raise ValueError(message)
    raw_entries = root.get("entries")
    if not isinstance(raw_entries, dict):
        message = "Baseline entries must be an object."
        raise TypeError(message)
    entries: dict[str, BaselineEntry] = {}
    for path_key, raw in raw_entries.items():
        if not isinstance(path_key, str):
            message = "Baseline entry keys must be strings."
            raise TypeError(message)
        entries[path_key] = _parse_entry_raw(path_key, raw)
    return Baseline(entries=entries)
