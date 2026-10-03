# Owned collection to thermal review v1

Status: software connection candidate, not G0/G1/G4 acceptance.

A protected OwnedCollectionReviewService takes only an actual completed owned
collection UUID and an idempotency key. It requires the same audited authority
JobStore, OwnedFixtureRegistry, ThermalRunStore and principal, plus metadata,
artifact, collection_read, collection_review_create, thermal_snapshot_write,
thermal_snapshot_read and decision_context_read scopes. It accepts no source
bytes, paths, URLs, signatures, dates, QC verdicts or model outputs.

The complete collection input/publication/record, original research proof and
owned bundle are reverified. Record timestamps and historical implementation
digests remain metadata, not independent release proof. A preexisting actual
signed decision context must match the collection's context/time/mode/kind and
derived snapshot ID. This service neither signs nor changes a planning event.

The original manifest/weather/thermal bytes form the existing immutable thermal
snapshot candidate. Insertion and collection_review intent admission share one
transaction with full binding/scope checks at commit. No snapshot or queued
review remains after an insertion or final validation fault. Existing identical
snapshots and intents can be reused. Staging a candidate is not G0 adoption.
The protected admission_prepare callback inserts the snapshot before the job row
so the publisher's existing snapshot-before-job chronology remains true. Other
callers retain their existing post-insert admission_action behavior.

The closed owned-collection-review-input-v1 extends the original thermal review
bindings with collection_job_id, collection_attempt, collection_input_sha256
and collection_record_sha256. No raw data enters the job input. The installed
OwnedCollectionReviewContract revalidates the actual completed collection and
snapshot before interpreting a CLI proposal. Its trusted authority resolver
still decides permitted claims/hold; a generated selection cannot grant approval.
Proceed emits the existing thermal review proposal; hold retains server reasons.

ThermalG1Publisher accepts this input only when configured with the exact
collection review service bound to its actual stores. It repeats verification
before its unchanged CLI/execution/release/physics gates. Missing configuration
does not fall back to the legacy input. Legacy review input behavior is retained.

Tests use a fake executable and controller-owned context keys. Actual Codex CLI,
independent planning/isolation/custody/release, snapshot adoption, full browser
flow and G0–G4 remain required. The initial ResearchRegistry remains held.
Operating factories still need stage-aware contract routing for the shared CLI
queue and the complete API/orchestration wiring; no default factory is enabled.
