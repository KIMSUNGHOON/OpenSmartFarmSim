# Farm registration uncertainty and connection lock

Date: 2026-10-01 (Asia/Seoul). Follow-up under the
[source/farm web contract](../contracts/web-source-farm-authoring-v1.md).
The current development CLI session's selected `turn_context` at
`2026-10-01T09:01:59.035Z` records `gpt-6.1-sol` / `xhigh`.
Only timestamp/model/effort metadata was read; private prompts and credentials
were not exported. No recursive product CLI was launched.

## Reproduction and fix

The composer already pinned an uncertain registration, but its pending state
stopped at the farm workspace. The root connection could still change and
discard that page-memory intent. The existing saved-source retry case was
extended first: Chromium failed because **connection setup remained enabled**
after the registration response was lost. This was a reproduced behavior,
not an inferred server failure.

The workspace now forwards composer pending state to the existing shell lock
pattern. Connection setup/disconnect, reset and other workspaces' new requests
or parent selection are blocked during registration or unresolved admission.
Source collection/review handlers and buttons also honor their existing
`blocked` prop. Navigation remains available; other screens show a short status
directing the user to 04 for the identical retry. No pending farm body or token
is added to browser storage.

A malformed positive registration response now retains the exact preview and
uncertainty lock. A recognized HTTP refusal clears uncertainty and preview so
the owner can correct/review input and reconnect. The registration validator,
current server authorization and immutable farm input bytes remain authoritative.

Review covered effect cleanup, the stable pending setter, the always-mounted
workspace across navigation, retry availability, client error classification
and source handler guards. The change follows the existing shell pattern and
adds no dependency, stylesheet, API endpoint or numeric default. The existing
notice component explains disabled controls. This is a behavior repair in the
established design; the earlier [layout target closes](source-farm-layout-refinement-implementation.md)
remain a separate visual record with their stated precision limits.

## Focused evidence

One Chromium worker and one local browser process at a time, `nice -n 10`:

- Source/farm, direct form, farm workflow, initial/source shell, authored finance
  and assessment: **33 passed in 42.1 s**. This includes the new malformed-positive
  then recognized-refusal case and the extended lost-response registration case.
- After aligning the root status button's disabled attribute with its handler,
  the affected saved-source case passed **1 test in 3.4 s**. A capture-only
  adjustment then passed the same case in **3.3 s**; these are reruns, not extra
  distinct cases.
- The lost-response case restores completed research/collection in 02, pins
  exact saved source/economic references in 04, submits explicit fixture farm
  values, then navigates to 01/02 while unresolved. Connection/reset/research,
  source status/history and reference-changing controls are disabled. Returning
  to 04 retries identical request bytes; a valid acknowledgement unlocks the shell.
- The new case receives an invalid HTTP 200 body, retains input and connection
  locks, retries identical bytes and receives the recognized HTTP 422 refusal.
  Inputs unlock and the submission preview clears. An initial HTTP 400 test
  fixture correctly stayed unresolved under the transport's unknown-status
  policy; that failed attempt is not acceptance evidence.
- Final build, including typecheck: passed, 637 transformed modules, **434 ms**.
  Existing chart/scene chunk size advisories remain.
- The [actual pending screen](artifacts/source-farm-registration-lock-desktop.png)
  was visually inspected. It contains public fixtures and an asserted empty
  password input; disabled connection controls and the recovery status are visible.

The owned Vite/browser children stopped after each test. Generated changes in
five older workflow/financial/assessment captures were restored. Local baseline
PostgreSQL and unrelated user services are preserved.

Hosted checks for this new behavior are pending. The successful full backend
and authored financial continuation at `5dc63f3` predate this UI change.
A hard reload still discards an unacknowledged page-memory intent and must use
the existing server history; this repair does not claim durable unknown-intent
recovery. Product CLI, independent G1 and real-source/field/future/deployment
gates remain held.
