select
  seller_id,
  order_id,
  row_number() over (partition by seller_id order by created_at desc) as order_rank
from sales
qualify order_rank = 1
