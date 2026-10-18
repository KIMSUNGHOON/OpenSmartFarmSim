# Request-local farm registration reads — v1

This is a prerequisite of the measured [Solar validation slice](../research/crop-solar-current-binding-cost-20261018.md).
It preserves current source and authorization reads while avoiding repeated
deterministic reconstruction within one explicitly opened custody operation.

`FarmAuthoringService.registration_read_scope(tenant, scenario, revision, sha)`
owns one private, bounded in-memory witness. The first read uses the original
full registration validation. It records the ordered public market lookups,
their arguments and canonical values, the research input and thermal snapshot.
Later reads repeat every recorded lookup, including duplicates, through the
actual repository's existing read scope and validators. They re-read the farm
and research rows, verify the current owned registry/context and thermal
snapshot, and recheck owner/principal/pointer/code/Decimal-context bindings.
Only identical validated inputs permit reuse of the deterministic reconstruction.
Source reads, rights checks and role audits are never satisfied by stored values.

The witness has no connection, filesystem authority, serialized representation,
cross-request lifetime or published status. Wrong scope/tenant/version, nested
scope, closed witness, changed data or authority and excessive trace size fail
closed. Returned registration values are copied. Ordinary reads outside this
explicit scope retain the existing full validation path.

Acceptance: one full reconstruction for repeated scoped reads; unchanged
ordered current lookups and bytes/UTC; current rights/source/row/grant/pointer
changes rejected; no SQL mutation, crop/climate/CLI execution or extra Run;
close/error isolation and a new full validation in the next scope. All existing
Solar current boundaries remain. Measure the same real1→2 advance after integration;
native64-step completion and resource/3D/gate acceptance remain separate.
