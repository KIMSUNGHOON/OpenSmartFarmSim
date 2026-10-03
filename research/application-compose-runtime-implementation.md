# Application Compose runtime — 2026-10-03

Status: API/web/automatic economic hosted software acceptance passed.
Remaining collection/CLI orchestration and independent writer/credential
custody keep the umbrella runtime task open.

The [contract](../contracts/application-compose-runtime-v1.md) defines the
`runtime` override, explicit private operator inputs, separate processes/mounts,
shared existing artifact writer authority, normal TLS proxy and resource bounds.
API and deterministic worker use the actual unchanged foreground entrypoints,
current SCRAM role audits and existing immutable stores. The image adds no
pytest or synthetic provider; the host harness uses the existing locked test
environment and installs explicitly synthetic code/data only in disposable
private mounts. Context signatures are actually checked with fixture HMAC keys;
the release callback refuses releases. No real CLI is recursively started.

Implementation/review used the existing `gpt-6.1-sol` / `xhigh` Codex CLI session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` (metadata `2026-10-03T00:51:10.130Z`).
The official Compose merge reference was inspected on 2026-10-03; its 2.24.4+
replacement requirement is recorded in the contract. Local Compose5.5.1
normalization, Python imports/private-plugin syntax and whitespace checks passed.
No new WSL daemon, local database mutation, arithmetic or dependency changed.

## Observed failures

- [147c8f6 run](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37123300727)
  failed application creation. Image checks and failure cleanup passed.
- [f673ba1 diagnostic run](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37123694658)
  still failed before app containers existed; no API exception trace was produced.
  Local normalized configuration exposed the unquoted tmpfs flow array as
  `['/tmp:rw','noexec','nosuid','size=32m','mode=1777']`. It was corrected to one
  quoted mount, and actual normalized configuration is asserted before startup.
  These logs do not contain the raw Docker error; the causal diagnosis comes
  from the normalized invalid mount model and subsequent actual startup.
- [d812174 run](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37123876066)
  passed actual app start, standard HTTPS/Bearer OpenAPI/intake, automatic
  economic completion/current result, UID/readonly/private mounts and actual
  CPU/memory limits. The result stayed conditional user arithmetic and Assessment
  hold. Restart then hit `ConnectionRefusedError` before a result comparison.
  The harness now re-reads Docker's dynamic host port after stop/start and waits
  for actual normal HTTPS401 readiness; it does not lengthen the30-second body
  timeout or turn off certificate verification. Failure cleanup again passed.

## Corrected hosted acceptance

[Run 37124064625](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37124064625)
at `7e451a57c83a965ce1e21cf0319854221de05e77` passed both image checks and actual
Compose proof. Actual logs record standard TLS/Bearer intake and automatic
completion/current result; Assessment stays hold with assumed user inputs.
After all three app services stop/start, the completed result is identical.
Current worker-role grant drift then yields503 without returning the result.
Actual readonly roots, private mount exclusions, UID and CPU/memory settings
pass. Test roles/schema are removed after app stop while DB remains alive, then
containers/volumes, private files and image tags are removed; absence of project
containers and volumes is asserted. No other Docker/WSL resource is pruned.

The readonly app image IDs for this hosted run are backend
`sha256:4f2a203c0b16a806ec09146b3828577033903a78d339505acb4253544e5713b1` and web
`sha256:6bc2bd64e917aa61cc18256ca384ad8e1ae28fda899ec77a2aadfa3fde25e36f`.
They are local image IDs, not published registry/G4 release digests.
Raw job log: `/tmp/ossf-ci-runtime-7e451a5-111205723416-20261003.log`, 23,954 bytes,
SHA-256 `1865b5119be332e6875fe13f2e8ee495b51229497a00d7ffb9e5146a61036b32`.
Terminal metadata is `/tmp/ossf-ci-runtime-7e451a5-terminal-20261003.json`.
The three failed logs remain `/tmp/ossf-ci-runtime-HEAD-JOB-20261003.log`.

| File | SHA-256 |
| --- | --- |
| `compose.application.yaml` | `681cc1ed10bceaadcbc2f9ad117d3012de0e23a3779ca4c8d532558c41735316` |
| `scripts/check-application-runtime.py` | `bcf12324906a02550e7a950775daef9d8886bce5bb523d1523fb1ffab7af142f` |
| `.github/workflows/application-runtime.yml` | `66b2486202ed20b2765df42174139380d79a8b9c79734d0d7c3e44ccb1445374` |

Review kept actual source/store/principal bindings, unchanged deterministic
calculation/gate code and real SCRAM. It fixed YAML splitting and host-port
rediscovery, and kept certificate verification/body deadline. Startup diagnostics
contain only process status and exception class/source line, no values. Local
plugin imports/syntax, Compose normalization, links and whitespace passed.

## Remaining acceptance boundary

API/simulation share the existing UID11001/GID11010 writer and authority class;
web UID/GID11002 receives only its own TLS/CA files. This tests actual process
separation and mount minimization, not independent release/credential custody.
DB SCRAM runs over a disposable internal Docker network with the existing local
fixture's `sslmode=disable`; remote DB TLS and G4 operating network proof remain
separate requirements. All source rights, actual product CLI, independent G1,
crop predictions/ranking, maximum concurrent load and G4 remain unchanged holds.
