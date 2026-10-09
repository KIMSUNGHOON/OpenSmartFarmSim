# Planning foreground command v1

Status: **software candidate**, extending [planning-rpc-v1](planning-rpc-v1.md).

```sh
python -m app.cli_plan --factory deployment.planning:create_server
```

The operator-controlled zero-argument factory must return the concrete
PlanningServer with its protected socket, fixed tenant/peer, authenticated
planning writer, private signing key and trusted immutable snapshot lookup.
The example deployment module is not installed. Factory code/configuration is
privileged application code, never derived from HTTP input, jobs, model output
or source data. The command does not sandbox factory imports/logging, provision
credentials, select a model, approve sources or issue a release.

`--max-sessions` optionally sets a positive bound for verification; otherwise
the service remains in the foreground. No credential, key, DSN, snapshot or D
argument is exposed. Static `--help` constructs no factory. Normal exit emits
no output; SIGTERM uses the existing service cleanup. Startup/argument/import/
factory/type rejection exits 2 with only
`{"version":1,"ok":false,"code":"planning_startup_rejected"}` on stderr.
Service errors exit 3 with `planning_service_failed` in the same envelope,
including failed writer admission before listening. Existing socket paths are
preserved. There is no restart or issuance retry policy.

## Authenticated downstream context storage

ThermalRunStore accepts `runtime_identity=(RuntimeLoginPolicy, "authority")`
for the existing closed 18-table job schema. Each bound connection enforces
SCRAM, explicit matching login/database and the complete existing grant audit.
Wrong profiles, wrong DSNs and changed grants hold; it never falls back to the
unbound connection path. No new database privilege is granted. The unbound
constructor remains available for explicit operator/software fixture use,
and supplies no operating custody evidence.

This permits the planner's public reader to validate a receipt while the
separate job authority stores that same signed context and queues collection
review. Planning event, context and queue commits are separate; the original
RPC uncertainty/recovery rules remain mandatory.

## Evidence and limits

[Command tests](../backend/tests/test_cli_plan.py) cover fresh process issuance,
SIGTERM, wrong-login/existing-path admission, fixed startup failures/static help
and a fresh client that uses real planning reader/job authority logins to store
actual/hypothetical contexts and queue their exact review inputs.
[Store tests](../backend/tests/test_thermal_login.py) check login identity,
immutable snapshot access, unsupported/wrong profiles and grant drift.
Local tests share one OS UID and test keys.

The explicit [root UID smoke](../backend/tests/uid_planning_smoke.py) runs the
planner under UID 11005 and its caller under UID 11001 with direct exec, narrow
environments and distinct private passfiles. UID 11004 has socket-group access
but must fail peer authorization. Private planning and caller files must be
denied in both directions; two verified contexts and queued inputs must persist.
It requires the hosted root controller and readable copied runtime. The
controller still owns all fixture keys; the registered fixture snapshot lookup
is test assembly. This is not independent deployment custody, database row
isolation, actual Codex execution, independent release or G1/G4 acceptance.
