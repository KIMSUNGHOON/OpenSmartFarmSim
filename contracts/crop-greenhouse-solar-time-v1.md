# Solar UTC binding v1

New frozen `Binding` uses the accepted [solar continuation](crop-greenhouse-solar-continuation-v1.md)
and unchanged original calendar/origin helpers. It does not convert old model types.
`prepare_binding(context,origin=...)` binds closed input_id/origin/start_at/precision,
explicit RFC3339 offset and microsecond precision to the original context. Different
UTC/KST source spellings retain different identity while mapping the same instant.

The positive step `Fraction(str(dt))*1000000` must be an integer. Unsupported
precision, ambiguous offsets, leap seconds or years outside1..9999 hold; no
rounding, implicit timezone, interpolation or dt change is permitted. Physical
binary64 elapsed values remain unchanged. UTC labels use integer microsecond
arithmetic on the original step index; absolute UTC never enters a crop equation.

`at_index`, `bind_checkpoint`, `source_chunk_sha256` and `bind_chunk` preserve
original source values/canonical digest and require trusted binding/chunk digests.
Closed context/model/status/schema, original schedule, cursor/prefix transitions,
confirmed call accounting, endpoint and failed-phase positions are checked.
Labels are separate for samples,events,last_confirmed and hold. Initial-ready and
committed boundary0 have the same time and distinct checkpoint identities.
Event-before-solar/removal/event-after-solar/global-event-balance holds retain a
same-time pre-event endpoint; interval/global-step holds retain the preceding one.
No failed event/output or successful checkpoint is fabricated.

All binding functions invoke zero numerical RHS/optics/ventilation/integration/
management/restore calls. Results are copied, canonical/hash bound and limited to
the existing8MiB. The producer digest does not authenticate custody or farm rights.

Acceptance: all11 solar programs with budgets1/7/128 preserve every original source
and prefix without numerics; UTC/KST/fractional/pre-epoch/leap-year/year rollover
labels match independent integer calendar arithmetic. Fresh process binding, t0
identities, real/injected interval and all event hold positions, tampered source/
digests/calls/cursors/order/units/contexts and bounds are checked. Exercise128
samples/events in a chunk and preserve old time consumers/original files/live roots.

Scope is synthetic software only, G0–G4 `not_assessed`. New storage/API/worker and
same-UTC3D remain subsequent acceptance; no production or prediction claim follows.
