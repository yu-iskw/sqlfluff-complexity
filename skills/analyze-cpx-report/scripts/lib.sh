# Shared helpers for CPX report cache scripts (bash + common Unix tools only).
# shellcheck shell=bash

# Resolve to an absolute path (best-effort; requires existing parent directory).
cpx_abspath() {
  local path=${1:?}
  if [[ "$path" != /* ]]; then
    path="${PWD}/${path}"
  fi
  local dir base
  dir=$(dirname -- "$path")
  base=$(basename -- "$path")
  if [[ -d "$path" ]]; then
    (cd -- "$path" && pwd -P)
  else
    (cd -- "$dir" && printf '%s/%s\n' "$(pwd -P)" "$base")
  fi
}

# File mtime as seconds since epoch (GNU stat or BSD stat).
cpx_mtime_epoch() {
  local f=${1:?} out
  if out=$(stat -c %Y -- "$f" 2>/dev/null); then
    printf '%s\n' "$out"
    return 0
  fi
  if out=$(stat -f %m -- "$f" 2>/dev/null); then
    printf '%s\n' "$out"
    return 0
  fi
  echo "cpx: could not read mtime for $f (stat)" >&2
  return 1
}

# Hash stdin; print first 20 hex characters of SHA-256.
cpx_sha256_key20() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum | awk '{print substr($1,1,20)}'
  elif command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 | awk '{print substr($2,1,20)}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 2>/dev/null | awk '{print substr($1,1,20)}'
  else
    echo "cpx: need sha256sum, openssl dgst, or shasum -a 256 for cache keys" >&2
    return 1
  fi
}

cpx_default_cache_base() {
  if [[ -n "${CPX_REPORT_CACHE_DIR:-}" ]]; then
    printf '%s\n' "$CPX_REPORT_CACHE_DIR"
  elif [[ -n "${TMPDIR:-}" ]]; then
    printf '%s\n' "$TMPDIR"
  else
    printf '/tmp\n'
  fi
}

# Validated TTL (seconds); warns on invalid env and falls back to 300.
cpx_cache_ttl_seconds() {
  local raw=${CPX_REPORT_CACHE_TTL_SECONDS:-300}
  if [[ "$raw" =~ ^[0-9]+$ ]]; then
    printf '%s\n' "$raw"
    return 0
  fi
  echo "cpx: invalid CPX_REPORT_CACHE_TTL_SECONDS (not digits), using 300" >&2
  printf '%s\n' 300
}

# Print absolute JSON cache path (no mkdir). Uses CPX_REPORT_* env + path args.
cpx_cache_json_path() {
  local dialect=${CPX_REPORT_DIALECT:-ansi}
  local cfg=${CPX_REPORT_CONFIG:-}
  local rec=${CPX_REPORT_RECURSIVE:-}
  local -a abs=()
  local p digest base cwd
  for p in "$@"; do
    abs+=("$(cpx_abspath "$p")")
  done
  local -a sorted=()
  mapfile -t sorted < <(printf '%s\n' "${abs[@]}" | LC_ALL=C sort -u)
  cwd=$(pwd -P)
  digest=$(
    {
      printf '%s\n' "$cwd" "$dialect" "$cfg" "$rec"
      printf '%s\n' "${sorted[@]}"
    } | cpx_sha256_key20
  ) || return 1
  base=$(cpx_default_cache_base)
  base=${base%/}
  printf '%s/sqlfluff-complexity-report-%s.json\n' "$base" "$digest"
}

# Exit 0 if file exists and age < TTL; else 1.
cpx_is_cache_fresh() {
  local f=${1:?} ttl now mt age
  [[ -f "$f" ]] || return 1
  ttl=$(cpx_cache_ttl_seconds)
  now=$(date +%s)
  mt=$(cpx_mtime_epoch "$f") || return 1
  age=$((now - mt))
  ((age >= 0 && age < ttl))
}
