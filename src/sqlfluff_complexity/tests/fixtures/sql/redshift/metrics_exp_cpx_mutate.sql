/*
source_url: https://docs.aws.amazon.com/redshift/latest/dg/r_INSERT_30.html
source_section: INSERT
license_note: Derived minimal SQL for sqlfluff-complexity fixture tests; not vendor verbatim.
verbatim: no
*/

INSERT INTO tgt_cpx_exp
SELECT n FROM (VALUES (1), (2)) AS s(n)
WHERE EXISTS (SELECT 1 FROM (VALUES (1)) AS e(x) WHERE e.x = s.n);
