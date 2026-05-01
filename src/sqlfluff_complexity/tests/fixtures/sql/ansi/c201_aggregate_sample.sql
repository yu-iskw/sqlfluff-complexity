select
  case when a.is_active then 1 else 0 end as active_flag
from a
join b on a.id = b.id
where a.country = 'US' or a.country = 'JP'
