# Solar immutable calculation files v1

The accepted [solar continuation](crop-greenhouse-solar-continuation-v1.md) and
[UTC binding](crop-greenhouse-solar-time-v1.md) feed new typed solar artifacts.
Existing22/25-ledger artifacts and code remain unchanged and incompatible.

`create_writer`, `open_writer`, `open_artifact` and writer/reader operations reuse
the existing bounded regular-file, fsync, content-addressed page, exclusive lock
and atomic HEAD policy. Solar storage has its own version/code/dependency identity.
It pins full initial solar/PAR/NIR/outdoor/core composition, original program and
profiles, source/notice/policies, current calendar and41-ledger context identities.
Raw108-state/41-continuous/6-event/15-balance quantities and original UTC/prefix/
checkpoint pairs are stored unchanged, including held prefixes and signed heat.

Limits remain64samples/8events and2MiB/page-response,128KiB metadata,3MiB context,
2MiB root,4097commits/18pages per commit,512MiB directory and65536 files.
The caller supplies a separately trusted root/HEAD and original producer chunk
digest. A recomputed digest is not farm authorization or server custody approval.

Publication order is pages→complete commit→atomic HEAD; only completed/hold
results finalize a root. Orphans before HEAD remain unpublished and are not
deleted or overwritten. Reopening validates actual HEAD and exact checkpoint
before continuing. Failed events/outputs are never fabricated. Independent reader
reassembles source/time/hash chains without context construction, restore, RHS,
PAR/NIR/ventilation, integration, management or CLI. Profile parsing for identity
validation is permitted. Reader checks current source/code/notice hashes before
and after each operation; mixed/modified/missing/symlink/FIFO/oversized/stale or
late-changed files and closed handles reject.

Acceptance:11 accepted synthetic programs×budgets1/7/128 preserve original
source/UTC/state/41/6 ledgers/15 balances, journals, checkpoint/prefix/hash across
actual writer/finalize/reader; fresh process reader has zero numerical/restore/CLI
calls. Reopen initial/event/final writer positions and force owned child SIGKILL
before/after HEAD, preserving committed prefixes. Cover real interval/first/last
event and injected global/before/after-solar holds. Exercise128sample/event chunk
with actual page/response caps, old22/25 mixing, new optical dependencies and
tampered solar records; preserve old files/frozen services/live process roots and
512MiB/PID/combined1GiB. This is software-only synthetic acceptance;
G0–G4 remain `not_assessed`. Input evidence/farm rights/signed custody/database/
API/worker/same-UTC3D and real crop/economic validation remain subsequent work.
