select
    orders.id,
    customers.customer_name
from (
    select id, customer_id
    from raw_orders
) as orders
join (
    select id, customer_name
    from raw_customers
) as customers
    on orders.customer_id = customers.id
