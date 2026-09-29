# Farm calculation assessment join v1

Status: verified software implementation candidate;
[evidence](../research/farm-calculation-assessment-implementation.md).
This joins actual farm thermal v3 and economic v2 completions to the held
assessment; it does not complete the agricultural FarmScenario or any gate.

The existing closed POST /v1/assessments body remains run_job_id,
economic_job_id and idempotency_key. The server infers the internal input
version from verified parent inputs. Legacy thermal v1/v2 plus economic v1
retain calculation-assessment-input-v1. Farm thermal v3 plus economic v2
require calculation-assessment-input-v2. Mixed parents are rejected rather
than downgraded, including different thermal jobs with identical Run IDs.

Both farm parents must use the exact same scenario ID/revision/full-input
hash and current derived binding hash. The economic input and completion
must name precisely the requested thermal job, its input/receipt hashes and
Run ID. Existing completion verification rechecks actual succeeded jobs,
publication/attempt/receipt integrity, immutable canonical inputs, source
rights, context, owned completed research/collection/review lineage and
deterministic result replay. Metadata alone cannot supply these proofs.

The v2 assessment input inherits every v1 field and adds farm_scenario_id,
farm_scenario_revision, farm_scenario_sha256 and farm_bindings_sha256. All
parent input/receipt/report/result/context hashes remain pinned. Candidate
and evidence arrays remain empty. The caller key retains the existing v1
API namespace across both internal input versions; same bytes reuse the job,
different bytes under the same key conflict. Admission and final commit revalidate current bindings
and pins. CLI input parsing and authority lookup revalidate the exact stored
input and parent/context chronology before accepting any decision envelope.

CalculationAssessmentService's configured farm service must be the actual
FarmReplayScenarioService over the same jobs, thermal scenario/run stores,
economic candidates, principals and market context. ApiRuntime assembles
that same service into admission and exposes it for an operator's shared
owned CLI contract routes. Runtime assembly does not install an operating
CLI worker or validator; the operator must bind those actual services.
Missing or replaced assembly is held, with no legacy fallback. The CLI router
supports both assessment input versions without changing the proposal schema
or required model/effort. Actual invocation/output custody still belongs to
the existing CLI worker/supervisor path.

Farm parents require the existing farm economic read scopes in addition to
the assessment read/create scopes; OpenAPI declares the conditional thermal
v3/economic v2 requirements. API errors and public JobStatus/hold projection
stay unchanged. No raw receipts, input numbers, private farm identifiers or
new approval field are returned by this join.

All existing ordered missing-evidence codes remain mandatory:
market_source_g0, eligible_crop_candidates, farm_scenario_binding,
local_measurements_g2, future_validation_g3a and paired_comparison_g3b.
Here farm_scenario_binding requires the complete agricultural scenario,
including admitted crop/facility/calendar/objective constraints. A replay
registration is an immutable partial selection and does not satisfy that
requirement. No selected crop, proceed status, claim or omitted hold code
can be approved. The valid CLI hold remains immutable evidence and produces
no successful recommendation publication.

Acceptance evidence must cover an actual SCRAM pair and shared fake-CLI held
decision; version inference, identical retry, mismatched/mixed/unfinished/
foreign parents, altered pins and forbidden claims; current scope/assembly
revocation including transactional rollback; unchanged legacy behavior and
OpenAPI; and an actual HTTPS/Bearer/runtime admission/hold read with the
existing 30s client timeout. Synthetic authorities prove software only.
Actual product CLI, full farm authoring, physical heat/purchased-energy/cost
coupling and independent G1/G0/G2/G3/G4 remain separate required work.
