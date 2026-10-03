# Protected API operator configuration v1

Status: implemented; local software acceptance below. Hosted regression and
deployment credential custody remain pending.

## Invocation and scope

`OSSF_API_CONFIG=/absolute/private/operator.json python -m app.api_serve --factory app.operator_config:api_service`
uses the existing foreground HTTPS entrypoint. `load_api_runtime(path)` returns
an exact existing ApiRuntime; `api_service()` returns its HttpsApiService.
The environment/file are trusted deployment inputs, never HTTP or CLI proposal
fields. Source repositories, verifiers, registry and Bearer identity are supplied
by an explicitly selected trusted dependencies factory. No source, key, grant,
release, account, schema or missing callback is fabricated or provisioned.

## Closed document

UTF-8 JSON has exactly these fields, with no duplicates or non-JSON numbers:

| Field | Meaning |
| --- | --- |
| `config_version` | Exact `operator-api-config-v1` |
| `policy` | All explicit RuntimeLoginPolicy fields below |
| `dsn_file` | Absolute private UTF-8 DSN file, 1–8,192 bytes |
| `artifact_root` | Absolute existing root for the existing artifact policy |
| `certificate` | Absolute certificate path for the existing TLS validator |
| `private_key` | Absolute TLS private-key path for the existing TLS validator |
| `thermal_gate_key_file` | Absolute private raw bytes, 32–4,096 bytes |
| `market_hold_key_file` | Absolute private raw bytes, 32–4,096 bytes |
| `authored_run_gate_key_file` | Explicit null or absolute private raw key path |
| `content_access` | Explicit null or `{owner_uid, reader_gid}` |
| `host` | Exact existing loopback host (`127.0.0.1` or `::1`) |
| `port` | Exact integer 0–65,535, excluding booleans |
| `dependencies_factory` | Trusted `module:callable`, ASCII identifier syntax |

`policy` has exactly `schema`, `owner`, `prefix`, `database`, `connection_limit`,
`market_calculation`, `break_even_calculation`, `market_source_storage`,
`thermal_scenario_storage`, `authored_release_storage`, `authored_run_storage`.
No field is inferred from a filename or current DB state. Existing policy and
ApiRuntimeConfig validators own flag combinations, names, identity and lengths.
`content_access` uses the existing exact ContentAccess contract. Paths are
absolute with no parent traversal; no URL, inline secret/key or arbitrary code
is accepted as a field. An operator file is bounded to 65,536 bytes.

## Private reads and assembly

Configuration, DSN and signing/gate key files must be ordinary files owned by
the effective service UID with exact 0600 permissions, one hard link and no
POSIX access/default ACL. Their containing directory must be owned by that UID
with exact 0700 permissions and no ACL. Every directory component is opened
without following symlinks, using the existing descriptor traversal helper.
The final file is opened relative to that parent with nofollow/nonblocking
flags, so FIFOs/devices and symlink substitution cannot become secret inputs.
The bounded read checks file identity, size, permissions and change times before
and after reading. The loader does not chmod, copy, create or print any secret.

Certificate/private-key paths receive the same component traversal and file
checks before assembly. A certificate may have 0600 or 0644 permissions in its
private parent; a TLS private key requires 0600. Their contents and pairing are
checked by the existing HttpsApiService validator. The existing root/content
policy owns private/group-readable artifacts; no new root is created.

After file/schema/type checks, `dependencies_factory(config=typed_config)` is
called once and must return an exact ApiRuntimeDependencies. It is trusted
deployment code and must protect its own output; module installation/custody
remain deployment requirements. HTTP clients/proposals cannot select it.
The existing ApiRuntime performs actual SCRAM identity/current selected-profile
role audit, artifact validation, provider/principal binding and TLS assembly.
Current request source rights and grant checks remain in the existing stores.

All failures raise only `OperatorConfigHold('operator_config_rejected')` without
paths, DSN/key bytes or provider error text. The existing foreground entrypoint
masks startup failures with `api_startup_rejected`. Typed sensitive fields remain
excluded from repr. There is no live configuration reload; explicit operator
replacement/restart creates a new frozen configuration. Configuration alone
does not authorize a release or any G0–G4 claim.

## Required acceptance

Focused tests must prove closed schemas/duplicates/type/size/path rejection,
actual permissions/symlink/FIFO/hard-link checks, change-during-read refusal,
descriptor cleanup and fixed errors before dependency invocation. Actual
disposable SCRAM and normal TLS/Bearer processes must prove a protected
configuration assembles the existing API and starts/stops, wrong current login/
role/provider bindings are refused, post-start grant drift blocks reads, and
owned processes/DB/roles/password files are cleaned. Synthetic keys/inputs and
shared-UID fixtures are software evidence; independent credential custody,
product CLI/releases/G1, app Compose and G4 remain subsequent acceptance.

## Local software acceptance — 2026-10-02

The implementation and review used the existing Codex CLI session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`. Its turn metadata at
`2026-10-02T07:51:43.460Z` records `gpt-6.1-sol` / `xhigh`; no recursive CLI
was launched. Configuration defaults and this development session do not prove
a product research/review/assessment invocation.

With Python 3.12 and the existing locked backend environment, the focused file
passed **45 tests in 5.61 seconds**, with no skips. The command was run at nice
level 10 with `PYTHONPATH` and both real-CLI smoke switches unset. The existing
local PostgreSQL 16.15 socket and binary directory supplied the test harness;
the harness created a separate disposable SCRAM cluster rather than changing
the persistent development database.

The 39 boundary cases cover closed fields, duplicate/non-JSON/invalid UTF-8 and
oversized input, explicit type/host/path restrictions, real file/directory modes,
symlinks, hard links and a FIFO. Real permission changes, appends, same-size
replacement and unlink during the descriptor read all refuse assembly and
leave no additional file descriptors. Wrong observed owner and POSIX ACL
inspection results use explicit inspection stubs; they do not prove separate
production UID or ACL custody. Missing verifiers, wrong dependency type,
exceptions and `SystemExit` produce the fixed error and no descriptor leak.

Five actual SCRAM assemblies refuse an incorrect login, changed current role
grants, absent source protocol, a MarketSourceStore with a different principal
provider, and invalid TLS private-key material. The grant/login failures occur
before the source factory. An additional separate `app.api_serve` process reads
the private JSON and secret files, assembles the existing runtime, and uses a
real test certificate with normal CA/hostname verification. It proves 401
without Bearer, the exact existing OpenAPI document, accepted research intake
and matching durable job read. A current grant change then produces 503. The
child stops with the existing Uvicorn SIGTERM behavior, has empty stdout and
does not print the token, gate keys, configuration path or passfile details.
The successful pytest return includes disposable database/role/password cleanup;
no owned API child or disposable login cluster remained afterward.

The first combined run had **44 passes and one failure**: the test factory's
research registration used `tenant-a` while its Bearer used `tenant-1`, so intake
correctly returned 422. The fixture now explicitly registers the same synthetic
tenant; runtime scope validation was preserved. The final log is
`/tmp/ossf-operator-config-scram-v2-20261002.log`; the original failed log remains
`/tmp/ossf-operator-config-scram-v1-20261002.log` as local diagnostic history.

Pinned file SHA-256:

| File | SHA-256 |
| --- | --- |
| `backend/app/operator_config.py` | `6cad7d50efda0256b29193219db7aad2d486eb19c672e5d0f685bdf32d2f3be2` |
| `backend/tests/test_operator_config.py` | `9286fb78b32e7c6bb057d5df873a87cc5926b5e6ce9c7cc430599dfb7d71566c` |

This is software assembly evidence with synthetic sources, verifiers, keys and
shared-UID fixtures. It supplies no independent source rights, release, live
product CLI, prediction, crop ranking or G0–G4 approval. No full backend rerun,
separate UID/ACL deployment or application Compose acceptance is claimed here.
