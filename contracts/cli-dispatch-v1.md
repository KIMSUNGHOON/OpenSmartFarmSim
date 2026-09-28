# General dispatcher command v1

[`app.cli_dispatch`](../backend/app/cli_dispatch.py) is an application entrypoint
for the existing [authority RPC](authority-rpc-v1.md). It constructs one
AuthorityClient and invokes `run_once` exactly once. It provisions no database,
credentials, key, authority/supervisor server or gate approval.

```sh
python -m app.cli_dispatch \
  --socket /run/ossf/authority/rpc \
  --authority-uid 11001 \
  --tenant tenant-a \
  --wait-seconds 660
```

The endpoint must be absolute. UID, tenant and wait validation remain those of
AuthorityClient; wait defaults to 660 seconds and is bounded 1–660. The provisioner
must supply the fixed endpoint/peer/tenant binding and filesystem socket group.
There are no job, stage, input, model, executable, DSN or private-key arguments.
The wire request remains exactly `{"version":1,"op":"run_next"}`. Both peers,
reply tenant/version, strict frame and result-field checks remain in AuthorityClient.

## Output and exit codes

| Exit | Stream | Meaning |
| --- | --- | --- |
| 0 | stdout, one JSON line | A validated authority reply. `result: null` means no eligible job. Otherwise it carries only job/attempt/state/reason/capture/decision references. |
| 2 | stderr, fixed JSON | Configuration rejected before dispatch: `dispatcher_configuration_rejected`. |
| 3 | stderr, fixed JSON | Exchange unresolved: `authority_dispatch_unresolved`. |

Successful output mirrors the existing RPC envelope with UUIDs encoded as
canonical strings. It is not a public farm assessment, output dataset or gate
decision. Exit 0 also covers known hold, failed, canceled, queued and unclosed job
states; automation must inspect `result.state`. Empty queue is a successful
exchange, not a completed farm simulation.

Argument errors omit parser details, and unresolved errors omit endpoint paths,
driver messages and raw replies. Unexpected/invalid credential-like arguments
are never echoed. JSON escapes control characters. `--help` prints static usage
and exits 0; it performs no RPC call.

There is no retry loop. An unresolved response or interrupted dispatcher does
not cancel an accepted durable job. It may already have completed; use the
authorized status/recovery path before dispatching again. In particular, a wrong
expected tenant can be rejected after the server has executed its own fixed
tenant dispatch. This command retains the original RPC recovery semantics.

## Verification scope

[Seventeen subprocess/Unix-socket tests](../backend/tests/test_cli_dispatch.py)
cover null queue and all six result states, one exact request, lost/malformed/
changed-tenant replies, wrong peer UID, no retries, wait/UID/argument rejection
without argument echo, and unavailable endpoint errors without path details.
They run no database/model call and make no farm/G1/G4 claim.

The [root service smoke](../research/uid-service-integration-verification.md)
now executes this command using the pinned public Python environment and a
read-only copy of application code/schema. The child receives only scope
arguments and HOME/PATH/LANG; exec replaces the controller fork's memory. Its
real UID is admitted by the existing authority peer check. The surrounding
probe also denies private credential/key, supervisor socket and content access.
Authority/supervisor still run controller forks with a fake CLI/test key, so
independent service/secret control, real model execution and G1/G4 remain unproved.
