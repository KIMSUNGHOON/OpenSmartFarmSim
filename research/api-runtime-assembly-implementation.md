# Implemented API runtime assembly evidence

Status: authenticated software assembly candidate, not G1/G4 acceptance.

Active Codex CLI thread `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` made this
architecture/interface judgment and implementation. Its selectively inspected
`turn_context` at `2026-09-28T11:26:36.420Z` records exact `gpt-6-sol`/`xhigh`.
No recursive CLI or additional model invocation was made. Reviewable output is
this change and the [assembly contract](../contracts/api-runtime-assembly-v1.md);
it is not independent data, execution or release approval.

Frozen typed configuration/dependencies require explicit v4 authority, artifact
and TLS locations, keys, registries, verifiers, scope and source callbacks.
Sensitive fields/store references are excluded from repr. Assembly checks the
existing artifact root and actual SCRAM/effective grants before source factory
initialization and listening; it provisions no role, schema, password or file.
All six request stores and existing nine routes share `current_principal`.
The market source view preserves the assembled signed hold/context chain even
when the supplied source has same-named methods. JobStore's new opt-in grants
audit is enabled on every assembled connection; its default is unchanged.

## Focused receipts

The new test first failed because the assembly module was absent. Initial typed
configuration/dependency tests passed **18 cases in 0.79 s**. After real DB/process
cases were added, **25 cases passed in 68.44 s** with locked Python 3.12 and local
PostgreSQL 16.15. Further cases cover a wrong content owner, source SystemExit,
and invalid/unbound grant-audit flags. The final combined run over **31 new
assembly cases**, existing HTTPS startup, identity, runtime login, content
access, durable jobs/recovery, job hold HTTP and thermal publisher passed
**224 cases in 134.41 s**, no skips. Exact `app.api_openapi --check` passed.

The actual Python API child uses real ephemeral TLS, Bearer and separate SCRAM
login in the temporary test DB. Its operator fixture seeds signed context/hold,
three market trials, a result and a plan with self-authored source records and
controller-owned test keys. This seeding is test setup, not assembly behavior
or a production fixture default. The source's own hold/context methods throw,
so successful economic/grid reads require the assembled verified chain.

The service returns the unchanged OpenAPI, accepts a registered region, reads
its actual queued job, returns 404 for that unheld job's hold report, reads the
signed market hold and conditional economic/grid results, and returns 404 for
three unpopulated thermal paths from the real ThermalRunStore. The grid retains
`hold` and string Decimal zeroes; economics retains `assumed`/`hold`. A post-start
grant change blocks job reads with 503. The child verifies all stores' actual
runtime binding and identical principal function, absence of request identity
outside requests, and disabled synthetic invocation mode on its JobStore.
Normal SIGTERM exits by signal; output contains no fixture token/private paths.

Startup rejection tests cover wrong identity, effective grants, widened/missing/
symlink artifact roots, bad source interface/exit and wrong content owner.
These tests run under the same local OS UID; they do not attest production
account/key/credential custody. Hosted UID/DAC tests remain separate software
receipts. The prior break-even commit's exact-head CI receipt is recorded in
[its evidence](break-even-read-implementation.md). New hosted verification is
required for this assembly commit.

## Remaining holds

Production source repositories and protected operator configuration provisioning,
independent context/release verifiers and custody, accepted thermal Run in this
assembled process, remaining submission/source/plan orchestration, actual
isolated Codex, public TLS/Compose app wiring, browser/full G1 and G4 remain
incomplete. Requests replay bounded but potentially large trial plans; no load,
latency/SLO or production capacity is asserted. The new module joins the closed
thermal digest and requires a fresh independent release; old immutable sources,
decisions/manifests/releases and economic arithmetic are unchanged. No package
or farm data was adopted. Changed links and staged whitespace are checked before
commit. Whole-task checkboxes remain open pending complete acceptance evidence.
