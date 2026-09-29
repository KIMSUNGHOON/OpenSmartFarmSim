# Farm replay scenario registration v1

Status: internal implementation contract candidate. This joins existing inputs
for the first synthetic path; it is not the complete agricultural FarmScenario,
a coupled heat-to-energy-cost model, source approval or a gate acceptance.

`POST /v1/farm-scenarios` accepts a closed `FarmReplayScenarioRequest` containing
schema_version=farm-replay-scenario-v1, scenario_id, scenario_revision,
research_job_id, thermal (scenario_id, revision, sha256), economic (scenario_id,
revision, sha256, candidate_id), decision_at, market_context, goal_id=
historical-thermal-replay, origin=user and evidence_level=assumed. All fields are
required. The tenant is the authenticated principal. The 4096-byte strict JSON
transport rejects duplicate keys, extra fields and nonfinite numbers.

The server reads the original, hash-verified research input and the protected
ResearchRegistry registration. The point, replay interval, goal and provider
set must match that registration and its digest. Spatial support remains
pending_research: registered coordinates do not prove that synthetic weather
describes the location. The original research job may still be queued or held;
input registration does not complete research or create a CLI decision.

The actual thermal selection must match its immutable version/hash and current
signed snapshot/context/market-hold references. The weather replay interval must
equal the registered research interval. The economic candidate is replayed with
MarketScenarioService.validate_pinned, including current source, rights and
settlement checks. Its ID/hash, decision time and unavailable MarketContext
must match the thermal context and the request. Korean calendar dates of the
thermal interval must lie in the economic evaluation period. No monthly amount
is converted to a thermal time-step value or energy purchase.

The canonical immutable job input contains the authenticated tenant, complete
request and server-derived binding hashes, point/interval and pending spatial
support. Registration uses the existing JobStore transaction, with a namespaced
tenant/stage key derived from scenario_id and revision. Identical retries reuse
the first job; changed bytes for that version conflict. The commit guard repeats
current scopes, exact store/registry bindings and all input checks. Failure rolls
back the job and submission event. No table, grant, schema migration or numeric
default is introduced.

`200` returns scenario_id, scenario_revision, scenario_sha256 (hash of the entire
stored input), registration_status=registered_intent and the actual intent_job.
The collection-stage row is a stored selection intent, not a collection result;
this route runs no worker, model, calculation or publication. Subsequent workflow
must bind its actual thermal/economic jobs and assessment to this version.

`GET /v1/farm-scenarios?scenario_id=...&scenario_revision=...` returns the same
summary after validating immutable bytes, tenant/version identity and every
current binding again. This is a current reference read, not historical receipt
recovery. No raw input, source, geometry, private point, money or approval is
returned. Corrections use a new revision. Missing/other-tenant intent is 404;
conflicts are 409; unsupported input/references are fixed 422; authentication
failures are 401/403; body/media errors are 413/415; missing assembly or internal
binding failures are fixed 503 without exception details.

AND read scopes: farm_scenario_read, metadata, artifact, thermal_scenario_read,
thermal_snapshot_read, decision_context_read, market_hold_context_read,
market_source_read and market_candidate_read. Registration additionally requires
farm_scenario_write. Exact actual stores must share the authority SCRAM policy,
DSN, schema and principal callable; the thermal scenario and market source
features must already be enabled. Protected runtime assembly also needs its
actual ResearchRegistry and owned source store. Custom repositories do not
enable this service.

General farm/event/settlement authoring, crop profiles and constraints, physical
and economic coupling, worker orchestration, actual CLI, independent custody and
release, browser/3D/full G1 and G0/G2/G3/G4 remain pending. Synthetic records and
signatures test software contracts only.
