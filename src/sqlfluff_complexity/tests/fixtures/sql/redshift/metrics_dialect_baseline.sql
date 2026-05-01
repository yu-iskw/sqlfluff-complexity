with recent_orders as (
  select id, customer_id, dateadd(day, 1, created_at) as ship_date
  from raw_orders
)
select
  r.id,
  case when c.status = 'active' then 1 else 0 end as active_flag,
  row_number() over (partition by c.region order by r.ship_date) as region_rank
from recent_orders as r
join customers as c on r.customer_id = c.id
where r.ship_date >= '2025-01-01'
  and (c.region = 'US' or c.region = 'JP')
