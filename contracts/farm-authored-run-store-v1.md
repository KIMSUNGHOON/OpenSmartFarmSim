# Authored thermal Run storage boundary v1

Status: internal schema and role boundary after [Run byte preparation](farm-authored-run-preparation-v1.md). No authored Run has been published by this change.

The owner installs `authored_thermal_runs` after the durable job and authored release tables. A row has a tenant/Run primary key, one simulation job, one completed review release, the registration and scenario revision, exact two final trace byte strings and SHA-256s, preparation and publication report bytes and SHA-256s, and a server gate signature. It has tenant/job foreign keys, byte-digest and critical identity/carry checks, and an owner-installed trigger that rejects update and delete. A later worker must insert this row and complete its simulation job in one transaction; a row's existence alone is not G1 acceptance.

`RuntimeLoginPolicy(authored_run_storage=True)` is an explicit profile that requires `authored_release_storage=True`. The authority login alone receives `SELECT, INSERT`; request, worker and supervisor logins receive neither. Its audit version is `runtime-authored-run-login-policy-v8`. Existing profiles do not acquire the table. The [focused PostgreSQL/SCRAM test](../research/farm-authored-run-store-implementation.md) checks role grants. Publisher, current-rights readback, worker transaction, actual CLI, independent release and G1 evidence remain pending.
