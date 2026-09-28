"""Owner-run fresh runtime grants; optional login profiles never receive secrets."""

from dataclasses import dataclass, field
import re

from psycopg import sql


VERSION = "runtime-role-policy-v1"
NAME = re.compile(r"[a-z][a-z0-9_]{0,62}\Z")
JOB_TABLES = (
    "jobs", "job_attempts", "evidence_authorizations", "attempt_evidence",
    "job_events", "attempt_invocations", "attempt_cli_launches", "attempt_cli_captures",
    "validation_receipts", "ai_decisions", "job_hold_reports", "attempt_outcomes",
    "job_publications", "market_hold_reports",
)
TABLES = JOB_TABLES + ("execution_attestations", "thermal_input_snapshots",
                      "decision_contexts", "thermal_g1_runs")
MARKET_TABLES = ("market_candidate_pins", "market_candidate_inputs", "market_result_records")
BREAK_EVEN_TABLES = ("break_even_plan_results",)
SUPERVISOR_TABLES = frozenset({"jobs", "job_attempts", "evidence_authorizations",
    "attempt_evidence", "attempt_invocations", "attempt_cli_launches",
    "attempt_cli_captures", "validation_receipts", "ai_decisions"})


class RolePolicyHold(ValueError):
    pass


@dataclass(frozen=True)
class RuntimeRolePolicy:
    schema: str
    owner: str
    prefix: str

    def __post_init__(self):
        if (any(type(value) is not str or not NAME.fullmatch(value) or value.startswith("pg_")
                for value in (self.schema, self.owner, self.prefix)) or len(self.prefix) > 40 or
                self.owner in self.roles.values()):
            raise RolePolicyHold("invalid_role_policy_scope")

    @property
    def roles(self):
        return {kind: self.prefix + "_" + kind for kind in
                ("request", "worker", "supervisor", "authority")}


@dataclass(frozen=True)
class RuntimeLoginPolicy(RuntimeRolePolicy):
    database: str
    connection_limit: int = 8
    market_calculation: bool = field(default=False, kw_only=True)
    break_even_calculation: bool = field(default=False, kw_only=True)

    def __post_init__(self):
        super().__post_init__()
        if (type(self.database) is not str or not NAME.fullmatch(self.database) or
                type(self.connection_limit) is not int or not 1 <= self.connection_limit <= 32 or
                type(self.market_calculation) is not bool or
                type(self.break_even_calculation) is not bool or
                (self.break_even_calculation and not self.market_calculation)):
            raise RolePolicyHold("invalid_login_policy_scope")


def _tables(policy):
    if not isinstance(policy, RuntimeLoginPolicy):
        return TABLES
    return (TABLES + (MARKET_TABLES if policy.market_calculation else ()) +
            (BREAK_EVEN_TABLES if policy.break_even_calculation else ()))


def _database(conn, policy):
    if isinstance(policy, RuntimeLoginPolicy):
        if conn.execute("SELECT current_database() AS name").fetchone()["name"] != policy.database:
            raise RolePolicyHold("runtime_database_scope_mismatch")


def _scope(conn, policy, *, hardened=True):
    row = conn.execute("""
        SELECT n.oid AS schema_oid, r.oid AS owner_oid, r.rolsuper, r.rolcanlogin,
            r.rolcreaterole, r.rolcreatedb, r.rolreplication, r.rolbypassrls
        FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner
        WHERE n.nspname=%s AND r.rolname=%s
    """, (policy.schema, policy.owner)).fetchone()
    if row is None or any(row[name] for name in (
            "rolsuper", "rolcanlogin", "rolcreaterole", "rolcreatedb", "rolreplication", "rolbypassrls")):
        raise RolePolicyHold("dedicated_nonruntime_owner_required")
    extra = conn.execute("""
        SELECT 1 FROM pg_namespace WHERE nspowner=%s AND oid<>%s
        UNION ALL SELECT 1 FROM pg_class WHERE relowner=%s AND relnamespace<>%s
            AND relnamespace<>'pg_toast'::regnamespace
        UNION ALL SELECT 1 FROM pg_proc WHERE proowner=%s AND pronamespace<>%s
        LIMIT 1
    """, (row["owner_oid"], row["schema_oid"]) * 3).fetchone()
    if extra:
        raise RolePolicyHold("owner_not_dedicated_to_project")
    creators = conn.execute("""
        SELECT rolname FROM pg_roles WHERE NOT rolsuper AND oid<>%s
            AND (has_schema_privilege(oid,%s,'CREATE') OR pg_has_role(oid,%s,'MEMBER'))
    """, (row["owner_oid"], row["schema_oid"], row["owner_oid"])).fetchall()
    if hardened and creators:
        raise RolePolicyHold("uncontrolled_project_creators")
    relations = conn.execute("""
        SELECT c.oid, c.relname, c.relkind, c.relowner FROM pg_class c
        WHERE c.relnamespace=%s AND c.relkind IN ('r','p','v','m','f','S')
        ORDER BY c.relname
    """, (row["schema_oid"],)).fetchall()
    routines = conn.execute("SELECT oid, proowner, prosecdef FROM pg_proc WHERE pronamespace=%s",
                            (row["schema_oid"],)).fetchall()
    if (not set(_tables(policy)) <= {item["relname"] for item in relations if item["relkind"] == "r"} or
            any(item["relowner"] != row["owner_oid"] for item in relations) or
            any(item["proowner"] != row["owner_oid"] or item["prosecdef"] for item in routines)):
        raise RolePolicyHold("unexpected_project_objects_or_owners")
    return row, relations, routines


def _allowed(policy, kind, name, privilege):
    if kind == "authority" and name in _tables(policy):
        return privilege in {"SELECT", "INSERT"} or (name == "jobs" and privilege == "UPDATE")
    return kind == "supervisor" and name in SUPERVISOR_TABLES and privilege == "SELECT"


def audit_runtime_roles(conn, policy):
    """Validate effective rights, including PUBLIC/columns/inheritance, after commit."""
    _database(conn, policy)
    scope, relations, routines = _scope(conn, policy)
    login = isinstance(policy, RuntimeLoginPolicy)
    roles = conn.execute("""
        SELECT oid, rolname, rolsuper, rolcanlogin, rolcreaterole, rolcreatedb,
            rolreplication, rolbypassrls, rolinherit, rolconnlimit FROM pg_roles WHERE rolname=ANY(%s)
    """, (list(policy.roles.values()),)).fetchall()
    if (len(roles) != 4 or any(row[name] for row in roles for name in (
            "rolsuper", "rolcreaterole", "rolcreatedb", "rolreplication", "rolbypassrls")) or
            any(row["rolcanlogin"] != login or
                (login and (row["rolinherit"] or row["rolconnlimit"] != policy.connection_limit))
                for row in roles) or
            conn.execute("SELECT 1 FROM pg_auth_members WHERE member=ANY(%s) OR roleid=ANY(%s)",
                         ([row["oid"] for row in roles], [row["oid"] for row in roles])).fetchone()):
        raise RolePolicyHold("runtime_role_attributes_or_membership")
    if login and any(not conn.execute("SELECT has_database_privilege(%s,%s,'CONNECT') AS allowed",
                    (role, policy.database)).fetchone()["allowed"] for role in policy.roles.values()):
        raise RolePolicyHold("runtime_database_connect_required")
    approved = [scope["owner_oid"], *[row["oid"] for row in roles]]
    unexpected_acl = conn.execute("""
        SELECT 1 FROM pg_class c CROSS JOIN LATERAL aclexplode(c.relacl) a
            WHERE c.relnamespace=%s AND NOT a.grantee=ANY(%s)
        UNION ALL SELECT 1 FROM pg_attribute t JOIN pg_class c ON c.oid=t.attrelid
            CROSS JOIN LATERAL aclexplode(t.attacl) a
            WHERE c.relnamespace=%s AND NOT a.grantee=ANY(%s)
        UNION ALL SELECT 1 FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a
            WHERE p.pronamespace=%s AND NOT a.grantee=ANY(%s)
        LIMIT 1
    """, (scope["schema_oid"], approved) * 3).fetchone()
    if unexpected_acl:
        raise RolePolicyHold("unexpected_project_acl_identity")
    privileges = ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"]
    if conn.info.server_version >= 170000:
        privileges.append("MAINTAIN")
    for kind, role in policy.roles.items():
        rights = conn.execute("""
            SELECT has_schema_privilege(%s,%s,'USAGE') AS usage,
                has_database_privilege(%s,current_database(),'CREATE') AS db_create,
                EXISTS (SELECT 1 FROM pg_namespace WHERE nspname !~ '^pg_(toast_)?temp_'
                    AND has_schema_privilege(%s,oid,'CREATE')) AS ddl,
                EXISTS (SELECT 1 FROM pg_proc p WHERE p.prosecdef
                    AND has_function_privilege(%s,p.oid,'EXECUTE')
                    AND has_schema_privilege(%s,p.pronamespace,'USAGE')) AS definer
        """, (role, scope["schema_oid"], role, role, role, role)).fetchone()
        if not rights["usage"] or rights["db_create"] or rights["ddl"] or rights["definer"]:
            raise RolePolicyHold("runtime_ddl_or_definer_escape")
        for relation in relations:
            oid, name = relation["oid"], relation["relname"]
            if relation["relkind"] == "S":
                if any(conn.execute("SELECT has_sequence_privilege(%s,%s,%s) AS allowed",
                       (role, oid, privilege)).fetchone()["allowed"] for privilege in ("SELECT", "UPDATE", "USAGE")):
                    raise RolePolicyHold("runtime_sequence_privilege")
                continue
            values = conn.execute("""
                SELECT p AS privilege, has_table_privilege(%s,%s,p) AS allowed,
                    has_table_privilege(%s,%s,p || ' WITH GRANT OPTION') AS grantable
                FROM unnest(%s::text[]) p
            """, (role, oid, role, oid, privileges)).fetchall()
            if any(item["allowed"] != _allowed(policy, kind, name, item["privilege"]) or item["grantable"]
                   for item in values):
                raise RolePolicyHold("runtime_table_grant_matrix")
            columns = conn.execute("""
                SELECT p AS privilege, has_column_privilege(%s,a.attrelid,a.attnum,p) AS allowed,
                    has_column_privilege(%s,a.attrelid,a.attnum,p || ' WITH GRANT OPTION') AS grantable
                FROM pg_attribute a CROSS JOIN unnest(ARRAY['SELECT','INSERT','UPDATE','REFERENCES']) p
                WHERE a.attrelid=%s AND a.attnum>0 AND NOT a.attisdropped
            """, (role, role, oid)).fetchall()
            if any(item["allowed"] != _allowed(policy, kind, name, item["privilege"]) or item["grantable"]
                   for item in columns):
                raise RolePolicyHold("runtime_column_grant_matrix")
        if any(conn.execute("SELECT has_function_privilege(%s,%s,'EXECUTE') AS allowed",
                            (role, routine["oid"])).fetchone()["allowed"] for routine in routines):
            raise RolePolicyHold("runtime_routine_privilege")
    bad_defaults = conn.execute("""
        SELECT 1 FROM unnest(ARRAY['r','S','f']::"char"[]) k
            LEFT JOIN pg_default_acl d ON d.defaclrole=%s
                AND d.defaclnamespace=0 AND d.defaclobjtype=k
            CROSS JOIN LATERAL aclexplode(coalesce(d.defaclacl,acldefault(k,%s))) a
            WHERE a.grantee<>%s
        UNION ALL
        SELECT 1 FROM pg_default_acl d CROSS JOIN LATERAL aclexplode(d.defaclacl) a
        WHERE d.defaclrole=%s AND d.defaclnamespace=%s
            AND a.grantee<>%s AND d.defaclobjtype IN ('r','S','f') LIMIT 1
    """, (scope["owner_oid"],) * 4 + (scope["schema_oid"], scope["owner_oid"])).fetchone()
    if bad_defaults:
        raise RolePolicyHold("uncontrolled_creator_defaults")
    return {"policy_version": ("runtime-break-even-login-policy-v4" if policy.break_even_calculation else
                               "runtime-market-login-policy-v3" if policy.market_calculation else
                               "runtime-login-policy-v2") if login else VERSION,
            "schema": policy.schema, "owner": policy.owner,
            "roles": policy.roles, "tables": len(relations), "routines": len(routines)}


def install_runtime_roles(conn, policy):
    """Atomic fresh-role installation by a trusted database provisioner."""
    with conn.transaction():
        _database(conn, policy)
        scope, relations, _ = _scope(conn, policy, hardened=False)
        if conn.execute("SELECT 1 FROM pg_roles WHERE rolname=ANY(%s)",
                        (list(policy.roles.values()),)).fetchone():
            raise RolePolicyHold("runtime_roles_already_exist")
        for role in policy.roles.values():
            attributes = (sql.SQL("LOGIN NOINHERIT PASSWORD NULL CONNECTION LIMIT {}").format(
                sql.Literal(policy.connection_limit)) if isinstance(policy, RuntimeLoginPolicy) else sql.SQL("NOLOGIN"))
            conn.execute(sql.SQL("CREATE ROLE {} {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS")
                         .format(sql.Identifier(role), attributes))
        namespace, owner = sql.Identifier(policy.schema), sql.Identifier(policy.owner)
        database = conn.execute("SELECT current_database() AS name").fetchone()["name"]
        conn.execute(sql.SQL("REVOKE CREATE ON DATABASE {} FROM PUBLIC").format(sql.Identifier(database)))
        conn.execute(sql.SQL("REVOKE ALL ON SCHEMA {} FROM PUBLIC").format(namespace))
        for objects in ("TABLES", "SEQUENCES", "ROUTINES"):
            conn.execute(sql.SQL("REVOKE ALL ON ALL {} IN SCHEMA {} FROM PUBLIC")
                         .format(sql.SQL(objects), namespace))
        for relation in relations:
            if relation["relkind"] == "S":
                continue
            columns = conn.execute("SELECT attname FROM pg_attribute WHERE attrelid=%s AND attnum>0 AND NOT attisdropped",
                                   (relation["oid"],)).fetchall()
            if columns:
                conn.execute(sql.SQL("REVOKE ALL ({}) ON TABLE {}.{} FROM PUBLIC")
                    .format(sql.SQL(",").join(sql.Identifier(row["attname"]) for row in columns),
                            namespace, sql.Identifier(relation["relname"])))
        for objects in ("TABLES", "SEQUENCES", "FUNCTIONS"):
            for scope_clause in (sql.SQL(""), sql.SQL(" IN SCHEMA {}").format(namespace)):
                conn.execute(sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {}{} REVOKE ALL ON {} FROM PUBLIC")
                             .format(owner, scope_clause, sql.SQL(objects)))
        for kind, role in policy.roles.items():
            identifier = sql.Identifier(role)
            if isinstance(policy, RuntimeLoginPolicy):
                conn.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(policy.database), identifier))
            conn.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(namespace, identifier))
            selected = _tables(policy) if kind == "authority" else tuple(sorted(SUPERVISOR_TABLES)) if kind == "supervisor" else ()
            for name in selected:
                conn.execute(sql.SQL("GRANT {} ON TABLE {}.{} TO {}")
                    .format(sql.SQL("SELECT,INSERT" if kind == "authority" else "SELECT"),
                            namespace, sql.Identifier(name), identifier))
            if kind == "authority":
                conn.execute(sql.SQL("GRANT UPDATE ON TABLE {}.jobs TO {}").format(namespace, identifier))
        return audit_runtime_roles(conn, policy)
