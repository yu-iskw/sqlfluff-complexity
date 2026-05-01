# Quick Start

This guide gets `sqlfluff-complexity` running in a SQLFluff project with the default CPX rules.

## 1. Install

Install `sqlfluff-complexity` in the same Python environment where you run SQLFluff.

```bash
pip install sqlfluff-complexity
```

If you use `uv` for your project environment:

```bash
uv add --dev sqlfluff-complexity
```

## 2. Configure SQLFluff

Add the CPX rules to your `.sqlfluff` config. Start with a small rule set if you want to roll out gradually.

```ini
[sqlfluff]
dialect = postgres
rules = CPX_C101,CPX_C102,CPX_C103,CPX_C104,CPX_C105,CPX_C106,CPX_C201
```

For dbt projects, keep your existing SQLFluff dbt templater configuration and add the CPX rules to the same config. See [dbt usage](dbt.md) for the v1 boundary.

## 3. Run SQLFluff

Run SQLFluff as usual:

```bash
sqlfluff lint models/
```

The plugin reports CPX violations as normal SQLFluff lint results, so existing rule selection, file selection, and `noqa` workflows still apply.

## 4. Try A Small Example

This query exceeds a join limit of `1`:

```sql
select *
from orders
join customers on orders.customer_id = customers.id
join regions on customers.region_id = regions.id
```

Use a lower threshold to see the rule fire:

```ini
[sqlfluff]
dialect = postgres
rules = CPX_C102

[sqlfluff:rules:CPX_C102]
max_joins = 1
```

Then run:

```bash
sqlfluff lint path/to/model.sql
```

## 5. Tune Your Rollout

Recommended rollout path:

1. Start with [report mode](reporting.md) to see current complexity without blocking CI.
2. Enable high-signal individual rules such as `CPX_C102` or `CPX_C103`.
3. Add `CPX_C201` once aggregate score thresholds are calibrated for your project.
4. Use [configuration](configuration.md) path overrides for staging, intermediate, and marts models.

## Next Steps

- [Configuration](configuration.md)
- [Rules reference](rules.md)
- [Reporting](reporting.md)
- [dbt usage](dbt.md)
- [Dialects](dialects.md)
- [Docs index](index.md)
