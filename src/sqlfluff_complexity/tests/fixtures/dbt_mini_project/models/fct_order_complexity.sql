{{ config(materialized='view') }}

with orders as (
    select *
    from {{ ref('stg_orders') }}
),

classified as (
    select
        order_id,
        case
            when amount > 100 then 'large'
            else 'standard'
        end as order_size
    from orders
)

select
    order_id,
    order_size
from classified
where order_size = 'large' or order_id = 1
