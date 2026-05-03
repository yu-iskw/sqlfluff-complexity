with orders as (
    select id, customer_id
    from raw_orders
),
customers as (
    select id, customer_name
    from raw_customers
)
select
    orders.id,
    customers.customer_name
from orders
join customers
    on orders.customer_id = customers.id
