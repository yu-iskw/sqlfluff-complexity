with prep as (
    select *
    from cte_a
    join cte_b on cte_a.id = cte_b.id
    join cte_c on cte_a.id = cte_c.id
)
select * from prep
