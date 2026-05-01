select *
from customers
where active = true and country = 'JP' or country = 'US'
