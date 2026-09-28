# Runtime role policy v1

Status: **software migration candidate**. This does not provision service logins,
bind IPC identities to DB identities, deploy independent processes, or pass G1/G4.
The supervised execution engine calls JobStore inside the new
[authority dispatcher candidate](authority-rpc-v1.md). General dispatchers use
that RPC without a DB connection; deployed service binding is still unaccepted.

[`runtime_roles.py`](../backend/app/runtime_roles.py) exposes an explicit
`install_runtime_roles(conn, RuntimeRolePolicy(schema, owner, prefix))` and
`audit_runtime_roles(conn, policy)`. Importing it changes nothing. The connection
uses Psycopg `dict_row`; a trusted provisioner with the necessary ownership/role
permissions calls installation after the durable job, signed execution,
thermal Run, and market hold schemas have been installed. The provisioner
commits and repeats the audit on a fresh connection. Installation creates fresh
roles only and rejects a repeated or partially preexisting role set.

The schema owner must be a dedicated `NOLOGIN` role without superuser, role/DB
creation, replication, or RLS bypass. It owns the project relations/routines
and no unrelated schema/relations/routines in this database; PostgreSQL's
dependent TOAST relations are excluded from that unrelated-object check.
Other non-superuser project creators or owner members are rejected after
hardening. Provisioning superusers remain outside the runtime boundary. The
installer does not transfer ownership, create passwords, or select an account.

| Profile | Project data rights | State/data mutation |
| --- | --- | --- |
| `request` | Schema `USAGE`; no base table/column/routine access | None; future public projections/trusted submission RPC required |
| `worker` | Schema `USAGE`; no base table/column/routine access | None; scoped authority dispatcher RPC candidate |
| `supervisor` | `SELECT` on jobs, attempts, evidence/authorization, invocation, launch, capture, receipt, decision | None |
| `authority` | `SELECT` on the 18 explicitly named job, execution, thermal, and market hold tables | `INSERT` on those tables, `UPDATE` on jobs only |

All four are fresh `NOLOGIN`, non-owner roles without privileged attributes,
memberships, grant options, persistent DDL, sequence rights, project routine
execution, or delete/truncate/trigger/reference rights. Other project tables,
including later economic/source tables, receive no grants implicitly. The
authority must still apply the existing JobStore/source/gate validators;
SQL permissions alone do not approve a decision or a thermal Run.
Version 1 rejects memberships both into and out of these profiles. A future
login binding needs a binding-aware policy/audit; attaching a login to these
profiles is not accepted by this candidate's audit.

One transaction revokes `PUBLIC` project schema/table/column/sequence/routine
rights and database `CREATE`. It revokes both global and schema-specific
`PUBLIC` creator defaults for tables, sequences and functions for the dedicated
owner. Global here means every schema in this database. Schema-specific revokes
cannot cancel global default grants; table revokes cannot cancel separate column
grants ([PostgreSQL 18 GRANT](https://www.postgresql.org/docs/18/sql-grant.html),
[default privileges](https://www.postgresql.org/docs/18/sql-alterdefaultprivileges.html)).
The owner restriction makes the default changes reviewable within the project.
Other schema permissions are checked rather than silently rewritten.

The audit checks ownership/creators, attributes/memberships, database and
persistent schema creation, reachable `SECURITY DEFINER` routines including
outside the project, unexpected ACL identities, exact effective table and
column rights/grant options, sequences, routines, and creator defaults.
Missing global default ACL rows are evaluated with PostgreSQL's implicit
defaults; restoring the normal PUBLIC function-execution default cannot evade
the audit by removing the explicit catalog row.
PostgreSQL 18's `MAINTAIN` is checked when supported; PostgreSQL 16 has no such
privilege. A changed policy, new object or login binding requires an audit and
explicit permission review. Effective rights include `PUBLIC` and role
memberships ([role membership](https://www.postgresql.org/docs/18/role-membership.html),
[privileges](https://www.postgresql.org/docs/18/ddl-priv.html)). Temporary objects
are outside the persistent DDL check; database `TEMP`/connection rights and other
databases are not deployment proof from this migration.

Tests use disposable schemas and test roles, with `SET SESSION AUTHORIZATION`
under an administrator-controlled connection. This exercises the effective SQL
permissions without claiming authenticated production logins. They reject
request/worker reads and writes to every authority table, DDL/role escalation,
PUBLIC column/global-default errors, privilege drift, and an external reachable
definer. They verify rollback after an injected final audit failure and unchanged
permissions after a rejected repeat installation. A fake-child issuance flow
performs durable writes as `authority` and issuer reads as `supervisor` for all
three AI stages. The test key and filesystem remain under one OS user.

The scoped authority candidate now owns JobStore mutation and attestation
ingestion; a fixed UID/tenant dispatcher requests the next eligible job without
job/input/lease fields. Request submission/public projections remain future
integration. Independent service logins must have audited
attributes, memberships, object/default rights, and authentication restrictions;
per-tenant access, independent key/UID control, actual model execution,
immutable image/binary identity, thermal release/planning evidence, and process
supervision remain required. Compose still contains dependency roles and the
shared deferred app DB identity; this migration has not been applied there.

Local acceptance evidence on 2026-09-28: the locked backend on PostgreSQL 16.15
completed with **1,104 passed, 0 skipped** and two preexisting Pydantic serializer
warnings. The role policy adds 29 cases, including a RED-to-GREEN check that
restoring normal global PUBLIC function defaults removes the explicit ACL row
but still triggers a hold. Tests used fake CLI processes/test keys, not actual
model execution or authenticated independent deployment accounts.
