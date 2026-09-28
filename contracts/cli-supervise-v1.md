# Foreground supervisor command v1

[`app.cli_supervise`](../backend/app/cli_supervise.py) starts the existing
[SupervisorServer](cli-execution-attestation-v1.md#local-supervisor-ipc-candidate)
from an operator-controlled, zero-argument Python application factory:

```sh
python -m app.cli_supervise --factory deployment.supervisor:create_server
```

The module must be installed trusted application code; the factory must return
the concrete SupervisorServer. `deployment.supervisor` above is an integration
example, not a supplied deployment. A real provisioner still has to construct
the trusted DecisionContract, scoped store, authenticated LOGIN v2 policy,
content policy, socket/peer/tenant binding, private key, CLI credentials and
execution pins. The command creates no roles, keys, credentials, directories,
approvals or release evidence and accepts no request/job/argv/model overrides.
Existing constructor, RPC, signature and cleanup rules remain authoritative.

Factory selection is executable configuration with full service privileges.
It must never come from an HTTP request, job input, model output or third-party
text. Protect the code/import path and service configuration before launching;
this command neither sandboxes the factory nor proves its custody. Factories
must avoid printing credentials, raw data or driver exceptions themselves.

The command stays in the foreground. Omit `--max-sessions` for the existing
unbounded service loop, or supply a positive integer for a bounded verification
run. Successful completion emits no output and returns 0. Native `--help`
prints static usage without constructing a factory. Startup/argument/import/
factory/type failures return 2 and only the fixed stderr JSON code
`supervisor_startup_rejected`; service exceptions return 3 with
`supervisor_service_failed`. Both envelopes carry `version: 1, ok: false`.
No automatic restart or retry is performed. Existing SIGTERM handling unwinds
the server, removes its owned socket and reaps an active observed child;
SIGKILL/cgroup crash cleanup remains deployment work.

## Evidence and scope

Ten [fresh subprocess tests](../backend/tests/test_cli_supervise.py) cover
version/stop over an actual Unix socket, successful bounded service exit,
SIGTERM cleanup, malformed/missing factory and argument rejection, wrong
return type, suppressed factory exception details and preservation of an
existing socket path. They use a fake CLI and test key with no database/model
execution and cannot establish runtime authentication or gate acceptance.

The hosted [UID service smoke](../research/uid-service-integration-verification.md)
uses a [test-only factory](../backend/tests/uid_supervisor_factory.py) in the
read-only public runtime. It reconstructs the existing synthetic contract and
LOGIN v2/content settings from a supervisor-owned fixture configuration, then
executes this command after dropping UID. The fixture is not a production
bootstrap or a source/claim approval. Authority still runs as a controller
fork, and the fake CLI still shares the supervisor UID/key access. Actual model
execution, independent custody, per-job containment, thermal release and G1/G4
acceptance remain unproved.
