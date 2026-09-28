# Conditional economic calculation worker v1

Status: implementation candidate for deterministic user-assumption arithmetic.
No farm performance, forecast, ranking or G1/G4 acceptance is granted.

An operator submits an actual simulation JobStore intent with input_version
economic-calculation-input-v1, scenario_id/revision/hash, candidate_id and the
literal existing economic-ledger-v9-sales-settlement formula_version. No result
bytes, numbers or gate proposals are accepted as worker input. HTTP submission
and job-to-economic-result lookup are subsequent api-flow work.

EconomicCalculationWorker targets one UUID and authenticated tenant. It requires
metadata, artifact, simulation_execute, market_source_read, market_candidate_read,
market_result_read/write, decision_context_read and market_hold_context_read.
Job, result, candidate and actual source/hold/context stores share the audited
authority policy/schema/DSN/principal. The existing market/source flags are
required; no grants, migrations or credential defaults are added. Different
models/stages/tenants are not claimed.

The worker validates immutable input bytes and live lease/cancellation, reloads
the candidate, verifies supplied pins and recalculates through the existing
MarketScenarioService/Decimal ledger. It writes a content-addressed receipt with
result/ledger IDs and hash, input pins, real calculation/Assessment statuses,
formula and implementation/environment digests. Current scopes, store pointers,
implementation/environment and the whole calculated result are rechecked before
and after insertion. Result row, fenced job completion, publication, event and
attempt outcome commit together. Failure leaves no visible partial result.

Succeeded means the deterministic procedure completed. The receipt preserves the
engine's calculation_status, including hold and null unknown totals, and its
assessment_status=hold. No CLI invocation, decision, usage or validation record
is fabricated; overall CLI/review/Assessment and G1/G4 remain pending. Orphan
content from a rolled-back attempt is not reachable through a job publication.

Input/pin failures use bounded economic_input_rejected/economic_input_hold;
internal failure uses economic_runtime_failure and bounded existing retries.
Cancellation/lease loss cannot publish. Errors expose no source values or
exception text. Protected operator configuration and process deployment remain
separate acceptance evidence; fixtures prove software contracts only.

## Foreground command

From backend, the operator supplies a protected importable factory returning the
exact worker and an existing job UUID:

```sh
uv run --locked --group dev python -m app.economic_work \
  --factory "$OSSF_ECONOMIC_FACTORY" --job-id "$OSSF_ECONOMIC_JOB_ID"
```

Factory/UUID validation precedes loading. Fixed JSON stderr with exit 2 denotes
startup rejection; exit 3 denotes unresolved execution. Exit 0 contains only
bounded job/attempt/state/reason/result-ID metadata (or null if not claimed),
not financial values or source/credential text. This command invokes no model.
Lease expiry is recovered through the existing targeted claim/new-attempt path.
