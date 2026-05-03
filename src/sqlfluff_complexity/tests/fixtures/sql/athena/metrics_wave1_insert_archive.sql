/*
source_url: n/a
source_section: INSERT SELECT
license_note: Derived minimal SQL for sqlfluff-complexity fixture tests; not vendor verbatim.
verbatim: no
*/

INSERT INTO arch_cpx_w1
SELECT s.a FROM (SELECT CAST(1 AS INT) AS a) AS s WHERE 1 = 1;
