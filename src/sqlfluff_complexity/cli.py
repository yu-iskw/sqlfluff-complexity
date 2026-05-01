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

"""Command line entry point for sqlfluff-complexity."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from sqlfluff_complexity.report import (
    ComplexityReport,
    analyze_paths,
    format_console_report,
    format_json_report,
    format_sarif_report,
    load_fluff_config,
    validate_cpx_plugin_config,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Run the sqlfluff-complexity command line interface."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "report":
        return _run_report(args)
    if args.command == "config-check":
        return _run_config_check(args)

    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlfluff-complexity",
        description="SQLFluff plugin for SQL and dbt model complexity rules.",
    )
    subparsers = parser.add_subparsers(dest="command")

    report_parser = subparsers.add_parser(
        "report",
        help="Report SQL complexity metrics for one or more files.",
    )
    report_parser.add_argument("paths", nargs="+", type=Path, help="SQL file paths to analyze.")
    report_parser.add_argument("--dialect", default="ansi", help="SQLFluff dialect to parse with.")
    report_parser.add_argument("--config", type=Path, help="SQLFluff config file to apply.")
    report_parser.add_argument(
        "--format",
        choices=("console", "json", "sarif"),
        default="console",
        dest="output_format",
        help="Report output format.",
    )
    report_parser.add_argument("--output", type=Path, help="Write report output to this path.")
    report_parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Return a non-zero status if any input cannot be parsed or read.",
    )

    check_parser = subparsers.add_parser(
        "config-check",
        help="Validate CPX-related SQLFluff configuration (weights, path overrides, mode).",
    )
    check_parser.add_argument("--dialect", default="ansi", help="SQLFluff dialect to parse with.")
    check_parser.add_argument("--config", type=Path, help="SQLFluff config file to apply.")
    return parser


def _run_report(args: argparse.Namespace) -> int:
    report = analyze_paths(args.paths, dialect=args.dialect, config_path=args.config)
    output = _format_report(report, args.output_format)

    if args.output is None:
        print(output)
    else:
        args.output.write_text(f"{output}\n", encoding="utf-8")

    if args.fail_on_error and report.has_errors:
        return 1
    return 0


def _format_report(report: ComplexityReport, output_format: str) -> str:
    if output_format == "console":
        return format_console_report(report)
    if output_format == "json":
        return format_json_report(report)
    if output_format == "sarif":
        return format_sarif_report(report)

    message = f"Unsupported report format: {output_format}"
    raise ValueError(message)


def _run_config_check(args: argparse.Namespace) -> int:
    try:
        config = load_fluff_config(dialect=args.dialect, config_path=args.config)
        validate_cpx_plugin_config(config)
    except ValueError as exc:
        print(f"config-check failed: {exc}", flush=True)
        return 1
    except OSError as exc:
        print(f"config-check failed: could not load config: {exc}", flush=True)
        return 1
    print("CPX configuration is valid.", flush=True)
    return 0
