# Conditional break-even HTTP and authenticated store implementation

Status: internal software candidate; no production or G1/G3/G4 acceptance.

## Judgment provenance and output

Active Codex CLI thread `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` performed this
interface/runtime judgment. Selectively inspected `turn_context` at
`2026-09-28T11:01:58.593Z` records exact `gpt-6-sol` and `xhigh`. No recursive
CLI or additional model call was launched. The reviewable output is this change,
[public read contract](../contracts/api-break-even-read-v1.md),
[optional v4 profile](../contracts/runtime-break-even-login-policy-v4.md), and
focused receipts below. These are proposals/software evidence, not approval of
data, independent domain/release review, or a gate decision.

The implementation uses the existing deterministic finite-grid engine and
Decimal formatter. No farm arithmetic, coefficient, tariff, dependency, source
record or immutable decision/manifest/release is changed. Bounds and targets
remain those of the pinned request. Each read replays every pinned full market
and economic trial before projection. Unknown cash stays null; zero remains a
string zero. Status/scope prevent brackets, no grid zero or nonmonotone branches
from implying a continuous root, future margin or ranking. Raw tenant/sale/batch,
source and internal proof details are excluded.

The bounded `plan_id` query preserves existing Unicode/slash identifiers.
HTTP authentication/scope, matching request ID, independently scoped store
lookup and replay failure are checked separately. An absent reader returns 503;
it does not bypass source/replay checks. OpenAPI adds only this operation and
its schemas, with the same scope tuple supplying runtime and documented guards;
existing operations/IDs are unchanged. Exact regeneration check passed.

V4 requires both explicit market and break-even calculation flags; v1/v2/v3
matrices and audit versions remain unchanged. Fresh authority grants additionally
allow only SELECT/INSERT on the immutable plan/result table. Bound BreakEvenStore
uses exact SCRAM identity and full effective auditing before every data query.
General roles, wrong login, missing opt-in and effective grant drift are denied.
Source/context dependencies keep their verified authority and tenant checks.
Existing deployed roles/records are not automatically migrated.

## Test receipts

The new HTTP/projection test first failed because the new module was absent.
The new profile test first failed because its explicit option was absent.
After implementation, the initial **11 HTTP/projection cases passed in 4.00 s**;
**5 actual SCRAM cases passed in 71.71 s** on local PostgreSQL 16.15 with locked
Python 3.12 dependencies. The latter pins signed-context/hold-backed three
market trials and a plan, replays through a fresh store and reads via HTTP,
then denies changed scope and effective grant drift. It also checks three
non-authority login roles and wrong-login rejection. Sources and principals are
synthetic; controller owns the local credentials/test keys under one OS UID.

Two further cases cover nonmonotone display and an existing Korean/slash ID.
The combined focused run over these paths plus old break-even, market runtime,
v1/v2 roles/login, signed hold, economic API, OpenAPI, request identity and thermal
publisher reported **179 passed and one failure in 193.79 s**. The failure was
an invalid new test fixture whose collection exceeded its gross sale. It was
corrected to the existing valid delayed-collection case; that test then passed
**1 case in 0.55 s**. No production calculation/guard was loosened. Hosted full
exact-head CI is required as the final regression receipt. The added documented
scope also participates in the existing denied-before-read OpenAPI tests.

The break-even engine/store/public projection and shared economic projection
now join the closed thermal code digest, requiring fresh independent release
review; old immutable releases remain intact. Changed document links and staged
whitespace are checked before commit.

## Holds

Baseline/shock/rights/settlement and plan/trial generation remain self-authored
test sources. Production source/plan generation, protected complete operator
assembly, credential/key/UID custody, DB TLS/HBA/RLS, actual isolated Codex,
independent economic and thermal release evidence, browser flow and G1/G4 remain
incomplete. Finite-grid results do not meet the full continuous-root or independent
validation acceptance of `economic-break-even`, so its checkbox remains open.
