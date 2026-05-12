select
  id,
  case status
    when 'active' then 1
    when 'inactive' then 0
    else null
  end as status_flag,
  date_sub(current_date(), 30) as past_date
from customers
where region = 'US'
