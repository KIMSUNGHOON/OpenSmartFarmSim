# Job break-even result lookup evidence

Status: software candidate for verified completed-job lookup, not G1/G4 proof.
The active root Codex CLI turn_context at 2026-09-28T22:15:17.349Z records
gpt-6-sol / xhigh in thread 01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc. No recursive
CLI, additional model invocation or subagent is used. Reviewable output is
[the lookup service](../backend/app/api_job_break_even_result.py),
[HTTP contract](../contracts/api-job-break-even-result-v1.md),
[versioned OpenAPI](../contracts/openapi-v1.json) and
[actual-store tests](../backend/tests/test_api_job_break_even_result.py).

The new GET resolves an actual completed simulation through its canonical job
input and publication/receipt before reading the actual break-even store.
Complete plan and request bytes must equal the admitted input. The existing
store replays every full trial; its result hash/status must equal the receipt.
Known receipt/input bindings and publication bounds are checked before expensive
replay. Current read scopes, authority identities and store pointers are checked
after reading/replay, including failed replay. The response reuses BreakEvenRead;
no arithmetic, coefficients, tariffs, crop values or forecast claims change.
The source-backed ApiRuntime assembles the service; read-only/schema assembly
keeps fixed 503. Execution/write scopes are unnecessary for this GET.

Historical code/environment digests are required to be well-formed receipt
metadata and are not promoted to independent release evidence. The new module
joins the selected implementation digest; fresh release proof remains required.
No credentials, raw source/input/receipt records or CLI decisions enter output.
The OpenAPI snapshot now documents 19 operations and the seven read scopes.

RED was the missing lookup module: **1 collection error in 0.56 s**. The actual
admission/worker/completion/read-only projection case passed **1 in 229.39 s
(3:49)**, 4 cases deselected. Queued/unknown/malformed IDs, the unchanged direct
projection, other tenant and unauthenticated access were checked in that case.
OpenAPI, existing break-even HTTP and job-status regressions passed **45 in
14.62 s**. Remaining HTTP checks and existing ApiRuntime regressions reached
**35 passed, 1 failed, 1 deselected in 763.78 s (12:43)**. The failure was a
test-only UUID object supplied to JobStore.claim, which requires a canonical
string. Its first focused retry then rejected the fixture's caller-supplied
manifest fields (**1 failed in 78.15 s**): publish accepts only schema_version
and generates job/hash/attempt fields itself. Both fixture calls were corrected
to the existing contracts; the second focused retry passed **1 in 78.36 s
(1:18)**, 4 cases deselected. Thus **82 unique cases** passed across four terminal
runs: 5 new lookup HTTP cases, 1 new OpenAPI scope case and 76 existing protocol/runtime regressions.
Receipt/publication/plan faults, post-replay scope/rebinding and fresh Bearer/
grant-drift cases passed. Hosted CI for this functional follow-up has not run.

The prior full plan suite took 66:55; the subsequent worker adds nine actual-
source cases and this lookup adds five, with the connected lookup taking 3:49
locally. The full job limit extends from 90 to 120 minutes for the added fixture/
replay work. Full commands, distinct-UID/content checks and cleanup remain intact.

Review checked immutable complete-input/plan/request/result binding, actual
publication bounds and identity, scope/pointer checks even after failed replay,
safe existing projection, unchanged money/grid semantics, fixed errors and
source-backed optional assembly. No broader local backend or distinct-UID gate
was rerun. The parent hosted run later reached 96% and was cancelled by its
90-minute maximum, with no terminal pytest summary; it is not accepted. The
observed timeout is recorded in the parent research document. Publishing this
functional follow-up with the corrected 120-minute limit permits the combined
head to rerun the unchanged full gate; no ordinary/UID gate is waived.
All **123 local Markdown targets** in changed/new documents resolve; a separate
staged whitespace gate is required before commit.

Fixtures use actual SCRAM/typed source/candidate/hold/context/result stores and
the real numerical worker, with self-authored synthetic records/signing keys.
They prove software contracts, not data rights, local crop validity, independent
execution/release/isolation/custody or protected deployment. No broad checkbox
or G0–G4 gate decision is promoted. Automatic trial assumptions, continuous-
interval proof, full CLI orchestration, browser flow and independent domain/
operating evidence remain subsequent acceptance work.

## Parent head terminal hosted CI receipt

The functional head `d3d93043689a891e4d58f450ad82f878a13c6295` completed
[backend run 36498554109](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36498554109)
on 2026-09-29 UTC: **1869 passed, 2 existing Pydantic serializer warnings in
6726.57 s (1:52:06)**. The separate four distinct-UID service cases passed in
**18.90 s**. UID content access, DB/password cleanup and post steps succeeded.
[Compose run 36498554148](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36498554148)
also completed successfully for that exact head. The warnings come from the
existing intentional malformed-policy cases in test_g0_authority. This receipt
is recorded with the following functional collection increment and is not
evidence for that later head or any G0–G4 acceptance.
