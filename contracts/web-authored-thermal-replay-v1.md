# Authored thermal replay web read v1

Status: internal browser implementation candidate. This extends the
[authored Run read contract](api-authored-thermal-run-v1.md) and the
[first thermal viewer](web-thermal-replay-v1.md). It does not accept `web-replay`,
G1, or public deployment.

The operator chooses either a fixed synthetic Run or an authored farm thermal
Run before entering an owned, completed job UUID. Choosing another kind or
changing the UUID clears the previous display and pending result. The authored
path reads `GET /v1/jobs/{job_id}/authored-run`, then
`GET /v1/authored-runs/{run_id}` and `/series` with the same in-memory Bearer
token and no-store/omitted-cookie policy as the fixed path. It never sends an
authored ID to `/v1/runs` or submits a simulation.

The client requires the discovery and summary to agree exactly, an authored
Run ID, accepted synthetic thermal-only scope, ex-post provenance, pinned
engine/units, two trace digests, and 120 bounded, finite points at adjacent
one-minute end times. Any mismatch or failed read leaves the scene absent and
shows a hold. The server owns authorization and current registration, release,
source-right and raw-trace validation on every read. Client checks only guard
against an incoherent display; they cannot grant a gate.

One selected stored point drives the conceptual Three.js greenhouse, chart,
numeric summary and HTML table. The authored notice identifies the input as
farm-authored and synthetic, and shows scenario revision and registration,
release and trace digests. It explicitly states that independent G1 and field
accuracy are not established. The view does not imply plant growth, harvest,
purchased energy, costs, future margin or crop selection.

## Verification boundary

Run typecheck, unit, build and browser checks. Browser response doubles verify
the three authenticated routes, actual WebGL draw, frame change, exact point
identity across the scene/chart/summary/table, kind reset and malformed scope
hold. They are software fixtures. A separate authenticated HTTPS/SCRAM smoke
against a normally assembled authored runtime is still required before
calling this an operator-visible authored flow. Product CLI and independent
release/G1 evidence remain separate.
