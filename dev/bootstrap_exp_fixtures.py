#!/usr/bin/env python3
"""One-shot writer for expanded ``metrics_*`` SQL fixtures and golden JSON.

**Dialects** use the same rule as ``discover_metrics_fixture_cases()``: each immediate
subdirectory of ``fixtures/sql/`` that contains at least one ``metrics_*.sql`` file.

**Stems** are **only** ``METRICS_BOOTSTRAP_STEMS`` in ``sqlfluff_complexity.tests.fixture_loader``.
Bootstrap does **not** regenerate every ``metrics_*.sql`` that discovery tests; any new
``metrics_*.sql`` outside that tuple needs manual SQL/JSON or an update to
``METRICS_BOOTSTRAP_STEMS`` plus ``sql_for()`` here.

Run from the **repository root** so imports resolve::

    uv run python dev/bootstrap_exp_fixtures.py

Uses the same metric emission path as ``dev/emit_fixture_metrics.py`` (parse tree,
reject ``unparsable``, ``collect_metrics``).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from sqlfluff.core import Linter

from sqlfluff_complexity.core.scan.segment_tree import collect_metrics
from sqlfluff_complexity.tests.fixture_loader import iter_metrics_bootstrap_targets

_DEV_DIR = Path(__file__).resolve().parent
if str(_DEV_DIR) not in sys.path:
    sys.path.insert(0, str(_DEV_DIR))
import fixture_parse_guard  # noqa: E402  # pylint: disable=wrong-import-position

tree_contains_unparsable = fixture_parse_guard.tree_contains_unparsable

_REPO = Path(__file__).resolve().parents[1]
_SQL = _REPO / "src/sqlfluff_complexity/tests/fixtures/sql"
_EXPECTED = _REPO / "src/sqlfluff_complexity/tests/fixtures/expected"


def hdr(url: str, section: str, license_note: str, verbatim: str) -> str:
    return (
        "/*\n"
        f"source_url: {url}\n"
        f"source_section: {section}\n"
        f"license_note: {license_note}\n"
        f"verbatim: {verbatim}\n"
        "*/\n\n"
    )


def emit_json(dialect: str, stem: str, sql: str) -> None:
    parsed = Linter(dialect=dialect).parse_string(sql)
    if parsed.tree is None:
        raise RuntimeError(f"{dialect}/{stem}: parse produced no tree")
    if tree_contains_unparsable(parsed.tree):
        raise RuntimeError(f"{dialect}/{stem}: unparsable segments in tree")
    metrics = collect_metrics(parsed.tree)
    text = json.dumps(asdict(metrics), indent=2, sort_keys=True) + "\n"
    out = _EXPECTED / dialect / f"{stem}.metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def sql_for(dialect: str, stem: str) -> str:
    derived = "Derived minimal SQL for sqlfluff-complexity fixture tests; not vendor verbatim."
    n = "n/a"
    pg_doc = "https://www.postgresql.org/docs/current/sql-createtable.html"

    if stem == "metrics_exp_cpx_ddl":
        h = hdr(pg_doc, "CREATE TABLE", derived, "no")
        bodies = {
            "ansi": "CREATE TABLE cpx_exp_ddl (id INT NOT NULL PRIMARY KEY, name VARCHAR(64));\n",
            "postgres": "CREATE TABLE cpx_exp_ddl (id INTEGER PRIMARY KEY, name TEXT);\n",
            "bigquery": "CREATE TABLE cpx_exp_ddl (id INT64, name STRING);\n",
            "athena": "CREATE TABLE cpx_exp_ddl (id INT, name STRING);\n",
            "redshift": "CREATE TABLE cpx_exp_ddl (id INTEGER, name VARCHAR(128));\n",
            "snowflake": "CREATE OR REPLACE TABLE cpx_exp_ddl (id INT, name VARCHAR);\n",
            "sparksql": "CREATE TABLE cpx_exp_ddl (id INT, name STRING) USING PARQUET;\n",
        }
        return h + bodies[dialect]

    if stem == "metrics_exp_cpx_mutate":
        h = hdr(
            "https://docs.aws.amazon.com/redshift/latest/dg/r_INSERT_30.html",
            "INSERT",
            derived,
            "no",
        )
        # Single-statement insert; dialects parse without requiring pre-existing table.
        return (
            h
            + "INSERT INTO tgt_cpx_exp\n"
            + "SELECT n FROM (VALUES (1), (2)) AS s(n)\n"
            + "WHERE EXISTS (SELECT 1 FROM (VALUES (1)) AS e(x) WHERE e.x = s.n);\n"
        )

    if stem == "metrics_exp_cpx_select":
        h = hdr(n, "Synthetic SELECT", derived, "no")
        return (
            h
            + "WITH base AS (SELECT 1 AS x)\n"
            + "SELECT b.x, row_number() OVER (ORDER BY b.x) AS rn\n"
            + "FROM base AS b\n"
            + "JOIN (SELECT 2 AS y) AS j ON j.y > (SELECT MIN(z) FROM (VALUES (3)) AS t(z));\n"
        )

    if stem == "metrics_exp_cpx_signature":
        if dialect == "bigquery":
            h = hdr(
                "https://cloud.google.com/bigquery/docs/reference/standard-sql/array_functions",
                "ARRAY subquery",
                derived,
                "no",
            )
            return (
                h + "SELECT ARRAY(SELECT v FROM UNNEST([10, 20, 30]) AS v WHERE v > 15) AS arr;\n"
            )
        if dialect == "snowflake":
            h = hdr(
                "https://docs.snowflake.com/en/sql-reference/functions/object_construct",
                "OBJECT_CONSTRUCT",
                derived,
                "no",
            )
            return h + "SELECT OBJECT_CONSTRUCT('k', 1) AS obj;\n"
        if dialect == "sparksql":
            h = hdr(
                "https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-transform.html",
                "TRANSFORM",
                derived,
                "no",
            )
            return h + "SELECT TRANSFORM(ARRAY(1, 2), x -> x + 10) AS bumped;\n"
        if dialect == "postgres":
            h = hdr(
                "https://www.postgresql.org/docs/current/functions-json.html",
                "jsonb_build_object",
                derived,
                "no",
            )
            return h + "SELECT jsonb_build_object('a', 1) AS j;\n"
        if dialect == "athena":
            h = hdr(
                "https://docs.aws.amazon.com/athena/latest/ug/presto-functions.html",
                "cardinality",
                derived,
                "no",
            )
            return h + "SELECT cardinality(ARRAY[1, 2, 3]) AS c;\n"
        if dialect == "redshift":
            h = hdr(
                "https://docs.aws.amazon.com/redshift/latest/dg/r_LISTAGG.html",
                "LISTAGG",
                derived,
                "no",
            )
            return (
                h
                + "SELECT LISTAGG(CAST(1 AS VARCHAR), ',') WITHIN GROUP (ORDER BY 1) AS s "
                + "FROM (SELECT 1 AS n UNION ALL SELECT 2 AS n) AS t;\n"
            )
        h = hdr(n, "CASE + scalar subquery", derived, "no")
        return h + "SELECT CASE WHEN TRUE THEN (SELECT 2) ELSE 0 END AS x;\n"

    if stem == "metrics_wave1_cte_join_window":
        h = hdr(n, "Synthetic CTE + join + window", derived, "no")
        return (
            h
            + "WITH w1 AS (SELECT 1 AS k)\n"
            + "SELECT w1.k, rank() OVER (ORDER BY w1.k) AS r\n"
            + "FROM w1\n"
            + "INNER JOIN (SELECT 2 AS m) AS j ON w1.k < j.m;\n"
        )

    if stem == "metrics_wave1_derived_union":
        h = hdr(n, "UNION ALL", derived, "no")
        return h + "(SELECT 1 AS key_src) UNION ALL (SELECT 2 AS key_src);\n"

    if stem == "metrics_wave1_exists_boolean":
        h = hdr(n, "EXISTS + boolean", derived, "no")
        return (
            h
            + "SELECT 1\n"
            + "WHERE EXISTS (SELECT n FROM (VALUES (1)) AS x(n) WHERE x.n = 1)\n"
            + "  AND (1 = 1 OR 2 = 2);\n"
        )

    if stem == "metrics_wave1_insert_archive":
        h = hdr(n, "INSERT SELECT", derived, "no")
        return (
            h
            + "INSERT INTO arch_cpx_w1\n"
            + "SELECT s.a FROM (SELECT CAST(1 AS INT) AS a) AS s WHERE 1 = 1;\n"
        )

    raise KeyError(stem)


def main() -> int:
    for dialect, stem in iter_metrics_bootstrap_targets():
        sql = sql_for(dialect, stem)
        path = _SQL / dialect / f"{stem}.sql"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sql, encoding="utf-8")
        try:
            emit_json(dialect, stem, sql)
        except RuntimeError as exc:
            print(exc, file=sys.stderr)
            return 1
        print(f"OK {dialect}/{stem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
