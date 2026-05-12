/*
source_url: https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax
source_section: SELECT * EXCEPT
license_note: Derived minimal SQL for sqlfluff-complexity fixture tests; not vendor verbatim.
verbatim: no
*/

WITH t AS (
  SELECT 1 AS column1, 2 AS column2, 3 AS keep_me
)
SELECT
  * EXCEPT (column1, column2)
FROM t;
