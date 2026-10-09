# Thermal Run submission v1

Status: internal software candidate, synthetic historical thermal profile only.
This implements the thermal submission component of `POST /v1/runs`, not the
complete farm/economic Scenario or workflow, an approved crop forecast or G1/G4.

## Request and authority

`submitThermalRun` accepts JSON of at most 4096 bytes. Every field is required:
input_version=`thermal-simulation-input-v2`, snapshot_id, scenario_id,
scenario_revision, scenario_sha256, review_job_id, model_version=`thermal-v1`,
parameter_set_version=`synthetic-thermal-parameters-v1`, idempotency_key.
Identifiers/hashes follow [scenario execution v2](thermal-simulation-worker-v1.md#scenario-bound-input-and-receipt-v2).
The closed strict request rejects extra tenant, coefficient, raw source, output,
approval or override fields, duplicate keys and nonfinite JSON numbers.

The AND scopes are thermal_run_submit, metadata, artifact,
thermal_scenario_read, thermal_snapshot_read, decision_context_read and
market_hold_context_read. Tenant comes only from the authenticated principal.
Headers/body cannot select a different tenant. The request principal does not
receive simulation_execute or thermal_run_publish merely to submit.

`ThermalRunSubmissionService` requires the actual publisher/Scenario store bound
to the exact shared Run store, audited SCRAM authority JobStore, v6 policy,
schema/DSN and principal callable. Binding is checked at construction and again
at admission/commit. No unbound owner, fake reader or implicit publisher exists.

## Admission, idempotency and execution

Before queueing, the service reads the actual immutable scenario and pins.
Publisher.validate_submission shares the same input-validation path as prepare:
exact completed collection review/input/publication/decision/capture/outcome,
signed tenant/snapshot DecisionContext and chronology, independently observed
execution, current synthetic source rights/QC/model limits and byte pins, actual
code/environment digest and independent signed release. It returns only a
private verified binding; it calculates no trace, publishes no Run and grants no
G1 approval. Actual review context/hash/manifest must match the selected record.

Only the canonical v2 simulation input is stored in the actual JobStore. Model
and parameter literals are checked by the request and scenario contracts;
idempotency_key is the existing tenant/stage intent identity. Same bytes/key
return the same job, including its current terminal state. Changed bytes/key
conflict. Corrections use a new scenario revision and a new intent.

JobStore.submit's optional commit_guard runs inside the job/event transaction
after immutable-input comparison and before commit. This service rechecks
current submission scopes, exact bindings, signed references and scenario/report
pins there. Failure rolls back the new job and its submission event. Other
submit callers retain the previous no-guard behavior. A queued job is not a
promise of successful execution: the targeted worker repeats all current
publisher and scenario checks, then atomically publishes Run/completion/receipt.

`202` returns the existing public JobStatus, not a Run ID, raw pins, review output
or gate approval. Poll `GET /v1/jobs/{job_id}`, then the verified
[job Run lookup](api-job-run-v1.md). Authentication/scope failures are fixed
401/403; unsupported JSON/input is 422; missing admission evidence is fixed
422 simulation_hold; differing intent is 409; transport size/media failures are
413/415. Missing configured service or unexpected internal failure is fixed
503 simulation_unavailable. Internal exceptions/data are never HTTP detail.

## Operator assembly and limits

ApiRuntimeDependencies adds optional thermal_publisher_factory, default None.
With explicit v6 storage, the protected factory receives the runtime's actual
run_store/job_store and returns the exact configured publisher. It must provide
independent release/execution resolvers and protect keys/output; initialization
must make no model call. Other policies reject this option. Without the factory,
the operation returns 503 after authorization. No credentials, owner provision,
new CLI call, deployment flag or runtime migration is supplied by this change.

Current tests use real SCRAM/immutable records and fresh Bearer assembly but
controller-owned synthetic keys/captures. They prove software admission and
publication contracts only. Actual product CLI execution, independent review
and release custody, protected deployment/operator factory, browser/full G1/G4,
complete crop/economic plans and G0/G2/G3 evidence remain separate holds. A new
code digest requires a fresh independent release; old evidence is not rewritten.
