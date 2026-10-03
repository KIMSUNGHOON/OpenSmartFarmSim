# Farm replay scenario input connection

Recorded 2026-09-29. This is software evidence for
[the registration contract](../contracts/farm-replay-scenario-v1.md), not full
FarmScenario, G1, source, crop, economic forecast or operating acceptance.

## Development decision and implementation

The active Codex CLI development session reports `gpt-6-sol` and `xhigh` in its
2026-09-29T12:17:55.991Z turn context, thread
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`. No recursive CLI was launched. This
development context is not a product runtime invocation or independent review.

[FarmReplayScenarioService](../backend/app/farm_replay_scenario.py) joins actual
registered research input, an immutable thermal selection and a replayed
economic candidate. The full authenticated request and server-derived input
pins are stored in the actual JobStore collection intent transaction. Version
identity is tenant/scenario/revision; changed bytes conflict and correction needs
a new version. Registration has no worker execution, publication or result.

The service uses the existing authority login and exact store/principal
bindings. It adds no dependency, table, migration, role grant, coefficient,
tariff, assumed numeric default or arithmetic result. Current scope/binding and
reference checks repeat inside the commit guard and on reads. Registered point
and period are checked against the protected ResearchRegistry. Initial queued
research is permitted as an input intent; its point remains pending_research.
For an owned signed-context research input, the actual OwnedResearchService
reconstructs the protected bundle/context binding and chronology. The selected
thermal context must match; a caller-supplied context is not approval evidence.

The thermal selection retains its synthetic fixed physical profile. Economic
registration validates current original source/rights/settlement pins through
MarketScenarioService.validate_pinned, without creating a money result. Both
components share the decision time and unavailable MarketContext. The thermal
interval must match the research interval and fit the economic period in the
Korean calendar. This does not establish physical heat-to-cost coupling or farm
accuracy. Input authorship labels remain those of their existing source records.

Protected ApiRuntime assembles this service when its actual source store and
thermal selection feature are enabled. A custom source reader or missing
assembly cannot enable registration. Public POST/GET summaries expose only
version/hash/registered intent and the actual public job state; no point, raw
input, source, geometry or money is returned. The new implementation is included
in the existing runtime code digest, requiring fresh independent release evidence
before an actual publisher can accept the changed code.

## Checks and observed failures

Focused checks use `uv run --locked --group dev pytest` with an explicit local
PostgreSQL DSN. Runtime login fixtures start an isolated SCRAM cluster; the
source inputs, context signatures and protected catalog are self-authored test
records. No actual Codex model or external provider is exercised here.

- Initial test collection failed because the new module did not exist
  (0.23s), establishing the missing behavior. The first implementation exposed
  a canonical serializer misuse: its input requires an object, not an array
  (1 failed, 20.03s). The version key now hashes a closed object.
- The first storage/reference increment passed 3 tests in 136.30s before the
  signed-root and HTTP additions.
- The expanded run had 4 passed, 1 failed in 225.69s. The four current storage,
  scope/rights/late rollback and owned signed-root cases passed. The HTTP helper
  incorrectly placed the query inside the ASGI path, yielding 404. The helper
  now supplies path and query separately; the route contract was preserved.
- OpenAPI registry verification first failed on four missing operation entries
  (1 failed, 1.21s). The registry now lists both farm operations and the existing
  cash/receipt reads. The next run had 37 passed, 2 failed in 18.86s because the
  scope harness lacked required GET parameters. Valid parameters now accompany
  scope-denial tests; no scope assertion was relaxed.
- Corrected HTTP/OpenAPI checks plus the initial runtime attempt had 40 passed,
  1 failed in 88.05s. The standalone runtime fixture had not provisioned its
  private artifact directory. That path was confirmed absent; the test now
  creates it with mode 0700. Runtime refusal for absent roots was preserved.
  A standalone test import also exposed a missing test-local backend path
  (collection failed, 0.18s); it now follows the neighboring test convention.
- The corrected actual HTTPS/Bearer/runtime/SCRAM case passed in 51.27s.
  Unauthenticated POST returned 401; a reader POST returned 403; actual POST
  and identical retry returned one queued intent; reader GET returned the same
  version; another tenant received 404. An unexpected worker DB grant caused
  current GET to return 503. The real service shut down and the test DB/roles
  were cleaned up.

There are **45 unique passing focused cases across terminal runs**: 5 joint
selection cases, 1 actual TLS runtime case and 39 OpenAPI cases. The mixed runs
above are not claimed as wholly green. Current-source registration/lookup timing
observations in the actual TLS test were 12.179s, 11.927s and 6.211s; its existing
30s HTTP client timeout was not extended. These are local observations for one
selection, not a production capacity claim.

Existing runtime configuration, least-privilege/default assembly, actual
foreground HTTPS API and scenario-bound thermal HTTP/worker/Run regressions
passed **35 in 49.92s**. Together with the focused cases above, this is 80 unique
passing cases across terminal runs. Frontend checks were not rerun locally:
no frontend source or dependency changed. `git diff --check` passed and all
266 local Markdown targets in the changed documentation resolved. Task counts
remain 19 accepted and 20 pending.

## OpenAPI correction

An isolated archive of exact pre-change HEAD `6c07917` generated its own schema
under the locked backend environment. Its checked-in artifact did not match its
source: `/v1/jobs/{job_id}/economic-cash-flow` and
`/v1/break-even-plans/receipt` were missing. Regeneration fixes that drift while
adding the new farm path. All preexisting path contracts compare equal between
the pre-change source generation and current generation; the farm path is the
only new path. The operation registry now checks all four previously unlisted
operations, including each required scope before any storage read. Current
`python -m app.api_openapi --check` succeeds.

## Review and remaining work

The review checked contract fidelity, bounded typed input and SQL parameters,
immutable replay/version identity, current rights/scopes and rollback,
minimal summary/error exposure, exact runtime bindings and digest coverage.
No frontend, dependency, provisioning or operating policy was changed. The
service intentionally stores a selection intent using the existing intake
pattern; a future version-aware workflow must bind actual thermal/economic
execution and assessment to it. Existing workers do not gain a new interpreter,
model authorization or permission from this registration.

General farm/event/settlement authoring, crop profiles/goals/constraints,
physical/economic coupling, workflow failure/restart recovery, browser connection,
3D and whole G1 remain pending. Real model execution, independent source/rights
and release custody, real G0/G2/G3a/G3b and operating G4 remain separate holds.
The larger existing task checkboxes are unchanged. Full backend CI and existing
runtime/execution regression outcomes are reported for their own terminal run
or exact commit; this document does not claim an unobserved full-suite pass.
