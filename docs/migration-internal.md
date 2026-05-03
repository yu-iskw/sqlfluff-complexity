# Internal module layout migration

The **public** surface of this package is unchanged for normal use:

- SQLFluff entry point: `sqlfluff_complexity` (plugin hooks, rules, default config).
- CLI: `sqlfluff-complexity` / `sqlfluff_complexity.cli`.

If you import **`sqlfluff_complexity.core`** submodules directly (for example in a fork, test harness, or custom tool), import paths were reorganized into domain subpackages. Update imports as below.

## Module path map (old → new)

| Old module                                        | New module                                                                                                                                                                                   |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sqlfluff_complexity.core.metrics`                | `sqlfluff_complexity.core.model.metrics`                                                                                                                                                     |
| `sqlfluff_complexity.core.structural_metrics`     | `sqlfluff_complexity.core.model.structural_metrics`                                                                                                                                          |
| `sqlfluff_complexity.core.cpx_config`             | `sqlfluff_complexity.core.config.cpx_config`                                                                                                                                                 |
| `sqlfluff_complexity.core.policy`                 | `sqlfluff_complexity.core.config.policy`                                                                                                                                                     |
| `sqlfluff_complexity.core.scoring`                | `sqlfluff_complexity.core.config.scoring`                                                                                                                                                    |
| `sqlfluff_complexity.core.remediation`            | `sqlfluff_complexity.core.messages.remediation`                                                                                                                                              |
| `sqlfluff_complexity.core.violation_messages`     | `sqlfluff_complexity.core.messages.violation_messages`                                                                                                                                       |
| `sqlfluff_complexity.core.findings`               | `sqlfluff_complexity.core.messages.findings`                                                                                                                                                 |
| `sqlfluff_complexity.core.analysis` (single file) | Package `sqlfluff_complexity.core.analysis` re-exporting contributors and explainability helpers; implementation modules are `core.analysis.contributors` and `core.analysis.explainability` |
| `sqlfluff_complexity.core.explainability`         | `sqlfluff_complexity.core.analysis.explainability` (or import from `sqlfluff_complexity.core.analysis` for the public names)                                                                 |
| `sqlfluff_complexity.core.segment_tree`           | `sqlfluff_complexity.core.scan.segment_tree`                                                                                                                                                 |

## API: threshold violation messages

- `metric_threshold_violation_message` takes a single argument: `MetricThresholdViolationParams` (see `core.messages.violation_messages`), not separate keyword arguments.
- For code that needs the message string, the ranked contributor tuple, and the remediation string in one `top_contributors` pass (and a single `remediation_for_rule` call), use `metric_threshold_violation_message_and_picked` in the same module. It returns `(message, picked, remediation)`.
