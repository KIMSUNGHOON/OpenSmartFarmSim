# Owned fixture collection implementation evidence

Status: collection software candidate; G0/G1/G4 remain unaccepted.
The active root Codex CLI turn_context records `gpt-6-sol` / `xhigh` at
2026-09-29T01:27:11.768Z and 2026-09-29T01:47:57.662Z in thread
01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc. This exact existing CLI session performs
the design and review. No recursive CLI, new model invocation or subagent was
used. Reviewable output is the [contract](../contracts/owned-fixture-collection-v1.md),
[owned registry](../backend/app/owned_fixture_registry.py),
[service and worker](../backend/app/owned_fixture_collection.py),
[foreground command](../backend/app/collection_work.py) and
[actual-store tests](../backend/tests/test_owned_fixture_collection.py).

## Implemented connection

The missing deterministic collection process now accepts a completed research
selection under an actual audited authority JobStore. It checks the immutable
parent input, publication, retained final/report, invocation/capture and server
proceed decision. The safe projection must equal the original context and
select the installed provider. Admission rechecks the complete parent/source
binding at commit and creates only an immutable collection intent.

The first adapter reads the existing fixed manifest v2 and its three original
directly authored files. Manifest/source hashes and lengths, owned rights and
the existing thermal clock/unit/input checks are required. File reads are
bounded; requests cannot choose URLs, paths, raw content, QC verdicts or numbers.
An ex_ante decision preceding source availability cannot collect that bundle.
Original bytes and metadata are preserved; no fixture, coefficient, tariff,
crop output or arithmetic was changed.

The target worker revalidates the full binding under a live tenant/attempt/token
lease. Code/environment, current scopes and authority/provider/content bindings
are checked around collection and again at publication. Durable canonical
record bytes precede the transaction that commits completion, publication,
event and outcome. Faults roll back visible publication. The record includes
the parent/source hashes, decision context, actual retrieval time and software
QC while explicitly retaining Assessment hold and G0/G1 not_accepted.
The protected Python foreground command prints metadata only and never calls
a model. The three new modules join the selected implementation digest.

## Focused verification

RED was the missing collection module: **1 collection error in 0.35 s**.
Initial integration failed **1 in 3.69 s**: the existing thermal contract
requires a UTC `Z` timestamp. After correcting it, a second attempt failed
**1 in 3.64 s** because job input serialization correctly forbids raw fields.
The adapter now uses a bounded separate collection-record serializer, while
admitted job inputs retain the original raw-content prohibition. The complete
positive case then passed **1 in 6.07 s**, five cases deselected.

The first collection suite passed **10 in 30.64 s**. After bounding file reads
and adding retained-proof corruption and command configuration cases, the final
focused suite passed **142 in 63.11 s (1:03)**: 14 collection cases and 128
existing CLI contract/worker, fixture policy/parameters and durable job/recovery
regressions. The command was:

```text
uv run --locked --group dev pytest -q
  tests/test_owned_fixture_collection.py tests/test_cli_contracts.py
  tests/test_cli_worker.py tests/test_fixture_policy.py
  tests/test_thermal_parameter_fixture.py tests/test_jobs.py
  tests/test_job_recovery.py
```

Tests use local PostgreSQL 16.15 with actual SCRAM authority credentials, grants,
private evidence and atomic JobStore publication. Research runs a fake Python
CLI executable with synthetic keys and output. The foreground collection test
runs an actual fresh Python child using private temporary operator configuration
and the same actual durable store; it does not launch Codex recursively. These
are software contract tests, not evidence of an actual product model call.
Idempotency, missing scope, foreign/unfinished parent, source failure, forged
input, provider rebinding, publication/scope faults, cancel, expiry/recovery,
changed original bytes, unavailable-at-D input and retained parent proof
corruption were checked. Source bytes are absent from job inputs and stdout.

Review covered complete parent/proof/hash/context binding, fixed provider and
bounded original reads, scope/identity changes, lease fencing, transaction
rollback, raw-content separation and private-error suppression. No dependencies,
locks, DB schema/grants or equations changed. No broad local backend,
distinct-UID, browser or actual provider/model smoke was run. Hosted CI for this
functional head is subsequent evidence; the green parent receipt is recorded
in [the prior lookup evidence](api-job-break-even-result-implementation.md).

## Remaining acceptance

The initial ResearchRegistry still returns hold. No new default permits source
selection or manufactures approved data. Signed planning/review, snapshot
adoption, actual provider rights/QC/vintages, independent CLI/isolation/custody/
release, complete API/browser flow and G0–G4 remain required. No broad task or
gate checkbox was promoted. A collected fixture is not agricultural validity,
crop growth, purchased energy, future profit or a crop ranking.
