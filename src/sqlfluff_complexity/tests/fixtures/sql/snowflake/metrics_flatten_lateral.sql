select
  orders.id,
  flattened.value:sku::string as sku
from orders,
lateral flatten(input => orders.items) as flattened
where flattened.value:sku is not null
