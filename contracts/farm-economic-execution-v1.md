# Farm-bound economic execution v1

Status: internal software candidate, following farm thermal execution V3.
Paired assessment and whole G1 remain subsequent acceptance work.

Closed economic-calculation-input-v2 extends V1 with required farm_scenario_id,
farm_scenario_revision, farm_scenario_sha256 and thermal_job_id. HTTP admission
retains the existing fixed formula, economic scenario/candidate pins and
idempotency_key. V1 shapes and Decimal arithmetic remain unchanged; V2 cannot
discard farm references or fall back to V1.

The exact FarmReplayScenarioService must share JobStore and MarketCandidateStore
with the economic worker/service, and its ThermalRunStore must be the candidate
source's actual context store. V2 verifies the current immutable whole selection,
economic scenario/revision/hash/candidate, and actual completed thermal job V3
through the existing verified Run discovery. The thermal input must name this
same farm plan/hash. A different plan, V1/V2 thermal input, pending/held job,
foreign tenant or missing configured service cannot authorize calculation.

The binding records farm identity/server-binding hash and the actual thermal
job ID, immutable input hash, canonical completion receipt hash and physical
Run ID. It is checked before arithmetic and again before/after economic result
insertion and before terminal publication within the same transaction. Current
rights, scopes, store pointers, cancellation/lease and code/environment guards
remain. Failed completion rolls back result/publication/job success and closes
with a fixed hold where the worker retains authority.

V2 admission validates that binding before and at commit, including the farm
service's current source/rights and pinned joint-scenario checks, and compares
its canonical fingerprint. 202 registers only an immutable intent. The full
derived-result Decimal calculation/replay runs in the fenced worker and on
completed result reads. V1 retains its original admission replay. No result or
gate is approved by admission, and no current-rights validation is cached.

Receipt economic-calculation-result-v2 retains V1's calculation/result hashes
and adds that binding. Economic result and cash-flow discovery validate the
actual immutable input/publication, replayed result and current farm/thermal
binding before returning the existing public DTO. V2 admission/read declare
the extra farm read scopes and thermal_run_read. Existing base scopes and V1
behavior are preserved; extra scope denial is 403 and public evidence failures
remain fixed holds/errors. ApiRuntime supplies its actual farm service.

This is conditional user-assumption arithmetic linked to a completed heat replay.
It does not convert heat into purchased energy, change tariffs, predict growth,
harvest, future margin or supply a crop ranking. Heat/cost physical coupling,
paired Assessment, full input authoring, 3D, actual CLI/independent custody and
the existing G0/G1/G2/G3/G4 acceptance remain separate work. No dependency,
schema migration or role grant is introduced. Synthetic test authorities prove
software contracts only.
