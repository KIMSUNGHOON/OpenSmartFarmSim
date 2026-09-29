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
from the three existing server models and have a backend drift check.

A numeric edit retains the selected input's unit, scope, origin and evidence
labels. Its decimal is a string, with explicit UTC knowledge date/time. A new
revision, source reference and idempotency key are pinned before the first
[source intake](api-market-user-source-v1.md). UTC is serialized in the canonical
whole-second form required by intake. `200` means a new assumption was registered,
not reviewed, applied to a ledger, or calculated. The original version is never
mutated. This screen does not yet create the new baseline/rights versions needed
to use that edited number in calculations; it says so next to registration and
selection. It supplies no crop outputs, coefficients, tariffs, or missing costs.

Calculation uses the explicitly selected existing baseline and joint shock.
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

Monthly/date series, break-even forms, baseline/rights/settlement authoring,
source adoption, complete farm input, real CLI research/review/assessment,
market-hold detail cards, maps/3D/replay and independent gate evidence are still
required by the existing [plan](../tasks/plan.md). Synthetic mock/TLS tests prove
software connection only. New code requires fresh release evidence.
