/*
source_url: n/a
source_section: CASE + scalar subquery
license_note: Derived minimal SQL for sqlfluff-complexity fixture tests; not vendor verbatim.
verbatim: no
*/

SELECT CASE WHEN TRUE THEN (SELECT 2) ELSE 0 END AS x;
