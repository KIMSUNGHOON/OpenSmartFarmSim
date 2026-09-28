# Authenticated implemented-API assembly v1

Status: software assembly candidate. Production source repositories, protected
operator configuration/custody, actual isolated Codex, independent release,
remaining submissions and browser/G1/G4 acceptance remain pending.

With explicit thermal_scenario_storage=True (v6 plus the existing market and
break-even flags), ApiRuntime also assembles ThermalScenarioStore using the
exact existing thermal/hold stores and current_principal. It supplies that
reader to job Run discovery. The default field is None, preserving the six
existing stores and v1 job behavior. No new caller-supplied factory, credential,
raw-input endpoint or source authority is introduced by this optional read.

`ApiRuntime(config, dependencies).service` is an exact `HttpsApiService` accepted
by the existing `python -m app.api_serve --factory operator_module:build` entrypoint.
The operator's build callable supplies the two frozen typed objects and returns
that service. HTTP clients and CLI proposals cannot choose configuration,
modules, paths, keys, grants or callbacks. This module neither loads an untrusted
file nor supplies default keys/verifiers/source data; the operator must provision
and protect these dependencies. Operator code is trusted and must avoid unsafe
logging and source/model invocation during initialization.

## Configuration and dependencies

`ApiRuntimeConfig` requires an exact RuntimeLoginPolicy with both explicit market
and break-even flags (v4, or optional v5 source storage), a nonempty DSN, absolute artifact/certificate/key Paths
with no parent traversal, and separate thermal-gate/market-hold byte key fields
of 32–4096 bytes. Optional exact ContentAccess permits existing explicit group
read; None requires private artifact metadata. Host/port retain the HTTPS
loopback-only contract. Sensitive configuration/dependency/store fields are
excluded from repr. No schema/role provisioning, migration, password setting,
chmod or existing-root creation occurs during assembly.

`ApiRuntimeDependencies` requires exact ResearchRegistry/BearerRegistry objects
and callable context/release verifiers, market scope resolver and market source
factory. The source factory receives only keyword `principal_provider` with the
same `current_principal` function bound to the API/request stores. It must return
a trusted reader with these callable methods:

- tenant_is_authenticated
- get_economic_scenario, get_economic_scenario_pin, get_economic_input
- get_joint_shock, get_joint_shock_pin, get_input_rights
- get_settlement_applicability, get_settlement_evidence, get_prior_batch_cost

The source is still responsible for durable immutable source evidence, tenant
ownership, rights, times/vintages, applicability and QC. Interface presence is
not source approval or independent verifier custody.

The optional [v5 user-assumption source store](market-user-source-store-v1.md)
implements this reader interface with actual immutable job input bindings. A
factory may construct it with the supplied principal_provider and explicit v5
authority configuration; the assembly still requires both calculation flags.
Its read principals also need market_source_read. This option supplies user
assumption persistence; external source approval/provisioning remains pending.

## Assembly and reads

Assembly first verifies the existing artifact root using the store's nofollow
path/descriptor and metadata checks. Explicit ContentAccess must admit the
writer UID/group. A real authority connection checks SCRAM identity and the full
effective selected-profile grant matrix before the source factory is called or listening starts.
The factory/remaining dependencies are validated and all implemented stores
are created: JobStore, ThermalRunStore, MarketHoldStore, MarketCandidateStore,
MarketResultStore and BreakEvenStore. LocationResearchService uses the exact
supplied immutable registry. PrincipalMiddleware supplies the same request
identity to every store and the existing fifteen routes. No unused reader doubles
or absent optional location/break-even service enter this assembly.

The market source view independently checks the current tenant and source
principal. Its hold/context methods always use the assembled signed MarketHoldStore
and ThermalRunStore chain; same-named methods on the source cannot override that
authority. Candidate/result/break-even reads retain existing full replay, rights,
context and application-scope checks. Deep source scopes remain independently
required; a denied source/replay is unavailable, never treated as approved data.

JobStore adds explicit `audit_runtime_grants=False`. True requires a login
binding and performs the full effective audit on every connection before data
queries, commits inspection, and closes with fixed `runtime_grants_rejected`
on audit failure. This assembly selects True. Defaults preserve legacy v1/v2
fixture/caller behavior; existing dispatcher and admission audits still apply.
Other assembled stores already audit their bound connections. A post-start grant
change therefore blocks job reads as well as market/thermal reads.

Construction failure raises only `API runtime assembly rejected`; invalid typed
objects raise fixed configuration/dependency messages. The foreground CLI masks
startup details under its existing fixed code. Trusted callbacks must also
protect their own output. All connections/descriptors opened by startup checks
are closed. TLS/server limits and signal behavior retain the HTTPS service
contract. No raw configuration or credential is returned through HTTP.

## Verification scope

[Thermal Run submission](api-run-submission-v1.md) is optionally assembled by
thermal_publisher_factory with the actual runtime Run/Job stores. Explicit v6
Scenario storage is required. The default None supplies no publisher or gate
evidence and leaves submission unavailable after authorization. The factory's
independent release/execution configuration remains an operator responsibility.

[Scenario registration/lookup](api-scenario-intent-v1.md) use the already
assembled v6 Scenario store. Other policies leave these routes unavailable
after authorization; no new default factory, migration or scope grant exists.

[User-assumption intake](api-market-user-source-v1.md) is enabled only by an exact
actual MarketSourceStore returned by the existing protected source factory and
bound to this runtime's JobStore. Custom read repositories leave it unavailable.
The same exact source enables [conditional scenario registration](api-economic-scenario-v1.md)
through the actual candidate store and source/hold view. The view's default
principal remains current_principal; the service verifies every store/view's
identical principal and authority binding at admission and commit.

Synthetic source/key/credential tests exercise real SCRAM, a fresh Python API
process, actual TLS/Bearer, signed hold replay, economic/grid reads and post-start
job grant denial. Thermal queries with no published Run return 404 from the real
store; this does not prove an accepted Run in this assembled process. Existing
publisher/read tests cover that separate software path. Real Codex, independent
sources/releases, deployed account/custody separation, public TLS/Compose app
wiring, source/plan generation, full end-to-end browser and G1/G4 remain holds.
