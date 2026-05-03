-- Fixture asserts nested subquery_depth and derived_tables (see metrics_nested_subquery_depth_2.metrics.json).
select *
from (
  select *
  from (
    select id from raw_orders
  ) inner_orders
) orders
