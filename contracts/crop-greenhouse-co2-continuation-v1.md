# CO₂/Solar forcing-program continuation v1

Status: research software accepted by122 focused tests on2026-10-21 KST. New frozen Context/Checkpoint types follow the
[accepted program](crop-greenhouse-co2-program-v1.md) and existing
[Solar transport limits](crop-greenhouse-solar-continuation-v1.md). They remain
incompatible with old108-state checkpoints; no equations/profiles are changed.

Current transport revision: [journal v2](crop-greenhouse-co2-event-journal-v2.md)
uses continuation/checkpoint-v2 and preserves all122 continuation tests in the
[combined270 proof](../research/artifacts/crop-greenhouse-co2-time-20261021.json).
Original v1 evidence below is retained. New context/prefix identities bind the
smaller committed journal; there is no silent v1 checkpoint conversion.

`prepare_context` takes exactly the new program arguments. One actual initial
CO₂/Solar RHS normalizes the seed and first forcing row. The immutable program
retains all remaining explicit forcing rows; their state-dependent checks occur
at activation. Canonical program/manifest/initial RHS total at most2MiB. Manifest
binds code/component/policy/source/notice/four-profile identities,109-state/44-flow/
6-event/17-balance schemas and Python/float environment. No hidden forcing cache.

`start` issues the initial-ready checkpoint before boundary0. `advance_chunk`
takes1..128 original boundaries including0. It preserves the exact interval →
new forcing → management → selected output order and individual floating-point
additions of the accepted program. It stores next index, forcing/event/output
cursors, current snapshot and canonical output/event prefix chains. The initial
forcing cursor is1 because the initial row is already active; subsequently it is
the count of forcing rows through the last committed boundary. Boundary0 events
and outputs remain unprocessed in the initial-ready checkpoint.

Canonical checkpoint bytes are at most64KiB. `restore_checkpoint` requires a
separately trusted expected SHA and rejects duplicate/noncanonical/nonfinite JSON,
wrong schema/context/code/profile/environment, non-float64 quantities, inconsistent
cursor/active forcing/phase/time, stale diagnostics and unresolved global ledgers.
Restore and each advance validate exactly one **current** coupled endpoint; they
perform zero previous RK intervals, forcing activations or management events.
This digest is not custody authentication. Signing/current farm rights, UTC,
storage/API/worker and3D remain subsequent tasks. Properties return copies.

Chunk boundaries do not enter physical result or final checkpoint identity.
Confirmed numerical evaluations are5 per original interval,2 per committed
management event and1 per noninitial forcing activation. Preparation1 and each
checkpoint validation1 are counted separately; failed trials are excluded from
confirmed numerical counts. An ordinary yield is only at a complete original
boundary. Failure returns hold with checkpoint=None, detached confirmed state/
selected prefix/journal and explicit global phase. It leaves the incoming
checkpoint unchanged. Same-time step/forcing confirmation may be exposed on hold
before a failed event, as in the original program. Invalid transport/context/
budget or completed advance raises ContinuationRejected. Crash/cancel exceptions
propagate. No partial or held run is labeled completed.

## Acceptance fixed before execution

- All10 accepted32s programs, budgets1/2/3/7/128 and mixed budgets: exact complete
  samples/journal/last state/44 flows/6 event totals/17 budgets/forcing diagnostics,
  output/event prefix chains and final checkpoint bytes. Reuse independently
  checked program results; no replacement oracle. Preserve the accepted fixed
  forcing/event times at dt8/4/2 for all three varying-forcing cases.
- Fresh Python restores initial-ready/event0, before/after interior forcing and
  event, before final boundary and completed checkpoints. Instrument actual
  current CO₂ RHS, interval and management calls to prove zero historical work,
  remaining steps/changes/events only and same final bytes/prefixes.
- Context/checkpoint/input/property immutability and deterministic retry;
  expected-digest, structure/type/unit/domain/cursor/active-forcing/policy/profile/
  source/environment rejection, including CO₂ inventory/ppm fields. Real depletion,
  late forcing/event and injected global balance holds match original prefixes.
  Invalid budgets/bytes/completed state and crash propagation are explicit.
- Exercise512 forcing rows,512 outputs,128 events with original2MiB/64KiB/128
  limits. Preserve old core modules/profiles/results,5healthy roots/frozen
  previews,512MiB/PID and combined1GiB, FD/owned cleanup. Focused tests only;
  no whole CI/browser/DB/full crop cycle/field/gate/deployment acceptance.

Scope is software_research_only, G0–G4 not_assessed. Next: UTC binding, then
custody/storage and the same saved-state3D; current external data/claim holds stay.

## Observed acceptance

[Machine evidence](../research/artifacts/crop-greenhouse-co2-continuation-20261021.json)
records122 passing tests in74.05s. All10 accepted programs at five budgets match
the original driver exactly, including all selected samples, journal, last state,
44 continuous/6 event ledgers,17 balances and final checkpoint bytes. Mixed chunks,
nine accepted convergence grids and retry/immutable-copy behavior pass.

Eight fresh Python restores at next indices0/1/4/5/8/9/16/17 produce the same final
hashes and remaining prefixes. Actual interval/event/current-RHS instrumentation
confirms zero past work and exactly one restore check plus one validation per
new chunk,5 per remaining interval,2 per remaining event,1 per remaining forcing
change. A separate restore probe forbids any interval/event and observes one
actual current CO₂ RHS call.

The tests also cover11 code/source/notice/profile/policy/environment changes,
20 checkpoint state/ledger/cursor mutations,7 invalid budgets,7 external JSON
forms, trusted digest/context/canonical-byte rejection, actual/injected hold
prefixes, late failure and crash propagation. The maximum512-forcing/512-output/
128-event program completes in five chunks within2MiB context and64KiB checkpoint
limits. These are asserted bounds, not a new public HTTP packet acceptance.

RED was a missing module; the first complete implementation passed122 tests.
GREEN guard74.580728s, single PID208,478,208bytes and combined802,992,128bytes,
290 samples at0.25s, FD4→4, original2,148 entries/five roots/frozen previews and
zero owned process/PG/temp/credential residue. Original program/models/profiles
are unchanged. No broad CI, UTC, custody, saved109-state3D, actual farm, gate or
deployment acceptance. Next: UTC binding without numerical replay.
