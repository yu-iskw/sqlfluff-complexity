/*
source_url: https://cloud.google.com/bigquery/docs/reference/standard-sql/array_functions
source_section: ARRAY subquery
license_note: Derived minimal SQL for sqlfluff-complexity fixture tests; not vendor verbatim.
verbatim: no
*/

SELECT ARRAY(SELECT v FROM UNNEST([10, 20, 30]) AS v WHERE v > 15) AS arr;
