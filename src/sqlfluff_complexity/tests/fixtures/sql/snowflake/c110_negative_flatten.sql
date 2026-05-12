select
  orders.id,
  flattened.value:sku::string as sku,
  flattened.value:qty::int as qty
from orders,
lateral flatten(input => orders.items) as flattened
where flattened.value:qty is not null
