select
  id,
  name,
  case status
    when 'active' then 1
    when 'inactive' then 0
    else null
  end as status_flag
from customers
where region = 'US'
