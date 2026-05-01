select
  case when status = 'active' then 1 else 0 end as active_flag,
  case when country = 'JP' then 1 else 0 end as jp_flag
from customers
