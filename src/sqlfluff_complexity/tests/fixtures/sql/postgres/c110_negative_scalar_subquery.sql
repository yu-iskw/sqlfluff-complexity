select
  id,
  name,
  (select max(amount) from orders where customer_id = customers.id) as max_order
from customers
where status = 'active'
