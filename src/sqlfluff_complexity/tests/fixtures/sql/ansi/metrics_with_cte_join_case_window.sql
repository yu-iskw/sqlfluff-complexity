with a as (select id, created_at from raw_a),
     b as (select id, status, country from raw_b)
select
  a.id,
  case when b.status = 'active' then 1 else 0 end as is_active,
  row_number() over (partition by b.country order by a.created_at) as row_num
from a
join b on a.id = b.id
where a.created_at >= '2025-01-01'
  and (b.country = 'US' or b.country = 'JP')
