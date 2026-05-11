"""Reusable CPX config string fragments for tests."""

from __future__ import annotations

import json

from sqlfluff_complexity.core.config.scoring import DEFAULT_WEIGHTS

# Historical CPX_C201 aggregate fixtures: zero weight on file-level / derived-table metrics.
CPX_C201_SAMPLE_COMPLEXITY_WEIGHTS_JSON = json.dumps(
    {
        **DEFAULT_WEIGHTS,
        "cte_dependency_depth": 0,
        "set_operation_count": 0,
        "expression_depth": 0,
        "derived_tables": 0,
    },
    separators=(",", ":"),
)
