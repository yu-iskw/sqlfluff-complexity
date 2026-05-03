/*
source_url: https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-transform.html
source_section: TRANSFORM
license_note: Derived minimal SQL for sqlfluff-complexity fixture tests; not vendor verbatim.
verbatim: no
*/

SELECT TRANSFORM(ARRAY(1, 2), x -> x + 10) AS bumped;
