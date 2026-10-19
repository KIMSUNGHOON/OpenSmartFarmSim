# Verified Solar input binding metadata — v1

Status: locally accepted with [88 final-source focused checks and product ABBA](../research/solar-input-binding-metadata-20261019.md).
Independent64 throughput, deployment and G0–G4 remain unaccepted.

`VerifiedSolarInputEvidence.binding_metadata` exposes only program ID, period,
context/time-binding/initial-state hashes, model identity, review and provenance.
The authority constructs its immutable canonical bytes after every existing
signature, schema, review, current-file and software-pin verification succeeds.
The getter checks the authority token and returns a fresh decoded object.
It is a snapshot of this verification, with no rights or gate approval.

The original immutable full record and `record` getter remain available with
their original meaning. No verification outcome, permission or authority result
is reused by later `verify` calls. The farm binding consumer still verifies on
each call, checks program identity, and preserves its original closed output.
Only its redundant full-record and whole-receipt JSON reads are replaced.

Acceptance requires exact old/new binding metadata, independent full-record
checks, mutation/token/bounds rejection, current source/review/rights and code
changes, original worker/query outputs/UTC and same-source paired cost. Keep
the original independent64/chunk1/360-second and deployment gates separate.
