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
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from sqlfluff_complexity.baseline import (
    baseline_from_report,
    format_baseline_json,
    load_baseline,
)
from sqlfluff_complexity.check import (
    FailOnMode,
    compare_report_to_baseline,
    format_check_console,
    format_check_json,
)
from sqlfluff_complexity.paths import gather_sql_paths, normalize_report_path
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

DEFAULT_BASELINE_PATH = Path(".sqlfluff-complexity-baseline.json")
DEFAULT_INCLUDE = ("**/*.sql",)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the sqlfluff-complexity command line interface."""
    if argv is not None and len(argv) == 0:
        return 0
    args = _build_parser().parse_args(argv)
    if args.command == "report":
        return _run_report(args)
    if args.command == "check":
        return _run_check(args)
    if args.command == "config-check":
        return _run_config_check(args)
    if args.command == "baseline" and args.baseline_command == "create":
        return _run_baseline_create(args)
    return 2


def _add_path_discovery_args(target: argparse.ArgumentParser) -> None:
    target.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="GLOB",
        help="Glob for directory discovery (repeatable). Default: **/*.sql",
    )
    target.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="Glob to exclude (repeatable).",
    )
    target.add_argument(
        "--files-from",
        metavar="PATH_OR_DASH",
        help="Read newline-delimited paths from a file, or stdin when set to '-'.",
    )
    target.add_argument(
        "--jobs",
        type=int,
        default=1,
        metavar="N",
        help="Parallel analysis workers (default: 1).",
    )


def _effective_include_exclude(args: argparse.Namespace) -> tuple[tuple[str, ...], tuple[str, ...]]:
    include = tuple(args.include) if args.include else DEFAULT_INCLUDE
    exclude = tuple(args.exclude) if args.exclude else ()
    return include, exclude


def _resolve_analysis_paths(args: argparse.Namespace, *, require_paths: bool) -> list[Path]:
    cwd = Path.cwd()
    include, exclude = _effective_include_exclude(args)
    explicit = getattr(args, "paths", None) or []
    merged = gather_sql_paths(
        explicit,
        cwd=cwd,
        files_from=getattr(args, "files_from", None),
        include_globs=include,
        exclude_globs=exclude,
    )
    if require_paths and not merged:
        print(
            "No input paths after discovery. Provide positional paths or --files-from.",
            flush=True,
        )
        sys.exit(2)
    return merged


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlfluff-complexity",
        description="SQLFluff plugin for SQL and dbt model complexity rules.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser(
        "report",
        help="Report SQL complexity metrics for files or directories.",
    )
    report_parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="SQL files or directories to analyze.",
    )
    _add_path_discovery_args(report_parser)
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

    baseline_parser = subparsers.add_parser(
        "baseline",
        help="Create or manage complexity baselines.",
    )
    baseline_sub = baseline_parser.add_subparsers(dest="baseline_command", required=True)
    baseline_create = baseline_sub.add_parser(
        "create",
        help="Analyze paths and write a JSON baseline snapshot.",
    )
    baseline_create.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="SQL files or directories to include (optional if --files-from is set).",
    )
    _add_path_discovery_args(baseline_create)
    baseline_create.add_argument(
        "--dialect", default="ansi", help="SQLFluff dialect to parse with."
    )
    baseline_create.add_argument("--config", type=Path, help="SQLFluff config file to apply.")
    baseline_create.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Baseline JSON output path (default: {DEFAULT_BASELINE_PATH}).",
    )
    baseline_create.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit non-zero if any input cannot be parsed or read.",
    )

    check_parser = subparsers.add_parser(
        "check",
        help="Compare current complexity to a baseline.",
    )
    check_parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="SQL files or directories to analyze.",
    )
    _add_path_discovery_args(check_parser)
    check_parser.add_argument("--dialect", default="ansi", help="SQLFluff dialect to parse with.")
    check_parser.add_argument("--config", type=Path, help="SQLFluff config file to apply.")
    check_parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="Path to baseline JSON.",
    )
    check_parser.add_argument(
        "--fail-on",
        choices=("regression", "threshold", "none"),
        required=True,
        dest="fail_on",
        help="When to fail the check for complexity findings.",
    )
    check_parser.add_argument(
        "--format",
        choices=("console", "json"),
        default="console",
        dest="output_format",
        help="Check output format.",
    )
    check_parser.add_argument("--output", type=Path, help="Write check output to this path.")
    check_parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit non-zero on read/parse errors.",
    )

    config_parser = subparsers.add_parser(
        "config-check",
        help="Validate CPX-related SQLFluff configuration (weights, path overrides, mode).",
    )
    config_parser.add_argument("--dialect", default="ansi", help="SQLFluff dialect to parse with.")
    config_parser.add_argument("--config", type=Path, help="SQLFluff config file to apply.")
    return parser


def _path_key_map(paths: Sequence[Path]) -> dict[Path, str]:
    cwd = Path.cwd().resolve()
    return {p.resolve(): normalize_report_path(p, root=cwd) for p in paths}


def _run_report(args: argparse.Namespace) -> int:
    resolved = _resolve_analysis_paths(args, require_paths=True)
    report = analyze_paths(
        resolved,
        dialect=args.dialect,
        config_path=args.config,
        jobs=args.jobs,
    )
    output = _format_report(report, args.output_format)

    if args.output is None:
        print(output)
    else:
        args.output.write_text(f"{output}\n", encoding="utf-8")

    if args.fail_on_error and report.has_errors:
        return 1
    return 0


def _run_baseline_create(args: argparse.Namespace) -> int:
    cwd = Path.cwd()
    include, exclude = _effective_include_exclude(args)
    merged = gather_sql_paths(
        getattr(args, "paths", None) or [],
        cwd=cwd,
        files_from=getattr(args, "files_from", None),
        include_globs=include,
        exclude_globs=exclude,
    )
    if not merged:
        print(
            "No input paths after discovery. Provide positional paths or --files-from.",
            flush=True,
        )
        return 2

    report = analyze_paths(
        merged,
        dialect=args.dialect,
        config_path=args.config,
        jobs=args.jobs,
    )
    keys = _path_key_map(merged)
    baseline = baseline_from_report(report, path_key=keys)
    out_path = args.output if args.output is not None else DEFAULT_BASELINE_PATH
    text = format_baseline_json(baseline)
    out_path.write_text(f"{text}\n", encoding="utf-8")

    if args.fail_on_error and report.has_errors:
        return 1
    return 0


def _run_check(args: argparse.Namespace) -> int:
    try:
        baseline = load_baseline(args.baseline)
    except OSError as exc:
        print(f"could not read baseline: {exc}", flush=True)
        return 2
    except (ValueError, TypeError) as exc:
        print(f"invalid baseline: {exc}", flush=True)
        return 2

    resolved = _resolve_analysis_paths(args, require_paths=True)
    fail_on: FailOnMode = args.fail_on

    try:
        report = analyze_paths(
            resolved,
            dialect=args.dialect,
            config_path=args.config,
            jobs=args.jobs,
        )
    except ValueError as exc:
        print(f"analysis failed: {exc}", flush=True)
        return 2

    keys = _path_key_map(resolved)
    check_result = compare_report_to_baseline(
        report,
        baseline=baseline,
        path_key=keys,
        fail_on=fail_on,
    )

    if args.output_format == "json":
        output = format_check_json(check_result)
    else:
        output = format_check_console(check_result)

    if args.output is None:
        print(output, end="")
    else:
        args.output.write_text(output if output.endswith("\n") else f"{output}\n", encoding="utf-8")

    complexity_failed = (fail_on == "regression" and check_result.summary.regressions > 0) or (
        fail_on == "threshold" and check_result.summary.threshold_violations > 0
    )

    error_failed = args.fail_on_error and check_result.summary.errors > 0

    if complexity_failed or error_failed:
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
