# Copyright 2025 yu-iskw
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""SQLFluff plugin for SQL and dbt model complexity rules."""

from __future__ import annotations

import importlib.metadata
from typing import TYPE_CHECKING, Any

from sqlfluff.core.config import load_config_resource
from sqlfluff.core.plugin import hookimpl

try:
    __version__ = importlib.metadata.version("sqlfluff-complexity")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

if TYPE_CHECKING:
    from sqlfluff.core.rules import BaseRule


@hookimpl
def get_rules() -> list[type[BaseRule]]:
    """Register SQLFluff complexity rules."""
    # SQLFluff expects plugin rule classes to be imported lazily from this hook.
    # pylint: disable=import-outside-toplevel
    from sqlfluff_complexity.rules.c101_too_many_ctes import (  # noqa: PLC0415
        Rule_CPX_C101,
    )
    from sqlfluff_complexity.rules.c102_too_many_joins import (  # noqa: PLC0415
        Rule_CPX_C102,
    )
    from sqlfluff_complexity.rules.c103_subquery_depth import (  # noqa: PLC0415
        Rule_CPX_C103,
    )
    from sqlfluff_complexity.rules.c104_too_many_case import (  # noqa: PLC0415
        Rule_CPX_C104,
    )
    from sqlfluff_complexity.rules.c105_boolean_complexity import (  # noqa: PLC0415
        Rule_CPX_C105,
    )
    from sqlfluff_complexity.rules.c106_too_many_windows import (  # noqa: PLC0415
        Rule_CPX_C106,
    )
    from sqlfluff_complexity.rules.c107_cte_dependency_depth import (  # noqa: PLC0415
        Rule_CPX_C107,
    )
    from sqlfluff_complexity.rules.c108_nested_case_depth import (  # noqa: PLC0415
        Rule_CPX_C108,
    )
    from sqlfluff_complexity.rules.c109_set_operations import (  # noqa: PLC0415
        Rule_CPX_C109,
    )
    from sqlfluff_complexity.rules.c201_aggregate_score import (  # noqa: PLC0415
        Rule_CPX_C201,
    )

    return [
        Rule_CPX_C101,
        Rule_CPX_C102,
        Rule_CPX_C103,
        Rule_CPX_C104,
        Rule_CPX_C105,
        Rule_CPX_C106,
        Rule_CPX_C107,
        Rule_CPX_C108,
        Rule_CPX_C109,
        Rule_CPX_C201,
    ]


@hookimpl
def load_default_config() -> dict[str, Any]:
    """Load plugin default configuration."""
    return load_config_resource(
        package="sqlfluff_complexity",
        file_name="plugin_default_config.cfg",
    )


@hookimpl
def get_configs_info() -> dict[str, dict[str, Any]]:
    """Expose plugin configuration metadata."""
    return {
        "max_ctes": {
            "definition": "Maximum CTEs allowed in one statement.",
        },
        "max_joins": {
            "definition": "Maximum JOIN clauses allowed in one statement.",
        },
        "max_subquery_depth": {
            "definition": "Maximum nested subquery depth allowed in one statement.",
        },
        "max_case_expressions": {
            "definition": "Maximum CASE expressions allowed in one statement.",
        },
        "max_boolean_operators": {
            "definition": "Maximum boolean AND/OR operators allowed in one statement.",
        },
        "max_window_functions": {
            "definition": "Maximum window functions allowed in one statement.",
        },
        "max_cte_dependency_depth": {
            "definition": (
                "Maximum longest CTE reference chain within one WITH clause "
                "(parsed-tree dependency depth)."
            ),
        },
        "max_nested_case_depth": {
            "definition": (
                "Maximum nesting depth of case_expression segments (inner CASE inside outer CASE)."
            ),
        },
        "max_set_operations": {
            "definition": (
                "Maximum set_operator segments (UNION / INTERSECT / EXCEPT arms) in one statement."
            ),
        },
        "max_complexity_score": {
            "definition": "Maximum aggregate complexity score allowed in one statement.",
        },
        "complexity_weights": {
            "definition": ("Comma-separated key:value weights for aggregate complexity scoring."),
        },
        "mode": {
            "definition": "Complexity enforcement mode: enforce or report.",
        },
        "path_overrides": {
            "definition": "Path-specific overrides as <glob>:key=value,key=value lines.",
        },
        "show_contributors": {
            "definition": "When true, append compact contributor locations to metric rule messages.",
        },
        "max_contributors": {
            "definition": "Maximum contributor locations to show per violation (lint and report).",
        },
    }
