# CO₂/Solar UTC binding v1

Status: accepted by110 UTC tests plus38 program/122 continuation regression tests on2026-10-21 KST. New frozen Binding types use the accepted
[CO₂ continuation](crop-greenhouse-co2-continuation-v1.md) and unchanged original
[calendar/origin policy](crop-greenhouse-solar-time-v1.md). No old model type is
converted and no equation, profile, source quantity or physical elapsed is changed.

`prepare_binding(context, origin)` binds closed input_id/origin/start_at/precision,
explicit RFC3339 offset and microsecond precision to the new context. Exact
`Fraction(str(dt))*1000000` must be a positive integer. No implicit timezone,
rounding, interpolation, leap-second conversion or dates outside years1..9999.
UTC labels are integer microsecond arithmetic on original step_index; absolute
time never enters a crop equation. Same UTC/KST instants keep distinct source
spellings/identities and identical UTC labels.

`at_index`, `bind_checkpoint`, `source_chunk_sha256`, `bind_chunk` preserve original
canonical source quantities, digests, schedules and prefix chains. Binding and
chunk digests require separately trusted expected values. These digests do not
authenticate custody/farm rights. Strict context/checkpoint/model/status, forcing/
event/output cursors, active forcing index, source order/elapsed/phase, final
checkpoint and confirmed evaluation accounting are checked without numerical
replay. Labels cover samples/events/last_confirmed/hold. Initial-ready and committed
boundary0 share UTC and retain distinct checkpoint identity.

Successful boundaries use the original interval → forcing → event order. Interval
or global-step failures retain the preceding boundary. Failed forcing retains the
same-time old-forcing step endpoint; failed event/global-event balance retains
the same-time post-forcing/pre-event state. No failed forcing/event is counted as
confirmed and no failed event/output/checkpoint is fabricated. Confirmed coupled
evaluation count is5 per confirmed interval +2 per committed event +1 per
confirmed noninitial forcing activation; validation is1 and separate.

Every binding function invokes zero RHS, optics, gas/net/mass, ventilation,
integration, management, advance or checkpoint restore. It returns copied,
hash-bound data under the original8MiB source/result cap. Larger in-memory chunks
are held; they are not new approved public storage/HTTP packets. UTC binding
does not validate agricultural truth or replay source physics.

## Acceptance fixed before execution

- All10 accepted programs at boundary budgets1/7/128: preserve every original
  source/prefix and checkpoint; exact labels at forcing/event/terminal points.
  Forbid all actual numerical functions and restore during every binding call.
- Independent integer calendar arithmetic covers UTC/KST, pre-epoch, fractional
  grid, leap-year/year rollover and range/precision/offset failures. Binary64
  physical elapsed remains unchanged. Fresh Python binds original producer
  transport after restore without further numerical calls.
- Real/injected interval/global-step/forcing/event/global-event holds and0/
  interior/endpoint positions preserve correct confirmed UTC and active forcing.
  Source/digest/cursor/count/phase/order/quantity/identity mutations and old types
  reject; properties/source/context remain immutable. Exercise128 samples/events
  and forcing activations in a chunk under original8MiB/resource limits. An
  observed oversized maximum remains a capacity hold until corrected/verified.
- Focused WSL guard preserves old clock consumers/model/profile/results,
  five healthy roots/frozen previews,512MiB/PID and combined1GiB, FD/owned cleanup.
  No whole CI/browser/DB/full crop cycle/field/gate/deployment acceptance.

Scope software_research_only, G0–G4 not_assessed. Next: immutable storage, then
input/farm binding and signed custody before the same saved-state API/3D, with
current external data/claim holds preserved.

## Observed acceptance

[Machine evidence](../research/artifacts/crop-greenhouse-co2-time-20261021.json)
records270 passing focused tests in125.93s: program38, continuation122, UTC110.
All10 programs at budgets1/7/128 preserve original producer source and prefixes,
with13 actual numerical/advance/restore entry points forbidden during binding.
Independent integer calendar cases, real fractional physical elapsed, fresh Python
binding and11 interval/forcing/event/global-balance hold positions pass. Source,
cursor, phase, call, digest, old-type and malformed checkpoint rejection pass.

The initial run passed100 then failed the unchanged8MiB maximum. The explicit
[journal v2 revision](crop-greenhouse-co2-event-journal-v2.md) retains all audit
fields and removes only transient after_rhs from committed journal entries.
The original program/continuation suites pass on these new source versions.
Maximum128 samples/events/forcing activations now has6,649,987 source bytes and
6,664,177 bound bytes, below8,388,608; no cap/count was lowered. Old v1 evidence
and raw fixtures remain unchanged; v1 checkpoints are not silently converted.

GREEN guard126.445084s, combined RSS792,162,304bytes, single PID195,665,920bytes,
492 samples at0.25s, FD4→4, original2,148 entries/five roots/frozen previews and
zero owned process/PG/temp/credential residue. No whole CI/browser/DB, full crop
cycle, rights/gate or new model deployment acceptance. Next is immutable file
storage, followed by input/farm binding and signed custody before DB/API/3D.
