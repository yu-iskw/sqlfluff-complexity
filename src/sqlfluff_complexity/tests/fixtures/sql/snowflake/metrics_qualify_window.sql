select
  customer_id,
  order_id,
  row_number() over (partition by customer_id order by created_at desc) as order_rank
from orders
qualify order_rank = 1
