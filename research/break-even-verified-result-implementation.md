# Completed break-even verification result implementation

Date: 2026-10-01 (Asia/Seoul). Development CLI: `gpt-6.1-sol` / `xhigh`.
Scope: internal current-dependency result reader after the
[asynchronous verifier](break-even-verification-implementation.md). The
[contract](../contracts/break-even-verified-result-v1.md) retains all outstanding
HTTP/web/load and independent gate requirements.

## Implemented behavior

The service resolves the actual completed verification Job, canonical input,
publication, attempt and bounded receipt, and the actual tenant-private evidence
bytes. All hashes, sizes, exact fields, code/environment and trial counts must
agree. Current parent calculation metadata is revalidated before and after
dependency reading. The actual immutable result row matches that parent and
the evidence covers the plan's complete candidate set.

The stored server-produced evidence inventory is rechecked through actual current
stores. Candidate/scenario/numeric/source descriptors use one authenticated,
audited market connection, invoking the same existing row/job-input/manifest
validators. Those stores' ordinary reads now use the extracted transaction
helpers too. Hold/current-scope/context and plan descriptors retain their original
verified store calls. Every descriptor is read fresh; nothing is cached across
requests. Principal/scopes/provider bindings are checked around each descriptor,
and the complete current role audit repeats before the shared connection closes.
Implementation/environment are checked before/after the full read.

The projection keeps existing Decimal-derived server strings/null, conditional
user assumptions, unavailable-market context and Assessment hold. Reading needs
read scopes only and performs no market, ledger or break-even arithmetic. Legacy
synchronous readers still replay their engines. Both new modules are in the
runtime code inventory; no dependency, schema, grant, formula, size limit or
request deadline changed.

## Verification history

One heavy local process at a time under `nice -n10`, PostgreSQL 16.15, actual SCRAM
stores, synthetic inputs and test signing keys; real model smoke flags unset.

- The first selection stopped with **3 passed, 1 failed in 256.40 s**. The
  incomplete-candidate evidence test replaced publication/artifact methods for
  every UUID, accidentally altering the parent calculation's receipt too. The
  reader correctly rejected that parent before candidate coverage was reached.
  The test now targets only the verification UUID and preserves actual parent
  methods. This is a test setup correction; no runtime check was relaxed.
- The corrected reader and existing source/candidate round-trip selection gave
  **11 passed, 0 skipped in 575.71 s**: new reader 9 and existing typed-source and
  candidate round-trip 2. Reading matches the existing full-replay projection
  with arithmetic paths disabled and write/execution scopes removed. The shared
  candidate connection count is **1**, source connection count **0**, for that
  actual two-trial read; original hold/context/plan/job connections remain.
  Restarted service reading matches. Pending/wrong model/other-tenant, exact
  receipt/publication corruption, private bytes and incomplete candidates,
  principal withdrawal/provider replacement/changed returns, actual unauthorized
  DELETE grant and implementation changes all withhold results. The seven source
  families and existing numeric candidate revisions round-trip unchanged.
  Earlier partial progress is not added to the passing count.

The tested code digest is
`244c63f2539d32cef3e944980be99eedc6c70e47af83f6ca6b68c7ea70d8db8a`;
the unchanged environment digest is
`e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3`.
The official CI collector observes **2,274 cases in 139 files**, with inventory
SHA-256 `4b86f9bd3d8470d60f1eedaaf8a05882a5731752d92392b01cea02583c1c47b0`.
The six groups contain **313/562/371/452/251/325** cases and their exact union is
the complete default inventory; the existing authored full-path pair retains
its separate workflow. Collection is not execution or hosted acceptance.
Owned temporary PostgreSQL children stopped after the local suite. Baseline
PostgreSQL and unrelated user services remain running.
Local file/anchor checks passed **437 links**. Staged whitespace review detected
an extra EOF blank line in each new application module; the earlier unstaged
check had not included those untracked files. The follow-up removes only those
two blank lines. Current code digest becomes
`63473aa3494683d21bc493e9fb2cd56ad055cebea41090250de0fe9ccbba5b94`;
environment and runtime behavior are unchanged. The 11-test digest above is the
actual tested earlier format; no additional heavy test is claimed for this
whitespace-only correction. Final staged whitespace checks pass.
Review checked server custody/parent and exact receipt/evidence bindings, existing
source resolution/validators, parameterized SQL, fresh scope/provider checks and
the final full role audit. The ongoing development CLI's selected metadata at
`2026-10-01T12:37:05.617Z` confirms `gpt-6.1-sol` / `xhigh`; both configuration
defaults agree. No nested model CLI, private prompt or credential was exported.

## Remaining acceptance

The actual SCRAM reader fixtures have two trials. The memory-provider 256-trial
capacity test is separate. Actual maximum-grid admission/calculation/verification,
current-rights result reading, cancel/retry/withdrawal and unchanged 30-second web
deadline still require their own load evidence. The serializer/inventory limits
are not a throughput claim.

There is no new HTTP endpoint, SDK/web workflow or operator process in this slice.
Private server custody and immutable completed publications are assumed by this
internal read contract; it does not accept arbitrary caller inventories or issue
independent release/CLI/G1/G4 proof. Actual product CLI and G0/G2/G3a/G3b/G4
evidence remain pending. The broader goal and dependent task checkboxes stay open.
