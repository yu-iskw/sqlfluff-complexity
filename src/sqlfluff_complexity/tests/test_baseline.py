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

"""Tests for baseline JSON format."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqlfluff_complexity.baseline import (
    baseline_from_report,
    format_baseline_json,
    load_baseline_from_string,
)
from sqlfluff_complexity.core.metrics import ComplexityMetrics
from sqlfluff_complexity.report import ComplexityReport, ReportEntry

_BASELINE_MIN = """{
  "entries": {
    "a.sql": {
      "errors": [],
      "metrics": {
        "boolean_operators": 0,
        "case_expressions": 0,
        "ctes": 0,
        "joins": 0,
        "subqueries": 0,
        "subquery_depth": 0,
        "window_functions": 0
      },
      "score": 0
    }
  },
  "schema_version": "1.0",
  "tool": "sqlfluff-complexity"
}"""


def test_baseline_json_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "a.sql"
    p.write_text("select 1", encoding="utf-8")
    path_key = {p.resolve(): "a.sql"}
    m = ComplexityMetrics()
    report = ComplexityReport(
        entries=[
            ReportEntry(
                path=p,
                metrics=m,
                score=0,
                errors=[],
            ),
        ],
    )
    b = baseline_from_report(report, path_key=path_key)
    text = format_baseline_json(b)
    data = json.loads(text)
    assert data["schema_version"] == "1.0"
    assert data["tool"] == "sqlfluff-complexity"
    again = load_baseline_from_string(text)
    assert again.entries["a.sql"].score == 0
    assert again.entries["a.sql"].metrics is not None


def test_baseline_load_from_string() -> None:
    b = load_baseline_from_string(_BASELINE_MIN)
    assert b.entries["a.sql"].errors == ()


def test_baseline_preserves_errors() -> None:
    p = Path("x.sql")
    report = ComplexityReport(
        entries=[
            ReportEntry(
                path=p,
                errors=["parse failed"],
            ),
        ],
    )
    b = baseline_from_report(report, path_key={p: "x.sql"})
    ent = b.entries["x.sql"]
    assert ent.errors == ("parse failed",)
    assert ent.score is None
    data = json.loads(format_baseline_json(b))
    assert data["entries"]["x.sql"]["errors"] == ["parse failed"]


def test_baseline_rejects_wrong_schema() -> None:
    with pytest.raises(ValueError, match="schema_version"):
        load_baseline_from_string(
            '{"schema_version": "0.1", "tool": "sqlfluff-complexity", "entries": {}}'
        )
