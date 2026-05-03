/*
source_url: https://docs.aws.amazon.com/athena/latest/ug/presto-functions.html
source_section: cardinality
license_note: Derived minimal SQL for sqlfluff-complexity fixture tests; not vendor verbatim.
verbatim: no
*/

SELECT cardinality(ARRAY[1, 2, 3]) AS c;
