with
  base as (
    select id, customer_id
    from orders
  ),
  filtered as (
    select *
    from base
    where customer_id > 0
  )
select *
from filtered
