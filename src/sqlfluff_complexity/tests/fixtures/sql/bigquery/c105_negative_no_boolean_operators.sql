select
  id,
  case status
    when 'active' then 1
    when 'inactive' then 0
    else null
  end as status_flag,
  date_diff(current_date(), created_at, day) as age_days
from `project.dataset.customers`
where region = 'US'
