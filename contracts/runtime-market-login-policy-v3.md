# Optional authenticated market calculation profile v3

The existing `RuntimeLoginPolicy` gains keyword-only `market_calculation=False`.
Only an exact boolean True opts into v3. False preserves the v2 policy, grant
matrix and audit version. The NOLOGIN v1 profile is unchanged.

V3 additionally requires three owner-created immutable tables:
`market_candidate_pins`, `market_candidate_inputs`, `market_result_records`.
Trusted fresh provisioning installs their schemas before role installation,
under the dedicated owner. The authority gets SELECT/INSERT on them; request,
worker and supervisor get no access. Other core grants remain the same.
Unknown/future tables, update/delete/truncate/grant options, column privileges,
membership/default/definer escapes and inconsistent ownership remain denied
by the effective audit. Neither roles nor existing records are silently
upgraded; existing deployments need separately reviewed owner migration.

MarketHoldStore, MarketCandidateStore and MarketResultStore accept an explicit
`runtime_identity=(RuntimeLoginPolicy, "authority")`. Candidate/result require
the v3 opt-in. Hold can use v2 or v3 because its table is already in v2. Invalid
profile/schema bindings fail at construction. Every bound connection uses
existing exact database/user SCRAM inspection, then the complete effective
grant audit, before any market query. Failure closes the connection and emits
a fixed private error. Identity or grant checks never fall back to an owner
connection. Constructor None preserves legacy explicitly limited fixture paths;
it is not operating login evidence and must not enter a deployed factory.

This profile grants no tenant identity, source right, market data approval,
crop/margin forecast or G0–G4 permission. Existing application scopes, source
repositories, signed hold verification, immutable pins and Decimal replay
remain required. Source/context dependencies keep their own verified authority;
the profile does not replace them. Protected operating accounts, credential
custody, DB TLS/HBA/RLS, real source repositories and independent release/G1/G4
remain separate evidence. Synthetic SCRAM/software tests prove no production
account separation or actual model invocation.

The [optional break-even profile v4](runtime-break-even-login-policy-v4.md)
adds a separately selected immutable plan/result table. V3 defaults and its
three-table matrix/version remain unchanged.
