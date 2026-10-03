# Authored farm review admission implementation

Date: 2026-09-30 KST. Internal software candidate under the
[authored review contract](../contracts/farm-authored-review-v1.md). The
development session's `2026-09-29T22:31:28.977Z` `turn_context` records
`gpt-6-sol` and `xhigh` in
`rollout-2026-09-27T10-04-50-01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc.jsonl`.
No recursive Codex CLI process was launched for this increment.

`FarmAuthoredReviewService` requires the exact owned authoring authority and
checks review-create plus all existing farm read scopes. It rereads the
registered source/context/economic pins and rights, recomputes the complete
authored trajectory, and records the source/registration/numeric/code and both
trace hashes as a canonical `collection_review` intent. A commit guard repeats
the current preparation. Its CLI contract redoes current validation for the
job and accepts only software-scope, no-claim proposals; a `proceed` artifact
binds the exact input and trajectory hashes. The user's rights declaration is
represented as a digest, not independent rights approval. Coordinates, farm
numeric records and restricted raw bytes do not enter the CLI job input.

## Focused verification

With the isolated local SCRAM PostgreSQL test database,
`uv run --locked --group dev pytest -q tests/test_farm_authored_review.py`
passed **1 in 219.49 s**. The test registered an owned authored farm, prepared
and admitted the review, retried the same key, verified stored job bytes,
exercised server CLI proceed and unsupported-claim rejection, confirmed no Run,
and held on missing review-create scope and revoked current source rights.
Synthetic source/context keys and direct proposal bytes were used; no runtime
CLI process was started. The slow multi-revalidation path is not a web latency
or load acceptance result.

The existing accepted fixture publisher and Run store were unchanged. The
authored route still needs operator runtime assembly and actual product CLI
capture, an independent reviewer and authored snapshot release, complete
code/environment proof, worker transaction and 3D projection. G1 and
G0/G2/G3/G4 remain held where their evidence is absent.

## Shared CLI route increment

The development session's `2026-09-29T22:52:25.972Z` `turn_context` again
records `gpt-6-sol` with `xhigh`; no recursive CLI was launched.

The optional `OwnedCliContractRouter` entry dispatches the authored review
version to `FarmAuthoredReviewContract`. Its installation checks exact identity
of owned research, source collection review, JobStore, signed context/thermal
store, candidate source and farm Assessment selection. The existing routes
remain the default when this service is absent; runtime swapping holds.

The same actual isolated SCRAM test was rerun with a coherent review/Assessment
assembly and router selection: **1 passed in 301.89 s**. It compared direct and
routed proposal artifacts. The legacy invalid-router-configuration focus
passed **2 in 0.63 s**. Neither check invoked the Codex executable; no
operator runtime factory, independent CLI containment/release or accepted
authored Run was installed. The five-minute fixture path requires asynchronous
product admission and a separate latency/load assessment before web use.
