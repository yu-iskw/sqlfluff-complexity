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

"""CLI smoke tests."""

from __future__ import annotations

import argparse
import json
from typing import TYPE_CHECKING

from sqlfluff_complexity.cli import _dispatch_cli, main

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_main_exits_successfully() -> None:
    """The initialized package CLI should be callable."""
    assert main([]) == 0


def test_dispatch_no_subcommand_returns_zero() -> None:
    """No subcommand: ``command`` is unset and dispatch returns idle success (see cli docstring)."""
    args = argparse.Namespace(command=None, config_command=None)
    assert _dispatch_cli(args) == 0


def test_report_prints_console_metrics(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The report command should analyze real SQL files through SQLFluff."""
    sql_file = tmp_path / "model.sql"
    sql_file.write_text(
        """
        select *
        from a
        join b on a.id = b.id
        where a.active = true or b.active = true
        """,
        encoding="utf-8",
    )

    assert main(["report", "--dialect", "ansi", str(sql_file)]) == 0

    output = capsys.readouterr().out
    assert "sqlfluff-complexity report" in output
    assert str(sql_file) in output
    assert " 1 " in output


def test_report_writes_sarif_without_sql_text(tmp_path: Path) -> None:
    """SARIF output should include complexity rule IDs without embedding SQL text."""
    sql_file = tmp_path / "wide_join.sql"
    sql_file.write_text(_join_heavy_sql(join_count=9), encoding="utf-8")
    output_file = tmp_path / "report.sarif"

    assert (
        main(
            [
                "report",
                "--dialect",
                "ansi",
                "--format",
                "sarif",
                "--output",
                str(output_file),
                str(sql_file),
            ],
        )
        == 0
    )

    sarif_text = output_file.read_text(encoding="utf-8")
    sarif = json.loads(sarif_text)
    rule_ids = {rule["id"] for rule in sarif["runs"][0]["tool"]["driver"]["rules"]}
    result_rule_ids = {result["ruleId"] for result in sarif["runs"][0]["results"]}

    assert sarif["version"] == "2.1.0"
    assert {"CPX_C102", "CPX_C201"}.issubset(rule_ids)
    assert "CPX_C102" in result_rule_ids
    assert "select * from base" not in sarif_text

    c102_results = [r for r in sarif["runs"][0]["results"] if r["ruleId"] == "CPX_C102"]
    assert c102_results
    assert "properties" in c102_results[0]
    assert c102_results[0]["properties"]["score"] >= 0
    assert "metrics" in c102_results[0]["properties"]
    assert "joins" in c102_results[0]["properties"]["metrics"]


def test_report_json_roundtrip(tmp_path: Path) -> None:
    """JSON report should parse and include metrics for valid SQL."""
    sql_file = tmp_path / "m.sql"
    sql_file.write_text("select 1", encoding="utf-8")
    out = tmp_path / "out.json"
    assert (
        main(
            ["report", "--dialect", "ansi", "--format", "json", "--output", str(out), str(sql_file)]
        )
        == 0
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] in {"1.0", "1.1"}
    assert data["tool"] == "sqlfluff-complexity"
    entry = data["entries"][0]
    assert entry["path"] == str(sql_file)
    assert entry["score"] is not None
    assert entry["metrics"]["joins"] == 0
    assert entry["errors"] == []


def test_report_json_parse_error_has_null_metrics(tmp_path: Path) -> None:
    """Parse errors should serialize with null score and metrics."""
    sql_file = tmp_path / "bad.sql"
    sql_file.write_text("select from", encoding="utf-8")
    out = tmp_path / "out.json"
    assert (
        main(
            ["report", "--dialect", "ansi", "--format", "json", "--output", str(out), str(sql_file)]
        )
        == 0
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    entry = data["entries"][0]
    assert entry["score"] is None
    assert entry["metrics"] is None
    assert entry["errors"]


def test_config_check_valid_returns_zero(tmp_path: Path) -> None:
    """config-check should succeed for default-valid config file."""
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        """
        [sqlfluff:rules:CPX_C201]
        complexity_weights = joins:2,derived_tables:0
        path_overrides =
            models/*.sql:max_joins=4,max_derived_tables=2
        """,
        encoding="utf-8",
    )
    assert main(["config-check", "--dialect", "ansi", "--config", str(cfg)]) == 0


def test_config_check_invalid_derived_table_threshold_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        """
        [sqlfluff:rules:CPX_C110]
        max_derived_tables = not-int
        """,
        encoding="utf-8",
    )
    assert main(["config-check", "--dialect", "ansi", "--config", str(cfg)]) == 1
    assert "config-check failed" in capsys.readouterr().out


def test_dispatch_config_unknown_subcommand_returns_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Future `config` subcommands without a handler must not exit 0 silently."""
    args = argparse.Namespace(command="config", config_command="unknown")
    assert _dispatch_cli(args) == 2
    err = capsys.readouterr().err
    assert "unknown or missing" in err
    assert "config_command='unknown'" in err


def test_dispatch_unknown_top_level_command_returns_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A namespace with a command but no matching handler must not exit 0 silently."""
    args = argparse.Namespace(command="not-a-real-command", config_command=None)
    assert _dispatch_cli(args) == 2
    err = capsys.readouterr().err
    assert "no handler for command" in err


def test_config_preset_prints_recommended_config(capsys: pytest.CaptureFixture[str]) -> None:
    """Preset generation should print plain SQLFluff config to stdout."""
    assert main(["config", "preset", "recommended", "--dialect", "postgres"]) == 0

    output = capsys.readouterr().out
    rules_line = (
        "rules = CPX_C101,CPX_C102,CPX_C103,CPX_C104,CPX_C105,CPX_C106,CPX_C107,"
        "CPX_C108,CPX_C109,CPX_C110,CPX_C201"
    )
    assert "[sqlfluff]" in output
    assert "dialect = postgres" in output
    assert rules_line in output
    assert "[sqlfluff:rules:CPX_C110]" in output
    assert "max_derived_tables = 4" in output
    assert "derived_tables:0" in output


def test_config_preset_report_only_uses_report_mode(capsys: pytest.CaptureFixture[str]) -> None:
    """The report_only preset should generate non-enforcing aggregate mode."""
    assert main(["config", "preset", "report_only", "--dialect", "snowflake"]) == 0

    output = capsys.readouterr().out
    assert "dialect = snowflake" in output
    assert "mode = report" in output


def test_config_check_invalid_weights_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        """
        [sqlfluff:rules:CPX_C201]
        complexity_weights = joins:not-an-int
        """,
        encoding="utf-8",
    )
    assert main(["config-check", "--dialect", "ansi", "--config", str(cfg)]) == 1
    assert "config-check failed" in capsys.readouterr().out


def test_config_check_invalid_path_override(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        """
        [sqlfluff:rules:CPX_C201]
        path_overrides =
            models/*.sql:max_joins=not-int
        """,
        encoding="utf-8",
    )
    assert main(["config-check", "--dialect", "ansi", "--config", str(cfg)]) == 1
    assert "config-check failed" in capsys.readouterr().out


def test_report_sarif_parse_error_has_no_metric_properties(tmp_path: Path) -> None:
    """Parse error SARIF rows should omit score/metrics properties."""
    sql_file = tmp_path / "bad.sql"
    sql_file.write_text("select from", encoding="utf-8")
    out = tmp_path / "e.sarif"
    assert (
        main(
            [
                "report",
                "--dialect",
                "ansi",
                "--format",
                "sarif",
                "--output",
                str(out),
                str(sql_file),
            ]
        )
        == 0
    )
    sarif = json.loads(out.read_text(encoding="utf-8"))
    parse_results = [r for r in sarif["runs"][0]["results"] if r["ruleId"] == "CPX_PARSE_ERROR"]
    assert parse_results
    assert "properties" not in parse_results[0]


def test_report_fail_on_error_returns_nonzero_for_parse_error(tmp_path: Path) -> None:
    """--fail-on-error should make parse errors visible to automation."""
    sql_file = tmp_path / "bad.sql"
    sql_file.write_text("select from", encoding="utf-8")

    assert main(["report", "--dialect", "ansi", "--fail-on-error", str(sql_file)]) == 1


def test_report_uses_path_override_thresholds(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The report command should apply path-specific policy thresholds."""
    sql_file = tmp_path / "models" / "staging" / "orders.sql"
    sql_file.parent.mkdir(parents=True)
    sql_file.write_text(_join_heavy_sql(join_count=2), encoding="utf-8")
    config_file = tmp_path / ".sqlfluff"
    config_file.write_text(
        """
        [sqlfluff:rules:CPX_C201]
        path_overrides =
            **/models/staging/*.sql:max_joins=1,max_complexity_score=999
        """,
        encoding="utf-8",
    )

    exit_code = main(
        [
            "report",
            "--dialect",
            "ansi",
            "--config",
            str(config_file),
            str(sql_file),
        ],
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "CPX_C102: join count 2 exceeds max_joins=1" in output


def _join_heavy_sql(join_count: int) -> str:
    select_clause = "select * from base"
    joins = "\n".join(
        f"join table_{index} on base.id = table_{index}.id" for index in range(1, join_count + 1)
    )
    return "\n".join([select_clause, joins])
