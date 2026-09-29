# Authored farm release verifier increment

Date: 2026-09-30 KST. The development session uses Codex CLI `gpt-6-sol` at `xhigh`; no nested CLI process was started. This increment follows the [release verification contract](../contracts/farm-authored-release-v1.md).

`AuthoredReleaseVerifier` builds a review request from the current completed job proof and full current server code/schema/lock hashes. It verifies a distinct reviewer Ed25519 key, canonical signed release/evidence/report bytes, chronological review and issuance, and each report's retained referenced bytes. It returns a packet, not a source approval, snapshot release row or Run. The completed-proof handoff now includes farm, numeric, rights declaration, source and context timing pins so the reviewer request does not rely on implicit lookup for those identities.

Focused verification:

- Pure synthetic reviewer test: `uv run --locked --group dev pytest -q tests/test_farm_authored_release.py` — **1 passed in 0.40 s**. It rejects wrong registration, forged signature, changed report, missing referenced evidence, changed server code and a reviewer key reused from the CLI observer. Its proof and reviewer are test doubles.
- Actual isolated local SCRAM PostgreSQL review completion regression: `uv run --locked --group dev pytest -q tests/test_farm_authored_review.py -k completion_requires_signed_attestation` with the local test DSN — **1 passed, 1 deselected in 240.86 s**. It verifies the expanded handoff after an actual stored worker completion using a fake CLI and synthetic attestation key.

No independent reviewer signed a real release; no product Codex CLI was invoked in this increment. The source references in the pure test are synthetic byte strings. The test does not prove agricultural quality, rights for external data, deployment isolation or G1/G4. The next dependency is an externally issued, retained release packet and an authored publisher/worker that rechecks it with complete runtime custody before creating any accepted Run.
