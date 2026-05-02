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

"""Tests for baseline vs current comparison."""

from __future__ import annotations

from pathlib import Path

from sqlfluff_complexity.baseline import Baseline, BaselineEntry
from sqlfluff_complexity.check import compare_report_to_baseline
from sqlfluff_complexity.core.findings import ComplexityFinding, SourceLocation
from sqlfluff_complexity.core.metrics import ComplexityMetrics
from sqlfluff_complexity.report import ComplexityReport, ReportEntry


def _finding(rule_id: str, path: str) -> ComplexityFinding:
    return ComplexityFinding(
        rule_id=rule_id,
        metric="joins",
        message="x",
        remediation="y",
        location=SourceLocation(path=path, line=1, column=1),
        metrics=ComplexityMetrics(),
        score=1,
        threshold=0,
        contributors=(),
        level="warning",
    )


def test_no_regression() -> None:
    p = Path("a.sql").resolve()
    m = ComplexityMetrics(joins=1)
    report = ComplexityReport(
        entries=[ReportEntry(path=p, metrics=m, score=5, findings=[], errors=[])],
    )
    baseline = Baseline(
        entries={
            "a.sql": BaselineEntry(
                score=10,
                metrics={
                    "boolean_operators": 0,
                    "case_expressions": 0,
                    "ctes": 0,
                    "joins": 2,
                    "subqueries": 0,
                    "subquery_depth": 0,
                    "window_functions": 0,
                },
            ),
        },
    )
    r = compare_report_to_baseline(
        report,
        baseline=baseline,
        path_key={p: "a.sql"},
        fail_on="regression",
    )
    assert r.summary.regressions == 0


def test_score_regression() -> None:
    p = Path("a.sql").resolve()
    m = ComplexityMetrics()
    report = ComplexityReport(
        entries=[ReportEntry(path=p, metrics=m, score=20, findings=[], errors=[])],
    )
    baseline = Baseline(
        entries={"a.sql": BaselineEntry(score=10, metrics=None)},
    )
    r = compare_report_to_baseline(
        report,
        baseline=baseline,
        path_key={p: "a.sql"},
        fail_on="regression",
    )
    assert r.summary.regressions == 1
    assert r.results[0].status == "regression"


def test_metric_regression_without_score_increase() -> None:
    p = Path("a.sql").resolve()
    m = ComplexityMetrics(joins=5)
    report = ComplexityReport(
        entries=[ReportEntry(path=p, metrics=m, score=5, findings=[], errors=[])],
    )
    baseline = Baseline(
        entries={
            "a.sql": BaselineEntry(
                score=100,
                metrics={
                    "boolean_operators": 0,
                    "case_expressions": 0,
                    "ctes": 0,
                    "joins": 3,
                    "subqueries": 0,
                    "subquery_depth": 0,
                    "window_functions": 0,
                },
            ),
        },
    )
    r = compare_report_to_baseline(
        report,
        baseline=baseline,
        path_key={p: "a.sql"},
        fail_on="regression",
    )
    assert r.summary.regressions == 1
    assert r.results[0].changed_metrics is not None
    assert "joins" in r.results[0].changed_metrics


def test_new_file_with_findings_regression_mode() -> None:
    p = Path("new.sql").resolve()
    report = ComplexityReport(
        entries=[
            ReportEntry(
                path=p,
                metrics=ComplexityMetrics(),
                score=1,
                findings=[_finding("CPX_C102", str(p))],
                errors=[],
            ),
        ],
    )
    baseline = Baseline(entries={})
    r = compare_report_to_baseline(
        report,
        baseline=baseline,
        path_key={p: "new.sql"},
        fail_on="regression",
    )
    assert r.summary.regressions == 1
    assert r.results[0].status == "new_threshold_violation"


def test_deleted_baseline_file_ignored() -> None:
    p = Path("still.sql").resolve()
    report = ComplexityReport(
        entries=[
            ReportEntry(path=p, metrics=ComplexityMetrics(), score=0, findings=[], errors=[]),
        ],
    )
    baseline = Baseline(
        entries={
            "gone.sql": BaselineEntry(score=99, metrics=None),
            "still.sql": BaselineEntry(score=0, metrics=None),
        },
    )
    r = compare_report_to_baseline(
        report,
        baseline=baseline,
        path_key={p: "still.sql"},
        fail_on="regression",
    )
    assert r.summary.regressions == 0


def test_threshold_mode() -> None:
    p = Path("a.sql").resolve()
    report = ComplexityReport(
        entries=[
            ReportEntry(
                path=p,
                metrics=ComplexityMetrics(),
                score=1,
                findings=[_finding("CPX_C102", str(p))],
                errors=[],
            ),
        ],
    )
    baseline = Baseline(entries={})
    r = compare_report_to_baseline(
        report,
        baseline=baseline,
        path_key={p: "a.sql"},
        fail_on="threshold",
    )
    assert r.summary.threshold_violations == 1


def test_none_mode_skips_findings() -> None:
    p = Path("a.sql").resolve()
    report = ComplexityReport(
        entries=[
            ReportEntry(
                path=p,
                metrics=ComplexityMetrics(),
                score=1,
                findings=[_finding("CPX_C102", str(p))],
                errors=[],
            ),
        ],
    )
    r = compare_report_to_baseline(
        report,
        baseline=Baseline(entries={}),
        path_key={p: "a.sql"},
        fail_on="none",
    )
    assert r.summary.regressions == 0
    assert r.summary.threshold_violations == 0


def test_fail_on_error_error_count() -> None:
    p = Path("bad.sql").resolve()
    report = ComplexityReport(
        entries=[ReportEntry(path=p, errors=["x"], findings=[])],
    )
    r = compare_report_to_baseline(
        report,
        baseline=Baseline(entries={}),
        path_key={p: "bad.sql"},
        fail_on="none",
    )
    assert r.summary.errors == 1
