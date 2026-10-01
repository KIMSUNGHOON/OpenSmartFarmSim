# Joined calculation assessment v1

`POST /v1/assessments` accepts only canonical lowercase `run_job_id`,
`economic_job_id` UUIDs and an ASCII `idempotency_key` of at most 200 characters.
The closed JSON body has a 4096-byte limit. Duplicate keys, client tenants,
paths, replacement results, profiles, claims and gate approvals are rejected.
The response is existing JobStatus with `202`; it does not mean a recommendation.

The authenticated tenant needs `assessment_create`, `metadata`, `artifact`,
`market_source_read`, `market_candidate_read`, `market_result_read`,
`decision_context_read`, `market_hold_context_read`, `thermal_run_read` and
`thermal_snapshot_read`. Scenario-bound thermal receipts additionally enforce
the existing scenario read scopes. The service uses the same actual audited
authority JobStore, signed-context ThermalRunStore and MarketResultStore.
Optional ThermalScenarioStore must use those exact thermal/market-hold stores.
ApiRuntime constructs this service when its source factory returns an actual
MarketSourceStore and exposes it as `assessments`.

The [farm extension](farm-calculation-assessment-v1.md) additionally accepts
verified thermal v3/economic v2 parents using internal assessment input v2.
Its conditional scopes, exact farm and thermal-job pins, and unchanged hold
requirements are specified there. Legacy inputs retain the v1 fields below.
The [authored extension](authored-calculation-assessment-v1.md) uses assessment
input V3 for authored thermal V1/economic V3, the actual configured authored
store and a distinct V3 validator. Its release/registration/trace pins and
conditional scopes are specified separately; the public POST body is unchanged.

OpenAPI declares those conditional scopes under parent receipt version
`thermal-simulation-result-v2`, using the same SCENARIO_SCOPES tuple as the
existing verified thermal completion path.

## Immutable input and validation

The server reads both actual succeeded simulation jobs through their existing
verified completion paths. It rechecks input bytes/SHA, attempts, publication
manifests and receipt bytes, accepted synthetic thermal traces/report/release,
and full deterministic market/economic replay. The economic Market hold must
bind the same tenant, snapshot, signed context, decision time, claim mode and
actual/hypothetical marker as the thermal Run. Missing, foreign, incompatible,
unfinished or corrupted parents cannot be admitted. No thermal quantity is
converted into purchased energy or economic cost by this join.

The input version is `calculation-assessment-input-v1`. Its exact fields are:

- `input_version`, `tenant_id`, `run_job_id`, `economic_job_id`, `run_id`,
  `economic_result_id`;
- `thermal_input_sha256`, `economic_input_sha256`, `thermal_receipt_sha256`,
  `economic_receipt_sha256`, `thermal_report_sha256`, `economic_result_sha256`;
- `snapshot_id`, `context_sha256`, `market_hold_report_id`;
- `decision_context_id`, `decision_at_utc`, `claim_mode`, `decision_time_kind`;
- `temporal_provenance=ex_post_replay`, `candidate_ids=[]`, `evidence_refs=[]`.

Receipts, reports and encoded economic results use their actual SHA-256 bytes.
The candidate/evidence arrays remain empty because this calculation join has
no admitted crop profiles or independent field/comparison evidence. A market
stress scenario's numeric candidate ID is not promoted into a crop profile.
No replacement `profile_id` is invented for the generic assessment input.

The idempotency namespace remains `calculation-assessment-input-v1` plus SHA-256 of the caller's
key. Matching requests reuse the original job; another input under that key
conflicts across supported internal input versions. Before commit, original store bindings, current scopes and the
complete prepared input are checked again; failure rolls back the new intent.

## CLI assessment and stored hold

The operator installs CalculationAssessmentContract as the
`('assessment', 'calculation-assessment-input-v1')` delegate in the shared
CliContractRouter and on the actual JobStore. The API only submits the intent.
The existing CLI worker invokes the specified model/effort, records actual
invocation/output and validates the decision envelope. CLI input parsing and
server authority lookup both recheck the stored parents and exact pins.
The context/Run and parent completion times must precede the assessment job.

All supported versions require these ordered server-owned missing evidence codes:

| Code | Missing acceptance |
|---|---|
| `market_source_g0` | Approved market source for this decision |
| `eligible_crop_candidates` | Admitted crop profiles and feasible candidates |
| `farm_scenario_binding` | Common farm, calendar and objective binding |
| `local_measurements_g2` | Independent applicable local measurements |
| `future_validation_g3a` | Independent future crop/economic validation |
| `paired_comparison_g3b` | Independent paired candidate comparison |

The decision may select no candidate and make no scientific/economic claim.
`proceed`, invented selected IDs, claims, missing-code edits or altered context
are rejected by the deterministic server. A valid CLI `hold` preserves the
existing immutable decision/output/validation evidence and `hold_v1` report;
it publishes no successful recommendation artifact.
`GET /v1/jobs/{job_id}` returns status; the existing auditor-protected
`GET /v1/jobs/{job_id}/hold-report` displays these bounded public categories.
Private identifiers still collapse to `other_evidence`. Raw prompts, outputs,
prose reasons, hashes, tenant identifiers and arithmetic are absent from that
public hold projection.

Authentication/scope failures are `401/403`, intent conflict `409`, excessive
body `413`, wrong media `415`, malformed body or unavailable parent evidence
`422`, missing configured service or private backend failure `503`. Responses
use fixed ErrorEnvelope messages; backend exception detail is withheld.

This is the initial synthetic held assessment. Actual model invocation,
independent planning/execution/release, complete farm scenario, browser/3D,
complete G1 and real G0/G2/G3/G4 acceptance remain required. Future forecasting
and ranking require their separate documented paths and evidence.
