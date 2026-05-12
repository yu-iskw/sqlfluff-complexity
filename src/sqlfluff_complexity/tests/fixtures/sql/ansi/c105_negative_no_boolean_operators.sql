select
  id,
  case status
    when 'active' then 1
    when 'inactive' then 0
    else null
  end as status_flag,
  amount * 1.1 as adjusted_amount
from orders
where region = 'US'
