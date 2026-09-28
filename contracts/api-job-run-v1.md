# Thermal job Run discovery v1

Status: internal software candidate; actual CLI, independent release and full
G1/G4 acceptance remain pending.

`GET /v1/jobs/{job_id}/run` returns the existing `ThermalRunSummary` with
operation ID `getJobRun`. Bearer identity requires all of `metadata`, `artifact`
and `thermal_run_read` before storage access. Stores independently check the
same tenant/scopes. The assembled API uses its existing authenticated JobStore
and ThermalRunStore; no new dependency, database authority or provisioning is
introduced.

Unknown/other-tenant jobs, unfinished/held/canceled jobs, non-simulation stages
and canonical receipts for another model return 404. Completed thermal jobs
must have their actual publication and a bounded canonical receipt (4096 bytes
maximum). The stored publication size is checked before artifact access.
Job/publication identity, tenant, current attempt, deterministic null AI decision,
artifact digest/size and the exact typed manifest must agree. The receipt's
snapshot/review references reconstruct the closed simulation input and must
reproduce the job's immutable input hash.

The existing Run store revalidates its signed packet and context. The receipt
must exactly match the actual Run's snapshot, review job, decision/context,
report hash and both trace hashes. The existing display projection checks
synthetic scope, rights and trace/release consistency. The route returns its
public summary only, allowing the client to use the existing Run series and
manifest paths. Raw receipts, input, decision/review IDs, signatures, secrets
and private source bytes are not returned.

Missing/inconsistent completion, malformed/noncanonical thermal receipts and
store failures return fixed 503 `store_unavailable` / `Job Run unavailable`.
Access denial returns fixed 403; authentication and UUID validation retain
401/422. No partial result, candidate or hold is converted to a successful Run.
The read creates no job, result or model invocation. A 200 demonstrates the
stored software replay only; it does not approve source G0, future economics,
crop ranking or deployment. Simulation submission, actual orchestration and
browser rendering remain separate tasks.

## Scenario-bound receipt v2

For thermal-simulation-result-v2, the route additionally requires
thermal_scenario_read, thermal_snapshot_read, decision_context_read and
market_hold_context_read. The OpenAPI x-ossf-conditional-scopes field declares
these AND requirements for that receipt version. Denial is fixed 403 before
Scenario/reference reads. Existing metadata/artifact/run scopes authorize the
bounded receipt inspection that selects the version.

The reader reconstructs input v2 including exact scenario ID/revision/hash,
checks the actual immutable job/publication, reloads the actual Scenario with
current signed references and matches its four pins/context to the verified
Run and receipt. Missing configuration/record or changed pins yields fixed 503;
it does not serve a legacy summary without the required binding. The returned
ThermalRunSummary and existing v1 requirements stay unchanged; private scenario
pins/review IDs are not added to the response.
