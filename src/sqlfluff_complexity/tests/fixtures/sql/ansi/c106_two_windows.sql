select
  row_number() over (partition by account_id order by created_at) as account_rank,
  count(*) over (partition by account_id) as account_rows
from orders
