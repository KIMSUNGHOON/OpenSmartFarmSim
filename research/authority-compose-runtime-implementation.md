# Scoped research RPC Compose candidate — 2026-10-04

Status: actual signed regional hold path observed; full hosted authority
acceptance pending. The [contract](../contracts/authority-compose-runtime-v1.md)
defines the explicit additive factory/process/IPC assembly. The existing exact
Codex CLI session `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` used `gpt-6.1-sol` /
`xhigh`, turn metadata `2026-10-04T00:48:34.512Z`, for implementation/review.
No recursive real model invocation, domain coefficient or gate approval was added.

## Observed failures and focused corrections

| Hosted candidate | Observed boundary |
| --- | --- |
| [098d1d3 /37171393930](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37171393930) | Baseline and full collector stage passed; authority held the research job but expected public validated report was unavailable. Failure cleanup passed. |
| [4083bd6 /37176347196](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37176347196) | Baseline/collector passed. Actual research reason `ai_validated_hold` and two public missing-evidence categories passed; operator inspection failed. Cleanup passed. |
| [bf2cac5 /37176897854](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37176897854) | Baseline/collector passed. Validated public hold and operator signature/capture/invocation inspection passed, as shown by control reaching the subsequent held-parent ingestion assertion. That assertion failed; no final authority event/restart/peer acceptance is claimed. Cleanup passed. |

The first private fixture's evidence policy had four parameters instead of the
existing six-argument `JobStore.append_evidence` callback. Actual disposable
SCRAM reproduced `invocation_evidence_withheld` (RED1/2.55s). Correcting only the
fixture policy produced the original registry's validated hold (GREEN1/2.51s),
not a source approval. The public reason is now asserted before report lookup.

The second inspection expected `disposition`/`capture_id` from the restricted
`list_decisions` metadata projection. A local actual SCRAM/supervisor/signed
inspection reproduced `KeyError: disposition` (RED1/4.09s). The trusted inspection
now reads the immutable decision by tenant/job/attempt, compares its decision ID
to the existing projection, verifies the stored signature and matching capture,
and checks actual invocation model/effort. That same path passed1/3.85s and the
final fixture timing revision passed1/3.77s. An instant local fake child earlier
failed closed with `execution_attestation_unverified` (2.66s); its failure is
retained. The fixture uses the existing supervised tests' `valid_slow` fake mode.
No production observation chronology check or worker guard was weakened.

The third assertion exercised ingestion without `collection_execute` on the
HTTP fixture grant, so it reached scope403 before evaluating the held parent.
Actual SCRAM/signed-regional-hold/ASGI reproduction returned403 (RED1/4.04s).
The private operator fixture now explicitly grants the existing COLLECTION_SCOPES
to this caller. The same authorized request returns422 `collection_hold`
(GREEN1/3.96s). This preserves the separate scope and held-parent checks.
Code review also aligned the rogue supervisor probe with its peer-first protocol:
receive the immediate fixed rejection without first sending an operation.
Actual separate-UID/container proof for these corrections remains pending.

## Preserved evidence

Raw hosted job logs and SHA-256:

- `/tmp/ossf-ci-runtime-098d1d3-111344879658-20261004.log`:
  `a1b601c4ead7f7f16e071cc7aa1aaa5b96a457fa4f21d3a09688ebdf8b9137d2`.
- `/tmp/ossf-ci-runtime-4083bd6-111359628403-20261004.log`:
  `c2e92204b2bb0abe948c9bc72a9e3792cd5a2373ea1c1557b75501f879bb8ca4`.
- `/tmp/ossf-ci-runtime-bf2cac5-111361289829-20261004.log`:
  `12446b89edb7b77853cd7085a69c9717125b578672c9d1c5f582bae1d4551db6`.

Immutable local logs use prefixes
`/tmp/ossf-application-authority-fixture-original-red`,
`fixture-green`, `fixture-fast-child`, `inspection-original-red`,
`inspection-green`, `inspection-final-green`, `ingestion-original-red` and
`ingestion-green`, each ending `-20261004.log`. The original policy RED SHA is
`6d881b7f4c67f033abb99feca3d04979be22430d6ccb5bd2cc8d11af9bbc2c32`;
inspection RED/GREEN are respectively
`39b390a15836ba3a7bedd0d7b21f2b06ba06a4821acd2cf19feb14735662ec9b` and
`b99a1b966523915873c0d30381bc7082273352497c394be1155d58df6d9c0fb6`.
The command's reused output path is not the immutable evidence copy.

Local focused execution uses actual disposable PostgreSQL16.15/SCRAM, actual
Unix supervisor/fake-child processes and real Ed25519 signature verification.
Only host filesystem/UID settings replace container constants; local tests do
not prove separate UID/Docker isolation. Processes/socket/fixture roles/schema/
passfiles/cluster are removed. Python/private-plugin syntax, local Compose5.5.1
normalization and whitespace checks passed; WSL has no local Docker daemon.

## Remaining scope

The synthetic controller owns all keys/accounts. API/authority/simulation share
the writer class; the supervisor's fake child shares its key-owning UID. The
production CliWorker isolation guard remains closed. Local/hosted signed bytes
are software evidence, not actual product Codex calls or independent custody.
Full authority peer/private-file/restart/grant-stop cleanup, subsequent whole-head
regression and general research→collection review/assessment orchestration still
need evidence. Actual source rights/release, G0–G4, crop/forecast/ranking claims
remain held.
