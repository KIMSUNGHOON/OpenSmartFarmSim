# Harvest request-scoped parent read v1

The full protected summary measured34.619s and failed the existing30s deadline.
This slice changes reader orchestration, never growth/harvest arithmetic or saved data.

## Request scope

`HarvestCurrentQuery.open` retains one normal `CalculationCurrentCycleQuery.open`
for its entire lifetime. That original context performs its unchanged whole input,
result evidence, current farm/row/rights and custody trace checks before yielding
and after all harvest projection/rechecks. It closes before HTTP body emission.
Each internal harvest guard still checks current principal/scopes, signed parent
row equality, current farm registration, rights-policy/resolver/notice bindings,
and current display permission. It returns an independent copy of the scoped
original metadata. No cross-request cache, synthetic query, proxy verifier, or
verification bypass is introduced. A captured callback expires with its context.

Harvest HEAD/root/selected-page hashes, metadata HMAC/first time, pre/post row
checks, 64-row/2MiB bounds and permission failures remain enforced. Late parent
input/artifact/proof or rights changes must fail the original context's final
check and prevent a successful HTTP response. Errors/caller cancellation close
both contexts. Original artifact/registry/parent-query decoder code remains pinned.

## Preserved data across reader versions

The old storage manifest contains absolute frozen dependency paths. The cost tool
first verifies it in a separate Python process using the exact original source
and records actual command/exit/output hash in a new private receipt. The current
service may differ only in `crop_harvest_current_query.py` among the manifest's
storage dependencies; helper, backup/runtime, registry, artifact and harvest
bytes must agree. The current normal runtime authenticates the original row and
artifact again. The old manifest/signature/record/first timestamp is not changed,
re-signed or rebound. This is an explicit new reader observation, not old evidence
claiming a different code version. Python subprocesses do not launch Codex CLI.

## Acceptance

Meaningful focused tests cover one parent open, current checks within the scope,
mutable-copy isolation, expired callbacks, final parent failure, late scope/farm/
rights/signed-row/HEAD/page changes and cleanup. Existing decoder/route/transport
regressions remain required; historical observation identities stay historical.

Native proof uses the accepted whole writer/independent Decimal/authenticated
backup/fresh/root. Same stored summary/first64/last1 must finish actual protected
HTTPS within30s/2MiB and match independent ASGI/wire observations and original
manifest hashes. Current scope/foreign tenant/display denials and restoration,
RHS/generation/registration/proof0, unchanged original bytes/DB counts/FD,
actual command exit and 512MiB/1GiB observed-tree cleanup are required.
No writer/RHS rerun, frontend replacement, realtime U3 or G0–G4 approval follows
from a passing reader-cost slice. Full representative WebGL is the next child.
