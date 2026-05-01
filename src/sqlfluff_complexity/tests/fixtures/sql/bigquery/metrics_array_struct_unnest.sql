with orders as (
  select
    1 as user_id,
    [struct('sku-1' as sku, 2 as quantity)] as items
)
select
  orders.user_id,
  item.sku,
  row_number() over (partition by orders.user_id order by item.sku) as item_rank
from orders
cross join unnest(orders.items) as item
where item.quantity > 0
