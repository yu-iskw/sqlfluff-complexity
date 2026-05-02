"""Complexity metric data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

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
    cte_dependency_depth: int = 0
    set_operation_count: int = 0
    expression_depth: int = 0
    anchors: dict[str, list[Any]] = field(default_factory=dict)

    def score(self, weights: Mapping[str, int]) -> int:
        """Compute a weighted aggregate complexity score."""
        return (
            self.ctes * weights.get("ctes", 0)
            + self.joins * weights.get("joins", 0)
            + self.subquery_depth * weights.get("subquery_depth", 0)
            + self.case_expressions * weights.get("case_expressions", 0)
            + self.boolean_operators * weights.get("boolean_operators", 0)
            + self.window_functions * weights.get("window_functions", 0)
            + self.cte_dependency_depth * weights.get("cte_dependency_depth", 0)
            + self.set_operation_count * weights.get("set_operation_count", 0)
            + self.expression_depth * weights.get("expression_depth", 0)
        )

    def format_breakdown(self) -> str:
        """Return a compact metric breakdown for lint messages."""
        return (
            f"ctes={self.ctes}, joins={self.joins}, subquery_depth={self.subquery_depth}, "
            f"case_expressions={self.case_expressions}, "
            f"boolean_operators={self.boolean_operators}, "
            f"window_functions={self.window_functions}, "
            f"cte_dependency_depth={self.cte_dependency_depth}, "
            f"set_operations={self.set_operation_count}, expression_depth={self.expression_depth}"
        )
