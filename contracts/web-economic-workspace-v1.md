# Internal economic workspace v1

Status: software candidate for stored user-assumption intake and conditional
calculation. This is a continuation of the [web shell](web-location-shell-v1.md),
not whole web-shell, API-flow, G1, forecast, ranking, or production acceptance.

The Korean third screen uses the same memory-only Bearer client and relative
same-origin HTTPS API. It manually lists and reads exact owner-scoped numeric
inputs, baseline ledgers, and joint supply/demand/macro assumptions through the
[stored-source reads](api-market-user-source-read-v1.md). No record is selected
automatically. Pages preserve the server cursor; empty, unavailable, denied, and
invalid responses expose no invented data. The browser's root field sets derive
from the four existing server models and have a backend drift check.

A numeric edit retains the selected input's unit, scope, origin and evidence
labels. Its decimal is a string, with explicit UTC knowledge date/time. A new
revision, source reference and idempotency key are pinned before the first
[source intake](api-market-user-source-v1.md). UTC is serialized in the canonical
whole-second form required by intake. `200` means a new assumption was registered,
not reviewed, applied to a ledger, or calculated. The original version is never
mutated. The user can then explicitly apply the saved number through a new joint-shock
revision as described below. General baseline/farm/settlement authoring remains
required. It supplies no crop outputs, coefficients, tariffs, or missing costs.

## Applying a saved numeric revision

After selecting a baseline and joint shock, the user requests the actual saved
numeric record and complete canonical joint shock. Their source hashes must
match the selected receipts. The screen offers only existing numeric edit slots
with the same input ID/unit and a different revision; there is no selected
slot or ownership declaration by default. It previews the existing and new
string values, driver hypothesis, knowledge time and applicability period.

The user declares ownership and permission to use/display the assumption;
redistribution is denied. The browser hashes the EconomicNumber's nine canonical
fields, excluding tenant and owned scope fields, to bind a new `input_rights`
record. This is identity bookkeeping, not farm arithmetic or G0 approval.
Knowledge time must be no later than the pinned decision, with microsecond
precision; applicability must cover the baseline period. The existing joint
and edited driver must also satisfy these bounds. The joint must retain all
three nonempty demand/supply/macro drivers.

The browser clones the selected complete joint, changes only the explicitly
selected numeric edit, gives the joint and edited driver new revisions, denies
redistribution on both, and preserves their later knowledge times. Other edits,
input references, hypotheses, caps and settlement bindings are retained. The
baseline is unchanged. The deterministic scenario server still validates all
rights, inventory, decision/scope and settlement applicability. If an edit
invalidates a settlement path, existing evidence is insufficient: the screen
does not manufacture replacement evidence or approve that scenario.

Two intake bodies/keys are pinned once: rights `200`, then joint `200`. An
acknowledged phase is not posted again after the following reply is lost.
After both acknowledgements, the exact new joint is read and selected; a
failed read retries only that read. Unknown writes freeze selection, editing
and authentication. Known rejection permits deliberate rewriting. Explicit
calculation is a separate action, and no amounts appear before its real result.
This increment does not create arbitrary event rows, baseline ledgers,
settlement evidence or break-even inputs.

Calculation uses the explicitly selected baseline and joint shock revision.
Their baseline hash and decision timestamp must match. The closed
[scenario registration](api-economic-scenario-v1.md) request is pinned first;
only its validated `200` candidate permits pinning the subsequent
[calculation request](api-economic-calculation-v1.md). The latter's `202` is a
job admission. An acknowledged first phase is retained while the second phase is
retried. Unknown replies freeze the applicable body and key, selected inputs,
and authentication changes. Returning to another screen retains them in memory.
A known rejection or acknowledgement allows a deliberate new edit/calculation.
Reloading/closing the page does not persist this state; durable browser recovery
is still a whole-path requirement.

The shared transport preserves the existing 30-second per-request deadline.
Source reads permit 131072 response bytes; other economic calls retain 65536.
Responses must have the exact expected status, JSON media type, bounded UTF-8,
closed keys, typed dates/identifiers and literals. Exact source identity and
candidate scenario identity, pinned decision time and market-hold identity are checked. No credentials or raw exception text
appear in the screen, URL, local/session storage, or checked-in fixtures.

Manual refresh reads the actual job. A succeeded simulation job then resolves
its verified public economic-result DTO. Until that result is received there
are no amount cards. Amounts remain strings; formatting only adds separators and
a currency label. Unknown values remain null/“미확인”, and negative values keep
their sign and fraction. Totals and ratios are never calculated in the browser.
The display shows revenue, management operating income, cash shortage, and the
server's other cost/cash totals. The result's assessment remains hold under
unavailable market context. It is the economic DTO's assessment status, not a
completed Codex crop assessment or evidence of final recommendation.

## Monthly cash result

After a verified completed result, a manual request reads its
[monthly cash page](api-economic-cash-flow-v1.md). The client checks both result
IDs, scenario/revision, decision/formula, market hold and all claim labels
against that exact result before rendering. A result refresh, new calculation
or connection reset clears the prior cash page. An unsuccessful read also
removes stale rows. Pagination requests the last returned month as the cursor;
the first-page button permits returning to the start without a new calculation.
There is no automatic collection or calculation while reading cash.

Available rows show opening, net, closing, minimum and shortage amounts as
server decimal strings, with minimum-balance instants explicitly in UTC and
month grouping in Asia/Seoul. Unavailable cash has null rows/count, no cursor,
and “미확인”; it is never replaced with zeros. The bounded horizontal table
region is focusable and uses native keyboard scrolling on narrow displays.

Date/event series, break-even plan/trial forms, baseline/event/settlement authoring,
source adoption, complete farm input, real CLI research/review/assessment,
market-hold detail cards, maps/3D/replay and independent gate evidence are still
required by the existing [plan](../tasks/plan.md). Synthetic mock/TLS tests prove
software connection only. New code requires fresh release evidence.
