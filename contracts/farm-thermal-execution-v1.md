# Farm-bound thermal execution v1

Status: internal software contract candidate. This connects a registered farm
replay selection to the existing thermal execution component. Economic execution,
paired completion/assessment, UI/3D and whole G1 remain subsequent work.

The closed `thermal-simulation-input-v3` extends scenario-bound v2 with required
farm_scenario_id, farm_scenario_revision and farm_scenario_sha256. It retains
the actual thermal scenario/revision/hash, snapshot and collection review job.
The corresponding POST /v1/runs request retains required model/profile literals
and idempotency_key. V1/v2 shapes and their physical equations remain unchanged.
V2 rejects extra farm fields; V3 requires all of them and never falls back.

The actual FarmReplayScenarioService must share the worker/API JobStore and exact
ThermalScenarioStore. It replays its immutable input under current reference
rights/scopes and checks the requested whole-selection hash. The thermal job's
version/hash/snapshot must equal that selection. Execution requires the actual
completed research root and owned collection/review lineage: review input must
reference the actual completed collection, whose typed immutable input names
the selected research job and its input hash. Parent input, attempt and original
collection-record hash must match; no unrelated review with the same snapshot
can substitute. All parents are tenant-scoped. Root and collection publication
bytes/manifests are verified for hash/input/attempt/identity consistency.

This lineage check is not CLI approval. The publisher still revalidates the
actual owned review service, capture/invocation/decision, independently observed
execution, release, source rights/QC and physical replay. A farm selection does
not supply any of those approvals. Initial queued/held research can be registered
as a selection intent but cannot authorize V3 execution.

Current farm binding is checked before calculation and against the verified
packet; it is rechecked before and after Run insertion within the completion
transaction. A mismatch or revoked access rolls back Run/publication/completion
and closes the attempt with a fixed hold where authority remains available.
Missing configured farm service is a hold; no optional fields are discarded.
Normal lease expiry, cancellation, recovery and independent release checks apply.

`thermal-simulation-result-v3` keeps V2's scenario pins and adds the three farm
identity fields and farm_bindings_sha256, the canonical hash of the registered
server-derived binding manifest. It exposes no raw point, economic input or
money. Physical Run/trace identity is unchanged: selection identity is bound by
the immutable job and its receipt rather than changing the physical model.

Job Run discovery reconstructs the exact V3 input and revalidates the receipt,
publication, current farm lineage and report. It returns the existing public
thermal summary, with no farm input bytes or approval added. The normal read
scopes and V2 conditional scopes remain; V3 additionally requires the farm
selection read scopes. V3 admission also declares and checks the existing owned
review verifier's collection_read, collection_review_create and
thermal_snapshot_write scopes before inspecting that evidence. Completion
discovery requires the farm read scopes, without these admission scopes.
API/worker operator assembly explicitly supplies the
actual service. Existing default constructors support their previous versions.

No model invocation, coefficient, purchased-energy conversion, monetary
calculation, schema migration or grant is introduced. Synthetic executable,
context/release keys and test records cannot demonstrate actual CLI, independent
custody, farm accuracy, G1 or G4.
