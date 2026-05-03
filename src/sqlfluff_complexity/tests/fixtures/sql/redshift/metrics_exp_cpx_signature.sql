/*
source_url: https://docs.aws.amazon.com/redshift/latest/dg/r_LISTAGG.html
source_section: LISTAGG
license_note: Derived minimal SQL for sqlfluff-complexity fixture tests; not vendor verbatim.
verbatim: no
*/

SELECT LISTAGG(CAST(1 AS VARCHAR), ',') WITHIN GROUP (ORDER BY 1) AS s FROM (SELECT 1 AS n UNION ALL SELECT 2 AS n) AS t;
