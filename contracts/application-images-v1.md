# Application images v1

Status: image and isolated hosted-test candidates implemented; hosted build/start
acceptance pending. Local web type checking and build passed on 2026-10-03;
the existing large chunk warning remains. Local WSL has no Docker Engine.

## Build targets

The existing `backend-deps` and `web-deps` targets remain the C0 dependency
targets. Explicit `backend-app` and `web-app` targets build the actual current
application. Their final images contain source/schemas/locked environment and
the compiled static web respectively; they do not create operating credentials,
registrations, sources, gate approvals, schemas or releases.

The backend uses the existing pinned Python/uv build, preserving `/app/backend`
and `/app/contracts` for module imports and current calculation file digests.
It includes only explicitly allowed project source/schema files, lock files,
project license and the five immutable synthetic JSON fixtures/manifests. The
venv is copied at its original `/app/.venv` prefix so console-script paths remain
valid; pytest and the builder's uv executable are excluded. The default command
is the existing `app.api_serve` with the protected
`app.operator_config:api_service` factory. Missing operator configuration fails
closed. Other existing foreground commands use this same image explicitly.

The web builder runs the existing locked `npm ci` and `npm run build` (including
type checking) without demo/API/TLS environment switches. Its compile inputs
include test TypeScript needed by the current tsconfig/Vite configuration, but
the final image contains only the generated bundle, license notices and NGINX
configuration. It does not run Vite's development server or serve source tests.

## TLS and process boundary

The web runtime uses the official pinned NGINX image below, UID 11002/GID 11002,
one worker, foreground process, an unprivileged TLS port 8444 and private
ephemeral `/tmp` paths. The backend defaults to UID 11001/GID 11010, disables
bytecode writes and uses unbuffered foreground output. Neither image starts as
root or makes its code/config writable. Compose supplies readonly roots, bounded
tmpfs/resources, private mounts and explicit UID/credential binding separately.

The web needs operator-owned files `/run/operator/web/cert.pem`, `key.pem` and
`api-ca.pem`. It serves the static bundle and proxies `/v1/` and `/openapi.json`
to `https://127.0.0.1:8443` with certificate verification and TLS name `localhost`.
The API certificate must therefore support that DNS name; normal client probes
also require the applicable IP/DNS SAN. Compose must give API and web the same
network namespace while retaining separate filesystems/UIDs. API host remains
loopback, port 8443. The web copies no API signing key, DSN, Bearer token or
private API TLS key. Untrusted forwarded identity headers are removed; the
existing API still derives identity from its Bearer registry.

Proxy buffering, caching and retry are disabled. API Cache-Control passes
through. Access logging is disabled so request paths/private identifiers and
tokens do not become web access records. NGINX emits startup/emergency
diagnostics only; operating metrics/health, certificate rotation, CSP,
browser login/accessibility and public deployment need their
separate operating tests before G4. Missing certificates fail startup; there is
no generated fallback certificate or sample account.

## Build input boundary

The root `.dockerignore` remains an allowlist. It admits application `.py`,
contract schemas/OpenAPI, exact fixture/manifest names and explicit web compile/config/
license files. `.env`, `.git`, `.codex`, credentials, keys/certificates, raw or
private data, venv/node_modules, screenshots, caches and generated outputs are
excluded, including nested copies. Runtime Docker COPY instructions select the
declared inputs rather than copying the repository wholesale.

## Source pin

Official image: `nginx:1.30.5-trixie@sha256:b972f831f200b19ef0767938224f9711e74cd783718738cd7405d5cabf75c442`.
The [official-image source](https://github.com/docker-library/official-images/blob/master/library/nginx)
listed that stable tag. The public OCI index at
`https://registry-1.docker.io/v2/library/nginx/manifests/1.30.5-trixie` was retrieved
at `2026-10-03T00:32:03.220794Z`, HTTP Date `2026-10-03T00:32:03Z`, 10,213 bytes.
Its raw SHA-256 equals the registry's content digest above; the index includes
Linux amd64. The tag listing captured on 2026-10-02 has SHA-256
`1f529936b38963ae7b6b029973b285b5c9fa368c0f51b0b347b59a0736a30104`.
Publication/revision time is not inferred from retrieval/HTTP Date. Local raw
index and metadata are `/tmp/ossf-nginx-1.30.5-trixie-manifest-20261003.json` and
`/tmp/ossf-nginx-1.30.5-trixie-metadata-20261003.json`; no registry token was saved
or printed. The NGINX upstream license and image's OS/transitive licenses must
be retained and checked in the operating license inventory before G4.

Primary references: [Docker multi-stage builds](https://docs.docker.com/build/building/multi-stage/),
[Compose merge rules](https://docs.docker.com/reference/compose-file/merge/),
[NGINX TLS proxy verification](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_ssl_verify),
[official NGINX image](https://hub.docker.com/_/nginx).

## Required acceptance

Validate the allowlist against actual excluded files and inspect the final image
contents, UID, default command and readonly execution. Build both new targets
from an empty hosted runner, type-check/compile the web, verify backend imports
and current code/environment digests, and reject default startup without private
configuration. Actual TLS/Bearer proxy/API/worker start, independent secret mounts,
restart, current grants and resource cleanup are the application-service test.
No image build or synthetic process test alone proves a real product CLI,
independent release, scientific/economic forecast or G0–G4 approval.

[`check-application-images.py`](../scripts/check-application-images.py) builds a
tracked-source temporary context, adds twelve explicit excluded synthetic files,
and checks the actual Docker-exported context. It builds both targets, checks UID,
readonly imports/digests, absent dev tools and closed default startup. It starts
the web with private temporary certificates and checks standard HTTPS static
assets/notices, cache policy, Bearer forwarding, removed forwarded headers and
rejection of a same-CA certificate with the wrong DNS name. That upstream is a
Python HTTPS fixture, explicitly not the authenticated API or a product CLI.
The harness removes its unique containers, image tags and temporary files on
success or failure; shared Docker build cache is retained. The
[application workflow](../.github/workflows/application-runtime.yml) uses a
separate `ci/application-runtime` push branch during development, preserving
the active full backend regression on `chore/bootstrap-c0`. Service acceptance
is still required before checking the umbrella runtime task.
