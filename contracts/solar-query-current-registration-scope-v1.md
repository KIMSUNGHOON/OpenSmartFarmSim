# Solar query current-registration scope — v1 candidate

Status: proposed from the [actual API request observation](../research/solar-api-request-cost-observation-20261020.md).
Isolated cost/functional evaluation passed; production verification is pending. Reuses the existing
[registration read scope](farm-registration-read-scope-v1.md),
[connection lifetime](farm-registration-connection-lifetime-v1.md) and accepted
checkpoint `_current` ownership pattern.

## Measured caller and change boundary

The observed successful prefix/sample requests each invoked the full farm
binding `current` six times and selected912 current source rows; their client
latency was13.775957–15.677736 seconds with the observer enabled. A successful
progress read invoked it four times and selected608 source rows.

`SolarExecutionQuery._current` currently calls the full binding without owning
a registration scope. Its binding performs two `read_registration` calls.
The checkpoint writer's `_current` already scopes that pair, but this query
entry does not. Confirm the actual reconstruction/call trace before attributing
the measured CPU cost to that reconstruction.

The candidate changes only this query `_current` call: after its original guard
and resolver, enter the existing farm registration scope for the exact verified
tenant/scenario/revision/hash if no owner exists; retain an existing owner with
`nullcontext` and its original argument/ownership checks. Call the original
binding with `write=False`, close the owned scope, then run the original final
guard. All other query, checkpoint, prefix and custody bodies stay unchanged.

The target is two reconstructions to one within that pair. Do not share a scope
across full queries, HTTP requests or worker quanta. Do not add the rejected
confirm-scope joining option. No permission result or JSON ownership cache is
introduced. Every ordered source/rights/root/snapshot read, current boundary,
lease/cancel/HEAD/proof/file/UTC check and response fence remains.

## Acceptance before adoption

1. RED then actual SCRAM reads: prove two baseline reconstructions, one candidate
   reconstruction, the same two registration reads and ordered fresh lookups,
   closed owned connections/tokens and no numerical calculation/data mutation.
   Existing owner behavior and wrong owner/arguments remain guarded.
2. Reject source/rights/grant/principal/research/snapshot changes between the
   paired reads and after serialization. Cover error/close/copy-context/Task/
   thread boundaries required by the reused scope; preserve original hold order.
3. Compare the whole real API handler sequence for progress → accepted prefix →
   samples on the same owned, yielded prefix of the original CASE6/64 program.
   Keep the actual SCRAM/TLS, source/profile bytes, selector, original values/
   counts/UTC and response/projection guards. Enumerate only the schema's runtime
   observation timestamps as volatile; do not remove model UTC from comparison.
   No concurrent worker advances are needed for this isolated cost comparison;
   it is not independent unpaused acceptance.
4. One original/candidate/candidate/original comparison must reduce wall time in
   both pairs with mean at least2%. Reconcile changed SQL/audit/connection counts
   with the scoped reconstruction, preserving current lookup order and all
   original fresh storage reads. Reject on failure without selecting a repeat.
5. Compare private and final product source and run affected query/prefix/HTTP,
   current/late rights, lease/cancel and projection regressions. Then the changed
   source's independent normal64 remains required before hold/cancel/WebGL/WSL
   activation. The diagnostic and local cost comparison do not pass that gate.

Native Codex CLI `gpt-6.1-sol`/`xhigh` owns this design judgment. Product claim
gates and source/parameter rights follow the authoritative specification.

## Evaluation environment

The local private candidate passed all11 focused cases in separate owned
processes with the original five protected roots live. The combined HTTPS
comparison reached its first baseline sequence, then the original1GiB limit
stopped it; no sequence completed and no valid cost trial exists.

`web-tests.yml` can select the research-only candidate evaluation with
`unpaused_solar=true`, `solar_query_scope_cost=true`, and worker diagnostics off.
It reuses the existing pinned hosted PostgreSQL/Python job. Its owned controller
keeps the512MiB single-PID/1GiB total and600second wall limits, runs the11
functional cases before one original/candidate/candidate/original HTTPS trial,
and exports only curated diagnostic evidence. It changes no application source,
original normal actor or acceptance threshold. A passing diagnostic still does
not accept normal64, WSL capacity, product adoption, new Solar deployment or any
claim gate. Preserve a valid failed cost result without selecting another trial.

For final product regressions, select `solar_query_scope_mode=product-regression`.
This mode runs29 actual-product cases (11 pair/16 query/2 prefix), checks the
product/candidate function AST, and never invokes the valid cost experiment.
Candidate-cost mode requires the original application tree. Product local20
passed, while the next UTC/heartbeat case was interrupted by the original RSS
limit and remains unaccepted; hosted regression evidence is still required.
