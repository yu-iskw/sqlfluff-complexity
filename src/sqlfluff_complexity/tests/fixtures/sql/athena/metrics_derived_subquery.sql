select recent.order_id
from (
  select order_id, customer_id
  from orders
  where order_total > 0
) as recent
where recent.customer_id is not null
