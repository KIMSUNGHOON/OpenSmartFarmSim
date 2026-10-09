"""Fresh two-login planning grants; separate from the closed job-runtime policy."""

from dataclasses import dataclass

from psycopg import sql

from .runtime_login import connect_runtime
from .runtime_roles import RuntimeLoginPolicy, RolePolicyHold


INSERT_COLUMNS = frozenset({"tenant_id", "decision_context_id", "event_raw", "event_sha256",
                           "context_raw", "context_sha256", "context_signature"})


@dataclass(frozen=True)
class PlanningLoginPolicy(RuntimeLoginPolicy):
    @property
    def roles(self):
        # Reuse the authenticated connector's writer/readonly profile semantics.
        return {"authority": self.prefix + "_writer", "supervisor": self.prefix + "_reader"}


def _scope(conn, policy):
    if type(policy) is not PlanningLoginPolicy:
        raise RolePolicyHold("planning_policy_required")
    if conn.execute("SELECT current_database() AS name").fetchone()["name"] != policy.database:
        raise RolePolicyHold("planning_database_scope_rejected")
    owner = conn.execute('''SELECT n.oid AS schema_oid, r.oid AS owner_oid, r.rolsuper, r.rolcanlogin,
        r.rolcreaterole, r.rolcreatedb, r.rolreplication, r.rolbypassrls
        FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner
        WHERE n.nspname=%s AND r.rolname=%s''', (policy.schema, policy.owner)).fetchone()
    if owner is None or any(owner[name] for name in
        ("rolsuper", "rolcanlogin", "rolcreaterole", "rolcreatedb", "rolreplication", "rolbypassrls")):
        raise RolePolicyHold("planning_nonruntime_owner_required")
    extra = conn.execute('''SELECT 1 FROM pg_namespace WHERE nspowner=%s AND oid<>%s
        UNION ALL SELECT 1 FROM pg_class WHERE relowner=%s AND relnamespace<>%s
            AND relnamespace<>'pg_toast'::regnamespace
        UNION ALL SELECT 1 FROM pg_proc WHERE proowner=%s AND pronamespace<>%s LIMIT 1''',
        (owner["owner_oid"], owner["schema_oid"]) * 3).fetchone()
    tables = conn.execute("SELECT oid,relname,relkind,relowner FROM pg_class WHERE relnamespace=%s "
        "AND relkind IN ('r','p','v','m','f','S')", (owner["schema_oid"],)).fetchall()
    routines = conn.execute("SELECT oid,proname,proowner,prosecdef FROM pg_proc WHERE pronamespace=%s",
                            (owner["schema_oid"],)).fetchall()
    if (extra or len(tables) != 1 or tables[0]["relname"] != "planning_events" or
            tables[0]["relkind"] != "r" or tables[0]["relowner"] != owner["owner_oid"] or
            len(routines) != 1 or routines[0]["proname"] != "reject_planning_change" or
            routines[0]["proowner"] != owner["owner_oid"] or routines[0]["prosecdef"]):
        raise RolePolicyHold("planning_objects_or_ownership_rejected")
    columns = conn.execute("SELECT attname FROM pg_attribute WHERE attrelid=%s AND attnum>0 AND NOT attisdropped",
                           (tables[0]["oid"],)).fetchall()
    if {row["attname"] for row in columns} != INSERT_COLUMNS | {"recorded_at"}:
        raise RolePolicyHold("planning_columns_rejected")
    return owner, tables[0]["oid"], routines[0]["oid"]


def audit_planning_roles(conn, policy):
    owner, table, routine = _scope(conn, policy)
    roles = conn.execute('''SELECT oid,rolname,rolsuper,rolcanlogin,rolcreaterole,rolcreatedb,
        rolreplication,rolbypassrls,rolinherit,rolconnlimit FROM pg_roles WHERE rolname=ANY(%s)''',
        (list(policy.roles.values()),)).fetchall()
    if (len(roles) != 2 or any(row[name] for row in roles for name in
            ("rolsuper", "rolcreaterole", "rolcreatedb", "rolreplication", "rolbypassrls", "rolinherit")) or
            any(not row["rolcanlogin"] or row["rolconnlimit"] != policy.connection_limit for row in roles) or
            conn.execute("SELECT 1 FROM pg_auth_members WHERE member=ANY(%s) OR roleid=ANY(%s)",
                         ([row["oid"] for row in roles], [row["oid"] for row in roles])).fetchone()):
        raise RolePolicyHold("planning_login_attributes_rejected")
    creators = conn.execute('''SELECT 1 FROM pg_roles WHERE NOT rolsuper AND oid<>%s AND
        (has_schema_privilege(oid,%s,'CREATE') OR pg_has_role(oid,%s,'MEMBER')) LIMIT 1''',
        (owner["owner_oid"], owner["schema_oid"], owner["owner_oid"])).fetchone()
    if creators:
        raise RolePolicyHold("planning_schema_creators_rejected")
    allowed = [owner["owner_oid"], *[row["oid"] for row in roles]]
    unexpected = conn.execute('''SELECT 1 FROM pg_class c CROSS JOIN LATERAL aclexplode(c.relacl) a
        WHERE c.relnamespace=%s AND NOT a.grantee=ANY(%s)
        UNION ALL SELECT 1 FROM pg_attribute t JOIN pg_class c ON c.oid=t.attrelid
        CROSS JOIN LATERAL aclexplode(t.attacl) a WHERE c.relnamespace=%s AND NOT a.grantee=ANY(%s)
        UNION ALL SELECT 1 FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a
        WHERE p.pronamespace=%s AND NOT a.grantee=ANY(%s)
        UNION ALL SELECT 1 FROM pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) a
        WHERE n.oid=%s AND NOT a.grantee=ANY(%s) LIMIT 1''', (owner["schema_oid"], allowed) * 4).fetchone()
    if unexpected:
        raise RolePolicyHold("planning_unexpected_acl_rejected")
    privileges = ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"]
    if conn.info.server_version >= 170000:
        privileges.append("MAINTAIN")
    for kind, role in policy.roles.items():
        bounds = conn.execute('''SELECT has_database_privilege(%s,current_database(),'CONNECT') AS connects,
            has_schema_privilege(%s,%s,'USAGE') AS usage,
            has_database_privilege(%s,current_database(),'CONNECT WITH GRANT OPTION') AS connect_grantable,
            has_schema_privilege(%s,%s,'USAGE WITH GRANT OPTION') AS usage_grantable,
            has_database_privilege(%s,current_database(),'CREATE') AS db_create,
            EXISTS(SELECT 1 FROM pg_namespace WHERE nspname !~ '^pg_(toast_)?temp_'
                AND has_schema_privilege(%s,oid,'CREATE')) AS ddl,
            EXISTS(SELECT 1 FROM pg_proc p WHERE p.prosecdef AND has_function_privilege(%s,p.oid,'EXECUTE')
                AND has_schema_privilege(%s,p.pronamespace,'USAGE')) AS definer''',
            (role, role, policy.schema, role, role, policy.schema, role, role, role, role)).fetchone()
        if not bounds["connects"] or not bounds["usage"] or any(bounds[name] for name in
                ("connect_grantable", "usage_grantable", "db_create", "ddl", "definer")):
            raise RolePolicyHold("planning_ddl_or_database_rejected")
        for privilege in privileges:
            rights = conn.execute("SELECT has_table_privilege(%s,%s,%s) AS allowed, "
                "has_table_privilege(%s,%s,%s) AS grantable", (role, table, privilege, role, table,
                    privilege + " WITH GRANT OPTION")).fetchone()
            if rights != {"allowed": privilege == "SELECT", "grantable": False}:
                raise RolePolicyHold("planning_table_grants_rejected")
        columns = conn.execute('''SELECT a.attname, p AS privilege,
            has_column_privilege(%s,a.attrelid,a.attnum,p) AS allowed,
            has_column_privilege(%s,a.attrelid,a.attnum,p || ' WITH GRANT OPTION') AS grantable
            FROM pg_attribute a CROSS JOIN unnest(ARRAY['SELECT','INSERT','UPDATE','REFERENCES']) p
            WHERE a.attrelid=%s AND a.attnum>0 AND NOT a.attisdropped''', (role, role, table)).fetchall()
        if any(row["grantable"] or row["allowed"] != (row["privilege"] == "SELECT" or
                (kind == "authority" and row["privilege"] == "INSERT" and row["attname"] in INSERT_COLUMNS))
                for row in columns):
            raise RolePolicyHold("planning_column_grants_rejected")
        if conn.execute("SELECT has_function_privilege(%s,%s,'EXECUTE') AS allowed",
                        (role, routine)).fetchone()["allowed"]:
            raise RolePolicyHold("planning_routine_grants_rejected")
    defaults = conn.execute('''SELECT 1 FROM unnest(ARRAY['r','S','f']::"char"[]) k
        LEFT JOIN pg_default_acl d ON d.defaclrole=%s AND d.defaclnamespace=0 AND d.defaclobjtype=k
        CROSS JOIN LATERAL aclexplode(coalesce(d.defaclacl,acldefault(k,%s))) a WHERE a.grantee<>%s
        UNION ALL SELECT 1 FROM pg_default_acl d CROSS JOIN LATERAL aclexplode(d.defaclacl) a
        WHERE d.defaclrole=%s AND d.defaclnamespace=%s AND a.grantee<>%s
            AND d.defaclobjtype IN ('r','S','f') LIMIT 1''',
        (owner["owner_oid"],) * 4 + (owner["schema_oid"], owner["owner_oid"])).fetchone()
    if defaults:
        raise RolePolicyHold("planning_creator_defaults_rejected")
    return {"policy_version": "planning-login-policy-v1", "schema": policy.schema, "roles": policy.roles}


def install_planning_roles(conn, policy):
    with conn.transaction():
        _scope(conn, policy)
        if conn.execute("SELECT 1 FROM pg_roles WHERE rolname=ANY(%s)", (list(policy.roles.values()),)).fetchone():
            raise RolePolicyHold("planning_logins_already_exist")
        namespace, owner = sql.Identifier(policy.schema), sql.Identifier(policy.owner)
        for role in policy.roles.values():
            conn.execute(sql.SQL('''CREATE ROLE {} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE
                NOREPLICATION NOBYPASSRLS PASSWORD NULL CONNECTION LIMIT {}''').format(
                sql.Identifier(role), sql.Literal(policy.connection_limit)))
        conn.execute(sql.SQL("REVOKE CREATE ON DATABASE {} FROM PUBLIC").format(sql.Identifier(policy.database)))
        conn.execute(sql.SQL("REVOKE ALL ON SCHEMA {} FROM PUBLIC").format(namespace))
        conn.execute(sql.SQL("REVOKE ALL ON ALL TABLES IN SCHEMA {} FROM PUBLIC").format(namespace))
        conn.execute(sql.SQL("REVOKE ALL ON ALL ROUTINES IN SCHEMA {} FROM PUBLIC").format(namespace))
        conn.execute(sql.SQL("REVOKE ALL ({}) ON TABLE {}.planning_events FROM PUBLIC").format(
            sql.SQL(",").join(sql.Identifier(name) for name in sorted(INSERT_COLUMNS | {"recorded_at"})), namespace))
        for objects in ("TABLES", "SEQUENCES", "FUNCTIONS"):
            for scope in (sql.SQL(""), sql.SQL(" IN SCHEMA {}").format(namespace)):
                conn.execute(sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {}{} REVOKE ALL ON {} FROM PUBLIC").format(
                    owner, scope, sql.SQL(objects)))
        for kind, role in policy.roles.items():
            identifier = sql.Identifier(role)
            conn.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(policy.database), identifier))
            conn.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(namespace, identifier))
            conn.execute(sql.SQL("GRANT SELECT ON TABLE {}.planning_events TO {}").format(namespace, identifier))
            if kind == "authority":
                conn.execute(sql.SQL("GRANT INSERT ({}) ON TABLE {}.planning_events TO {}").format(
                    sql.SQL(",").join(sql.Identifier(name) for name in sorted(INSERT_COLUMNS)), namespace, identifier))
        return audit_planning_roles(conn, policy)


def connect_planning(dsn, policy, kind):
    if type(policy) is not PlanningLoginPolicy:
        raise RolePolicyHold("planning_policy_required")
    conn = connect_runtime(dsn, policy, kind)
    try:
        audit_planning_roles(conn, policy)
        conn.commit()
        return conn
    except Exception:
        conn.close()
        raise RolePolicyHold("planning_login_or_grants_rejected") from None
