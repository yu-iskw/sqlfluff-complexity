"""SARIF 2.1.0 report built from ComplexityFinding objects."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import quote

from sqlfluff_complexity.core.findings import ComplexityFinding
from sqlfluff_complexity.core.remediation import REMEDIATIONS

SARIF_SCHEMA_URL = "https://json.schemastore.org/sarif-2.1.0.json"


def _sarif_rule_metadata(rule_id: str) -> dict[str, Any]:
    remediation = REMEDIATIONS[rule_id]
    return {
        "fullDescription": {"text": remediation},
        "help": {"text": remediation},
        "helpUri": "https://github.com/sqlfluff/sqlfluff-complexity",
        "id": rule_id,
        "name": rule_id.replace("CPX_", "CPX "),
        "shortDescription": {"text": remediation[:120] + ("..." if len(remediation) > 120 else "")},
    }


def _sarif_rules() -> list[dict[str, Any]]:
    rule_ids = (
        "CPX_C101",
        "CPX_C102",
        "CPX_C103",
        "CPX_C104",
        "CPX_C105",
        "CPX_C106",
        "CPX_C201",
        "CPX_PARSE_ERROR",
    )
    rules = [_sarif_rule_metadata(rid) for rid in rule_ids if rid != "CPX_PARSE_ERROR"]
    rules.append(
        {
            "fullDescription": {"text": "SQLFluff could not parse the input."},
            "help": {"text": "Fix syntax errors so SQLFluff can build a parse tree."},
            "id": "CPX_PARSE_ERROR",
            "name": "SQLFluff parse error",
            "shortDescription": {"text": "Parse error"},
        },
    )
    return rules


def _file_uri(path: Path) -> str:
    """RFC 8087 style file URI for SARIF artifact locations."""
    return "file:///" + quote(str(path.resolve()).replace("\\", "/"), safe="/:@")


def _physical_location(finding: ComplexityFinding) -> dict[str, Any]:
    path = finding.location.path
    if path is None:
        return {
            "physicalLocation": {
                "artifactLocation": {"uri": "file:///"},
                "region": {
                    "startColumn": finding.location.column,
                    "startLine": finding.location.line,
                },
            },
        }
    p = Path(path)
    return {
        "physicalLocation": {
            "artifactLocation": {"uri": _file_uri(p)},
            "region": {
                "startColumn": finding.location.column,
                "startLine": finding.location.line,
            },
        },
    }


def findings_to_sarif_payload(findings: Sequence[ComplexityFinding]) -> dict[str, Any]:
    """Build minimal valid SARIF 2.1.0 with one run and ``results``."""
    results: list[dict[str, Any]] = []
    for finding in findings:
        body: dict[str, Any] = {
            "level": finding.level,
            "locations": [_physical_location(finding)],
            "message": {"text": finding.message},
            "ruleId": finding.rule_id,
        }
        if finding.rule_id != "CPX_PARSE_ERROR":
            prop: dict[str, Any] = {}
            agg = finding.aggregate_score if finding.aggregate_score is not None else finding.score
            if agg is not None:
                prop["score"] = agg
            prop["metrics"] = {
                "boolean_operators": finding.metrics.boolean_operators,
                "case_expressions": finding.metrics.case_expressions,
                "ctes": finding.metrics.ctes,
                "joins": finding.metrics.joins,
                "subqueries": finding.metrics.subqueries,
                "subquery_depth": finding.metrics.subquery_depth,
                "window_functions": finding.metrics.window_functions,
            }
            prop["remediation"] = finding.remediation
            body["properties"] = prop
        results.append(body)

    return {
        "$schema": SARIF_SCHEMA_URL,
        "runs": [
            {
                "results": results,
                "tool": {
                    "driver": {
                        "name": "sqlfluff-complexity",
                        "rules": _sarif_rules(),
                    },
                },
            },
        ],
        "version": "2.1.0",
    }


def write_sarif_report(
    findings: Sequence[ComplexityFinding],
    output: TextIO,
) -> None:
    """Write SARIF JSON to ``output``."""
    payload = findings_to_sarif_payload(findings)
    output.write(json.dumps(payload, indent=2, sort_keys=True))
    output.write("\n")
