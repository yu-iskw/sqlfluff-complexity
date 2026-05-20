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
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from sqlfluff_complexity import __version__
from sqlfluff_complexity.core.config.presets import preset_names, render_preset_config
from sqlfluff_complexity.report import (
    ComplexityReport,
    analyze_paths,
    cli_scan_roots,
    expand_report_paths,
    format_console_report,
    format_html_report,
    format_json_report,
    format_sarif_report,
    load_fluff_config,
    validate_cpx_plugin_config,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

REPORT_FORMATTERS = {
    "console": format_console_report,
    "html": format_html_report,
    "json": format_json_report,
    "sarif": format_sarif_report,
}


def _first_directory_arg(paths: Sequence[Path]) -> Path | None:
    """Return the first path that is an existing directory, if any."""
    for path in paths:
        if path.is_dir():
            return path
    return None


def _format_report(report: ComplexityReport, output_format: str) -> str:
    formatter = REPORT_FORMATTERS.get(output_format)
    if formatter is not None:
        return formatter(report)

    message = f"Unsupported report format: {output_format}"
    raise ValueError(message)


def _run_report(args: argparse.Namespace) -> int:
    if not args.recursive:
        dir_path = _first_directory_arg(args.paths)
        if dir_path is not None:
            print(
                f"sqlfluff-complexity: {dir_path} is a directory; use --recursive to analyze nested .sql files.",
                file=sys.stderr,
            )
            return 2

    paths = expand_report_paths(args.paths, recursive=args.recursive)
    report = analyze_paths(paths, dialect=args.dialect, config_path=args.config)
    report = replace(report, scan_roots=cli_scan_roots(args.paths))
    output = _format_report(report, args.output_format)

    if args.output is None:
        print(output)
    else:
        args.output.write_text(f"{output}\n", encoding="utf-8")

    if args.fail_on_error and report.has_errors:
        return 1
    return 0


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


def _run_config_preset(args: argparse.Namespace) -> int:
    print(render_preset_config(args.name, dialect=args.dialect), flush=True)
    return 0


def _dispatch_cli(args: argparse.Namespace) -> int:
    """Run the subcommand handler for parsed CLI args (also used from tests).

    With no subcommand, ``args.command`` is ``None`` and this returns ``0`` without
    consulting ``config_command``; hand-built ``Namespace`` values should mirror argparse.
    """
    config_command = getattr(args, "config_command", None)
    handlers = {
        ("config", "preset"): _run_config_preset,
        ("config-check", None): _run_config_check,
        ("report", None): _run_report,
    }
    handler = handlers.get((args.command, config_command))
    if handler is not None:
        return handler(args)

    err: str | None = None
    if args.command == "config":
        err = f"sqlfluff-complexity: unknown or missing `config` subcommand (got config_command={config_command!r})."
    elif args.command is not None:
        err = f"sqlfluff-complexity: no handler for command {args.command!r} (config_command={config_command!r})."
    if err is not None:
        print(err, file=sys.stderr)
        return 2
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlfluff-complexity",
        description="SQLFluff plugin for SQL and dbt model complexity rules.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show package version and exit.",
    )
    subparsers = parser.add_subparsers(dest="command")

    report_parser = subparsers.add_parser(
        "report",
        help="Report SQL complexity metrics for one or more files.",
    )
    report_parser.add_argument("paths", nargs="+", type=Path, help="SQL file paths to analyze.")
    report_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help=("Expand each directory argument to all nested .sql files (suffix matched case-insensitively)."),
    )
    report_parser.add_argument("--dialect", default="ansi", help="SQLFluff dialect to parse with.")
    report_parser.add_argument("--config", type=Path, help="SQLFluff config file to apply.")
    report_parser.add_argument(
        "--format",
        choices=tuple(REPORT_FORMATTERS),
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

    config_parser = subparsers.add_parser(
        "config",
        help="Generate CPX SQLFluff configuration snippets.",
    )
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    config_subparsers.required = True
    preset_parser = config_subparsers.add_parser(
        "preset",
        help="Print a generated CPX preset config to stdout.",
    )
    preset_parser.add_argument("name", choices=preset_names(), help="Preset name to render.")
    preset_parser.add_argument("--dialect", default="ansi", help="SQLFluff dialect for the config.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the sqlfluff-complexity command line interface."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    return _dispatch_cli(args)
