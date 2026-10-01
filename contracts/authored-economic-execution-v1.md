# Authored farm economic execution v1

Status: internal software candidate; implementation and acceptance evidence are
recorded separately. This extends the conditional economic calculation path
after an authored thermal Run has actually completed.

## Input and authority

Closed `economic-calculation-input-v3` retains the V1 economic scenario ID,
revision, SHA-256, candidate ID and fixed formula. It requires
`authored_scenario_id`, `authored_scenario_revision`, `registration_sha256` and
`thermal_job_id`. HTTP admission additionally requires the existing stable
`idempotency_key`. V1 and V2 keep their original meaning. V3 never downgrades to
an unbound calculation, a farm replay selection or an unpublished candidate.

The configured actual AuthoredRunStore, preparer, owned FarmAuthoringService,
release store, JobStore, farm replay service and economic candidate authority
must share their existing identities. Missing authority rejects V3. Admission,
worker publication and completed result/cash reads require current authored
Run/release and farm read scopes in addition to their existing economic scopes.
No new role grant, schema migration or dependency is introduced.

The exact succeeded, uncanceled authored simulation job must have a canonical
immutable input and the matching publication, bounded receipt and currently
verified stored Run. Current registration must match the named scenario,
revision and registration hash, current source/rights/decision context and
the exact economic scenario/revision/hash/candidate pinned by that farm.
The receipt binds the authored identity, registration, current server binding
hash, compiled numeric input hash, release hash and actual thermal job/input/
receipt/report/Run. Client supplied completion hashes are not accepted.

## Lifecycle and result

Admission fingerprints this binding before and at immutable intent commit.
202 authorizes a queued request only. The economic worker repeats the binding
before arithmetic and before/after result insertion and before terminal
publication, retaining its lease, cancellation, code/environment and store
identity guards. A changed right, release, parent or binding holds the work and
rolls back any result/publication/success in that transaction.

`economic-calculation-result-v3` retains V1's arithmetic result pins and adds
the authored binding. Completed reads replay the existing economic result and
currently verify the same parent and binding before returning the existing
bounded money/cash DTO. No new numeric formula, coefficient, tariff, crop
quantity or public claim is introduced. Results remain conditional user
assumption arithmetic with assessment `hold`.

The owned authored Run is a synthetic thermal replay. This connection does not
establish purchased energy, future harvest/margin, a crop ranking or an
independent G1 review. Paired authored Assessment, general user orchestration,
actual product CLI with `gpt-6.1-sol`/`xhigh`, independent release and G0–G4
acceptance remain subsequent work. Synthetic authorities test software only.
