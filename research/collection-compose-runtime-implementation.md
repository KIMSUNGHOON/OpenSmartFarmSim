# Owned collector Compose acceptance — 2026-10-04

Status: deterministic owned collector service assembly passed hosted software
acceptance. The [contract](../contracts/collection-compose-runtime-v1.md) and
[local consumer evidence](collection-consumer-implementation.md) define the scope.
No source approval, actual product model execution or G0–G4 gate is accepted.

Implementation/review used the existing Codex CLI `gpt-6.1-sol` / `xhigh` session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`, turn metadata
`2026-10-04T00:48:34.512Z`. No recursive real CLI was launched. The private
fixture executes the existing self-authored fake CLI; the image contains no
pytest, provider approval or private fixture.

## Counterexamples retained

- [b2c8b66 run](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37170157222)
  passed baseline API/economic Compose but failed parent seed with
  `evidence_scope_mismatch`. Its reused fixture grants named another tenant.
  Correcting only the private fixture's tenant reproduced RED1/11.00s and
  GREEN1/11.49s against actual disposable SCRAM. The immutable logs are
  `/tmp/ossf-application-collection-fixture-original-red-20261004.log` and
  `/tmp/ossf-application-collection-fixture-green-20261004.log`.
- [4bfffc3 run](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37170789428)
  completed actual HTTPS ingestion and automatic collection of three original
  synthetic sources, then failed the harness mount lookup. The service name is
  `collector` but its protected mount is `/run/operator/collection`. The lookup
  was corrected; no process permissions were relaxed. Failure cleanup passed.

## Accepted actual stage

[Run37171393930](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37171393930)
at `098d1d3bb9bc453e7efbf89e16e33697f0fa19e4`, job111344879658, passed image checks,
baseline API/economic Compose and the complete separate `--collection` stage:

- Standard TLS/Bearer HTTP ingestion discovers and publishes once without a
  manually supplied worker UUID; the current original record has three sources
  and remains `software_fixture_only`, Assessment hold/G0/G1 not accepted.
- Actual collector UID11001:GID11010, readonly root/private mount, writer
  artifact mount, PID64, CPU0.5 and256MiB memory are inspected. API/simulation
  share its existing writer authority; this is not independent custody.
- Stop/start preserves the same current job, record and single attempt. Parent
  retained proof withdrawal makes new ingestion422. Current role grant drift
  makes the API503 and collector exit3 with its fixed unresolved error.
- Owned services, volumes, scoped roles/schema, credentials/private files and
  image tags are removed. Baseline API/economic restart/current-result and
  grant-denial checks pass separately in the same run.

The overall workflow **failed** at the later `--authority` stage. That failure
does not constitute authority acceptance or whole-head regression acceptance.
The collector stage ended successfully with cleanup at02:37:28UTC; the later
authority failure also recorded cleanup. Local Docker execution was not run:
WSL has no Docker daemon. Local Compose5.5.1 normalization/embedded-code syntax
and whitespace passed; these are separate from the hosted execution proof.

Raw combined job log: `/tmp/ossf-ci-runtime-098d1d3-111344879658-20261004.log`,
28,253bytes, SHA-256
`a1b601c4ead7f7f16e071cc7aa1aaa5b96a457fa4f21d3a09688ebdf8b9137d2`.
Terminal metadata: `/tmp/ossf-ci-runtime-098d1d3-terminal-20261004.json`.
Backend image ID is
`sha256:3651a7eb737b77bb162cedcc9d5519d3cbfc9f92df3b6dca17937aa3f8c48495`;
web is `sha256:ffa08acbcf1dbe81a7a7a7ecd3439efce15da5baffed4b9e08918e729a290e0c`.
These are disposable image IDs, not registry/G4 release digests.

| Accepted file | SHA-256 |
| --- | --- |
| `compose.collection.yaml` | `987cb0d3fcf3a5f618f40d9b11210b8e09d501d9dca43cde4e55d8c136f0539b` |
| `scripts/application-collection-fixture.py` | `bae35b341d4460b825450d74a7a89bf0c85872371d0f43bd3dcc73cf8eefbfa9` |

Actual product CLI, source rights/independent release, successful general
regional source research and collection review/assessment orchestration remain
held. Full regression for the newer service candidate is still pending.
