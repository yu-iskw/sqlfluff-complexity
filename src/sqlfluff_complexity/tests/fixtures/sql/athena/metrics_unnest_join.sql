select
  o.order_id,
  item
from orders as o
cross join unnest(o.items) as t(item)
where o.status = 'shipped'
  and item is not null
