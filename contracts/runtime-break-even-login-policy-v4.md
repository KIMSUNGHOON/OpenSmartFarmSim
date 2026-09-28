# Optional authenticated break-even profile v4

`RuntimeLoginPolicy` adds keyword-only `break_even_calculation=False`.
An exact True requires `market_calculation=True` and opts into audit version
`runtime-break-even-login-policy-v4`. Default v2, explicit market v3 and
NOLOGIN v1 matrices/versions remain unchanged; existing roles/records receive
no automatic upgrade. Existing deployments need a reviewed owner migration.

Fresh owner provisioning creates the existing immutable `break_even_plan_results`
table/function before role installation. Authority gets SELECT/INSERT on that
table in addition to v3 grants. Request/worker/supervisor get no rights on it.
The existing full effective audit rejects unexpected/missing table/column rights,
grant options, DDL/default/membership/definer/ownership escapes and extra granted
objects. The owner remains dedicated NOLOGIN; secrets are provisioned separately.

BreakEvenStore accepts explicit `(RuntimeLoginPolicy, "authority")` only with
v4 opt-in and matching schema. Every bound connection uses existing exact
SCRAM database/login/session checks, then the full grant audit before data
queries; failure closes with a fixed private error and no owner fallback.
Unbound constructors remain limited legacy fixture paths and must not enter a
deployed factory. Source/context stores retain their own verified bindings and
application tenant/scope checks. This policy never changes monetary arithmetic,
approves data, bypasses replay or grants G0–G4 evidence.

Real SCRAM/software tests still use controller-owned synthetic source records,
keys and credentials. Operating UID/credential/key custody, DB TLS/HBA/RLS,
source evidence, isolated actual CLI, independent release and G1/G4 remain
pending. An authority credential holder can execute its permitted SQL outside
RPC; the profile alone cannot enforce credential custody or server workflow.
