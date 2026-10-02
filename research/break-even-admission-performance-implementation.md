# Break-even admission performance investigation

Date: 2026-10-02 (Asia/Seoul). Status: committed local performance, compatibility
and hosted regression accepted; the reference-access experiment was rejected.
The lexical field-check change passed local protected maximum admission;
its hosted regression and the protected maximum operator/result path remain pending.
Development uses the current Codex CLI `gpt-6.1-sol` / `xhigh` session.
The inputs and all database authority fixtures are synthetic software evidence.

## Actual maximum baseline

The unchanged 256-trial generator registered 1,630 source records and 256 actual
candidates in a disposable PostgreSQL 16.15 SCRAM environment. Admission returned
202 with 256 queued trials and no published result, but took
**1,324.4641323270043 seconds**, exceeding the existing **30-second** budget.
The explicit suite failed: **1 failed in 2,297.44 seconds** including cold setup.
The [calculation fence record](break-even-calculation-fence-implementation.md)
preserves the exact baseline runtime code hash and setup measurements.
The local log is `/tmp/ossf-break-even-maximum-admission-20261002.log`.

This ASGI component measurement is not actual TLS response-body EOF, calculation
or verification capacity, nor maximum-grid cancellation/retry/rights withdrawal.

## Profile and first change

The explicit profiler builds the existing actual two-trial database fixture and
profiles the entire ASGI admission response with `cProfile`. Only function/module
names, line numbers, counts and timings are printed; no SQL, input values or
credentials are exported. This diagnostic is outside default test collection.

The baseline component took **11.58184089299175 seconds**. It opened 468 audited
market connections; connection handling consumed 10.142799754 seconds. There
were 485 role audits and 8,642 cursor execute calls. The existing baseline ledger
ran four times as part of full market validation. This corrected the earlier API
contract wording that incorrectly described validation as doing no arithmetic.
The log is `/tmp/ossf-break-even-admission-profile-20261002.log`.

A regression counting actual candidate/source connections while observing
repeated actual source validator reads failed before the change:
**1 failed in 25.41 seconds**, with 152 candidate connections instead of at most
two. A bounded connection window retains both full preparations, actual private
store validators and fresh repeated queries. It checks current principal/scopes
and the exact store binding before/after each read, then repeats the full role
audit before closing successfully. It does not memoize records or permissions.

The connection/fresh-read and actual source replacement tests then gave
**2 passed in 24.61 seconds**. The same profiler measured
**1.531952777004335 seconds**, 29 role audits and 1,344 cursor execute calls.
The remaining audited hold/context connections were the next measured bottleneck.
The log is `/tmp/ossf-break-even-admission-profile-window-20261002.log`.

## Late policy rejection

After complete actual preparation, tests either remove a live application scope
or grant an otherwise forbidden SELECT to the synthetic worker role. The final
role audit detected that grant, but its `RolePolicyHold` subclass of `ValueError`
was incorrectly returned as HTTP 422. The profile/scope/role run gave
**1 failed, 2 passed in 43.87 seconds**. The connection window now translates
that server policy failure to the fixed HTTP 503 class and closes its read wrapper
even when its final live scope/binding check raises.

The actual connection/fresh-read, source replacement, late scope and late database
grant selection gave **4 passed in 50.90 seconds**, with no partial intent/result
on rejected requests. The log is
`/tmp/ossf-break-even-admission-window-policy-20261002.log`.
An initial misspelled test selector collected no tests; it supplies no acceptance
evidence and was corrected before the four-case run.

## Shared hold/context connection candidate

Strengthening the same actual connection regression to require zero extra hold
and context connections produced **1 failed in 15.10 seconds**; eight hold
connections remained. The log is
`/tmp/ossf-break-even-admission-context-connection-red-20261002.log`.

The existing hold HMAC/canonical-byte/intent/scope checks and signed decision
context checks now have private transaction read paths. The bounded reference
reader uses them only after checking exact store types and shared authority
policy, DSN, schema and principal provider. Public readers keep their interfaces.
Repeated reports, resolver calls and contexts are still fetched and verified.
Replay dependency checks reuse these same actual validators.

The same two-trial profiler measured **0.7918566929874942 seconds**,
five role audits and 960 cursor execute calls. The focused regression run is
**20 passed in 158.03 seconds**: the profiler, complete actual admission module,
hold store module and signed-context/read-authority regressions. Its log is
`/tmp/ossf-break-even-admission-shared-context-20261002.log`.
Profiling overhead, system load and this small grid limit comparison precision.
These timings do not establish the 256-trial budget.

The measured candidate runtime code SHA-256 is
`0512f764b938f203eb294bf998ecdf873f8bafb4c19ac4734ac9ba3d28e22129`;
the locked environment SHA-256 is
`e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3`.
Earlier measurements describe earlier code bytes, not this new candidate.

The follow-up actual SCRAM selection gave **14 passed in 439.78 seconds**:
late source/hold/context application-scope withdrawal and database grant changes,
atomic calculation completion, cancellation during final calculation replay,
late hold/provider/replay-byte changes, completed result reads with arithmetic
disabled, and current dependency/scope/byte/grant refusal. The log is
`/tmp/ossf-break-even-admission-worker-reader-compatibility-20261002.log`.
Two late-policy cases also belong to the earlier 20-case selection; these counts
are per selection rather than a claimed number of distinct tests.

The unchanged 256-trial fixture is being prepared again for the unprofiled first
admission against the original 30-second budget. Only if that admission is slow,
the same stored intent is repeated under a diagnostic profiler before teardown.
The diagnostic timing does not replace or average the first admission budget,
and the original assertion still fails when that first admission exceeds it.
This avoids regenerating the expensive actual dataset solely for diagnosis.
The rerun log is `/tmp/ossf-break-even-maximum-admission-candidate-20261002.log`.

While that measurement retains unchanged application code, a separate explicit
[TLS/operator harness](../backend/tests/break_even_maximum_full_smoke.py) was
prepared. It builds the same actual SCRAM source/candidate fixture, uses the
standard Bearer HTTPS assembly and separate protected Python calculation and
verification operators, reads every response to EOF with the unchanged 30-second
limit, reuses the stored plan/verification intents and checks result withholding
after the current hold scope changes. Private factory configuration resides in
an owned 0700 directory with 0600 files. Printed observations contain only
counts/statuses/timings/byte sizes, not money, credentials or input records.

The harness has explicit two-trial and 256-trial tests; neither is in default
collection. At preparation, only Python AST parsing had passed. The two-trial test checks
assembly before the expensive maximum path; it cannot establish capacity.
The maximum operator's two-hour watchdog is a local resource bound, not a
production latency acceptance criterion. Maximum cancellation/lease recovery,
source-rights withdrawal and automatic deployment remain additional required
checks. No model is invoked by these deterministic Python operators.

## Remaining acceptance

Run focused admission/hold/context and worker/replay/result compatibility checks.
Remeasure the unchanged actual 256-trial fixture against the same 30-second
budget before accepting this optimization. Protected TLS response-body EOF,
maximum calculation/verification/read capacity and maximum cancellation,
retry and current-rights withdrawal remain separate required evidence.
No performance task or parent delivery task is complete on the basis of this
candidate. No product CLI, source G0, local G2, future G3a, paired G3b or
deployment G4 evidence is supplied by these fixtures.

## Actual maximum after shared connections

The rerun finished: **1 failed in 1,138.64 seconds**, retaining all 1,630 source
records and 256 candidates. Candidate preparation finished at
1,009.183539323014 seconds. The first unprofiled admission returned 202 with
256 queued trials and no result but took **44.63732304799487 seconds**.
This is an improvement over the original 1,324.4641323270043 seconds but still
exceeds the unchanged **30-second** budget. The performance task remains open.
The measured application code is the `0512f764...` candidate recorded above.

The same stored intent was repeated without changing application code under
`cProfile`, taking **82.7095757330244 seconds**. The repetition returned exactly
the original accepted metadata and did not replace the first budget observation.
The profile recorded 42,496 reference reads, 39,424 source reads and 112,720
cursor execute calls. Source verification used 26.925797841 seconds; source
model validation 15.693614246 seconds; cursor execution 24.561315998 seconds;
reference guards 11.643772655000001 seconds; candidate reference retrieval
12.889275496000002 seconds. These overlapping cumulative times are not summed.

Current source reads issue separate fresh source and immutable-job queries.
Candidate validation also issues a query per manifest input on every read.
The next measured changes will combine related fresh queries while keeping
all typed/canonical/hash/tenant/manifest/role checks and repeated reads. No
rights or permission cache, smaller dataset or extended request timeout will
be used to satisfy the budget. Protected maximum TLS/worker/read acceptance
remains pending; the prepared two-trial harness is being checked separately.

## Two-trial protected harness result

The actual standard HTTPS/private SCRAM/separate Python calculation and
verification path gave **1 passed in 51.34 seconds** on the shared-connection
`0512f764...` application. Ten actual `http.client` response bodies were read to
EOF, with maximum **0.5008803060045466 seconds**, all `no-store` and below the
unchanged 30-second limit. Calculation took 19.300672190991463 seconds and
verification 15.789010770997265 seconds. Both commands returned succeeded for
the actual stored parent/child. Repeated plan/verification requests reused their
existing identities; unauthenticated reads returned 401. Changing the actual
server hold-scope resolver after completion caused 503 with no trial values.
The owned HTTPS thread/socket closed and temporary database cleanup completed.
This is not a browser SDK measurement or a 256-trial acceptance claim.
The log is `/tmp/ossf-break-even-full-harness-two-trial-20261002.log`.

## Candidate manifest query batching

An actual SCRAM regression read the same full candidate twice. Before batching,
it observed **22 input queries rather than two** and gave **1 failed in
12.87 seconds**. The candidate still checks every manifest item's type, unique
identity, ordering, canonical/hash/tenant binding and actual stored input. It
now fetches all bounded manifest inputs in one fresh query per candidate read;
both repeated reads perform the query and all input validators.

The query regression, entire candidate-store module and profiler gave
**7 passed in 28.28 seconds**. Two-trial profile time was
0.7669443439808674 seconds; cursor calls fell from 960 to 880. This small timing
difference is not precise capacity evidence. The application code SHA-256 was
`6d899f486a563ca79190e2973ccfa9a00eceae0375615b08d2f074f365524968`.
Logs: `/tmp/ossf-break-even-candidate-manifest-batch-red-20261002.log` and
`/tmp/ossf-break-even-candidate-manifest-batch-green-20261002.log`.

## Source and immutable-job query join

An actual repeated source read initially used **four queries instead of two**:
**1 failed in 13.00 seconds**. The source read now left-joins the original
tenant-bound Job in the same fresh SQL statement and invokes the same typed,
canonical, version, authority, hash, allowed-stage and byte-equality checks.
A missing Job remains an invalid binding rather than an absent source. Existing
admission/catalogue paths retain their original interfaces. No input/rights row
is memoized.

The repeated query regression, entire source-store module, admission connection
regression and profiler gave **25 passed in 124.68 seconds**, including all
seven source families, original-job corruption, wrong grants/login, tenant,
decision-time/rights and immutable-source replay checks. Cursor calls fell from
880 to 572; two-trial profiled admission was 0.7501225399901159 seconds.
The application SHA-256 was
`1a8be2a0151e00d4af5506127696d903f59b7fe6a73d051a127a782274ed694d`.
Logs: `/tmp/ossf-break-even-source-job-join-red-20261002.log` and
`/tmp/ossf-break-even-source-job-join-green-20261002.log`.

## Fresh principal grouping candidate

The actual maximum profile also measured repeated current-access parsing.
An access regression performed a permitted check, withdrew the actual live
source-read scope and checked again. The old implementation parsed principals
15 times for the two checks instead of once each: **1 failed in 13.89 seconds**.
Admission now uses the existing validated `JobStore._principal_scopes` exactly
once per access check and tests every required scope against that current value.
Each subsequent access check still invokes the provider again. The read window's
before/after guards, current source/candidate/hold/context checks, pointer binding
and final complete role audit remain. No permission value persists across checks.

The complete admission/profiler regression gave **17 passed in 218.60 seconds**,
including all required-scope denials, live source/hold/context scope loss,
actual database grant drift, source replacement, immutable intent/retry/rollback
and both fresh-query bounds. Two-trial profiled admission was
**0.6509293309936766 seconds**; this is not a maximum-grid budget result.
Current code SHA-256 is
`c2427f3c532d610a5d8bd122cf45c03065aeff63beb8da47074c4c7b9d09f2fb`;
locked environment bytes remain unchanged. Logs:
`/tmp/ossf-break-even-principal-group-red-20261002.log` and
`/tmp/ossf-break-even-principal-group-green-20261002.log`.
The same actual 256-trial/30-second measurement is still required before
performance acceptance, followed by the full protected maximum path.

That maximum benchmark has now been started against the unchanged actual
generator and `c2427f3c...` code, alone at `nice -n 10`. Its log is
`/tmp/ossf-break-even-maximum-admission-batched-20261002.log`; source registration
has finished at 1,630 records and candidate preparation remains live. No admission
timing or acceptance is claimed while that process runs. Application code remains
fixed for the complete measurement.

## Batched maximum result: still outside budget

The `c2427f3c...` run terminated with **1 failed in 1,086.44 seconds**.
The unchanged generator registered 1,630 source records in 90.01505685900338
seconds and finished 256 candidates at 986.5714978750038 seconds. The first
unprofiled admission returned 202 with 256 queued trials and no result in
**32.06383955999627 seconds**, still exceeding the unchanged 30-second budget.
The diagnostic retry reused the stored intent and took 65.69904239597963 seconds
under profiling; that slower diagnostic does not replace the failed first timing.
It measured 42,496 reference reads, 39,424 source reads and 63,056 cursor
executions. Source reads consumed 30.268097084 profiled cumulative seconds,
including 12.909591841 seconds selecting joined source/job rows. Cumulative
function times overlap. Numeric input fallback still performs a candidate query
followed by a source/job query when the candidate row is absent. A single fresh
lookup retaining candidate precedence and both existing validators is the next
measured experiment. Performance acceptance remains open.

## Numeric candidate/source lookup experiment

An actual SCRAM regression read one source-owned and one candidate-owned numeric
input twice each. The original path executed **six queries instead of four**:
**1 failed in 12.74 seconds**. A bounded CTE/union query now returns the candidate
when present, or the source with its tenant-bound original Job otherwise. It
still invokes the existing complete candidate input validator or source/job
validator on every read. Both current scope checks remain; no rights, permission
or input row is cached. The focused query regression gave **1 passed in
12.68 seconds**. That result verifies query count and identical input values,
not the maximum HTTP budget.

The broader regression was interrupted after detecting a newly added collision
fixture that attempted to add an integer to a decimal string. The fixture now
uses `Decimal` and serializes back to the required string; no production
arithmetic was changed. The interrupted selection is not acceptance evidence.
Its log is `/tmp/ossf-break-even-numeric-union-green-20261002.log`. The corrected
selection includes candidate precedence under an actual cross-store identity
collision and refusal after privileged synthetic corruption of original Job
bytes. It is running with both full store suites and the explicit profiler in
`/tmp/ossf-break-even-numeric-union-green-fixed-20261002.log`.

The corrected admission, candidate-store, source-store and profiler selection
finished with **47 passed in 327.21 seconds**. It includes repeated fresh numeric
reads, actual cross-store candidate precedence, changed original Job refusal,
all required-scope and late-policy checks, source replacement and immutable
intent replay. Two-trial profiled admission was 0.6428671370085794 seconds and
cursor calls fell from 572 to **436**. The component timing remains small-grid
diagnostic evidence. The application code SHA-256 is
`258559bc294e063d0258508d072b50aa4c4a57aa5704ba6ca89f5351454d4bf8`;
the environment remains
`e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3`.
The unchanged actual maximum benchmark is the next required measurement.

That maximum benchmark has started alone at `nice -n 10`, with application bytes
fixed at `258559bc...` for the whole run. Its log is
`/tmp/ossf-break-even-maximum-admission-numeric-union-20261002.log`. The generator,
256-trial range, actual source registration and 30-second first-admission budget
are unchanged. No result is claimed before process completion; worker/current
reader compatibility and the protected two-trial harness still need repetition
on this code before performance acceptance.

## Numeric lookup maximum result

The unchanged maximum benchmark terminated successfully: **1 passed in
1,034.14 seconds**. It generated 256 trials in 36.87510031199781 seconds,
registered 1,630 actual source records by 88.7293104880082 seconds and finished
all 256 candidates by 1,002.6284610140137 seconds. The first unprofiled admission
returned **202**, with **256 queued trials** and no published result, in
**29.510263765987474 seconds**, below the unchanged **30-second** budget.
No slow-retry profiler was invoked. The source/generator/parameter range and
`258559bc...` runtime bytes were held fixed for the complete measurement.
The log is `/tmp/ossf-break-even-maximum-admission-numeric-union-20261002.log`.

This is one ASGI component measurement with only 0.489736234012526 seconds of
budget remaining. It is not an actual TLS response-body EOF or production
latency claim. The separate same-code worker/current-reader compatibility and
two-trial protected TLS selection is now running alone, in
`/tmp/ossf-break-even-numeric-union-worker-reader-tls-20261002.log`. The 256-trial
protected full path remains unexecuted, and the performance checkbox is still
open until the required compatibility result exists.

## Change review

Review of the six runtime module diffs found no formula, tariff, unit, schema,
grant, dependency-lock or public response change. Candidate manifest batching
is bounded by the existing 1,000-item manifest limit and retains duplicate,
ordering, tenant, canonical-input and hash checks. Source joins include both
tenant and Job identity and still reject a missing or changed original Job.
The numeric union retains candidate precedence and calls the same full input
validator for its selected branch. SQL identifiers use Psycopg composition and
values remain parameters. Each preparation still rechecks live store pointers
and current scopes before/after reads and repeats the complete role audit.
The public hold/context methods keep their interfaces; the private transaction
helpers share only the already audited, identically bound authority connection.
No rights/data/permission cache or new generated agricultural judgment is added.

The measured component meets its local budget, while maximum TLS, worker,
cancellation/recovery, automatic operations and actual product CLI/independent
gate requirements remain separate. The terminal hosted `6a264c6` results cover
the previous code, not this uncommitted performance revision. A new hosted
regression is required after the accepted increment is committed.

## Same-code compatibility and local performance acceptance

The same `258559bc...` application finished **11 passed in 432.37 seconds**:
atomic calculation/result publication, cancellation during final replay without
waiting for the calculation lock, three late hold/provider/replay-byte refusals,
completed result reading with arithmetic and write scopes disabled, four current
dependency/scope/bytes/grant refusals, and the protected two-trial TLS harness.
The log is `/tmp/ossf-break-even-numeric-union-worker-reader-tls-20261002.log`.

The actual standard HTTPS/private SCRAM/separate Python operators produced ten
whole response bodies with maximum **0.4550876459979918 seconds**; all were
`no-store` and below the unchanged 30-second/524,288-byte bounds. Calculation
took 18.194587577017955 seconds and verification 15.008589012984885 seconds.
Pending verification withheld results with 404; completed verification returned
the same two trials with user-assumption scope and assessment hold. Plan and
verification retries reused their stored identities, unauthenticated reads
returned 401, and changing the actual hold scope returned 503 without trial
values. The owned server thread/socket and disposable database were cleaned up.

Together, the focused 47-case selection, unchanged 256-trial admission budget
pass and same-code 11-case compatibility selection satisfy the local
`break-even-admission-performance` acceptance. The 256-trial protected full path,
maximum cancellation/lease recovery/source-rights withdrawal, automatic assembly,
hosted regression and actual product CLI/independent G1/G4 remain required.
This acceptance concerns software contracts and performance; it does not release
agricultural, future-margin or ranking claims.

## Committed increment and protected maximum follow-up

The accepted software increment is committed and pushed as
`c3ff00ef6e5150904333b5475592ceb5f1071f18` on `chore/bootstrap-c0`; the preceding
`8eef2a4` records terminal predecessor CI evidence. The actual 256-trial standard
HTTPS/separate Python calculation and verification/current-reader test has now
started alone at `nice -n 10` on the same fixed `258559bc...` runtime bytes.
Its log is `/tmp/ossf-break-even-maximum-full-c3ff00e-20261002.log`. No protected
maximum result is claimed while it runs. The ASGI maximum success above is not
substituted for the forthcoming whole-response and worker measurements.

Hosted runs for the exact commit are backend `36959130046`, authored workflows
`36959130044`, web `36959130032` and C0 `36959130048`. The initial API observation
reported backend queued, authored/web running and C0 completed successfully.
Counts, complete test inventories and cleanup for the new revision are not yet
accepted from that initial status observation. PR #1 remains a draft; no merge
or public deployment is claimed.

## Terminal web and C0 at c3ff00e

The exact-commit web run `36959130032` completed successfully: **160 unit tests
in 11 files**, **51 Chromium tests using one worker** (1.4 minutes), typecheck,
production build and dependency audit at the configured high-severity threshold
all passed. This is the
existing browser/SDK suite, not the protected 256-trial capacity measurement.
Its terminal log is `/tmp/ossf-ci-c3ff00e-web-20261002.log`.

C0 run `36959130048` also completed successfully. Both Compose models validated,
web/backend dependency images built, the pinned PostgreSQL 18.6 image became
healthy, and the sentinel survived actual database-container recreation.
The explicit containers/volumes/password-files removal step and all post-job
steps succeeded. Its log is `/tmp/ossf-ci-c3ff00e-c0-20261002.log`.
Backend and authored workflow counts/cleanup remain pending. These terminal
results do not prove whole-app deployment, actual product CLI or independent
G1/G4 acceptance.

## Protected maximum stopped at fixture certificate expiry

The first protected maximum run terminated with **1 failed in 975.72 seconds**.
It registered all 1,630 sources and completed all 256 candidates at
973.0538141840079 seconds, then the first HTTPS handshake failed with
`SSLCertVerificationError: certificate has expired`. No plan response, queued
calculation, verification or current-result measurement was reached. The log is
`/tmp/ossf-break-even-maximum-full-c3ff00e-20261002.log`.

The imported `test_api_serve.tls_files` fixture creates its certificate before
the test body with ten minutes of validity. The unchanged maximum preparation
takes over sixteen minutes, so that fixture is already expired before the first
request and would also expire during long operators if merely issued after
preparation. This is a demonstrated harness lifecycle failure, not evidence that
the protected maximum request/worker path meets or exceeds its budget.

The maximum harness now reissues only its owned synthetic certificate after
data preparation. It retains the original key, subject/issuer and all extensions,
including the loopback IP SAN, and has twelve hours of validity, matching the
existing Bearer window and covering both two-hour operator watchdogs. Private-key
permissions and default short-lived API fixtures are unchanged. Full certificate
and hostname verification remain enabled; no HTTP/body/time budget is increased.
An explicit regression advances the issuance clock beyond the original expiry
without sleeping, checks coverage of both watchdogs plus overhead, and verifies
key digest/identity/extensions/0600 preservation. The actual two-trial TLS path
is also being rerun before retrying the unchanged 256-trial path.

The first focused selection hit a collection error because the module-wide
indirect login parameter also covered the new certificate-only test. That
parameter is now attached to the two database integration tests; the certificate
regression does not allocate PostgreSQL. The collection error is not acceptance
evidence. Logs are `/tmp/ossf-break-even-full-tls-lifecycle-focused-20261002.log`
and `/tmp/ossf-break-even-full-tls-lifecycle-focused-fixed-20261002.log`.
Runtime application bytes remain `258559bc...`; only the explicit test harness
and evidence record have changed, and protected maximum acceptance remains open.

The corrected collection ran the actual two-trial protected path successfully,
with ten whole response bodies (maximum 0.4473646589904092 seconds), calculation
18.699908189009875 seconds and verification 15.042906101007247 seconds. The same
selection's certificate assertion failed because `x509.Extensions` collection
objects compare by identity. The assertion now compares their ordered extension
values. The certificate-only regression gave **1 passed in 0.73 seconds** in
`/tmp/ossf-break-even-full-tls-lifecycle-unit-green-20261002.log`; the combined
selection is being rerun to produce a terminal green result before maximum retry.

## Terminal authored workflow at c3ff00e

The exact-commit authored run `36959130044` completed successfully. All seven
actual database/password-file cleanup steps also completed successfully.
The terminal log is `/tmp/ossf-ci-c3ff00e-authored-20261002.log`.

| Selection | Passed executions | Seconds |
| --- | ---: | ---: |
| Authored API | 104 | 477.97 |
| Authored economics | 13 | 595.52 |
| Authored assessment | 15 | 899.11 |
| Assessment HTTPS | 1 | 337.26 |
| Financial selection | 3 | 466.81 |
| Authored browser | 4 | 738.49 |
| Financial browser | 1 | 484.17 |

These **141 executions** cover the stated software selections and fake-CLI
fixtures. They do not establish protected maximum throughput, actual product
CLI, independent gate release or G1/G4. The full hosted backend remains pending.

## TLS lifecycle correction verified

The combined certificate lifecycle regression and actual two-trial protected
path gave **2 passed in 49.25 seconds**. Ten complete actual HTTPS bodies took
at most **0.4259001840255223 seconds**; calculation took 18.38600547501119 seconds
and verification 15.065594307990978 seconds. The identity reuse, pending/result
withholding, unauthenticated refusal and current hold-scope withdrawal checks
also passed. The owned server/socket/database cleanup completed. The log is
`/tmp/ossf-break-even-full-tls-lifecycle-focused-green-20261002.log`.
This fixes the demonstrated fixture lifetime failure while retaining normal
TLS/hostname verification and all existing limits. It is a prerequisite result,
not protected maximum acceptance. The unchanged actual 256-trial generator and
runtime bytes will now be retried with this corrected test lifecycle.

The corrected harness is committed locally as
`6cb750d5ac408cf579cb5f448c263695ec0b7655`; it has not been pushed while the
existing runtime CI is still running. The actual maximum retry has started
alone at `nice -n 10`, using the same 256 values, actual source/candidate builder,
runtime `258559bc...` and unchanged HTTP/operator limits. Its log is
`/tmp/ossf-break-even-maximum-full-tls-lifecycle-20261002.log`. Source registration
has completed at 1,630 records; no protected maximum response/worker result is
yet claimed. Backend partitions 0 and 1 are terminal success, 2 and 3 are running,
and 4 and 5 remain queued at the latest actual status observation. Overall backend
acceptance still requires all partitions, complete inventory, UID checks and cleanup.

## Partial backend evidence at c3ff00e

The GitHub CLI refused `run view --log` while the overall matrix was still
running. The completed-job REST log endpoints succeeded, yielding actual
terminal partition logs without restarting CI. The exact-commit observations are:

| Partition | Passed | Deselected | Seconds | Other evidence |
| --- | ---: | ---: | ---: | --- |
| 0 | 299 | 2,006 | 1,124.67 | Two serializer warnings; separate Linux UID selection: 4 passed in 18.72 seconds |
| 1 | 277 | 2,028 | 1,697.46 | No skipped cases in the terminal summary |

Both report the complete **2,305-case collection** and inventory SHA-256
`50af1ff371b313e43804dbf285caf7dcbdbe3637954299a48a690c2539934894`.
Both actual database/password cleanup steps succeeded; partition 0's owned UID
runtime preparation and distinct-UID smoke steps also succeeded. Logs:
`/tmp/ossf-ci-c3ff00e-backend-p0-20261002.log` and
`/tmp/ossf-ci-c3ff00e-backend-p1-20261002.log`.
This is partial matrix evidence. Partitions 2–5 and the all-partition aggregate
must still pass with the same complete inventory before full backend acceptance.

## Corrected protected maximum: first request exceeded budget

The corrected-certificate maximum attempt terminated with **1 failed in
1,056.27 seconds**. All 256 actual candidates were prepared by
1,023.0476925209805 seconds. Certificate verification succeeded, but the first
plan response did not reach the client before the unchanged **30-second** read
timeout; `getresponse()` failed with `TimeoutError`. No whole-body success,
calculation, verification or completed-result capacity was reached. The log is
`/tmp/ossf-break-even-maximum-full-tls-lifecycle-20261002.log`.

The earlier 29.5103-second ASGI component result has insufficient evidence to
establish protected maximum acceptance. The actual standard assembly uses the
live `current_principal` provider, including current request activity and Bearer
expiry checks on each access. The previous component profile used the mutable
synthetic provider. A focused standard-assembly ASGI profiler has now been added
to measure those actual identity/guard costs before changing runtime code; it
retains the standard source/store assembly and exports only function counts and
timings. Its scope is diagnostic ASGI, not a substitute TLS measurement.
The log is `/tmp/ossf-break-even-standard-bearer-admission-profile-20261002.log`.
The protected maximum checkbox remains open and no timeout is increased.

## Standard Bearer diagnostic and grouped reference-access candidate

The standard-assembly diagnostic gave **1 passed in 13.84 seconds**. Two-trial
profiled admission took 0.6184087209985591 seconds and still executed 436 cursor
calls. `current_principal` was called **7,053 times**, with 0.022756457 profiled
cumulative seconds. Total reference-read time was 0.379268084 seconds versus
0.310044161 seconds in its value-reading child; the difference includes the
surrounding guards and overlaps other function costs. Small-grid timings do not
measure protected maximum latency, and the difference from the earlier mutable
provider profile is within variation. No individual identity-time cost is
claimed to explain the entire maximum failure.

Inspection found that each surrounding read guard recursively parses the same
bound principal for break-even, candidate and source scopes. An actual SCRAM
regression observed **eight provider reads instead of one** for a guard:
**1 failed in 12.62 seconds**. Its log is
`/tmp/ossf-break-even-reference-principal-group-red-20261002.log`.

The candidate groups only those three access checks. Every guard checks the
actual store/view/source identities, matching policy/schema/DSN and common
provider, invokes that provider afresh, validates authenticated tenant/scopes
and requires all three read scopes. Before/after guards and caller checks remain,
as do each actual private record validator, fresh SQL query, both full admission
preparations and final complete role audits. There is no permission/data/rights
cache. The same helper also checks each final replay dependency. No formula,
schema, grant, input budget or transport deadline is changed.

The complete admission and standard-provider profiler selection is running in
`/tmp/ossf-break-even-reference-principal-group-green-20261002.log`. This new
runtime candidate is not covered by the predecessor `c3ff00e` CI and is not yet
accepted. Current-access/provider/cancel/worker compatibility and unchanged
protected maximum measurements remain required.

The complete admission/standard-provider selection terminated successfully:
**21 passed in 267.19 seconds**, including the one-fresh-principal regression,
all required-scope denials, late source/hold/context scope loss, actual role
grant drift, source replacement, original Job corruption, identity precedence,
fresh query bounds and immutable intent/retry behavior. The standard-provider
profile now records **2,237 `current_principal` calls** and
0.009862096 cumulative seconds, versus 7,053/0.022756457 before grouping.
Overall profiled component time is 0.6136255339952186 seconds, too close to the
earlier small-grid result to establish protected maximum improvement.

The new runtime code SHA-256 is
`3f4619a1dbc480f5f858936fa0f5b2392f80f4a5d684ce1b220a1df5951c102c`;
the environment remains
`e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3`.
The same-code worker/current-reader/two-trial TLS compatibility selection is
running alone at `nice -n 10` in
`/tmp/ossf-break-even-reference-principal-worker-reader-tls-20261002.log`.
Runtime bytes are fixed for that selection. The candidate remains unaccepted
until compatibility and the unchanged actual protected maximum budget are met.

The same-code compatibility selection completed with **11 passed in
468.77 seconds**, including atomic result/job publication, final-replay
cancellation, late hold/provider/result refusal, arithmetic-disabled completed
reading and current dependency/scope/bytes/grant withdrawal. The two-trial
protected path's ten whole response bodies had maximum
**0.48197452002204955 seconds**; calculation took 19.88697394100018 seconds and
verification 16.508792156993877 seconds. The owned server/socket/database cleanup
completed. Small-grid compatibility does not establish protected maximum capacity.

The actual maximum is the remaining acceptance measurement for this candidate.
If its unchanged first HTTPS plan request times out again, the explicit harness
now stops its owned server and profiles the same standard assembly/intent/data
through diagnostic ASGI before teardown. Only counts/functions/timings are
exported. The original TLS timeout is still raised, no first-request or deadline
assertion is relaxed, and the diagnostic is not treated as whole-body success.
This avoids another expensive fixture preparation solely to diagnose a known
maximum failure. No runtime source bytes changed after the compatibility result.

The unchanged actual protected 256-trial measurement has restarted on fixed
`3f4619a1...` application bytes, alone at `nice -n 10`. Its log is
`/tmp/ossf-break-even-maximum-full-reference-group-20261002.log`. All 1,630 source
records are registered and candidate generation remains live. No protected
maximum response, operator completion or current-result acceptance is claimed
while that process runs. This candidate has not been committed or pushed;
the ongoing predecessor CI remains attached to `c3ff00e` rather than this code.

## Terminal hosted regression at c3ff00e

[Backend run 36959130046](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36959130046)
terminated successfully on exact head
`c3ff00ef6e5150904333b5475592ceb5f1071f18`. All six PostgreSQL 18.6
partitions and the aggregate passed:

| Partition | Passed | Deselected | Seconds | Warnings |
| --- | ---: | ---: | ---: | ---: |
| 0 | 299 | 2,006 | 1,124.67 | 2 serializer warnings |
| 1 | 277 | 2,028 | 1,697.46 | 0 |
| 2 | 374 | 1,931 | 1,479.25 | 0 |
| 3 | 570 | 1,735 | 1,629.74 | 0 |
| 4 | 306 | 1,999 | 1,538.60 | 0 |
| 5 | 479 | 1,826 | 1,932.24 | 0 |

The total is **2,305 passed, zero skipped**. All six complete collections have
SHA-256 `50af1ff371b313e43804dbf285caf7dcbdbe3637954299a48a690c2539934894`;
the aggregate explicitly accepted the identical inventory. Partition 0's
separate Linux UID selection gave **4 passed in 18.72 seconds**, and its
runtime preparation and content UID boundary check succeeded. All six actual
database/password/owned-runtime cleanup steps and all terminal job statuses
were checked. The full log is
`/tmp/ossf-ci-c3ff00e-backend-full-20261002.log`, supplemented by the earlier
partition 0/1 logs. The asserted partition summary and step metadata are
`/tmp/ossf-ci-c3ff00e-backend-summary-20261002.json` and
`/tmp/ossf-ci-c3ff00e-backend-steps-20261002.json`.

Together with the already recorded 141 authored executions, web 160/51 and C0
successes on this same head, this accepts the committed admission changes'
hosted software regression. It does not cover the uncommitted `3f4619a1...`
reference-access candidate, protected maximum capacity, actual product CLI,
independent evidence release or scientific/production gates.

## Reference-access experiment rejected at actual maximum

The `3f4619a1...` protected measurement terminated with **1 failed in
1,165.68 seconds**. All 256 candidates were prepared by 1,041.7191486230004
seconds, but the original first HTTPS request exceeded its unchanged 30-second
timeout. No successful maximum whole response or operator completion was reached.
The owned server was stopped; the same standard assembly, input and database
were then profiled diagnostically before the original timeout was raised.

That diagnostic returned 202/256 in **80.94940907298587 profiled seconds**.
It recorded 42,496 reference reads, 39,424 source validations and 45,648 cursor
executions. Overlapping cumulative times include 59.7734 seconds in reference
reads, 29.5330 in source transactional reads, 27.5250 in the existing baseline
ledger checks, 20.6333 in source validation and 13.0150 in canonical input
serialization. Canonical field validation visited 1,445,558 nodes in 11.4721
cumulative seconds. These instrumented, overlapping times identify investigation
targets; they are not TLS timings or independently additive costs.
The log is `/tmp/ossf-break-even-maximum-full-reference-group-20261002.log`.

The grouped principal helper and its helper-specific regression were removed
because the required maximum improvement was not demonstrated. The runtime hash
again equals the accepted committed
`258559bc294e063d0258508d072b50aa4c4a57aa5704ba6ca89f5351454d4bf8`,
with unchanged environment hash `e73e9ec0...`. The diagnostic standard-provider
profiler and timeout profile export remain useful test instrumentation. No
timeout, source validator, rights check, calculation or claim gate was relaxed.

A fresh standard-provider baseline on those restored bytes gave **1 passed in
15.72 seconds**, with profiled admission 0.8123810160032008 seconds and canonical
serialization 0.101054819 seconds across 314 calls. Its log is
`/tmp/ossf-break-even-standard-field-validation-baseline-20261002.log`.
The next experiment targets repeated lexical checks of credential/raw field
names, whose static rules can be matched directly without any record, rights
or principal cache. It must retain all rejected keys, the exact `raw_sha256`
exception, nested/non-JSON/size handling and identical canonical bytes, then
pass the same protected maximum before acceptance.

## Lexical field-check candidate

The candidate replaces the 17 repeated substring tests with one compiled
alternation of the exact same literal ASCII markers. Normalization, blocked
exact keys, the `raw` prefix check, exact lowercase-hex `raw_sha256` exception,
recursive traversal and canonical JSON encoding/size bounds are unchanged.
There is no field-name, input, approval, rights or principal cache.

Using the same 85 typed synthetic source documents, 400 repetitions per sample
and three samples, 34,000 canonicalizations per sample changed from
**1.8647374300053343 seconds median** (1.994416317989817,
1.8548702879925258, 1.8647374300053343) to
**1.218367074005073 seconds median** (1.218367074005073,
1.2482614690088667, 1.21093604399357), a **34.66%** reduction in this diagnostic.
Logs: `/tmp/ossf-canonical-field-baseline-20261002.log` and
`/tmp/ossf-canonical-field-regex-candidate-20261002.log`.
The repeatable diagnostic is [canonical_input_profile.py](../backend/tests/canonical_input_profile.py);
expected bytes come from an independent canonical JSON encoding of the same
documents. No field values, private records or credentials are exported.

The existing canonical/non-JSON/size and raw-digest checks plus a regression for
changed nested digest values, mixed case/punctuation, Unicode casefolding and
embedded prohibited names gave **3 passed in 0.92 seconds**. Source/job/admission
and standard-provider regression is running alone at `nice -n 10` in
`/tmp/ossf-break-even-field-regex-focused-20261002.log`.
The candidate code SHA-256 is
`6ed29db3653a7c8e82b373941fde28f3d25d759fc22444428774495e9e5f1f9a`;
the environment remains `e73e9ec0...`. The lexical diagnostic is insufficient
for protected maximum acceptance. Existing API limits and all claim gates remain.

The source/job/admission/standard-provider selection completed with **55 passed
in 351.88 seconds**. The same standard-provider diagnostic admission took
0.6417973320058081 seconds versus the restored baseline's 0.8123810160032008.
This includes generic immutable job submission, all typed source families and
integrity checks, the complete admission scope/binding/refusal/retry selection
and the new nested credential/raw field regression. The earlier focused
three-case check overlaps this collection and is not added to its count.

The same-code atomic publication/final-replay cancellation/current dependency
withdrawal/arithmetic-disabled reader/two-trial actual TLS selection, together
with the reproducible lexical diagnostic, is now running alone in
`/tmp/ossf-break-even-field-regex-worker-reader-tls-20261002.log`.
No application bytes are being changed during those checks. Both this
compatibility and the unchanged protected maximum remain required; no new
acceptance checkbox has been completed.

The same-code compatibility/diagnostic selection completed with **12 passed in
445.05 seconds**. Ten actual two-trial HTTPS bodies took at most
**0.4444843929959461 seconds**. Separate Python calculation took
18.250444870995125 seconds and verification took 15.11679546200321 seconds.
The current hold-scope change returned fixed 503 without trial amounts;
identity reuse, pending withholding, unauthenticated refusal, atomic publication,
final-replay cancellation and current dependency/scope/bytes/grant withdrawal
passed. Owned server/socket/database cleanup completed. The repeatable lexical
diagnostic also passed, with three samples 1.1875696860079188,
1.2128624269971624 and 1.163602170010563 seconds (median
1.1875696860079188); these remain synthetic diagnostic timings.

After asserting the exact `6ed29db3...` code and `e73e9ec0...` environment hashes,
the unchanged 256-trial protected full-path measurement started alone at
`nice -n 10`. Its log is
`/tmp/ossf-break-even-maximum-full-field-regex-20261002.log`. Source/candidate
preparation, first-request and whole-body limits, both operator watchdogs and
all current-result/refusal assertions are unchanged. The candidate remains
uncommitted and unaccepted until that measurement demonstrates the required
budget. The predecessor hosted CI does not cover this runtime change.

## Protected maximum admission accepted locally

The unchanged full-path measurement prepared 1,630 actual sources and 256
candidates by 992.9793196629907 seconds. On exact `6ed29db3...` application
bytes, the standard Bearer/TLS client received these complete bodies:

| Request | Status | Bytes | Body EOF seconds |
| --- | ---: | ---: | ---: |
| Initial 256-trial plan | 202 | 508 | 29.637331181002082 |
| Identical plan reuse | 202 | 508 | 29.01403817400569 |
| Queued calculation status | 200 | 237 | 0.04302241298137233 |

All have `Cache-Control: no-store`, normal certificate/hostname verification,
the unchanged 30-second timeout and complete-body bound. The initial response
has only **0.362668818997918 seconds** remaining under that limit. These single
local samples prove this admission check; they do not establish a production
latency distribution or additional capacity margin.

Together with the same-code 55-case focused selection, 12-case worker/reader/
TLS/diagnostic selection and unchanged canonical byte checks, this accepts the
lexical field matcher for local protected admission. The grouped principal
experiment remains reverted. The actual maximum process is still live in
`/tmp/ossf-break-even-maximum-full-field-regex-20261002.log`, now running its
separate Python calculation operator. Maximum calculation, verification,
current-result reading and withdrawal acceptance remain unproven until their
terminal assertions and cleanup succeed. Application bytes remain frozen.
The new runtime needs its own hosted regression; predecessor CI is not substituted.

The locally accepted lexical change is committed as `04c517c`, followed by the
operator assembly plan/discovery contract in `82ee0cd`. The authorized branch
push succeeded at exact head `82ee0cd66f7ba595e50fcf1d513dbb9b0d9b8e4f`.
The worktree was clean before push, and the live maximum application's
`6ed29db3...` hash was rechecked unchanged. That process continues its calculation
operator; committing/pushing did not edit its application bytes.

The new exact-head hosted runs are backend **36969920769**, authored
**36969920731**, web **36969920738** and C0 **36969920726**. Initial observations
were backend queued and the other three in progress. None is yet terminal
acceptance. These runs include the earlier certificate lifecycle fix; actual
maximum operators/results, actual product CLI and independent gates remain open.

## Terminal web and C0 at 82ee0cd

On exact head `82ee0cd66f7ba595e50fcf1d513dbb9b0d9b8e4f`,
[web run 36969920738](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36969920738)
completed successfully with **160 unit cases in 11 files** and **51 Chromium
cases with one worker in 1.4 minutes**. Type checking, production build,
locked install and audit at the high-severity threshold also succeeded, as did
all terminal/post steps. The log is `/tmp/ossf-ci-82ee0cd-web-20261002.log`.

[C0 run 36969920726](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36969920726)
also completed successfully: both Compose models/dependency builds, pinned
PostgreSQL 18.6 health/`pg_isready`, replacement container and persisted sentinel
passed. Its actual container/volume/password cleanup and all terminal/post
steps succeeded. The log is `/tmp/ossf-ci-82ee0cd-c0-20261002.log`.

Backend run 36969920769's overall status was `queued`, but its actual partition
0 and 1 jobs were already `in_progress`; the remaining four were queued under
the existing two-partition limit. Overall workflow text is not used to infer
that active partition processes stopped. All seven authored jobs in run
36969920731 were also in progress. Neither workflow has terminal acceptance yet.

The local maximum's owned separate calculation process was verified live with
its exact parent/factory and queried only for job metadata. Its first attempt
was `simulating`, its lease was current, and the last renewal/update was
2.289497 seconds earlier. No private configuration or raw input was exported.
This proves live execution and current lease activity, not completed calculation
or maximum-result acceptance. The same maximum session remains running.

The exact-head authored HTTPS job `110721556403` became terminal success:
**1 passed in 259.96 seconds**, with actual database/password cleanup success.
Its completed-job REST log is
`/tmp/ossf-ci-82ee0cd-authored-assessment-https-20261002.log`.
This is one of seven authored selections, not acceptance of the whole workflow.
The other authored jobs and full backend remain pending.

The local owned calculation child was subsequently still live under its original
pytest parent at `nice 10`, using about 77 MiB RSS. WSL reported zero swap usage,
about 21 GiB available memory and 678 GiB free workspace filesystem space.
These resource observations support continuing the existing single heavy local
run; they are not deployment or completed maximum evidence.

## Terminal authored regression at 82ee0cd

[Authored run 36969920731](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36969920731)
completed successfully on exact head
`82ee0cd66f7ba595e50fcf1d513dbb9b0d9b8e4f`. All seven terminal selections and
their actual database/password cleanup steps succeeded:

| Selection | Passed | Seconds |
| --- | ---: | ---: |
| API | 104 | 486.69 |
| Economics | 13 | 559.32 |
| Assessment | 15 | 677.58 |
| HTTPS assessment | 1 | 259.96 |
| Financial selection | 3 | 760.93 |
| Authored browser | 4 | 789.42 |
| Financial browser | 1 | 485.48 |

The **141 executions** were asserted from completed-job REST logs at
`/tmp/ossf-ci-82ee0cd-authored-<selection>-20261002.log`, with step metadata
`/tmp/ossf-ci-82ee0cd-authored-steps-20261002.json` and the asserted summary
`/tmp/ossf-ci-82ee0cd-authored-summary-20261002.json`. These software/fake-CLI
selections, same-head web 160/51 and C0 are accepted for their stated scopes.
The full backend matrix is still pending, and the local actual maximum process
continues its calculation. Neither authored success nor small-grid/standard
admission samples replace maximum operators/results or actual CLI/independent
G1/G4 evidence.

## Partial backend at 82ee0cd

Exact-head backend partition 0 (`110721556628`) completed successfully with
**299 passed, 2,007 deselected and two warnings in 1,051.49 seconds**.
Its complete collection is **2,306 cases**, inventory SHA-256
`b9ff73078ad2b822966ae37c53a5b8ae7e37696cee83cf5a4e51fc265f11ad45`.
The separate Linux UID selection gave **4 passed in 18.04 seconds**;
owned runtime preparation, distinct-UID content access and actual
database/password/runtime cleanup all succeeded. The completed-job log is
`/tmp/ossf-ci-82ee0cd-backend-p0-20261002.log`.

Partition 1 and the newly started partition 2 are in progress; 3–5 and the
final aggregate are still pending. The inventory and cleanup must agree across
all six terminal partitions before full backend acceptance. This first
partition/UID result does not establish maximum operator completion.

## Additional partition and maximum calculation progress (2026-10-02)

At the same exact `82ee0cd66f7ba595e50fcf1d513dbb9b0d9b8e4f` head,
backend partition 1 (`110721556545`) completed with **277 passed,
2,029 deselected in 1,684.65 seconds** and partition 2 (`110721556664`)
completed with **375 passed, 1,931 deselected in 1,070.35 seconds**.
Both reported the same 2,306-node complete inventory and SHA-256
`b9ff73078ad2b822966ae37c53a5b8ae7e37696cee83cf5a4e51fc265f11ad45`.
Their terminal job/cleanup/post-step metadata and completed-job REST logs
were inspected. Database/password-file removal succeeded. Logs are
`/tmp/ossf-ci-82ee0cd-backend-p1-20261002.log` and
`/tmp/ossf-ci-82ee0cd-backend-p2-20261002.log`; partial job metadata is
`/tmp/ossf-ci-82ee0cd-backend-live-20261002.json`. Together partitions
0–2 account for 951 passed cases, with 3–5/aggregation still pending.
UID preparation/access checks are intentionally confined to partition 0;
their skip steps in partitions 1–2 are not skipped test cases.

The actual 256-trial protected local run in session `67775` completed its
separate Python calculation operator in **2,258.1148612760007 seconds**,
below the unchanged 7,200-second resource watchdog. The normal HTTPS
calculation-complete response was **200 / 240 bytes / 0.04800109000643715
seconds** through body EOF. Verification admission was **202 / 237 bytes /
0.32838568699662574 seconds** and the pending verified-result read was
**404 / 79 bytes / 0.046192275010980666 seconds**, with the same protected
response checks and original 30-second client bound. The independent
verification Python process is running; verified current result and terminal
cleanup are not yet accepted. The log remains
`/tmp/ossf-break-even-maximum-full-field-regex-20261002.log`.

This is software-only synthetic calculation progress, not G1/real CLI,
throughput, scientific, crop ranking or deployment evidence. Main application
bytes remain frozen at `6ed29db3653a7c8e82b373941fde28f3d25d759fc22444428774495e9e5f1f9a`.
The next discovery implementation is prepared in a separate worktree so it
does not change these measured inputs. Its actual SCRAM acceptance waits for
the local heavy test to terminate.

## Terminal protected maximum path acceptance (2026-10-02)

Session `67775` terminated with exit code 0: **1 passed in 4,527.33 seconds**
(75 minutes 27 seconds). The same 256 actual trial inputs and 1,630 stored
synthetic sources completed both separate Python operators, then the actual
normal TLS/hostname/Bearer client read the entire verified result. Main runtime
code/environment hashes remain `6ed29db3653a7c8e82b373941fde28f3d25d759fc22444428774495e9e5f1f9a`
and `e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3`.
The original client timeout/body EOF threshold remains 30 seconds; the response
bound remains 524,288 bytes. All ten responses passed `Cache-Control: no-store`,
normal certificate/hostname validation and full-body checks.

| HTTPS response | Status | Body bytes | EOF seconds |
| --- | --- | --- | --- |
| Plan admission | 202 | 508 | 29.637331181002082 |
| Identical plan reuse | 202 | 508 | 29.01403817400569 |
| Queued calculation | 200 | 237 | 0.04302241298137233 |
| Completed calculation | 200 | 240 | 0.04800109000643715 |
| Verification admission | 202 | 237 | 0.32838568699662574 |
| Verification pending | 404 | 79 | 0.046192275010980666 |
| Verified result, all 256 trials | 200 | 25,382 | 3.7966569639975205 |
| Identical verification reuse | 202 | 240 | 0.3100903250160627 |
| Unauthenticated current result | 401 | 72 | 0.04494219200569205 |
| Changed current hold scope | 503 | 89 | 3.393046076002065 |

The calculation process took **2,258.1148612760007 seconds**; independent
verification took **1,207.0974715680059 seconds**. Both respected their original
7,200-second resource watchdogs. Repeated admission retained the same jobs;
the completed result had the same plan and calculation parent, all 256 trials,
`conditional_user_grid_only`, user inputs and assessment hold. The changed
current hold scope exposed no trials. The normal server/socket shutdown and
disposable DB/role/password-file teardown completed before pytest's terminal
success; no owned calculation or verification process remained. Evidence:
`/tmp/ossf-break-even-maximum-full-field-regex-20261002.log` and the explicit
[harness](../backend/tests/break_even_maximum_full_smoke.py).

This satisfies the local `break-even-maximum-protected-path` task's stated
software boundary. The first admission has only **0.362668818997918 seconds**
of margin in one local sample; neither p95, concurrent capacity nor production
headroom is established. Separate maximum cancellation/lease recovery/source
withdrawal, automatic consumer/application deployment, hosted backend completion,
actual product CLI/independent G1 and scientific/deployment gates remain open.
The released local heavy slot is now used for discovery's actual SCRAM checks.

## Discovery acceptance and fourth backend partition (2026-10-02)

The isolated discovery implementation completed **47 focused cases in 22.11
seconds**, including actual SCRAM queue/corruption/current grant checks and
competing existing economic workers with atomic publication and expired
cancel/exhaustion recovery. Its three files and evidence were reviewed and
cherry-picked into the working branch as `d2e8536` and `afc7acb` only after the
maximum test terminated. Details and the separate discovery implementation/test
hashes are in [its contract](../contracts/deterministic-job-discovery-v1.md#actual-scram-software-acceptance-2026-10-02).
Automatic foreground consumption and application Compose remain separate tasks.

At the prior published `82ee0cd` head, backend partition 3 (`110721556444`)
also completed: **570 passed, 1,736 deselected in 1,623.06 seconds**.
It reported the same 2,306-node collection/inventory digest and successful
database/password cleanup and terminal steps. The actual log is
`/tmp/ossf-ci-82ee0cd-backend-p3-20261002.log`. Partitions 0–3 account for
1,521 passed cases; 4–5 and aggregation remain in progress. These prior-head
CI results do not cover discovery's newly added files. The next push waits
for this existing run's terminal evidence so it does not cancel its remaining
regression work.

## Terminal hosted regression at 82ee0cd (2026-10-02)

Backend run [36969920769](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36969920769)
completed successfully at the exact published
`82ee0cd66f7ba595e50fcf1d513dbb9b0d9b8e4f` head. All six partitions and the
final aggregation succeeded. Their actual log counts sum to **2,306 passed,
zero skipped**, with the same complete 2,306-node inventory SHA-256
`b9ff73078ad2b822966ae37c53a5b8ae7e37696cee83cf5a4e51fc265f11ad45`.

| Partition | Passed | Seconds |
| --- | --- | --- |
| 0 | 299 | 1,051.49 |
| 1 | 277 | 1,684.65 |
| 2 | 375 | 1,070.35 |
| 3 | 570 | 1,623.06 |
| 4 | 306 | 1,311.62 |
| 5 | 479 | 1,714.15 |

The separate Linux UID cases passed **4 / 18.04 seconds**. Each partition's
database/password removal succeeded; partition 0's owned UID preparation and
content access succeeded, and the terminal jobs/post steps and aggregation
were inspected. The asserted summary is
`/tmp/ossf-ci-82ee0cd-backend-summary-20261002.json`, metadata is
`/tmp/ossf-ci-82ee0cd-backend-terminal-20261002.json`. `gh run view --log`
omitted partition 0 from `/tmp/ossf-ci-82ee0cd-backend-full-20261002.log`;
the actual completed-job REST log already retrieved at
`/tmp/ossf-ci-82ee0cd-backend-p0-20261002.log` supplied that partition and UID
proof. The assertions required all six logs, rather than treating the partial
aggregate download as complete evidence.

Together with the previously recorded terminal authored 141, web 160/51 and
C0 at this same head, this accepts the static lexical input-field optimization
for its software scope. The protected local 256-trial path is also terminal.
This CI head predates discovery and the automatic consumer additions, which
require their own later hosted regression. Real product CLI, independent
releases/G1, separate maximum faults/withdrawal and scientific/G4 gates remain open.

## Automatic foreground consumer accepted locally (2026-10-02)

Commit `3ff02b4` adds one explicitly configured existing deterministic worker
per foreground process. It discovers owned economic/break-even calculation or
verification jobs, follows bounded unrelated-version pages, dispatches
sequentially and waits after each page. Existing workers retain exact-ID claims,
current source/access checks, cancellation/recovery and atomic publication.
The module loads the canonical factory type, uses signal wakeup descriptors
without acquiring Event locks, restores prior signal/wakeup state and closes
its owned descriptors. Public process output contains closed attempt metadata.

The full focused file gave **37 passed in 130.07 seconds**. Actual separate
Python/SCRAM processes completed economic work and the two-trial break-even
calculation/verification/current read without UUID arguments; they also proved
graceful SIGTERM, cancel without publication and kill/restart/expired-lease
recovery with a single result and intact attempt history. The local idle sample
gave CPU **0.03 seconds over 2.2 seconds**, three page reads at minimum
**1.039364358 seconds** spacing, and SIGTERM exit **0.113946827 seconds**.
Source details, failing evidence/fixes, immutable file/environment hashes and
limits are in [the consumer contract](../contracts/deterministic-worker-loop-v1.md#software-acceptance-2026-10-02);
the actual terminal log is `/tmp/ossf-deterministic-worker-loop-scram-v5-20261002.log`.

The discovery cases also passed in the earlier combined selection; that
selection had a consumer test argument failure and is not reported as fully
green. Final consumer acceptance comes from its full 37-case v5 result.
The new added files require hosted regression at the next pushed head.
Protected operator files/application Compose, actual CLI and independent
releases/G1, scientific gates and G4 remain subsequent tasks.
