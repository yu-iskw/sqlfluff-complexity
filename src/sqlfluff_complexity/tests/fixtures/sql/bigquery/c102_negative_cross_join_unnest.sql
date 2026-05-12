with orders as (
  select
    1 as user_id,
    ['sku-1', 'sku-2'] as skus
)
select
  orders.user_id,
  sku
from orders
cross join unnest(orders.skus) as sku
