select
  orders.id,
  item
from orders
lateral view explode(items) exploded_items as item
where item is not null
