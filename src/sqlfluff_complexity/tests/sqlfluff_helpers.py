"""Shared SQLFluff test helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlfluff.core import FluffConfig, Linter
from sqlfluff.core.errors import SQLLintError

if TYPE_CHECKING:
    from sqlfluff.core.errors import SQLBaseError
    from sqlfluff.core.linter.linted_file import LintedFile


def join_sql(join_count: int) -> str:
    """Return simple ANSI SQL with a configurable number of joins."""
    join_lines: list[str] = [
        f"join table_{index} on base.id = table_{index}.id" for index in range(1, join_count + 1)
    ]
    return "select *\nfrom base\n" + "\n".join(join_lines)


def lint_sql(sql: str, config: str, *, fname: str = "model.sql") -> LintedFile:
    """Lint SQL through SQLFluff with a config string."""
    return Linter(config=FluffConfig.from_string(config)).lint_string(sql, fname=fname)


def rule_violations(linted: LintedFile, rule_code: str) -> list[SQLBaseError]:
    """Return violations matching one SQLFluff rule code."""
    return [violation for violation in linted.violations if violation.rule_code() == rule_code]


def single_sql_lint_violation(linted: LintedFile, rule_code: str) -> SQLLintError:
    """Return the sole lint violation for ``rule_code``, narrowed to ``SQLLintError``.

    Intended for **pytest** tests. Uses explicit exceptions (not ``assert``) so checks
    still run under ``python -O``. Wrong count raises ``AssertionError``; wrong type
    raises ``TypeError``.
    """
    violations = rule_violations(linted, rule_code)
    if len(violations) != 1:
        message = f"expected one {rule_code} violation, got {len(violations)}"
        raise AssertionError(message)
    first = violations[0]
    if not isinstance(first, SQLLintError):
        message = f"expected SQLLintError for {rule_code}, got {type(first).__name__}"
        raise TypeError(message)
    return first
