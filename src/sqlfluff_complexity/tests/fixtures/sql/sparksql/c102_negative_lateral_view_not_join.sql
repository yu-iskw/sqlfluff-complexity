select
  orders.id,
  tag
from orders
lateral view explode(tags) tag_table as tag
