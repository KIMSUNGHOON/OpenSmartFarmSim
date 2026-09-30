# Authored thermal Run read v1

Status: internal authenticated read candidate. Its successful response means a
current, owned, signed-release-backed synthetic thermal replay is available; it
does not assert independent G1 acceptance or crop/economic accuracy.

`GET /v1/authored-runs/{run_id}` returns bounded summary metadata and
`GET /v1/authored-runs/{run_id}/series` returns exactly 120 one-minute points.
`GET /v1/jobs/{job_id}/authored-run` resolves a succeeded authored simulation
job to the same summary after checking its input, immutable receipt,
publication, tenant and Run binding. A fixed-fixture simulation job is not an
authored result. The authored ID has the form
`authored-thermal-run-v1:<64 lowercase hex>` and is never passed through the
fixed-fixture `/v1/runs` routes.

All three reads require an authenticated owner with `metadata`, `artifact`,
`authored_run_read`, `authored_release_read`, and current authored farm read
scopes. The server revalidates the stored job/publication/receipt, gate HMAC,
exact trace bytes and their SHA-256s, signed release, source rights, farm
registration and current code before projection. A missing or foreign result
returns 404, missing scope 403, invalid request 422, and stale or corrupt
current evidence 503. Errors reveal no private source, release or trace text.

Summary fields identify the authored scenario revision, registration digest,
release digest, exact trace digests, decision/review times, two-hour interval,
engine and unit versions, and `synthetic=true`,
`claim_scope=synthetic_thermal_replay_only`,
`temporal_provenance=ex_post_replay`. Series points contain UTC time, indoor
temperature (K), humidity ratio (kg_v/kg_da), relative humidity (fraction),
model heat demand and delivery (W_th), and delivered thermal energy in each
minute (kWh_th). The response does not expose input records, user rights
declarations, raw release packets, signatures, CLI capture, purchased energy,
plant growth, future margin or a crop ranking.

This is a read contract only. It does not submit authored inputs, assemble a
product CLI worker, or grant G0/G1/G2/G3/G4. A browser may render the values
with the existing conceptual greenhouse geometry only when it keeps the
synthetic and claim-scope labels visible.
