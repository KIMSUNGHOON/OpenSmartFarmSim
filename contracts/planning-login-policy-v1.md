# Planning login policy v1

Status: **software candidate**. This policy covers the separate schema from
[planning-event-v1](planning-event-v1.md), independently of the closed four-role
[job runtime policy](runtime-login-policy-v2.md). It installs no product service,
private key, operating account, HBA configuration or deployment proof.

## Provisioning and grants

An operator first installs the planning schema and transfers its table and
trigger function to a dedicated NOLOGIN owner. `PlanningLoginPolicy` binds the
exact database, schema, owner, prefix and connection limit (1–32). The owner
must have no extra ownership outside this schema. `install_planning_roles`
requires administrative provisioning rights and creates two fresh LOGIN,
NOINHERIT roles with null passwords, no memberships or privilege attributes.
Existing requested role names are rejected without changing their credentials.
The complete installer and its final audit run in one transaction.

| Login | Internal connector profile | Project privileges |
| --- | --- | --- |
| `<prefix>_writer` | `authority` | CONNECT, schema USAGE, table SELECT, INSERT on seven event/context columns |
| `<prefix>_reader` | `supervisor` | CONNECT, schema USAGE, table SELECT |

Neither login may assign `recorded_at`, mutate/truncate rows, alter objects,
create project objects, execute the trigger function directly, grant table or
column privileges, or assume the owner/other login. The writer's column INSERT
omits `recorded_at`, allowing its server default to supply the timestamp.
Column INSERT/default behavior and owner alteration rights follow the
[PostgreSQL privilege contract](https://www.postgresql.org/docs/18/ddl-priv.html).

Provisioning revokes PUBLIC database CREATE and project schema/table/column/
routine privileges, plus owner global and schema-specific PUBLIC defaults.
These changes affect the specified database and the dedicated owner; use an
operator-controlled installation, not an arbitrary shared database. Other
ambient privileges outside this project are not exhaustively audited.

## Connection and authority admission

The operator separately provisions private SCRAM credentials. Every bound store
connection uses the existing authenticated connector with explicit user and
database, `require_auth=scram-sha-256`, actual password use and matching libpq,
session-user and current-user identities. The reader starts read-only with a
two-second statement timeout; the writer uses five seconds. Read-only session
settings can be changed, so the SQL grants enforce the write restriction.
The [libpq authentication contract](https://www.postgresql.org/docs/18/libpq-connect.html)
defines `require_auth`; it does not configure transport encryption or HBA.

Before returning a connection, the audit checks object inventory/ownership,
login attributes and memberships, effective project table/column privileges,
unexpected PUBLIC/outsider ACLs, schema creators, reachable SECURITY DEFINER
routines and owner default grants. Any mismatch closes the connection and holds.
This is an admission snapshot, not a lock against later privileged catalog edits.

`PlanningAuthority` requires the writer-bound store by default.
`DecisionContextVerifier` requires the reader-bound store's exact `read_event`
method. Owner stores, wrong profiles and arbitrary callbacks are rejected.
`synthetic_smoke=True` explicitly permits software test doubles only.

## Evidence limits

The [tests](../backend/tests/test_planning_roles.py) authenticate both distinct
SCRAM logins and exercise issuance, public verification, snapshot/context
integration, denied timestamp insertion/mutation/escalation, catalog drift and
installer rollback. Keys and credential provisioners still share one OS UID.
The planning credentials can directly SELECT all tenant rows; application scope
checks do not supply database row isolation. The writer can append direct SQL
rows; pinned signatures and event/context verification remain mandatory.

Independent key custody, operating identities, clock operations, row isolation
or a trusted credential boundary, full schema attestation, factory assembly,
actual CLI execution and independent release remain unresolved. These checks
grant no real-source, crop, economic, ranking, G1 or G4 claim.
