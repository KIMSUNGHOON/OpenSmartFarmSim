# Current runtime privilege matrix queries — v1

Scope: reduce repeated farm-registration validation overhead without changing
the [runtime role policy](runtime-role-policy-v1.md) or its login extensions.
The actual profiled read performed 21 audits; its two matrices returned 24,024
rows. This is component evidence, not independent worker throughput evidence.

Each audit still checks the full current role/table/privilege cross product.
Expected grants come from the existing `_allowed` policy, not a permission cache.
The two existing statements retain their order. The column statement compares
current table and any-column rights together and rejects every grant option.
NULL inquiry results must fail closed, including an object dropped after scope
discovery. Existing owner, role, membership, schema, routine, sequence, default
and unexpected ACL checks remain in place.

Acceptance: successful matrix statements each return zero rows; a mismatch
returns at most one row and the existing hold reason. Real PostgreSQL tests
cover selected/unselected storage, forbidden/missing/table/column grants,
revocation between statements, and disappearing objects. Repeat the same
component probe after the change. Native unpaused success, WSL capacity, G0–G4
and deployment require their separate original evidence.

PostgreSQL defines [effective privilege inquiries](https://www.postgresql.org/docs/16/functions-info.html#FUNCTIONS-INFO-ACCESS-TABLE)
and [NULL-aware comparisons](https://www.postgresql.org/docs/16/functions-comparison.html).
The choice to filter mismatches on the server is a project implementation decision.
