-- DML: INSERT ... SELECT with inline derived table (ansi parse tree coverage).
insert into target_table (id)
select x.id
from (select id from source_table) x;
