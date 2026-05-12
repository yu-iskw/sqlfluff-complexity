select
  id,
  case status
    when 'active' then 1
    when 'inactive' then 0
    else null
  end as status_flag,
  dateadd(day, 30, created_at) as expiry_date
from customers
where region = 'US'
qualify row_number() over (partition by id order by created_at desc) = 1
