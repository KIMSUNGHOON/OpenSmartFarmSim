# Owned fixture collection v1

Status: deterministic collection software candidate; no G0/G1/G4 acceptance.
This connects a verified research selection to one collection intent and an
immutable collected record. The first adapter is the directly authored fixture
bundle required by [the first slice](../docs/IMPLEMENTATION_SLICE.md).

The protected operator installs an actual audited JobStore authority and
OwnedFixtureRegistry. Its provider ID identifies the fixed manifest v2 bundle;
requests cannot supply file paths, URLs, raw bytes, metadata, credentials, QC
verdicts, prices or coefficients. The registry checks the existing manifest pin,
all original file hashes/lengths, Apache rights, source/review declarations,
clock/units and existing thermal input checks. It retains source metadata and
original raw UTF-8 bytes without filling gaps or changing inputs. Synthetic
applicability labels do not establish geographic or agricultural validity.

Admission requires metadata, artifact and collection_execute scopes. An actual
same-tenant succeeded research job must have a verified immutable input,
publication, retained final/report/invocation/capture evidence and server proceed
decision selecting this provider. Its canonical safe projection must match the
original input/selection/context. A hold, different tenant/stage, unsupported
provider, missing/mismatched evidence or invalid scope cannot create an intent.
The source bundle must cover the exact requested period; unavailable-at-D source
data cannot enter an ex_ante collection. Admission stores only a canonical
collection intent and checks complete parent/source binding again at commit.

The worker targets one actual tenant/collection UUID. It revalidates the full
admission binding, source bytes, scopes and implementation/environment around
collection, cancellation and expiry checkpoints. Canonical collected bytes are
durable before publication. A live attempt/token/input fence, completed state,
publication, event and attempt outcome commit together, with a final binding
check. Failure has no visible publication; existing bounded retry/hold/cancel
semantics apply. Other models/stages/tenants are not claimed.

The record preserves the research/registry/source hashes, decision context/time/
claim mode and declared source
metadata, includes an actual retrieval timestamp and versioned software QC,
and explicitly keeps Assessment hold and G0/G1 unaccepted. A collection success
means byte capture/contract checks, not source approval, actual Codex execution,
crop growth, energy purchases, future profit or ranking. Fixtures may enter
prompts/display only under their declared owned rights; restricted third-party
adapters are not installed by this contract. Credential/public-manifest rules
remain those of [AGENTS](../AGENTS.md) and [source research](../docs/RESEARCH_BASELINE.md).

Signed planning/review, snapshot adoption, actual provider adapters/rights/QC,
independent CLI/isolation/release/custody and full browser/G0–G4 remain acceptance
work. The existing initial ResearchRegistry still yields hold; it is not relaxed
to manufacture a usable research decision.

## Protected foreground execution

`python -m app.collection_work --factory operator_module:build --job-id UUID`
loads a protected operator factory returning the actual CollectionWorker.
The factory configures authority login, tenant/scopes, private artifact access
and the installed owned registry. Configuration and execution failures emit
fixed metadata with exits 2 and 3; an unresolved lease is not command success.
Successful output contains outcome metadata or null, never raw records, source
paths, credentials or private evidence. This command makes no model call.
