# Solar read validation lock scope — v1 candidate

Basis: [current55 checks, native22/64 and diagnostic15/64](../research/crop-solar-shared-read-locks-implementation-20261019.md).
The current diagnostic has16 confirm returns/0 exception events, but7 actual
writer advance Pending events. Current validation remains expensive. This is an
implemented read/read boundary followed by a proposed narrower read lock scope;
the new candidate is not implemented or accepted. The actual post-capture
reader/current vs writer RED passed as a diagnosis in41317:1: writer advance
was rejected with SolarCustodyPending; no GREEN exists yet.

## Next increment

First reproduce an actual writer being excluded while an already captured
reader is performing current validation. Use separate execution contexts and
independent lock descriptions. This RED must identify writer Pending, without
changing actor timing, retry, input64/chunk1, equations or resource caps.

For readers, protect the signed snapshot capture and final identity/HEAD
recheck with the same root/intent shared locks. Perform expensive current
database/source validation outside those file critical sections. All current
checks and their failure semantics remain required. This is no authorization
cache and no unlocked confirmation. The writer retains its existing exclusive
locks. Reads never create files, prepare/advance arithmetic or publish evidence.

A writer advancing during validation must cause the affected captured progress
read to reject changed HEAD/proof/intent/directory identity without partial
bytes. Release/reacquisition must verify the same lock file descriptions and
named identities, preserve order and fail closed if a writer holds either lock.
Do not silently upgrade locks, accept a replaced directory, or return mixed
snapshots. A fresh read after the writer completes must match the original
stored values and UTC. Existing accepted immutable prefix selection semantics
remain required.

## Acceptance

1. Meaningful actual RED/GREEN: writer advances while the reader validates;
   stale captured progress is Pending, recovery reads the new original snapshot.
2. Same-head concurrent reads/confirm remain valid; writers still exclude
   protected capture/recheck; invalid mode/missing/replaced lock files fail closed.
3. Current rights/source/review/principal changes, cancellation, lease expiry,
   proof/HEAD rollback/fork and directory replacement retain their rejection.
   Read queries perform no arithmetic or SQL mutation. No current check is skipped.
4. Relevant existing custody/worker/query/prefix55 checks, original values/UTC,
   frozen services/inputs5root and512MiB/PID/combined1GiB/owned cleanup pass.
5. Review and local acceptance precede a changed-source original trace-OFF64
   normal. Independent hold/cancel/calculating WebGL, WSL capacity and user
   activation follow. Rights/independent G0–G4 evidence and the whole product
   remain separate. Same-source failed normal/diagnostic reruns are not evidence.

Use the current native Codex CLI gpt-6.1-sol/xhigh session; no recursive CLI.
