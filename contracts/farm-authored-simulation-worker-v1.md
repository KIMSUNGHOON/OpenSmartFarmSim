# Authored thermal simulation worker v1

Status: internal deterministic worker candidate after [authored simulation admission](farm-authored-simulation-v1.md) and [Run storage](farm-authored-run-store-v1.md). It is a software path, not independent G1 acceptance.

An authority worker is given one tenant and one exact simulation job UUID. It leaves other simulation input versions untouched. With `simulation_execute` and `authored_run_publish` scopes, it claims only that job, verifies the canonical authored input, rereads the signed reviewer release and owned registration, recalculates the 120 thermal steps, and renews its lease. It builds a canonical result receipt from the prepared Run and proposed publication report. The Run store repeats current evidence checks inside the transaction. The worker then inserts the two final traces and accepted gate report, updates the same live job to succeeded, inserts the receipt publication and terminal event/outcome, and commits. The database's deferred constraint rejects a Run without its matching successful job publication. A canceled, expired, changed, malformed or failed attempt cannot expose a partial Run. Content-addressed receipt bytes written before the transaction may remain unreferenced after rollback; no public lookup is created for them.

The read boundary rechecks the current release, registration, hashes, gate signature and exact receipt. The worker does not call Codex CLI for deterministic thermal arithmetic: the mandatory product CLI `gpt-6.1-sol`/`xhigh` collection review is upstream and its completed signed evidence is required by the preparer. The [SCRAM test record](../research/farm-authored-simulation-worker-implementation.md) uses a fake CLI and constructed reviewer proof, so it establishes transaction software behavior only. Authenticated API and 3D projection candidates exist; their combined production path, actual product CLI execution, independent release/custody and G1 remain held. This worker makes no crop, purchase-energy or future-margin claim.

The existing foreground authority command accepts this exact worker type from a
protected operator factory:

```bash
python -m app.simulation_work --factory operator_module:build --job-id UUID
```

The factory supplies the tenant, audited authority login, current reviewer
release and Run store. The command accepts no source bytes, keys or tenant
override from arguments. It executes only the named job; an idle or unrelated
job returns `null`, and an unresolved lease returns a fixed error without an
automatic retry. Command success is software execution evidence, not G1 or
independent release approval.
