select
  customers.id,
  recent.order_id
from customers
left join lateral (
  select orders.id as order_id
  from orders
  where orders.customer_id = customers.id
  order by orders.created_at desc
  limit 1
) as recent on true
where customers.status = 'active'
