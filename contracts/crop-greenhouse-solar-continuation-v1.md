# Solar/ventilation continuation v1

New frozen `Context`/`Checkpoint` types compose the accepted
[solar program](crop-greenhouse-solar-program-v1.md). Existing22/25-ledger types
remain unchanged and incompatible. No agricultural equations or profiles change.

`prepare_context` accepts exactly the solar program arguments. One complete
solar RHS normalizes source scenario/solar/weather and binds initial diagnostics.
Canonical program/manifest/initial result bytes total at most2MiB. Identity binds
code and component policies, four profiles, source/notice hashes,108-state and
41-ledger schemas,6 event totals, elapsed-grid policy and Python/float environment.

`start` issues an initial-ready checkpoint before boundary0. `advance_chunk`
accepts1..128 original boundaries, including0, and reuses the accepted interval,
event and15-global-balance sequence. It accumulates each original step/event in
the original order. Complete boundary processing updates next index, output/event
cursors, canonical record prefix chains and the last confirmed snapshot. Chunk
sizes and wall time never change the result or final checkpoint identity.

`checkpoint_bytes` returns canonical immutable bytes,at most64KiB.
`restore_checkpoint(...,expected_sha256=...)` requires a separately trusted digest,
rejects duplicate/noncanonical/nonfinite JSON, mixed versions/contexts, malformed
state/ledger units/cursors/diagnostics and inconsistent current balances. Restore
and each advance evaluate only the current coupled endpoint once. They perform
zero past step/event replay. A digest is not custody authentication; server signing
and farm/current rights binding are subsequent tasks. Properties return copies.

Confirmed advanced s steps/e events report coupled solar/PAR/NIR/ventilation
`5*s+2*e`, total core RHS `5*s+4*e`. Preparation1 and each checkpoint validation1
are separate; unavailable trial calls are excluded from confirmed counts.
Failure preserves the incoming checkpoint and returns `hold`, checkpoint=None,
explicit global phase/time and only the confirmed output/event prefix. An event
failure can retain its same-time pre-event step-end without committing that event
or requested output. Invalid context/transport/budget or completed advance raises
`ContinuationRejected`; cancellation/crash exceptions do not become normal yields.

Acceptance: all11 independently accepted programs at budgets1/2/3/7/128 and mixed
budgets match every original state/41/6 ledger/15 balances/diagnostic/journal and
final canonical checkpoint bytes. Fresh Python restores pending/committed event0,
interior and completed boundaries with zero historical step/event replay. Preserve
accepted dt8/4/2 grids, signed energy, output order, context/input immutability,
trusted-digest/cursor/unit/policy/profile/source/schema rejection and real/injected
hold prefixes. Exercise128events/512outputs and original byte/resource limits.
Related old continuation/time consumers and five live roots/original files remain
preserved. UTC is bound separately by [solar time](crop-greenhouse-solar-time-v1.md).

Synthetic software acceptance only; G0–G4 `not_assessed`. Storage/API/worker/3D,
full-season validity, real crop/economic predictions and deployment remain pending.
