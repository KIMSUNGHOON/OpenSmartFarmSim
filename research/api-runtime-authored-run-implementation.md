# Standard HTTPS authored Run assembly implementation

Date: 2026-09-30 KST. Scope: [assembly contract](../contracts/api-runtime-authored-run-v1.md).
This is the existing Codex CLI session with `gpt-6-sol` and `xhigh`; no
nested CLI was launched. The exact current model/effort is the AGENTS.md
design and research requirement, while the tests below are software evidence.

The existing `ApiRuntime` now accepts a separate optional authored Run gate
key and trusted operator factory. A one-sided pair or a profile without v8
authored storage fails before invoking the source factory. With both present,
the runtime requires its own stored farm selection and owned research, then
passes the exact job/farm services and configured key to the factory. It
accepts only an exact `AuthoredRunStore` bound to those services and the key;
the app receives that store through its existing authenticated authored read
routes. With no option, the former unavailable route is preserved.

The factory is the trusted operator boundary for independent reviewer keys,
execution proof, evidence resolver, code root and current authored release.
Runtime assembly does not issue or approve a release. The synthetic integration
test deliberately replaces the preparer's authority method and is only a
software test of a previously stored synthetic Run, SCRAM, HTTPS, Bearer,
tenant/scope denial and stale-evidence hold. It must not be used as independent
release or G1 proof.

Local `uv run --locked --group dev pytest -q -rs tests/test_api_runtime.py
tests/test_api_authored_runtime.py` reported **31 passed, 10 skipped**. The
skips include the new stored-Run HTTPS integration because
`OSSF_TEST_PG_DSN` is absent and this workspace has no PostgreSQL or Docker
binary. Python compilation and `git diff --check` passed. The hosted backend
workflow has a PostgreSQL/SCRAM environment; its result for this commit must
be checked before treating the integration as verified. No authored browser
request against this standard HTTPS runtime was run here.

An explicit [authored browser smoke](../backend/tests/web_authored_thermal_replay_smoke.py)
now connects the stored Run through the standard TLS API and Vite HTTPS proxy
to Chromium. It reuses the existing read-only browser comparator for 120
points, scene/chart/table identity, narrow viewports, and console/network
checks, selecting the authored mode and expecting three successful Run GETs.
The backend workflow installs locked Node/Chromium dependencies and runs this
smoke with its disposable PostgreSQL. It skipped locally for the same missing
database setting; CI has not yet supplied passing evidence for this addition.

Product CLI execution, actual independent release issuance, complete farm
input authoring and G1/G4 are still holds. Real source G0, local G2 and future
G3a/G3b need their separate evidence.
