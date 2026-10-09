# Scoped research RPC Compose candidate — 2026-10-04

Status: actual hosted regional research-hold service acceptance passed atb8df8f9.
The [contract](../contracts/authority-compose-runtime-v1.md)
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

## Corrected actual hosted acceptance

[Run37177418837](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37177418837)
at `b8df8f9687d9ee3fadf10bc732a37ddbd277aa8a`, job111362843998, completed
successfully. Its actual image checks and three separate baseline/collection/
authority harness modes passed. This is not a combined seven-service owned
source-success orchestration test.

The authority stage admitted a regional request through normal TLS/Bearer,
automatically dispatched it through the real separate supervisor and preserved
one decision/capture/signed execution. The stored invocation has the exact
model/effort and actual Ed25519 signature/capture identity is checked. The public
registry hold contains the two existing missing-evidence categories. Authorized
ingestion of that held research returns422 `collection_hold`.

Private credential/key/artifact denials and both rogue-UID socket probes passed
before `automatic_scoped_research_hold` was emitted. Actual processes/mounts,
UIDs, readonly/capability/PID64 and CPU/memory settings were inspected:
supervisor11003:11020/512MiB/CPU0.5; authority11001:11010/768MiB/CPU0.5;
dispatcher11004:11030/128MiB/CPU0.25, only readonly authority IPC and no network.
The supervisor has readonly artifacts and its own private mount; authority has
its own private mount and readonly supervisor IPC. Exact socket owners/groups/
0660 readiness and peer checks passed. Same-writer API/simulation are explicit.

After graceful stop, both owned socket paths were absent. Restart created fresh
owned sockets; the same held job/public report and single signed/capture/decision
chain were unchanged. Current role grant drift made API503 and dispatcher exit3
with its fixed unresolved error. Every mode recorded complete container/volume/
scoped-schema-role/password-key/private-file/image-tag cleanup. No WSL daemon
or unrelated host resource was added or pruned.

Raw combined job log: `/tmp/ossf-ci-runtime-b8df8f9-111362843998-20261004.log`,
29,581bytes, SHA-256
`8bafe260870720ac2fb5ef07e9fc6f4bdb6fdf4f63ed5cb743b5aec27b3ae46d`.
Terminal metadata: `/tmp/ossf-ci-runtime-b8df8f9-terminal-20261004.json`.
Actual backend image ID
`sha256:cec4bd6afb40afaaa8bf465b9e572fe41faeddc624646bc14da26118af4dcaae`;
web `sha256:c039e462e45733fd6338eeaa4e48af8ee32ec84565f337636b6edd56193c9d56`.
These are disposable image IDs, not registry/G4 release digests.

| Accepted file | SHA-256 |
| --- | --- |
| `compose.authority.yaml` | `a75a46f5fce5d0332f6758517776a401016018ad9627c8d7d21fbb79423b14d8` |
| `scripts/application-authority-fixture.py` | `76a4e691e1395af2b04808c49813d927c7fcd0e5d620afae8f993c487b810f29` |
| `scripts/check-application-runtime.py` | `f81558b65eb20e20b16cfece1648fe62efd08434bb0e9a8da87039b9faa446fc` |
| `backend/tests/test_application_authority_fixture.py` | `0f51f0c4371272c4e367214ec7ebd1cc4965079eee321e5eee929a87cabbcc0d` |
| `.github/workflows/application-runtime.yml` | `9ff32a2900b92f904118947021c7b28ad6457d1239728510df570813d792286a` |

## Remaining scope

The synthetic controller owns all keys/accounts. API/authority/simulation share
the writer class; the supervisor's fake child shares its key-owning UID. The
production CliWorker isolation guard remains closed. Local/hosted signed bytes
are software evidence, not actual product Codex calls or independent custody.
Subsequent whole-head regression and combined general owned research→collection
review/assessment orchestration still need evidence. Actual source rights/release,
G0–G4, crop/forecast/ranking claims
remain held.
