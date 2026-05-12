with
  recent_orders as (
    select
      id,
      customer_id,
      total_amount
    from `project.dataset.orders`
    where status = 'complete'
  )
select
  o.id,
  o.customer_id,
  o.total_amount
from recent_orders as o
join `project.dataset.customers` as c on o.customer_id = c.id
