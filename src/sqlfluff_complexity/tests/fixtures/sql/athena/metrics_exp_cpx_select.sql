/*
source_url: n/a
source_section: Synthetic SELECT
license_note: Derived minimal SQL for sqlfluff-complexity fixture tests; not vendor verbatim.
verbatim: no
*/

WITH base AS (SELECT 1 AS x)
SELECT b.x, row_number() OVER (ORDER BY b.x) AS rn
FROM base AS b
JOIN (SELECT 2 AS y) AS j ON j.y > (SELECT MIN(z) FROM (VALUES (3)) AS t(z));
