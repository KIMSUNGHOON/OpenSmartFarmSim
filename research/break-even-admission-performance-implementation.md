# Break-even admission performance investigation

Date: 2026-10-02 (Asia/Seoul). Status: local performance and compatibility accepted;
hosted regression and the protected maximum path remain pending.
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
