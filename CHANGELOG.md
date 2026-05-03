# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed (internals only)

- Reorganized `sqlfluff_complexity.core` into subpackages (`model`, `config`, `messages`, `analysis`, `scan`). **Plugin entry points and the public CLI are unchanged.**
- If you import internal `core` modules, see [docs/migration-internal.md](docs/migration-internal.md) for the old → new import map.
- `metric_threshold_violation_message` now takes `MetricThresholdViolationParams`. Report code that needs the contributor tuple and remediation without extra passes may use `metric_threshold_violation_message_and_picked` (same module), which returns `(message, picked, remediation)`.
