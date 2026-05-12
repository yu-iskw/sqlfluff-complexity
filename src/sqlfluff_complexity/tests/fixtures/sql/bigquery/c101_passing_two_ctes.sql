with
  raw_orders as (
    select id, customer_id, total_amount
    from `project.dataset.orders`
    where status = 'complete'
  ),
  raw_customers as (
    select id, name, region
    from `project.dataset.customers`
  )
select
  o.id,
  c.name,
  o.total_amount
from raw_orders as o
join raw_customers as c on o.customer_id = c.id
