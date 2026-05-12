with
  base_orders as (
    select id, customer_id, total_amount
    from orders
  ),
  filtered_orders as (
    select *
    from base_orders
    where total_amount > 100
  )
select
  f.id,
  f.customer_id,
  f.total_amount
from filtered_orders as f
