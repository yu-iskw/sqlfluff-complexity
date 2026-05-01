select *
from outer_a
join outer_b on outer_a.id = outer_b.id
join outer_c on outer_a.id = outer_c.id
where outer_a.id in (
    select inner_a.id
    from inner_a
    join inner_b on inner_a.id = inner_b.id
    join inner_c on inner_a.id = inner_c.id
)
