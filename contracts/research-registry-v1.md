# Research provider registry v1

[ResearchRegistry](../backend/app/research_registry.py) supplies the same immutable
registration facts to [location admission](api-location-research-v1.md) and
`DecisionContract`'s research authority resolver. Only privileged server assembly
may construct it, using canonical raw JSON bytes and an independently configured
expected SHA-256. Neither input is taken from a request or CLI proposal.

The closed document has `registry_version="research-registry-v1"` and
`registrations` (1–64 items), within 65,536 raw bytes. Each closed registration
has `tenant_id`, `point` (latitude/longitude), `period_start_utc`, `period_end_utc`,
`goal_id` and 1–20 unique `provider_ids`. Coordinates, goal and increasing UTC
period follow the location contract. Tenant/provider identifiers are bounded.
The internal `research-registry-sha256:` provider namespace is reserved.
Duplicate exact tenant/point/period/goal registrations are rejected, rather than
silently selecting an entry. Unknown fields, duplicate JSON keys, invalid
canonical bytes and pin mismatches reject construction with a fixed message.

`scope_for_location(tenant, LocationRequest)` returns a matching frozen
`ResearchScope` with the catalog's actual raw hash, or `None`. It performs no
SQL, network request, signing or collection. A registry entry authorizes only
inspection of these candidate IDs. It is not a source record, rights/QC review,
geographic coverage measurement or G0 approval. The operator must separately
protect the configured hash and file; hashing alone proves no authorization.

`authority_snapshot(job, parsed_input)` reparses the job's hash-checked raw bytes,
requires research stage, exact matching input and registration/provider/catalog
identity, no evidence refs and the existing all-null planning context. Mismatch
returns no authority. It creates server bindings from registration facts, not
from proposed output, with no evidence/approved claims or G3 permissions.
Its `allow_proceed=False` and ordered missing evidence are
`research_source_evidence`, `signed_decision_context`. The CLI must still execute
and propose the exact structured hold; this resolver does not manufacture a
decision or replace required runtime research with static text.

This resolver covers initial preparation only. Later collection and assessment
need separate evidence/context authorities and gates. A new registry creates
new raw bytes/hash; it cannot rewrite stored job input, approve old requests
against a changed catalog or erase past holds. A retired hash returns no authority
unless the operator deliberately assembles its original approved registry.
Operating authentication/custody, actual CLI invocation, G0/G1 and G4 remain
separate acceptance requirements.
