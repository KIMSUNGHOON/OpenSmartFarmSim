# Farm economic execution: implementation evidence

Date: 2026-09-29. Internal software candidate; no whole G1 or farm claim.
Contract: [farm economic execution v1](../contracts/farm-economic-execution-v1.md).

## Development context and implementation

The active Codex CLI turn context at `2026-09-29T13:49:45.270Z` records model
`gpt-6-sol`, effort `xhigh`, thread `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`.
This already-running session supplied the reviewable development judgment.
No recursive CLI, product model invocation or provider data adoption was
performed for this increment.

- Closed economic input/request V2 adds required farm ID/revision/hash and
  thermal job ID. V1 remains supported without discarding V2 references.
- A dedicated binder requires the exact Farm/Job/Candidate/Context assembly,
  current farm/thermal read scopes, and an actual completed thermal V3 job for
  the same immutable farm selection and economic candidate pins.
- Verified thermal completion now internally returns its already-verified
  selection/input/receipt along with the public summary. The economic binder
  checks the actual canonical thermal job input too. Public Run discovery still
  returns the existing DTO; all publication/Run/release/context/lineage checks
  remain. There is no caller-provided selection or permission cache.
- V2 admission compares the canonical current binding before and at commit.
  Farm references still replay baseline validation and check the joint candidate,
  source rights and immutable pins. Full derived-result Decimal arithmetic is
  left to the fenced worker and completed-result discovery. V1 admission replay
  is unchanged. 202 publishes only an immutable intent, not a result or gate.
- The worker checks the current farm/thermal binding before calculation and
  before/after result insertion, retains full deterministic result replay, and
  atomically commits the result, receipt/publication and terminal job state.
- Receipt V2 retains the existing result/calculation digests and adds farm,
  binding, thermal job/input/receipt and Run identity. Result and monthly cash
  discovery revalidate the current binding and retain their public DTOs.
- ApiRuntime supplies its actual farm service. No dependency, table, role grant,
  physical model, purchased-energy conversion, tariff or Decimal formula changes.

## Checks and observed failures

Local PostgreSQL 16.15 uses actual isolated SCRAM logins with the existing
market/source/thermal-scenario/break-even profiles. HTTPS/Bearer transport is
actual. The CLI executable, weather and research/review/release/execution
authorities are controlled synthetic fixtures. These tests do not establish an
actual product model decision, independent custody/release, G0 or full G1/G4.

- The first closed input test failed at import because ECONOMIC_INPUT did not
  exist; both input/request tests then passed. OpenAPI initially failed its
  snapshot test; regeneration restored all 39 cases. Together **41 passed in
  19.21s** before performance refactoring.
- Initial joined execution/completion, mismatched/pending thermal selection and
  late result authority rollback passed **3 in 705.85s**.
- Existing runtime and selected V1 economic admission/read/worker regression
  cases passed **37 in 297.85s** before the completion refactor.
- The first new TLS helper failed in 107.32s because the test referenced a
  nonexistent ApiRuntime.economic_calculations attribute. The invalid assertion
  was removed; the real HTTP paths remain the integration check.
- The next actual TLS run failed in 150.34s when the first POST exceeded the
  unchanged 30s client timeout. Temporary cProfile instrumentation reproduced
  the timeout in 148.70s: admission took 40.317s under profiling, with four full
  farm selection reads, 625 market connections, 711 role-policy audits and
  71,605 connection.execute calls. This is a diagnostic sample, not an SLA.
- Returning the verified selection from completion removes its duplicate full
  read within a binding check. The richer three execution cases, adding late
  admission-event rollback and rejection of a completed legacy thermal V1 job,
  passed **3 in 584.44s**. OpenAPI/input and legacy Run discovery passed **42 in
  22.62s**. A concurrent TLS runner still timed out in 144.22s; this did not
  establish that the first refactor met the request budget.
- V2 admission was then changed to compare the verified current input binding
  while leaving complete derived-result calculation/replay to the worker and
  result reader. With no other local test runner, the actual economic HTTPS
  case passed: denied calls 0.003/0.003s, POST 13.462s, same-key retry 13.540s,
  completed result 15.878s, cash 15.843s and foreign read 0.049s. The 30s client
  timeout and all current-rights checks were retained. These two admission
  calls meet this functional check's budget; they are no production capacity
  or p95/SLA evidence.
- That combined TLS run ended **1 passed, 1 failed in 338.05s**: the subsequent
  thermal case completed its actual HTTP flow but its final test assertion used
  an undefined local jobs name after fixture extraction. It now uses farm.jobs.
  The isolated rerun passed **1 in 123.92s**: denied calls 0.004/0.005s, POST
  20.408s, retry 21.381s, completion 6.933s and foreign read 0.054s.
  The last V2 change is verified by the completed economic HTTPS case. The
  admission rollback case was separated from the large positive test for
  focused verification, retaining the same actual transaction/event assertions.
- Final late admission scope loss and late result-insertion authority loss
  passed **2 in 260.42s**. Admission leaves neither a job nor event; failed
  completion leaves no result/publication and records the existing fixed hold.
  Source remained unchanged throughout both final HTTPS and rollback runs.

The 42 OpenAPI/input/legacy discovery checks and the richer three execution
checks preceded the V2 admission-only change; the 37 earlier regressions
preceded the completion refactor. The final source was verified with both actual
HTTPS workflows and the two relevant transaction rollback cases rather than
represented as a full local suite rerun. Against the previous committed OpenAPI,
only POST /v1/economic-results and GET /v1/jobs/{job_id}/economic-result and
/economic-cash-flow change. Paths and public response components are identical.
Diff whitespace and **667 relative documentation links** passed; task counts
remain **19 accepted / 20 pending**.

Frontend, full local backend and Docker app launch were not rerun for this
backend increment. Source is held fixed while published-Run checks execute.

## Review and remaining work

Review covers closed version dispatch, current authority, immutable actual
inputs/publications, completed same-farm thermal provenance, receipt identity,
transaction rollback, exact assembly and fixed public errors. The internal
verified-selection carrier introduces no new public fields or bypass input.

The [first internal thermal viewer](../contracts/web-thermal-replay-v1.md) is
prioritized next by the user's request. Paired Assessment, whole farm/settlement
authoring, physical heat-to-purchased-energy/cost evidence, actual product CLI
and independent custody/release remain subsequent work. The existing G0/G1/
G2/G3/G4 acceptance and checklist remain unaccepted. No crop growth, harvest,
purchased energy, future margin or ranking was demonstrated.
