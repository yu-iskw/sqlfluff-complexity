with recent_orders as (
  select id, customer_id, date_parse(created_at, '%Y-%m-%d') as order_ts
  from raw_orders
)
select
  r.id,
  case when c.status = 'active' then 1 else 0 end as active_flag,
  row_number() over (partition by c.region order by r.order_ts) as region_rank
from recent_orders r
join customers c on r.customer_id = c.id
where r.order_ts >= timestamp '2025-01-01 00:00:00'
  and (c.region = 'US' or c.region = 'JP')
