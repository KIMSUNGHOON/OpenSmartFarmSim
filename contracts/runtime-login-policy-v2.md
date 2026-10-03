# Authenticated runtime login policy v2

Status: **software authentication candidate**, with real SCRAM handshake tests.
This is not operating-account/private-key separation, production HBA/TLS proof,
independent exact-model execution, or G1/G4 acceptance. The synthetic-only CLI
guard remains closed. No existing deployment or local database auth configuration
is changed by this implementation.

## Fresh direct login profiles

[`RuntimeLoginPolicy`](../backend/app/runtime_roles.py) extends the v1 policy
with an expected database and a connection limit (default 8, allowed 1–32).
Trusted provisioning passes it explicitly to `install_runtime_roles`. This
creates fresh direct `LOGIN NOINHERIT` request/worker/supervisor/authority
profiles, with no memberships, the same closed grant matrix and dedicated
NOLOGIN owner. It adds CONNECT on the expected database. The v2 audit requires
LOGIN, NOINHERIT, the configured connection limit, CONNECT and that database,
as well as all existing effective/default/column/definer/ownership checks.
The unchanged `RuntimeRolePolicy` v1 rejects LOGIN profiles; this is an explicit
new policy, not an exception applied silently to v1.

Each fresh login starts with `PASSWORD NULL`. A trusted secret provisioner must
configure authentication separately; the installer receives no password and
never resets a provisioned one. Installation rejects any preexisting profile
set and preserves existing credentials on rejection. PostgreSQL defines LOGIN
as an initial session authorization identity; null passwords fail password
authentication. Its connection limit is approximate, not strict worker
concurrency ([PostgreSQL 18 CREATE ROLE](https://www.postgresql.org/docs/18/sql-createrole.html)).
The explicit limit is a candidate configuration, not measured production capacity.

An explicit [market calculation profile v3](runtime-market-login-policy-v3.md)
adds three immutable calculation tables. The default remains v2; existing roles
are not upgraded automatically.
The optional [authored release packet profile](farm-authored-release-store-v1.md)
adds one immutable reviewer-packet table to a fresh `RuntimeLoginPolicy` profile
and leaves the request/worker/supervisor roles without base-table access.

## Every runtime connection

[`connect_runtime`](../backend/app/runtime_login.py) accepts trusted DSN/policy/
profile settings. The DSN must explicitly identify the matching login and database.
It forces `require_auth=scram-sha-256` and a three-second libpq connection timeout,
overriding conflicting DSN values. Trusted startup options are retained before
appending a five-second statement timeout, or a two-second statement timeout and
read-only transactions for the supervisor. Libpq's connection timeout applies
per configured host; this does not prove an independent total DB wall-time limit.

Before any project-data query, the connection must have the expected immutable
libpq login user/database, enforced require_auth, actual password use, and matching
SQL session_user/current_user/current_database. Administrator connections that
use SET ROLE or SET SESSION AUTHORIZATION cannot pass by changing SQL identity.
Successful identity inspection commits its read transaction so later advisory
reservation connections can set autocommit. Connection/identity failures close
the connection and produce only `runtime_login_rejected`, without DSN, password
or driver error text.

Libpq's positive SCRAM requirement rejects skipped or incomplete authentication;
password-use alone would not distinguish SCRAM from other methods
([libpq connection parameters](https://www.postgresql.org/docs/18/libpq-connect.html)).
The locked Psycopg binary currently reports libpq 18.6. Its low-level wrapper
provides password-use inspection and client-side password encryption
([Psycopg pq API](https://www.psycopg.org/psycopg3/docs/api/pq.html)); these operations
were exercised on the locked 3.3.6 installation, independently of the moving
documentation site's version banner.

`JobStore(runtime_identity=(policy, profile))` uses this path for every connection.
The supervisor read proxy also retains it rather than creating an unbound
connection. With this v2 binding, SupervisorServer audits grants/identity before
listening. AuthorityServer checks v2 identity and the complete grant policy at
startup and before each dispatch. The v1 candidate remains available for its
existing explicitly limited SQL-identity tests.

## Credential ownership and remaining boundary

The general dispatcher still receives no database credential or input/lease
data. The authority and supervisor receive only their respective trusted
credentials. **An authority credential holder can use its SQL grants directly
without AuthorityServer.** RPC seriality and validators constrain callers
without that credential; authentication and grants do not force a credential
holder to use those validators. Adding login memberships would not establish
that protection. Independent control of credential/key material and operating
accounts remains a required deployment boundary.

This increment does not attest credential custody, per-tenant DB isolation,
HBA restrictions to one database/user/network, other databases' PUBLIC rights,
TLS/server-certificate policy, rotation, hard-crash cleanup, immutable images,
budget limits or independent release/planning evidence. Compose's shared
deferred app identity is still unchanged. Actual accounts and deployment
configuration must be separately verified before G1/G4 acceptance.

## Observed test scope

[The login tests](../backend/tests/test_runtime_login.py) use real SCRAM logins
with independently generated credentials, and spawned authority/supervisor
processes with a fake CLI and test Ed25519 key. They run all three AI stages.
Database users differ, while OS UID, filesystem and secret provisioner remain
shared. They are not independently controlled operating services or a runtime
model execution acceptance run.

Local tests create a private temporary PostgreSQL instance bound only to
loopback, with SCRAM TCP authentication and a private Unix provisioning socket.
The original local DB config stays untouched. Test binaries are discovered
from the local server's postmaster command; `OSSF_TEST_PG_BIN` can override the
directory. Hosted CI reuses its disposable PostgreSQL 18 SCRAM server, requiring
a completed admin SCRAM handshake before accepting that fixture. Test secrets
use private password files outside the repository and are removed on teardown.
Provisioning encrypts passwords client-side and disables statement/error logging
in that fixture's provisioning transaction; plaintext is not sent in SQL.

The 25 new cases cover positive identity/idle connections, all base-table access
and role escalation denial for general logins, missing/wrong passwords and
disabled login, conflicting DSN parameters on JobStore/supervisor paths,
administrator identity laundering, attribute/membership/grant drift, fresh null
passwords, repeat installation preserving credentials, wrong database, three
authenticated AI stages and direct authority SQL outside RPC. A complete protocol
peer that skips authentication succeeds with unforced `require_auth=none` but
is rejected by the bound runtime path; this is a protocol rejection test, not
another PostgreSQL deployment.

Local verification on 2026-09-28 used the locked backend and PostgreSQL 16.15:
`OSSF_TEST_PG_DSN=… uv run --locked --group dev pytest -q` completed with
**1,161 passed, 0 skipped**, including these 25 login cases, with two preexisting
Pydantic serializer warnings. The focused login suite passed all 25 cases.
Lock, changed local link targets and whitespace checks also passed. The auxiliary
database shut down and private password files were removed; the original local
database authentication configuration was not modified.

JobStore now has explicit `audit_runtime_grants=False`. True requires a login
binding and audits effective grants on every connection before data queries.
The [API assembly](api-runtime-assembly-v1.md) selects True; the default and
v2 role matrix remain unchanged. Audit failure closes with fixed
`runtime_grants_rejected`. This does not establish credential custody.

The auditor groups the four fixed roles in set queries for privilege inquiries.
It still runs the complete current policy on every audited connection, including
whole-table checks alongside column access and grant options. It introduces no
rights cache or connection reuse. [Focused and browser evidence](../research/runtime-role-audit-batching-implementation.md#all-role-query-batching-follow-up-2026-10-01)
records the SQL reduction and unchanged 30-second HTTP bound; hosted and
production load acceptance remain separate.
