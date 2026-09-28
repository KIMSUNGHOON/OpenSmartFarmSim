# Distinct UID service integration smoke

This verifies the existing RPC, LOGIN v2 and content-access contracts together.
It introduces no production policy, executable allowlist, credentials or release
approval. The [explicit test file](../backend/tests/uid_service_smoke.py) is outside
ordinary pytest discovery because it requires a disposable root controller.
It must pass as a separate hosted invocation; collection is not execution proof.
CI installs the same locked Python 3.12.13/packages in a bounded public code-only
runtime under `/tmp/ossf-uid-runtime-RUN-ATTEMPT`, with others' write permission
removed. Package copying avoids changing shared cache inode permissions. This
runtime contains no credential/key files and is removed in always-run cleanup.
Services exercise a date-parser operation after dropping UID; controller
preloads alone are not enough to establish readable interpreter/library code.

## Tested boundary

| Process | Real/effective/saved UID | Primary GID | Supplementary groups | Configured access |
| --- | --- | --- | --- | --- |
| authority | 11001 | 11012 | 11010, 11011 | Authority SCRAM profile; content writer; supervisor client |
| supervisor and fake executable | 11002 | 11011 | 11010 | Read-only SCRAM profile; content reader; private test key |
| general dispatcher | 11003 | 11012 | none | Authority socket and result references only |

The root controller creates no system users/groups and edits no operating
configuration. It refuses assigned probe UIDs, drops and checks all UID/GID
identities, clears the inherited process environment, sets each private HOME
with a fixed PATH/LANG, and uses existing forced
SCRAM connections. The two service credential files and key remain in separately
owned `0700` directories/`0600` files. Socket directories are owner-controlled
`0750`; sockets use the existing `0660` policy and Linux peer checks. The
synthetic ancestor is readable/searchable so descriptor traversal can work.

Each research, collection-review and assessment case runs separate foreground
authority and supervisor processes and an actual exec of the fake CLI. The
executable records its UID/GID/groups in its private fixture home. Research and
collection review exercise fixture-authorized success; assessment exercises the
existing evidence-missing hold. Root readback checks durable state, signed
capture/decision references, process exit, foreign-tenant queue preservation and
socket cleanup.

The general dispatcher now launches the application [command v1](../contracts/cli-dispatch-v1.md)
as a fresh exec from the pinned public runtime's read-only code/schema copy.
Only socket/peer/tenant/wait arguments and HOME/PATH/LANG are supplied. Its
address space no longer contains the controller's inherited credential/key
memory. Authority and supervisor remain forks, so this change does not establish
independent control of those services or production containment.

Negative probes connect with socket group permission but an unapproved UID:
the supervisor rejects the general worker, and authority rejects UID 11004.
The ordinary dispatcher has no supervisor socket access, private credential/key
access or content access. Authority cannot open the supervisor key; supervisor
cannot open the authority credential file. Fixed error diagnostics contain
exception class/errno, internal probe codes or validated WorkResult states/reasons,
excluding driver messages, prompts and raw outputs.
All test processes are bounded and reaped, and owned temporary files/DB roles
are removed by the existing fixture teardown.

## Limits

This is software integration evidence under actual Linux UIDs and authenticated
test database users. It is not independent secret custody: trusted forks inherit
controller memory, and the controller owns every fixture credential/key. The
fake executable shares the supervisor UID and can read its files. No per-job
container, distinct CLI UID, readonly deployment mount, egress restriction,
actual model call, operating-account authorization, immutable release identity,
thermal release, G1 or G4 acceptance follows. Production isolation remains
closed by the existing CliWorker constructor guard.

The general command's fresh exec replaces only its own forked address space;
the surrounding root probe and both trusted services retain the limitations above.

## Verification procedure

The [backend CI](../.github/workflows/backend-tests.yml) uses its disposable
PostgreSQL 18 instance before ordinary regression tests, exposing smoke failures
without waiting for the full suite. It passes only the
explicit test DSN and private admin passfile path to the root test controller:

```sh
sudo -- env OSSF_TEST_PG_DSN="$OSSF_TEST_PG_DSN" PGPASSFILE="$PGPASSFILE" \
  "$uid_runtime/venv/bin/python" -B -m pytest -p no:cacheprovider -q -s tests/uid_service_smoke.py
```

The evidence is a terminal hosted result with three passing cases and the fixed
`Distinct UID service smoke passed` stage messages. The local account cannot
drop into these UIDs; only collection of the three cases and the existing
same-UID real-SCRAM service regression (six passed) were run locally.
Root pytest disables bytecode and its cache plugin so it does not create
root-owned caches in the checkout used by the subsequent ordinary test runner.

The first hosted attempt stopped at service startup with a RolePolicyHold.
Inspection of the installed Psycopg 3.3.6 `ConnectionInfo.get_parameters` found
that it calls `Path.home()` when computing default passfile values. A local
reproduction with HOME absent and an unknown passwd UID raises RuntimeError;
an explicit HOME resolves it. The fixture now supplies the appropriate private
home without restoring inherited credentials or broad environment variables.
It also uses the root controller's internal SQL helper to verify the foreign
tenant queue, retaining the ordinary metadata API's tenant denial.

Later hosted failures were narrowed using only the validated WorkResult state
and reason. The generic worker setup failure disappeared with the public pinned
runtime and UID-side date-parser operation; its masked underlying exception was
not retained. The assessment path then passed actual service execution, signed
persistence and final hold. Research/collection readback still failed because
the fixture referenced a nonexistent attestation `decision_id`. Readback now
uses the durable decision list, compares its output hash with the signed final
hash, and matches publication to that durable decision ID.

The previous service version at commit `fe8df7f` passed [backend CI run
36383044589](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36383044589):
three UID service cases in 7.66 seconds, 1,190 ordinary tests in 247.19 seconds
with two preexisting warnings, and the UID DAC smoke. The three fixed stage
messages occurred at `2026-09-28T05:42:34Z`–`05:42:38Z`. This is the original
forked-dispatcher scope; the new application command/fresh-exec change requires
its own terminal hosted verification.
