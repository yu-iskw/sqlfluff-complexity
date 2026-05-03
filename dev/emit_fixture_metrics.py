#!/usr/bin/env python3
"""Emit golden ``ComplexityMetrics`` JSON for a ``metrics_*.sql`` test fixture.

Usage::

    uv run python dev/emit_fixture_metrics.py <dialect> <stem>
    uv run python dev/emit_fixture_metrics.py ansi metrics_exp_cpx_ddl --write

By default prints JSON to stdout. ``--write`` updates
``src/sqlfluff_complexity/tests/fixtures/expected/<dialect>/<stem>.metrics.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from sqlfluff.core import Linter

from sqlfluff_complexity.core.scan.segment_tree import collect_metrics

_DEV_DIR = Path(__file__).resolve().parent
if str(_DEV_DIR) not in sys.path:
    sys.path.insert(0, str(_DEV_DIR))
import fixture_parse_guard  # noqa: E402  # pylint: disable=wrong-import-position

tree_contains_unparsable = fixture_parse_guard.tree_contains_unparsable

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = _REPO_ROOT / "src/sqlfluff_complexity/tests/fixtures"
_SQL_ROOT = _FIXTURES / "sql"
_EXPECTED_ROOT = _FIXTURES / "expected"


def _run_emit(dialect: str, stem: str, *, write: bool) -> int:
    sql_path = _SQL_ROOT / dialect / f"{stem}.sql"
    if not sql_path.is_file():
        print(f"Missing SQL fixture: {sql_path}", file=sys.stderr)
        return 2
    sql = sql_path.read_text(encoding="utf-8")
    parsed = Linter(dialect=dialect).parse_string(sql)
    if parsed.tree is None:
        print("Parse produced no tree.", file=sys.stderr)
        return 3
    if tree_contains_unparsable(parsed.tree):
        print("Tree contains unparsable segments; fix SQL before emitting.", file=sys.stderr)
        return 4
    metrics = collect_metrics(parsed.tree)
    text = json.dumps(asdict(metrics), indent=2, sort_keys=True) + "\n"
    if write:
        out = _EXPECTED_ROOT / dialect / f"{stem}.metrics.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Wrote {out}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dialect", help="SQLFluff dialect name (e.g. ansi, bigquery).")
    parser.add_argument("stem", help="Fixture stem without .sql (e.g. metrics_dialect_baseline).")
    parser.add_argument(
        "--write",
        action="store_true",
        help=f"Write metrics JSON under {_EXPECTED_ROOT}/<dialect>/",
    )
    args = parser.parse_args()
    return _run_emit(args.dialect, args.stem, write=args.write)


if __name__ == "__main__":
    raise SystemExit(main())
