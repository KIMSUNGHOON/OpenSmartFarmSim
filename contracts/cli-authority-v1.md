# Foreground authority command v1

[`app.cli_authority`](../backend/app/cli_authority.py) starts the existing
[AuthorityServer](authority-rpc-v1.md) from an operator-controlled zero-argument
Python application factory:

```sh
python -m app.cli_authority --factory deployment.authority:create_server
```

The factory must return the concrete AuthorityServer. The example deployment
module is not supplied. A real provisioner must construct the trusted contract/
evidence policy, scoped store and authenticated DB profile, supervisor client,
public verification key/pins, content policy and fixed socket/peer/tenant scope.
General callers cannot select those settings. The command provisions no roles,
credentials, key, data approval, gate or release evidence, and preserves the
existing CliWorker production isolation guard. The test factory explicitly
uses `synthetic_smoke=True`; it is not a production bootstrap.

Factory selection/import paths are privileged executable configuration. They
must be operator-controlled application code and must never be derived from
an HTTP request, job input, model output or third-party data. This entrypoint
does not sandbox or validate the factory's own code/logging; the provisioner
must protect code/configuration and keep secrets out of factory output.

The process stays in the foreground. `--max-sessions` accepts a positive integer
for bounded verification; omit it for the existing service loop. Exit 0 emits
no output. Startup/argument/import/factory/type rejection returns 2 with only
`{"version":1,"ok":false,"code":"authority_startup_rejected"}` on stderr.
Service exceptions return 3 with the same envelope and
`authority_service_failed`; this includes failed DB role admission before
listening. Existing SIGTERM cleanup removes the owned socket and closes a
supervised session. No automatic restart/retry is added; accepted durable jobs
retain the [RPC recovery rules](authority-rpc-v1.md#waiting-cancellation-and-recovery).
Static `--help` constructs no factory. SIGKILL/cgroup crash cleanup and
independent operational control remain deployment requirements.

## Evidence and limits

Thirteen [focused tests](../backend/tests/test_cli_authority.py) exercise a fresh
application process with real SCRAM authority/supervisor DB profiles for all
three AI stages, validated success/hold and durable references; idle SIGTERM
cleanup; wrong-profile admission and preservation of an existing socket path;
and fixed argument/import/factory errors without exception details. They use
a fake CLI/test key and the same local OS UID, so they do not prove service
custody, actual model execution or G1/G4.

The hosted [UID smoke](../research/uid-service-integration-verification.md)
uses a [test-only authority factory](../backend/tests/uid_authority_factory.py)
after directly execing the command under UID 11001. Its private fixture config
contains its DB passfile reference, scoped settings and the public test key,
not the supervisor's private key or credentials. Authority, supervisor and
dispatcher commands now load code/settings in fresh address spaces. The root
controller still owns all fixture secrets, and the fake CLI shares supervisor
UID/private-file access. Actual per-job containment, runtime model execution,
independent deployment/custody and thermal release/G1/G4 remain unproved.
