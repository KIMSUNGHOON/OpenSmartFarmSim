# Current solar/ventilation management program v1

Research version `joint-solar-ventilation-management-program-research-v1` composes
the accepted [solar RK](crop-greenhouse-solar-integration-v1.md) and unchanged
[atomic management](crop-climate-joint-management-v1.md) on an elapsed step grid.
It has108 states,41 continuous transfer ledgers,6 instantaneous event totals and
15 global balances. It issues no UTC, checkpoint, custody, storage or API context.

## Inputs and ordering

`integrate_events` accepts the solar RK scenario/solar/ventilation/four pinned
profiles, plus the existing boundary driver's closed `events` and `output_steps`.
Its limits remain1..4096 steps,positive finite dt,at most600s,128 uniquely ordered
events and512 strictly ordered outputs including0 and the endpoint. All origins,
including event origins, agree. No optical coefficient or forcing is defaulted.

At each boundary: confirm the preceding RK interval; apply the scheduled atomic
event; recompose current PAR/NIR/ventilation; check global balances; then emit a
selected output. Events at0 or the endpoint obey this same order. Intermediate RK
trials and uncommitted events are never emitted as confirmed states.

Every interval uses the accepted one-step shared RK unchanged. Each event
explicitly evaluates current solar/ventilation before removal, supplies its fully
composed core scenario to unchanged management, then restores the immutable
**source** forcing on the changed stocks before composing solar/ventilation again.
The management journal's before/after core evaluations hold the **pre-event
composed** forcing solely for its existing atomic checks; these are not the
post-event coupled forcing. Separate before/after solar diagnostics and composed
forcing identify that distinction. Source non-solar heat/other air inputs must
never be replaced by already composed inputs.

Leaf removal retains temperature while removing capacity and signed sensible
energy relative to the reference temperature. Cohort removal uses the existing
decimal-rational retention rule. There is zero elapsed time during removal:
no continuous solar/ventilation transfer is credited to an event. The original
7 stock balances include event totals exactly once;3 ventilation and5 radiation
partitions use the unchanged accepted formulas/budgets. No floor/cover heat,
purchased energy, harvest conversion, money or recommendation is added.

## Counts, identities and failure

For n steps and e events, composed PAR/NIR/ventilation/core RHS counts are
`1+5*n+2*e`; management adds `2*e` core RHS evaluations. Thus total core RHS is
`1+5*n+4*e`. Extra solar validation calls are0. Output selection changes identity,
never physical state or continuous/event totals. Code/component/profile/source/
notice/policy hashes, normalized source inputs, schedule and numerical settings
bind a new immutable calculation identity; payload hashes bind outputs/journal.
The ledger schema is `joint-solar-ventilation-ledgers-v1`.

Any unavailable input, interval, event, coupled boundary or global balance raises
`SolarProgramHold` with global step/phase, deep-copied last confirmed state,
selected prefix and journal. An event failure retains the same-time pre-event
endpoint without committing removal or that boundary's requested output. An
interval failure retains only the preceding confirmed program boundary. No held
program becomes a completed Run.

## Acceptance

Independent app-free Decimal80 solar149-vector RK and separately pinned
retention/capacity-energy removal reproduce selected108 states,41 continuous
ledgers,6 event totals,3 derived values and journal before/after/removals.
Existing tolerances: rel5e-12/abs5e-14; canopy temperature abs2e-10K. All15 native
budgets must pass; independent absolute stock/energy bounds1e-7,number1e-12,
water1e-13,capacity1e-8 apply without widened thresholds. Fixed-time management
trajectories at dt8/4/2 vs independent dt.25 must improve by ratios>8 on the
registered nondegenerate metrics. Verify event0/interior/end, signed energy,
no-events/current short RK, darkness/old driver, source forcing preservation,
actual call order/counts, output selection, full128/512 limits, injected holds
and immutable originals/five live roots within512MiB/PID and combined1GiB.

Self-authored synthetic software evidence only; `G0_G4: not_assessed`. Current
PAR/NIR/ventilation is not a complete greenhouse heat closure or validated crop
production prediction. New context/UTC/storage/API/same-time3D and farm evidence
remain separate tasks.
