/*
source_url: n/a
source_section: EXISTS + boolean
license_note: Derived minimal SQL for sqlfluff-complexity fixture tests; not vendor verbatim.
verbatim: no
*/

SELECT 1
WHERE EXISTS (SELECT n FROM (VALUES (1)) AS x(n) WHERE x.n = 1)
  AND (1 = 1 OR 2 = 2);
