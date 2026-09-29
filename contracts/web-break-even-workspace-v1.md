# Conditional break-even workspace v1

Status: software candidate, within the existing Korean economic screen. This
connects stored user assumptions to the existing server plan/worker/result
contracts; it is not forecast, continuous-root, whole G1 or operating acceptance.

The user explicitly selects an owned baseline, one actual sale/collection pair,
one of three targets and a variable unit, and supplies minimum/maximum/step as
decimal strings. The sale's batch, grade, channel and exact UTC dispatch,
delivery, inspection, recognition and collection instants come from the pinned
baseline record. Unknown collections permit no invented sale/collection choice.
Decision time, calendar and unavailable market-hold identity also remain pinned.

The user adds 2–256 distinct saved joint-shock revisions in grid order. They
must share the baseline hash and decision time; the display shows their actual
stored numeric changes without calculating grid values, quantities or money.
There are no preselected trials, target, range, ownership declaration or prices.
The server remains responsible for exact grid cardinality, each derived trial
value, fixed-input/shock equality, rights, settlement and conservation checks.
Automatic generation of trial assumptions from a response rule is still pending.

One deliberate submit action pins the complete request and a scenario intent
for each selected joint revision. Scenarios are registered sequentially through
the existing economic endpoint. Every acknowledged candidate is retained; an
unknown response retries only the pending body/key. Only after all candidate
pins exist is the closed break-even plan submitted. The server derives the
grid and plan; the browser sends no computed values or proposed plan.

The plan ID is the immutable idempotency identity. Response loss retains exact
inputs and acknowledged phases and locks editing/connection changes. Navigation
retains in-memory state; reload recovery remains unfinished. Known rejection
permits deliberate rewriting. After an unknown plan POST, manual confirmation
uses the [historical intent receipt](api-break-even-plan-receipt-v1.md) with a
SHA-256 of the canonical full request and ordered candidate pins. It does not
repeat source preparation or issue another POST. Missing, denied or inconsistent
receipt reads keep the original write unresolved. Safe resubmission when no
intent was stored remains unfinished. A receipt proves stored intent only;
current execution/result validation remains separate.
Read-only result refresh checks the actual simulation job and then the completed
job result, with exact plan, decision, calendar, target, unit, bounds and market
hold binding. Result bodies are bounded to 524288 bytes for up to 256 trials.
Requests use the existing authenticated transport and 30-second deadline.

Money and trial values are server strings; missing cash remains null/“미확인”.
The result distinguishes zero at a listed point, no zero at listed points,
crossing intervals, nonmonotone listed values and hold. A crossing interval is
not an interpolated root, and no grid zero does not rule out a continuous
solution. Every result remains user/assumed, conditional_user_grid_only and
Assessment hold. No crop ranking, future profit, source approval or gate release
is generated. The bounded result table supports keyboard horizontal scrolling.

Actual farm/baseline/event/settlement authoring, automatic trial assumptions,
runtime CLI and independent release/domain/operating evidence, 3D/replay and
whole G1 remain required by the existing plan. Large-grid asynchronous read
validation and capacity/cancellation/revocation budgets also remain required;
bounded response bytes do not bound full replay work. Synthetic tests prove software
contracts only.
