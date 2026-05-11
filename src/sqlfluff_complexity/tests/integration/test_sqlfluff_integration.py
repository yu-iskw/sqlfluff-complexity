"""SQLFluff integration tests for plugin discovery and configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from sqlfluff_complexity import get_rules
from sqlfluff_complexity.core.config.presets import WEIGHT_JSON
from sqlfluff_complexity.tests.sqlfluff_helpers import join_sql, lint_sql, rule_violations

ALL_CPX_RULE_CODES = {
    "CPX_C101",
    "CPX_C102",
    "CPX_C103",
    "CPX_C104",
    "CPX_C105",
    "CPX_C106",
    "CPX_C107",
    "CPX_C108",
    "CPX_C109",
    "CPX_C110",
    "CPX_C201",
}
ALL_CPX_RULE_LIST = ",".join(sorted(ALL_CPX_RULE_CODES))

_C201_WEIGHTS_PARTIAL_MULTILINE_INI = (
    "complexity_weights =\n"
    '            {\n              "joins": 2,\n              "derived_tables": 0\n            }\n'
    "        mode = enforce"
)


def test_sqlfluff_discovers_cpx_rule_by_code() -> None:
    """SQLFluff should discover CPX rules by rule code through the plugin entry point."""
    linted = lint_sql(
        join_sql(join_count=2),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102

        [sqlfluff:rules:CPX_C102]
        max_joins = 1
        """,
    )

    violations = rule_violations(linted, "CPX_C102")

    assert len(violations) == 1
    assert "join count 2 exceeds max_joins=1" in violations[0].desc()


def test_sqlfluff_loads_plugin_default_config() -> None:
    """SQLFluff should load CPX defaults from the plugin default config resource."""
    linted = lint_sql(
        join_sql(join_count=9),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102
        """,
    )

    violations = rule_violations(linted, "CPX_C102")

    assert len(violations) == 1
    assert "join count 9 exceeds max_joins=8" in violations[0].desc()


def test_sqlfluff_accepts_all_cpx_rule_codes() -> None:
    """SQLFluff should accept every CPX rule code in normal rule selection config."""
    linted = lint_sql(
        "select 1 as id",
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C101,CPX_C102,CPX_C103,CPX_C104,CPX_C105,CPX_C106,CPX_C107,CPX_C108,CPX_C109,CPX_C110,CPX_C201
        """,
    )

    assert [violation.rule_code() for violation in linted.violations] == []


@pytest.mark.parametrize(
    "c201_weights_tail",
    [
        pytest.param(
            f"complexity_weights = {WEIGHT_JSON}\n        mode = enforce",
            id="preset_default_json",
        ),
        pytest.param(
            'complexity_weights = {"joins": 2, "derived_tables": 0}\n        mode = enforce',
            id="partial_inline_json",
        ),
        pytest.param(_C201_WEIGHTS_PARTIAL_MULTILINE_INI, id="partial_multiline_ini"),
    ],
)
def test_sqlfluff_applies_plugin_config_keywords_json_weights(c201_weights_tail: str) -> None:
    """CPX_C201 ``complexity_weights`` JSON (inline or multiline INI) loads with path_overrides."""
    linted = lint_sql(
        join_sql(join_count=2),
        f"""
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102

        [sqlfluff:rules:CPX_C102]
        max_joins = 8

        [sqlfluff:rules:CPX_C201]
        max_complexity_score = 60
        {c201_weights_tail}
        path_overrides =
            models/*.sql:max_joins=2
            models/staging/*.sql:max_joins=1
        """,
        fname=str(Path("models/staging/orders.sql")),
    )

    violations = rule_violations(linted, "CPX_C102")

    assert len(violations) == 1
    assert "join count 2 exceeds max_joins=1" in violations[0].desc()


def test_sqlfluff_surfaces_invalid_complexity_weights_json_value() -> None:
    """Non-integer JSON weight values should surface during lint (not silent mis-scoring)."""
    linted = lint_sql(
        "select 1",
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C201

        [sqlfluff:rules:CPX_C201]
        complexity_weights = {"joins":"not-an-int"}
        """,
    )

    descriptions = " ".join(v.desc() for v in linted.violations)
    assert len(linted.violations) >= 1
    assert "Complexity weight" in descriptions or "integer" in descriptions.lower()


def test_cpx_c201_reports_templated_select_when_ignoring_templated_areas() -> None:
    """CPX_C201 should survive SQLFluff's default templated-area filtering."""
    linted = lint_sql(
        """
        {% set payment_methods = ['credit_card', 'coupon'] %}

        select
            {% for payment_method in payment_methods %}
            sum(
                case
                    when payment_method = '{{ payment_method }}' then amount
                    else 0
                end
            ) as {{ payment_method }}_amount{% if not loop.last %},{% endif %}
            {% endfor %}
        from payments
        """,
        """
        [sqlfluff]
        dialect = bigquery
        templater = jinja
        rules = CPX_C201
        ignore_templated_areas = True

        [sqlfluff:rules:CPX_C201]
        max_complexity_score = 1
        """,
    )

    violations = rule_violations(linted, "CPX_C201")

    assert len(violations) == 1
    assert "aggregate complexity score" in violations[0].desc()
    assert "max_complexity_score=1" in violations[0].desc()


def test_all_cpx_rules_report_through_native_lint_on_templated_sql() -> None:
    """Every CPX rule should survive native SQLFluff linting on templated SQL."""
    # Keep real project fixtures like jaffle_shop/orders.sql as smoke tests for
    # actual configured violations. This synthetic query intentionally exercises
    # every CPX metric so one test can verify the native lint contract.
    linted = lint_sql(
        """
        {% set relation_name = 'base_table' %}

        with a as (
            select * from {{ relation_name }}
        ),
        b as (
            select * from a
        ),
        c as (
            select * from b
        )
        select
            case
                when a.id = 1 and b.id = 2 or c.id = 3 then
                    row_number() over (partition by a.id order by b.id)
                else (
                    select max(x.id)
                    from other_table as x
                    where x.id = a.id
                )
            end as metric
        from a
        join b on a.id = b.id
        join c on b.id = c.id
        join (select id from c) as d on d.id = c.id
        union all
        select 1 as metric
        """,
        f"""
        [sqlfluff]
        dialect = bigquery
        templater = jinja
        rules = {ALL_CPX_RULE_LIST}
        ignore_templated_areas = True

        [sqlfluff:rules:CPX_C101]
        max_ctes = 0
        [sqlfluff:rules:CPX_C102]
        max_joins = 0
        [sqlfluff:rules:CPX_C103]
        max_subquery_depth = 0
        [sqlfluff:rules:CPX_C104]
        max_case_expressions = 0
        [sqlfluff:rules:CPX_C105]
        max_boolean_operators = 0
        [sqlfluff:rules:CPX_C106]
        max_window_functions = 0
        [sqlfluff:rules:CPX_C107]
        max_cte_dependency_depth = 0
        [sqlfluff:rules:CPX_C108]
        max_nested_case_depth = 0
        [sqlfluff:rules:CPX_C109]
        max_set_operations = 0
        [sqlfluff:rules:CPX_C110]
        max_derived_tables = 0
        [sqlfluff:rules:CPX_C201]
        max_complexity_score = 0
        mode = enforce
        """,
        fname="all_cpx.sql",
    )

    actual_rule_codes = {violation.rule_code() for violation in linted.violations}

    assert actual_rule_codes >= ALL_CPX_RULE_CODES


def test_cpx_rules_target_templated_sql() -> None:
    """CPX rules analyze rendered SQL, so SQLFluff should not filter templated anchors."""
    cpx_rules = get_rules()

    assert cpx_rules
    assert all(getattr(rule, "targets_templated", False) for rule in cpx_rules)
