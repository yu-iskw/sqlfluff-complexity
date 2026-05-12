with
  raw_orders as (
    select id, customer_id, total_amount
    from raw_orders_table
    where status = 'complete'
  ),
  raw_customers as (
    select id, name, region
    from raw_customers_table
  )
select
  o.id,
  c.name,
  o.total_amount
from raw_orders as o
join raw_customers as c on o.customer_id = c.id
