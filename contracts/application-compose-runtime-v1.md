# Application Compose runtime v1

Status: API/web/deterministic service model candidate; hosted process acceptance
pending. Collection/CLI service orchestration and independent credential custody
remain open, so the umbrella application-runtime task is not complete.

## Explicit model and inputs

Use `docker compose -f compose.yaml -f compose.application.yaml --profile runtime`.
The override requires Compose 2.24.4 or later for explicit replacement/reset
([official merge rules](https://docs.docker.com/reference/compose-file/merge/)).
It preserves the C0 model and dependency targets. Only `db`, `api`, `web` and
`simulation` are enabled by this profile. The original `app` profile still has
deferred collection/CLI placeholders; it is not an operating application.

Required external inputs are `DB_ADMIN_PASSWORD_FILE`, `DB_APP_PASSWORD_FILE`
(the C0 model's legacy file, not mounted in the enabled API/simulation),
`OSSF_API_PRIVATE_DIR`, `OSSF_WEB_PRIVATE_DIR`, `OSSF_SIMULATION_PRIVATE_DIR`,
`OSSF_ARTIFACT_DIR` and `OSSF_SIMULATION_FACTORY`. `OSSF_WEB_PORT` defaults to
8444 on host loopback; zero permits a dynamically allocated CI port.
`OSSF_BACKEND_IMAGE`/`OSSF_WEB_IMAGE` select explicit locally built operator tags;
release image digests/provenance and registry distribution are G4 requirements.
The model neither installs schemas/roles nor initializes trusted source data or
keys. Operators must provision those separately before starting the API.

The API private directory supplies the existing closed `operator.json` pointing
to files inside `/run/operator/api`, an explicit trusted dependency plugin in
`plugins`, and `api-ca.pem` for a normal CA/hostname health probe. The API binds
loopback 8443. Its health check expects the existing unauthenticated 401; this
establishes TLS/process readiness, not database/source rights or scientific gates.
Web shares its network namespace and serves TLS 8444, the only host published
application port. Its private mount contains only web cert/key and API CA.
Actual HTTPS requests must verify readiness and upstream behavior.

Simulation loads one trusted factory via the existing deterministic foreground
entrypoint. It must validate its protected files, tenant, current runtime role
and existing worker/store bindings. No UUID or HTTP input chooses the factory.
Missing/rejected configuration exits without generating defaults. Collection
and actual isolated Codex research/review/assessment consumers remain subsequent
service work; a test harness must never recursively launch the current CLI.

## Ownership and bounds

API/simulation currently require the existing artifact writer UID 11001/GID11010;
they are separate processes and mounts but share one authority class. This is
explicitly not proof of independent writer credentials, release custody or G4.
Web uses UID/GID11002 and mounts no artifacts, DSN, gate keys or Bearer records.
Private directories/files follow the existing owner 0700/0600 contracts; the
artifact directory must already satisfy the selected ContentAccess policy.
Bind mounts refuse automatic host-directory creation. Roots and operator mounts
are readonly; artifacts are writable only in the writer services.

Processes have no added capabilities, no-new-privileges, PID limits and bounded
non-executable temporary mounts. DB/API/simulation/web memory limits are
512/768/768/128 MiB; CPU bounds are 0.5/0.5/1/0.25. Logs use bounded local rotation.
Restart is explicit and graceful stop is 30 seconds; long active attempts may
need existing lease recovery after force termination. WSL receives no new daemon
or automatic Docker installation. These are initial bounds requiring hosted
verification, not production throughput/cost/availability commitments.

## Software acceptance

Build and start actual application images and a fresh SCRAM PostgreSQL, use
synthetic source records/keys only, then prove normal TLS/Bearer HTTP intake,
automatic economic completion without a UUID argument, current result lookup,
same completed result after API/worker restart, and current grant drift refusal.
Inspect actual UID/readonly/resource settings and private mount exclusions.
On success or failure, stop processes and remove the test's volumes, roles,
password files and image tags; never prune unrelated host resources. Separate
credentials/UID deployment for the remaining CLI/collection boundaries,
production health/restore/rotation and actual product CLI/independent release
must remain holds until their corresponding acceptance evidence exists.
