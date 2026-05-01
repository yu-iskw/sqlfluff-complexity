"""Complexity metric data model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True)
class ComplexityMetrics:
    """Complexity metrics for one SQL segment tree."""

    ctes: int = 0
    joins: int = 0
    subqueries: int = 0
    subquery_depth: int = 0
    case_expressions: int = 0
    boolean_operators: int = 0
    window_functions: int = 0

    def score(self, weights: Mapping[str, int]) -> int:
        """Compute a weighted aggregate complexity score."""
        return (
            self.ctes * weights.get("ctes", 0)
            + self.joins * weights.get("joins", 0)
            + self.subquery_depth * weights.get("subquery_depth", 0)
            + self.case_expressions * weights.get("case_expressions", 0)
            + self.boolean_operators * weights.get("boolean_operators", 0)
            + self.window_functions * weights.get("window_functions", 0)
        )

    def format_breakdown(self) -> str:
        """Return a compact metric breakdown for lint messages."""
        return (
            f"ctes={self.ctes}, joins={self.joins}, subquery_depth={self.subquery_depth}, "
            f"case_expressions={self.case_expressions}, "
            f"boolean_operators={self.boolean_operators}, "
            f"window_functions={self.window_functions}"
        )
