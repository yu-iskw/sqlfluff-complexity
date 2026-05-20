#!/usr/bin/env bash
# Run sqlfluff-complexity report --format json or reuse a cache file within TTL.
# Prints the absolute cache path as the only stdout line. Status 0 on success.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

usage() {
  cat <<'USAGE'
Usage: ensure-json-report.sh [options] [--] PATH [PATH...]

Run sqlfluff-complexity report --format json, or reuse a JSON file within TTL.
Prints the absolute cache path as the only stdout line.

Options:
  -d, --dialect D     SQLFluff dialect (default: ansi)
  -c, --config FILE   SQLFluff config file
  -r, --recursive     Pass -r to report (required for directory trees)
      --force         Ignore cache and regenerate
  -h, --help          Show this help

Environment: CPX_REPORT_CACHE_TTL_SECONDS (default 300), CPX_REPORT_CACHE_DIR,
CPX_REPORT_PREFIX (e.g. "uv run"), CPX_REPORT_FORCE=1.

Requires bash plus sha256sum, openssl dgst, or shasum -a 256 (see lib.sh).
USAGE
}

dialect=ansi
config=""
recursive=false
force=false
paths=()

while (($#)); do
  case "$1" in
    -d | --dialect)
      dialect=$2
      shift 2
      ;;
    -c | --config)
      config=$2
      shift 2
      ;;
    -r | --recursive)
      recursive=true
      shift
      ;;
    --force)
      force=true
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    --)
      shift
      while (($#)); do paths+=("$1"); shift; done
      break
      ;;
    -*)
      echo "ensure-json-report.sh: unknown option: $1" >&2
      exit 2
      ;;
    *)
      paths+=("$1")
      shift
      ;;
  esac
done

if ((${#paths[@]} == 0)); then
  echo "ensure-json-report.sh: at least one PATH is required" >&2
  exit 2
fi

export CPX_REPORT_DIALECT=$dialect
if [[ -n "$config" ]]; then
  export CPX_REPORT_CONFIG
  CPX_REPORT_CONFIG=$(cpx_abspath "$config")
else
  unset CPX_REPORT_CONFIG
fi
if [[ "$recursive" == true ]]; then
  export CPX_REPORT_RECURSIVE=1
else
  unset CPX_REPORT_RECURSIVE
fi

cache_file=$(cpx_cache_json_path "${paths[@]}")

if [[ "${CPX_REPORT_FORCE:-}" == "1" || "${CPX_REPORT_FORCE:-}" == "true" ]]; then
  force=true
fi

if [[ "$force" == false ]] && [[ -f "$cache_file" ]] && cpx_is_cache_fresh "$cache_file"; then
  echo "Using cached report: $cache_file" >&2
  printf '%s\n' "$cache_file"
  exit 0
fi

_prefix=()
if [[ -n "${CPX_REPORT_PREFIX:-}" ]]; then
  read -r -a _prefix <<<"$CPX_REPORT_PREFIX"
fi

_cmd=(
  "${_prefix[@]}"
  sqlfluff-complexity
  report
  --format
  json
  --output
  "$cache_file"
  --dialect
  "$dialect"
)
if [[ -n "$config" ]]; then
  _cmd+=(--config "$CPX_REPORT_CONFIG")
fi
if [[ "$recursive" == true ]]; then
  _cmd+=(-r)
fi
_cmd+=(-- "${paths[@]}")

mkdir -p -- "$(dirname -- "$cache_file")"
echo "Generating report to $cache_file" >&2
"${_cmd[@]}"
printf '%s\n' "$cache_file"
