# Stored user-grid break-even workspace — software candidate

Date: 2026-09-29. This connects the existing [plan admission](../contracts/api-break-even-plan-v1.md),
[worker](../contracts/break-even-calculation-worker-v1.md) and
[completed result](../contracts/api-job-break-even-result-v1.md) to the
[economic screen](../contracts/web-break-even-workspace-v1.md). Whole-task
checkboxes and G0–G4 holds remain unchanged.

## Development context and boundary

The existing CLI turn context at `2026-09-29T11:31:13.535Z` reports exact model
`gpt-6-sol`, effort `xhigh`, thread `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`.
This is development context, not a product-runtime invocation receipt. No
recursive CLI or subagent was launched.

The browser chooses an owned baseline, actual sale/collection terms, one of
three existing targets, quantity or price, and a decimal minimum/maximum/step.
It explicitly selects 2–256 saved joint-shock revisions in grid order. No
prices, forecasts, rights decisions, settlement rules or trial inputs are
invented. The baseline's exact hash, decision time, period and unavailable
market-hold identity remain pinned. The browser projects only stored sale and
collection identities/times; it does not adopt or calculate their amounts.
The deterministic server retains full source, rights, conservation, settlement,
grid cardinality and fixed-assumption checks.

Sequential scenario registrations retain every acknowledged pin and exact
remaining intent/key. A plan is submitted only after all candidate pins exist.
Completed result reads bind plan, decision, calendar, target, unit, range,
market hold and user/assumed/conditional/Assessment-hold labels. Money stays
the exact server decimal string and unknown cash stays null/“미확인”. Listed
zeros, crossing intervals, no listed zero, nonmonotonicity and hold retain
their distinct meanings. There is no browser finance arithmetic or continuous
root interpolation. The result body is bounded to 524288 bytes.

## Actual timeout and receipt recovery

The initial actual TLS/PG/browser run failed **1 case in 189.82s**. Two scenario
admissions took about 20 seconds each. The plan POST crossed the existing
30-second browser request deadline and was canceled by the client. A canceled
response alone did not establish whether the server had committed an intent.
No worker/result success was claimed from that run.

The new [historical receipt route](../contracts/api-break-even-plan-receipt-v1.md)
looks up the exact tenant/stage/namespaced plan-ID job, verifies stored input
bytes/hash and full schema, request/plan identity and canonical ordered
submission digest, and returns only stored-intent metadata plus JobStatus.
Current metadata/artifact/break_even_read scopes and store bindings are checked
again even when inspection fails. This read does not reprepare sources or
grant source approval. Execution and completed-result readers retain their
current rights and full replay checks. No migration, grant, dependency,
coefficient or request deadline was changed.

After an unknown POST response the browser deliberately reads this receipt;
404, denial or broken replies preserve the unresolved original write and locks.
Navigation preserves in-memory state. A never-stored intent cannot yet be
resubmitted through this flow, and reload recovery remains pending.

## Verification

- Initial API unit checks were red before the methods existed, then passed.
  The canonical full-submission SHA-256 is checked against a Python-generated
  golden digest with a Unicode baseline ID. Strict TypeScript and **50 web unit
  cases passed**. Tests reject changed admission identity/count, result context,
  claim labels, numeric money and extra fields, preserving long signed decimal
  strings, null cash and crossing intervals.
- **14 Playwright cases passed in 18.4s**, including three new break-even cases.
  An acknowledged first scenario is retained after second-scenario response
  loss; lost plan confirmation performs receipt reads rather than another POST.
  A missing receipt keeps connection/editing locked. Missing collection records
  create no fabricated sale choice or zero cash. Keyboard actions, navigation,
  actual completion labels and table scrolling were checked.
- A failed/mismatched completed-result refresh now clears old amounts and its
  stale “querying” banner. On these final web sources, strict TypeScript,
  **50 unit cases**, **14 browser cases in 24.1s** and the Vite production
  build passed. The browser check also rejects a different plan result after
  a valid completion without retaining the old table or completion heading.
- The actual receipt HTTP/PG test initially needed the repository test-path
  bootstrap before it could collect. After that correction, **1 passed in
  74.82s** with exact Unicode query identity, historical metadata-only scopes,
  no source reprepare, 409 digest conflict, tenant isolation, authentication,
  bad query and revocation during failed inspection. The OpenAPI 409 response
  was subsequently added and its assertion passed in the renewed combined run
  (**1 passed, 1 failed in 204.84s**). That run's actual browser reached a
  historical receipt 200 about 39 seconds after the plan POST began, following
  three 404 receipt reads. It failed when the test tried to obtain the response
  body through DevTools after the page's bounded transport had consumed it.
  The harness was changed to read the actual displayed job ID and exact
  outgoing plan ID rather than retrieving that consumed body. The worker/result
  path still required verification; a receipt 200 alone was not completion evidence.
- The next actual browser run recovered the stored job through its displayed
  identity, but its Python harness tried to verify raw input using the public
  `get_job` projection, which intentionally has no `input_bytes`. It failed
  **1 case in 126.64s** before worker execution. The harness now queries the
  actual tenant/job row and applies the existing immutable input-byte/hash
  verifier, preserving that verification rather than skipping it.
- With the harness corrected, the real worker succeeded and the stored result
  replayed, but the actual completed-result HTTP read crossed the 30-second
  browser deadline. That run failed **1 case in 306.27s**; no browser result
  success was claimed. The repeated effective privilege audit was measured
  and [batched](runtime-role-audit-batching-implementation.md), retaining all
  predicates. Its focused security/budget suites passed **76 in 72.18s**;
  statements fell from 270 to 94 and the three-audit median from 66.718ms to
  31.874ms. No source/replay check or deadline was relaxed. Actual normal and
  lost-reply browser integration was rerun on those sources.
- The combined run then had **2 passed, 1 failed in 398.36s**. Normal actual
  TLS/PG/browser admission, worker, full stored-input/result replay, matching
  amounts, receipt reads and one stored job passed. Its plan POST took 23.102s,
  completed-result GET 19.063s and receipt reads about 61ms. The renewed actual
  receipt HTTP/PG/OpenAPI case also passed. The lost-reply case recovered the
  actual stored job and displayed the verified result (GET 18.678s), then failed
  only because the harness classified its deliberately aborted POST's console
  network error as unexpected. The harness now requires exactly that one
  endpoint-specific `net::ERR_FAILED` message and continues to reject every
  other page/console error. Only that failed parameter was selected for retry; no
  product source, check or deadline changed for this harness correction.
- The final lost-reply parameter passed **1 in 171.20s, 1 deselected**. The
  harness forwarded the exact real plan POST, required its actual 202, then
  deliberately dropped the browser reply. Manual receipt recovery found the
  same persisted job; the real worker succeeded, stored request/trial pins
  matched the fixture, and the displayed trial values, three money fields and
  crossing interval matched the actual full replay projection. Result GET took
  17.960s; receipt reads took 55–66ms. Exactly two scenario POSTs and one plan
  POST were observed, repeated receipt returned the same job, PostgreSQL had
  one identical-input job, and a second worker call consumed nothing. Exactly
  the injected network diagnostic was observed; no other page/console error
  passed. These are three unique passing actual integration cases across the
  combined run and focused retry, not a claim that the mixed run was green.

## Change review

The receipt is historical metadata under current tenant/read permissions; it
does not bypass worker or result source validation. The frontend retains exact
ordered pins and immutable keys, sends no computed plan/amounts, and rejects
changed completion context/claim labels. The shared money formatter preserves
the existing string-only behavior in both economic sections. The new API and
workspace modules are bounded and use the existing transport, source readers,
form/table styles and authenticated runtime; no dependency or migration was
added. Review identified the synchronous replay latency and stale refresh
banner, addressed above. Never-stored-intent/reload recovery and large-grid
capacity remain explicit acceptance gaps rather than successful claims.

## Hosted browser follow-up

Exact head `ae8a4004c769fc263f00235ded0e6b7d9b0598be` passed
[Compose run 36565677643](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36565677643).
Its [Web run 36565677669](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36565677669)
passed type/unit/build/audit steps but had **12 browser passed, 2 failed in
31.0s**: the new break-even and existing monthly-cash keyboard scroll checks
observed zero horizontal movement. This is not a green hosted Web result.

On unchanged tests, `CI=true` repeated those two cases three times and reproduced
**4 passed, 2 failed in 25.5s** locally. The test now brings the actual region
into view, checks viewport intersection and actual focus, then sends the native
ArrowRight through that locator. It still requires positive horizontal movement
at the same 320/768/1440px and 16/32px text sizes. No scripted positive scroll,
timeout extension, skipped assertion, product key handler or test retry was
added. [Playwright's locator API](https://playwright.dev/docs/api/class-locator)
documents the viewport/focus/key actions; missing action readiness is an
inference consistent with the reproduction, not an independently proved browser
engine cause. The focused `CI=true` repeat passed **6 in 16.9s** after the change.
Full local `CI=true` browser verification passed **14 in 18.8s**. Hosted
verification of the follow-up is reported for its own exact head separately.

## Design verification

The existing approved economics D direction and its original LayerDoc were
retained. `12ui improve` completed using conversion
`c78c3be8-0563-43aa-9412-9837c541b34d` and the original target; DOM match was
29.1%, below the tool's 60% close threshold. This is not a pixel-fidelity claim.
The original D image SHA-256 is
`faf808bc9a97251530509bb10078e84c08b9912bbe8d5da654101a32ccd80113`;
the unchanged original LayerDoc SHA-256 is
`d7fe438a1ee53aaa0ec2894e54382c300bd8d0fb3f60305eed07d16f0df184e7`.
No paid assets or fabricated farm charts were added. Unsupported decorative
icons/dials and incorrect title/status semantic mappings remain excluded;
the established palette, border, radius, font and readable type sizes remain.

Independent section captures at 320/768/1440px and 16/32px root font sizes
checked the new lower section, beyond the close tool's upper viewport capture.
Desktop and 320px/200% section images were inspected after fixing the stale
admission banner on completed results. No document-width overflow was observed;
wide financial tables retain native, keyboard-accessible scrolling.

## Remaining acceptance

General farm/baseline/event/settlement
authoring, automatic trial assumptions/response rules, continuous-interval
proof, durable reload/never-stored-intent recovery, actual runtime CLI and
independent release/domain/operating evidence, 3D/replay and whole G1 remain.
The actual latency observations concern two trials on local synthetic data;
they do not validate 256-trial or operating capacity. Large-grid asynchronous
read validation remains a required `economic-break-even`/`api-flow` follow-up.
All fixtures here are self-authored synthetic software inputs. They do not
prove crop growth, harvest, energy purchases, future margin or crop ranking.
