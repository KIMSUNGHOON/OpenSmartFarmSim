# Source to farm browser client implementation

Date: 2026-10-01 (Asia/Seoul). A transport increment toward the
[complete web connection contract](../contracts/web-source-farm-authoring-v1.md).
The ongoing development CLI is the exact `gpt-6.1-sol` / `xhigh` session recorded
in [migration evidence](cli-model-migration-implementation.md). No nested product
CLI, new data research or coefficient adoption was performed.

## Changes and review

The existing `createApi` now assembles a small source/farm read client. It reads
the exact completed research/collection references, pages their economic
metadata and re-reads the chosen candidate. Closed responses require the
software-only/hold/G0/G1 markers and the distinct list/current verification
markers. Source comparisons include every parent, attempt, raw-input hash,
point, UTC period, signed context/hash and decision field. Current candidate
comparisons include the exact economic pin, existing hold, dates and recording
time. No data or approval is issued by the browser.

The list checks duplicate IDs and descending timestamp/digest order, including
the boundary after a cursor. Its cursor is the exact last record of a full
20-item page. UTC microseconds are compared and sent as strings; JavaScript's
millisecond Date representation never rounds a cursor. The shared transport
keeps its existing full-body 30-second deadline, size limit, Bearer policy and
no-store behavior.

`farmReferenceFields` yields only source/economic references and evaluation
dates. It supplies no farm name/version, agricultural value, money, input
provenance or rights agreement. The existing request builder now accepts and
preserves UTC precision up to six fractional digits, matching the server's
source/decision contract. Previously it accepted whole seconds only, which
would reject a legitimate server decision time. It still rejects malformed
dates, non-UTC values and excess precision; numeric Decimal strings are unchanged.

## Verification

Node **22.22.3**, npm **11.16.0**, the existing locked web dependencies and
`nice -n 10`, one local heavy check at a time:

```text
npm run test -- src/source-farm-api.test.ts src/farm-authoring-input.test.ts \
  src/api.test.ts src/authored-farm-api.test.ts src/authored-financial-api.test.ts
```

Final result: **95 passed**, five files, **377 ms**. The new source client has
31 cases and the builder has one new precision case. These exercise exact
source/pin mapping, unsafe parent IDs, unsupported ex-ante authoring, unknown
private fields, false approval markers, changed context/one-microsecond decision
time, duplicates/order/cursor, invalid dates and rights/backend errors. A
microsecond boundary whose Date.parse values are equal still paginates in the
correct order. Empty metadata stays empty and malformed cursors make no request.
The builder preserves server/user microseconds in the actual request object.
The earlier 95-case run is a rerun, not extra distinct tests.

Type checking and `npm run build` passed. Vite's existing >500 kB replay/chart
chunk advisory remains; no limit was raised or check disabled. Changed links
and whitespace are checked before commit. Build output is not committed.

## Design work and remaining acceptance

The owned 12ui branch at `/tmp/ossf-source-farm-design-20261001` uses the existing
public synthetic authored-workflow capture, three requested states, HTML export,
prototype generation and page concurrency one. Its actual generated source,
economic and authoring PNGs were visually inspected. Invented crop names,
personal/farm details, climate values and verification-complete labels are
rejected as product content. Generated page geometry is a proposal for the
existing interface; it is not reviewed source/economic data or approval.
At this transport checkpoint page exports/prototype generation are still
running; the command is allowed to finish and will not be bought again.

No new selection UI or browser/HTTPS path is accepted by this transport test.
Integration, combination changes, uncertain admission, account/reconnection
fences, rendered design close and actual HTTPS/SCRAM new-farm→Run→economic/
assessment→same-3D acceptance remain required before checking the web task.
Existing [backend candidate API acceptance](api-farm-economic-candidate-selection-implementation.md)
is separate evidence. All model children/signatures in those software tests are
fixtures. Actual product CLI, independent release/full G1 and the other source,
field, forecast, comparison and deployment gates remain held.

Following checkpoint: the branch/export/prototype later completed and the
[composer selection increment](source-farm-web-implementation.md) records its
actual terminal design status and UI/recovery checks. This does not retroactively
turn the transport checkpoint into browser or full-chain acceptance.
