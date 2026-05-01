with recent_orders as (
  select id, customer_id, created_at::date as order_date
  from raw_orders
)
select
  r.id,
  case when c.status = 'active' then 1 else 0 end as active_flag,
  row_number() over (partition by c.region order by r.order_date) as region_rank
from recent_orders as r
join customers as c on r.customer_id = c.id
where r.order_date >= date '2025-01-01'
  and (c.region = 'US' or c.region = 'JP')
