# Authored release packet storage verification

Date: 2026-09-30 KST. Internal software increment under the [storage contract](../contracts/farm-authored-release-store-v1.md). The development session uses Codex CLI `gpt-6-sol` at `xhigh` and did not start a nested model process.

The new PostgreSQL table retains the exact signed release request, signature, evidence and three report byte strings under one tenant/review-job key. Digests, core JSON identities, job foreign key, recording chronology and an update/delete trigger protect storage. `AuthoredReleaseStore.put` verifies before insertion and requires a succeeded review job; `get` rechecks current source/code/signature/evidence and exact stored bytes. An optional login policy grants only the authority profile read/insert rights.

Focused local results with an isolated SCRAM PostgreSQL 16 test server:

- `uv run --locked --group dev pytest -q tests/test_farm_authored_release_store.py` with the test DSN: **1 passed in 2.02 s**. It exercised a genuine durable job/worker completion using a fake CLI, then a synthetic completion proof and reviewer signature. It checked one-row retry, conflicting packet rejection, tenant scope, current-proof drift, owner UPDATE rejection, and request/worker/supervisor SELECT denial under distinct SCRAM logins. This does not prove that the constructed proof or review came from independent authorities.
- Existing role/login regression excluding the separate exhaustive general-login denial case: **55 passed, 2 deselected in 36.58 s**. The new table was installed only for the explicit optional profile; default profiles retained their policy. The pure signed release test after including the storage module in the code manifest passed **1 in 0.41 s**.

An initial test tried to mark a queued job succeeded by direct SQL and failed the database's deferred attempt-closure constraint. It was replaced with an actual fake-CLI worker completion. The first storage comparison then failed because PostgreSQL returned a non-UTC display offset; comparison now normalizes the stored timestamp to UTC. After this fix, the focused storage test passed. These observed failures are software corrections, not G1 evidence.

No real reviewer issued a packet, no actual product CLI ran, and no authored snapshot or accepted Run was published. The next boundary is an actual independent release with documented signer/evidence custody, then an authored publisher and worker that reverify it before atomic Run publication. G0/G2/G3/G4 remain separately held.
