"""False-positive regression tests for CPX metric counting.

Each test asserts that a specific SQL pattern produces the expected metric values
and does NOT trigger violations under standard thresholds.  Tests are named after
the pattern they guard against, not the rule code.

These are P0 accuracy tests and run in the default suite (not @pytest.mark.dialect_extra).
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlfluff.core import Linter

from sqlfluff_complexity.core.scan.segment_tree import collect_metrics
from sqlfluff_complexity.tests.fixture_loader import read_sql_fixture
from sqlfluff_complexity.tests.sqlfluff_helpers import lint_sql, rule_violations


def _metrics(sql: str, *, dialect: str) -> Any:
    parsed = Linter(dialect=dialect).parse_string(sql)
    assert parsed.tree is not None, f"SQLFluff failed to parse {dialect!r} SQL"
    return collect_metrics(parsed.tree)


# ---------------------------------------------------------------------------
# Boolean operators (C105)
# ---------------------------------------------------------------------------


def test_boolean_operators_zero_when_only_case_and_equality() -> None:
    """CASE/WHEN expressions and equality predicates must not inflate boolean_operators.

    A CASE WHEN clause is not a boolean operator (AND/OR).  A single equality
    predicate ``WHERE region = 'US'`` contains no logical connectives.
    """
    sql = read_sql_fixture("ansi", "c105_negative_no_boolean_operators")
    m = _metrics(sql, dialect="ansi")
    assert m.boolean_operators == 0, f"Expected 0 boolean_operators for CASE-only query; got {m.boolean_operators}"


def test_boolean_operators_zero_bigquery_case_only() -> None:
    """BigQuery CASE WHEN without AND/OR must produce zero boolean_operators."""
    sql = read_sql_fixture("bigquery", "c105_negative_no_boolean_operators")
    m = _metrics(sql, dialect="bigquery")
    assert m.boolean_operators == 0


def test_boolean_operators_zero_snowflake_case_only() -> None:
    """Snowflake CASE with QUALIFY must not inflate boolean_operators when no AND/OR."""
    sql = read_sql_fixture("snowflake", "c105_negative_no_boolean_operators")
    m = _metrics(sql, dialect="snowflake")
    assert m.boolean_operators == 0


def test_boolean_operators_zero_sparksql_case_only() -> None:
    """SparkSQL CASE WHEN without AND/OR must produce zero boolean_operators."""
    sql = read_sql_fixture("sparksql", "c105_negative_no_boolean_operators")
    m = _metrics(sql, dialect="sparksql")
    assert m.boolean_operators == 0


def test_boolean_operators_zero_postgres_case_only() -> None:
    """Postgres CASE WHEN without AND/OR must produce zero boolean_operators."""
    sql = read_sql_fixture("postgres", "c105_negative_no_boolean_operators")
    m = _metrics(sql, dialect="postgres")
    assert m.boolean_operators == 0


# ---------------------------------------------------------------------------
# CTE bodies not double-counted as derived tables (C110)
# ---------------------------------------------------------------------------


def test_cte_bodies_not_counted_as_derived_tables_ansi() -> None:
    """A CTE body (SELECT inside WITH) must not be counted as a derived table.

    CTEs are named subqueries, not inline FROM subqueries.  Counting them as
    derived tables would cause false positives for any query that uses CTEs.
    """
    sql = read_sql_fixture("ansi", "c101_negative_cte_not_derived_table")
    m = _metrics(sql, dialect="ansi")
    assert m.derived_tables == 0, f"Expected 0 derived_tables for CTE-only query; got {m.derived_tables}"
    assert m.ctes == 2


def test_cte_bodies_not_counted_as_derived_tables_postgres() -> None:
    """Postgres: CTE bodies must not be counted as derived tables."""
    sql = read_sql_fixture("postgres", "c110_negative_cte_not_derived_table")
    m = _metrics(sql, dialect="postgres")
    assert m.derived_tables == 0
    assert m.ctes == 2


def test_cte_bodies_not_counted_as_derived_tables_bigquery() -> None:
    """BigQuery: two-CTE query must have 0 derived tables and 2 CTEs."""
    sql = read_sql_fixture("bigquery", "c101_passing_two_ctes")
    m = _metrics(sql, dialect="bigquery")
    assert m.derived_tables == 0
    assert m.ctes == 2


def test_cte_bodies_not_counted_as_derived_tables_snowflake() -> None:
    """Snowflake: two-CTE query must have 0 derived tables and 2 CTEs."""
    sql = read_sql_fixture("snowflake", "c101_passing_two_ctes")
    m = _metrics(sql, dialect="snowflake")
    assert m.derived_tables == 0
    assert m.ctes == 2


def test_cte_bodies_not_counted_as_derived_tables_sparksql() -> None:
    """SparkSQL: two-CTE query must have 0 derived tables and 2 CTEs."""
    sql = read_sql_fixture("sparksql", "c101_passing_two_ctes")
    m = _metrics(sql, dialect="sparksql")
    assert m.derived_tables == 0
    assert m.ctes == 2


# ---------------------------------------------------------------------------
# Set operation counting without duplicate violations (C109)
# ---------------------------------------------------------------------------


def test_no_set_operations_for_simple_select() -> None:
    """A plain SELECT with no UNION/INTERSECT/EXCEPT must have 0 set_operation_count."""
    sql = read_sql_fixture("ansi", "c109_negative_no_set_operations")
    m = _metrics(sql, dialect="ansi")
    assert m.set_operation_count == 0


# ---------------------------------------------------------------------------
# Dialect-specific false-positive guards
# ---------------------------------------------------------------------------


def test_bigquery_unnest_from_not_a_derived_table() -> None:
    """BigQuery UNNEST() as a table function in FROM must not be counted as a derived table.

    UNNEST([...]) is a table-valued function, not a bracketed SELECT subquery.
    Counting it as a derived table would produce a false C110 violation on any
    BigQuery array-unpacking query.
    """
    sql = read_sql_fixture("bigquery", "c110_negative_unnest_from")
    m = _metrics(sql, dialect="bigquery")
    assert m.derived_tables == 0, f"Expected 0 derived_tables for UNNEST-only query; got {m.derived_tables}"
    assert m.subquery_depth == 0


def test_bigquery_cross_join_unnest_not_derived_table() -> None:
    """BigQuery CROSS JOIN UNNEST must count as a JOIN but not as a derived table.

    CROSS JOIN UNNEST(array_col) is a join operation over a table function.
    It produces a join (C102) but not a FROM subquery (C110).
    """
    sql = read_sql_fixture("bigquery", "c102_negative_cross_join_unnest")
    m = _metrics(sql, dialect="bigquery")
    assert m.derived_tables == 0, f"Expected 0 derived_tables for CROSS JOIN UNNEST; got {m.derived_tables}"


def test_bigquery_schema_qualified_names_not_cte_deps() -> None:
    """Schema-qualified names (project.dataset.table) must not be treated as CTE references.

    A qualified name like `project.dataset.customers` cannot refer to a CTE
    because CTEs use bare identifiers.  Treating qualified names as CTE
    dependencies would inflate cte_dependency_depth for any BigQuery query.
    """
    sql = read_sql_fixture("bigquery", "c107_negative_schema_qualified_names")
    m = _metrics(sql, dialect="bigquery")
    assert m.cte_dependency_depth <= 1, (
        f"Expected cte_dependency_depth <= 1 (one CTE, no deps); got {m.cte_dependency_depth}"
    )


def test_snowflake_flatten_not_a_derived_table() -> None:
    """Snowflake LATERAL FLATTEN must not be counted as a derived table.

    LATERAL FLATTEN(input => col) is a Snowflake-specific table function, not
    an inline SELECT subquery.  Treating it as a derived table would produce
    false C110 violations on any Snowflake JSON-unpacking pattern.
    """
    sql = read_sql_fixture("snowflake", "c110_negative_flatten")
    m = _metrics(sql, dialect="snowflake")
    assert m.derived_tables == 0, f"Expected 0 derived_tables for LATERAL FLATTEN; got {m.derived_tables}"
    assert m.joins == 0


def test_sparksql_lateral_view_not_a_derived_table() -> None:
    """SparkSQL LATERAL VIEW EXPLODE must not be counted as a derived table.

    LATERAL VIEW EXPLODE(array_col) is a Spark-specific table generator syntax,
    not an inline SELECT subquery.  Treating it as a derived table would produce
    false C110 violations on any Spark array-expansion query.
    """
    sql = read_sql_fixture("sparksql", "c110_negative_lateral_view")
    m = _metrics(sql, dialect="sparksql")
    assert m.derived_tables == 0, f"Expected 0 derived_tables for LATERAL VIEW; got {m.derived_tables}"


def test_sparksql_lateral_view_not_counted_as_join() -> None:
    """SparkSQL LATERAL VIEW without JOIN keyword must not count as a join.

    LATERAL VIEW is its own syntactic form (not JOIN).  The joins metric (C102)
    should count only explicit JOIN clauses.
    """
    sql = read_sql_fixture("sparksql", "c102_negative_lateral_view_not_join")
    m = _metrics(sql, dialect="sparksql")
    assert m.joins == 0, f"Expected 0 joins for LATERAL VIEW without explicit JOIN; got {m.joins}"
    assert m.derived_tables == 0


def test_postgres_scalar_subquery_not_a_derived_table() -> None:
    """Postgres scalar subquery in SELECT list must not be counted as a derived table.

    A correlated scalar subquery ``(SELECT max(...) FROM ... WHERE ...)`` in the
    SELECT column list is NOT in the FROM clause.  The derived_tables metric
    (C110) counts only FROM-position subqueries.  Scalar subqueries belong to
    the subqueries/subquery_depth metrics (C103).
    """
    sql = read_sql_fixture("postgres", "c110_negative_scalar_subquery")
    m = _metrics(sql, dialect="postgres")
    assert m.derived_tables == 0, f"Expected 0 derived_tables for scalar subquery in SELECT; got {m.derived_tables}"


# ---------------------------------------------------------------------------
# No-violation guard using lint path
# ---------------------------------------------------------------------------


def test_c101_two_ctes_no_violation_with_default_threshold() -> None:
    """Two CTEs must not trigger CPX_C101 with the default threshold of 8."""
    sql = read_sql_fixture("postgres", "c101_passing_two_ctes")
    linted = lint_sql(
        sql,
        """
        [sqlfluff]
        dialect = postgres
        rules = CPX_C101

        [sqlfluff:rules:CPX_C101]
        max_ctes = 8
        """,
    )
    violations = rule_violations(linted, "CPX_C101")
    assert violations == [], f"Expected no CPX_C101 violations for 2 CTEs with max_ctes=8; got {violations}"


def test_c110_no_violation_for_cte_only_query() -> None:
    """A CTE-only query with no inline FROM subqueries must not trigger CPX_C110."""
    sql = read_sql_fixture("ansi", "c101_negative_cte_not_derived_table")
    linted = lint_sql(
        sql,
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C110

        [sqlfluff:rules:CPX_C110]
        max_derived_tables = 1
        """,
    )
    violations = rule_violations(linted, "CPX_C110")
    assert violations == [], f"Expected no CPX_C110 violations for CTE-only query; got {violations}"


@pytest.mark.parametrize("dialect", ["bigquery", "snowflake", "sparksql", "postgres"])
def test_two_ctes_do_not_violate_c101_at_default_threshold(dialect: str) -> None:
    """All official dialects: 2 CTEs must not trigger CPX_C101 with max_ctes=8."""
    sql = read_sql_fixture(dialect, "c101_passing_two_ctes")
    linted = lint_sql(
        sql,
        f"""
        [sqlfluff]
        dialect = {dialect}
        rules = CPX_C101

        [sqlfluff:rules:CPX_C101]
        max_ctes = 8
        """,
    )
    violations = rule_violations(linted, "CPX_C101")
    assert violations == [], f"Dialect {dialect!r}: expected no CPX_C101 violations for 2 CTEs; got {violations}"
