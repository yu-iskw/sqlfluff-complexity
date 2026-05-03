/*
source_url: n/a
source_section: Synthetic CTE + join + window
license_note: Derived minimal SQL for sqlfluff-complexity fixture tests; not vendor verbatim.
verbatim: no
*/

WITH w1 AS (SELECT 1 AS k)
SELECT w1.k, rank() OVER (ORDER BY w1.k) AS r
FROM w1
INNER JOIN (SELECT 2 AS m) AS j ON w1.k < j.m;
