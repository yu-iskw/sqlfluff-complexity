#!/usr/bin/env bash
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
  local f=${1:?}
  local out
  if out=$(stat -c %Y -- "$f" 2>/dev/null); then
    printf '%s\n' "$out"
    return 0
  fi
  stat -f %m -- "$f"
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
