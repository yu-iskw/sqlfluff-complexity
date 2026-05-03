# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed (internals only)

- **Dev/coverage tooling only:** `dev/coverage_importlib_meta.json` no longer includes `io_importlib_spec`, and `read_io_importlib_spec` was removed from `dev/coverage_importlib_meta_access.py`. The published package API is unchanged.
- `file_segment_from_context` raises `RuntimeError` when no `file` segment can be resolved (broken parent pointers or an unusual rule context). File-level rules **CPX_C108** and **CPX_C109** use this path via `eval_file_root_metric_threshold`; custom callers of those helpers outside normal SQLFluff crawlers may need to ensure the parse tree exposes a `file` root.
- `ComplexityAnalysis` now includes a `root` field: the `BaseSegment` passed to `analyze_segment_tree`. Integrators who construct `ComplexityAnalysis` manually must supply `root`; prefer calling `analyze_segment_tree` only.
- Reorganized `sqlfluff_complexity.core` into subpackages (`model`, `config`, `messages`, `analysis`, `scan`). **Plugin entry points and the public CLI are unchanged.**
- If you import internal `core` modules, see [docs/migration-internal.md](docs/migration-internal.md) for the old → new import map.
- `metric_threshold_violation_message` now takes `MetricThresholdViolationParams`. Report code that needs the contributor tuple and remediation without extra passes may use `metric_threshold_violation_message_and_picked` (same module), which returns `(message, picked, remediation)`.
