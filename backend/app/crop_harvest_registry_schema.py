"""Provisioner-owned PostgreSQL metadata and isolated harvest registry logins."""
from dataclasses import dataclass
from psycopg import sql
from psycopg.rows import tuple_row

from .runtime_roles import NAME
from .crop_cycle_input_stream import MAX_RECORDS

VERSION = 'crop-harvest-registered-result-v1'
TABLE = 'harvest_registered_results'
MAX_METADATA_BYTES = 128 * 1024
MAX_ROWS = 2 * MAX_RECORDS
IMMUTABLE_BODY = " BEGIN RAISE EXCEPTION 'harvest research result is immutable'; END "
_DOC = sql.SQL("convert_from(payload_raw,'UTF8')::jsonb")
_RAW = sql.SQL("convert_from(payload_raw,'UTF8')::json")


@dataclass(frozen=True)
class HarvestRegistryPolicy:
    schema: str
    owner: str
    publisher: str
    reader: str
    database: str

    def __post_init__(self):
        values = (self.schema, self.owner, self.publisher, self.reader, self.database)
        if any(type(v) is not str or not NAME.fullmatch(v) or v.startswith('pg_') for v in values) or len(set(values)) != 5:
            raise ValueError('invalid harvest registry scope')


def _database(conn, policy):
    if type(policy) is not HarvestRegistryPolicy:raise ValueError('explicit harvest registry policy required')
    if _one(conn, 'SELECT current_database()')[0] != policy.database:
        raise ValueError('harvest registry database mismatch')


def _all(conn, query, params=None):
    with conn.cursor(row_factory=tuple_row) as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def _one(conn, query, params=None):
    rows = _all(conn, query, params)
    return rows[0] if rows else None


def _path(doc, keys, text=False):
    return sql.SQL('({} {} {}::text[])').format(doc, sql.SQL('#>>' if text else '#>'), sql.Literal(list(keys)))


def _closed(keys, path=()):
    obj = _path(_DOC, path) if path else _DOC
    return sql.SQL("(CASE WHEN jsonb_typeof({v})='object' THEN {v} ?& {k}::text[] AND ({v}-{k}::text[])='{{}}'::jsonb ELSE false END) IS TRUE").format(v=obj, k=sql.Literal(list(keys)))


def _pin(column, path, kind='string'):
    return sql.SQL('(jsonb_typeof({v})={kind} AND {raw}={col}::text) IS TRUE').format(
        v=_path(_DOC, path), kind=sql.Literal(kind), raw=_path(_RAW, path, True), col=sql.Identifier(column))


def install_harvest_registry(conn, policy):
    _database(conn, policy)
    previous_role = _one(conn, 'SELECT current_user')[0]
    ns = sql.Identifier(policy.schema);table = sql.Identifier(policy.schema, TABLE)
    top = ('schema_version', 'status', 'claim_scope', 'rights_or_gate_approval', 'tenant_id', 'result_id',
           'parent_result_id', 'farm', 'source', 'artifact', 'parameters', 'code')
    checks = [_closed(top), _closed(('scenario_id','scenario_revision','registration_sha256','crop_id'), ('farm',)),
        _closed(('result_id','payload_sha256','input_root_sha256','artifact_sha256','math_manifest_sha256','source_status'), ('source',)),
        _closed(('key','sha256','row_count','row_chain_sha256','writer_code_sha256'), ('artifact',)),
        _closed(('mass_sha256','allocation_sha256'), ('parameters',)),
        _closed(('publication_code_sha256','registry_schema_code_sha256','artifact_code_sha256'), ('code',))]
    for key, value in (('schema_version', VERSION), ('status', 'stored_unpublished_research'),
                       ('claim_scope', 'synthetic_harvest_allocation_math_only')):
        checks.append(sql.SQL('({}={}::jsonb) IS TRUE').format(_path(_DOC, (key,)), sql.Literal('"'+value+'"')))
    checks.append(sql.SQL("({}='false'::jsonb) IS TRUE").format(_path(_DOC, ('rights_or_gate_approval',))))
    checks.append(sql.SQL("({} IN ('completed','hold')) IS TRUE").format(_path(_RAW, ('source','source_status'), True)))
    pins = {'tenant_id':('tenant_id',), 'result_id':('result_id',), 'parent_result_id':('parent_result_id',),
        'scenario_id':('farm','scenario_id'), 'scenario_revision':('farm','scenario_revision'),
        'registration_sha256':('farm','registration_sha256'), 'crop_id':('farm','crop_id'),
        'artifact_key':('artifact','key'), 'artifact_sha256':('artifact','sha256'),
        'row_chain_sha256':('artifact','row_chain_sha256'), 'mass_parameter_sha256':('parameters','mass_sha256'),
        'allocation_parameter_sha256':('parameters','allocation_sha256')}
    checks.extend(_pin(column, path) for column, path in pins.items())
    checks += [_pin('parent_result_id', ('source','result_id')), _pin('row_count', ('artifact','row_count'), 'number')]
    for section, names in [('source', ('payload_sha256','input_root_sha256','artifact_sha256','math_manifest_sha256')),
        ('artifact', ('writer_code_sha256',)), ('code', ('publication_code_sha256','registry_schema_code_sha256','artifact_code_sha256'))]:
        for name in names:
            checks.append(sql.SQL("(jsonb_typeof({v})='string' AND {s} ~ '^[0-9a-f]{{64}}$') IS TRUE").format(
                v=_path(_DOC, (section,name)), s=_path(_RAW, (section,name), True)))
    constraints = sql.SQL(',').join(sql.SQL('CHECK ({})').format(check) for check in checks)
    with conn.transaction():
        conn.execute(sql.SQL('CREATE ROLE {} NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS').format(sql.Identifier(policy.owner)))
        for role in (policy.publisher, policy.reader):
            conn.execute(sql.SQL('CREATE ROLE {} LOGIN NOINHERIT PASSWORD NULL CONNECTION LIMIT 8 NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS').format(sql.Identifier(role)))
            conn.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(policy.database), sql.Identifier(role)))
        conn.execute(sql.SQL('CREATE SCHEMA {} AUTHORIZATION {}').format(ns, sql.Identifier(policy.owner)))
        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
        conn.execute(sql.SQL('''CREATE TABLE {t} (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            result_id text NOT NULL CHECK (result_id ~ '^crop-harvest-registered-result-v1:[0-9a-f]{{64}}$'),
            parent_result_id text NOT NULL CHECK (parent_result_id ~ '^crop-cycle-verified-result-v1:[0-9a-f]{{64}}$'),
            scenario_id text NOT NULL CHECK (length(scenario_id) BETWEEN 1 AND 200),
            scenario_revision text NOT NULL CHECK (length(scenario_revision) BETWEEN 1 AND 200),
            registration_sha256 char(64) NOT NULL CHECK (registration_sha256 ~ '^[0-9a-f]{{64}}$'),
            crop_id text NOT NULL CHECK (length(crop_id) BETWEEN 1 AND 200),
            artifact_key char(64) NOT NULL CHECK (artifact_key ~ '^[0-9a-f]{{64}}$'),
            artifact_sha256 char(64) NOT NULL CHECK (artifact_sha256 ~ '^[0-9a-f]{{64}}$'),
            row_count integer NOT NULL CHECK (row_count BETWEEN 0 AND {rows}),
            row_chain_sha256 char(64) NOT NULL CHECK (row_chain_sha256 ~ '^[0-9a-f]{{64}}$'),
            mass_parameter_sha256 char(64) NOT NULL CHECK (mass_parameter_sha256 ~ '^[0-9a-f]{{64}}$'),
            allocation_parameter_sha256 char(64) NOT NULL CHECK (allocation_parameter_sha256 ~ '^[0-9a-f]{{64}}$'),
            payload_raw bytea NOT NULL CHECK (octet_length(payload_raw) BETWEEN 1 AND {maxbytes}),
            payload_sha256 char(64) NOT NULL CHECK (payload_sha256=encode(sha256(payload_raw),'hex')),
            integrity_signature char(64) NOT NULL CHECK (integrity_signature ~ '^[0-9a-f]{{64}}$'),
            registered_by text NOT NULL CHECK (length(registered_by) BETWEEN 1 AND 200),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id,result_id),
            CHECK ((convert_from(payload_raw,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS TRUE),
            {checks})''').format(t=table, rows=sql.Literal(MAX_ROWS), maxbytes=sql.Literal(MAX_METADATA_BYTES), checks=constraints))
        conn.execute(sql.SQL('CREATE INDEX harvest_registered_results_parent ON {} (tenant_id,parent_result_id)').format(table))
        routine = sql.Identifier(policy.schema, 'reject_harvest_result_change')
        conn.execute(sql.SQL('CREATE FUNCTION {}() RETURNS trigger LANGUAGE plpgsql AS {}').format(routine, sql.Literal(IMMUTABLE_BODY)))
        conn.execute(sql.SQL('CREATE TRIGGER harvest_result_immutable BEFORE UPDATE OR DELETE ON {} FOR EACH ROW EXECUTE FUNCTION {}()').format(table, routine))
        conn.execute(sql.SQL('REVOKE ALL ON SCHEMA {} FROM PUBLIC').format(ns))
        conn.execute(sql.SQL('REVOKE ALL ON TABLE {} FROM PUBLIC').format(table))
        conn.execute(sql.SQL('REVOKE ALL ON FUNCTION {}() FROM PUBLIC').format(routine))
        for role, rights in ((policy.publisher, 'SELECT,INSERT'), (policy.reader, 'SELECT')):
            conn.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO {}').format(ns, sql.Identifier(role)))
            conn.execute(sql.SQL('GRANT {} ON TABLE {} TO {}').format(sql.SQL(rights), table, sql.Identifier(role)))
        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(previous_role)))


def audit_harvest_registry(conn, policy):
    _database(conn, policy)
    owner = _one(conn, 'SELECT r.oid,n.nspowner FROM pg_roles r JOIN pg_namespace n ON n.nspname=%s WHERE r.rolname=%s',
                         (policy.schema,policy.owner))
    if owner is None or owner[0] != owner[1]:raise ValueError('harvest registry owner mismatch')
    roles = (policy.owner,policy.publisher,policy.reader)
    for role in roles:
        row = _one(conn, 'SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,rolcanlogin,rolinherit,rolconnlimit FROM pg_roles WHERE rolname=%s', (role,))
        if row is None or any(row[:5]) or row[5] != (role != policy.owner) or row[6] or (role != policy.owner and row[7] != 8):
            raise ValueError('harvest registry role mismatch')
    membership = _one(conn, 'SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid JOIN pg_roles v ON v.oid=m.member WHERE r.rolname=ANY(%s) OR v.rolname=ANY(%s) LIMIT 1', (list(roles),list(roles)))
    if membership:raise ValueError('harvest registry role membership forbidden')
    relations = _all(conn, 'SELECT c.relname,c.relkind,c.relowner FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=%s', (policy.schema,))
    expected = {(TABLE,'r'),(TABLE+'_pkey','i'),(TABLE+'_parent','i')}
    if {(r[0],r[1]) for r in relations} != expected or any(r[2] != owner[0] for r in relations):raise ValueError('harvest registry objects mismatch')
    routines = _all(conn, 'SELECT p.proname,p.proowner,p.prosecdef,p.prosrc,p.pronargs,p.prorettype,l.lanname,p.proconfig FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_language l ON l.oid=p.prolang WHERE n.nspname=%s', (policy.schema,))
    if routines != [('reject_harvest_result_change',owner[0],False,IMMUTABLE_BODY,0,2279,'plpgsql',None)]:raise ValueError('harvest registry routine mismatch')
    triggers = _all(conn, "SELECT t.tgname,t.tgenabled,t.tgtype,p.proname,n.nspname,t.tgnargs,t.tgqual IS NULL,t.tgattr=''::int2vector FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace s ON s.oid=c.relnamespace JOIN pg_proc p ON p.oid=t.tgfoid JOIN pg_namespace n ON n.oid=p.pronamespace WHERE s.nspname=%s AND NOT t.tgisinternal", (policy.schema,))
    if triggers != [('harvest_result_immutable','O',27,'reject_harvest_result_change',policy.schema,0,True,True)]:raise ValueError('harvest registry immutable trigger mismatch')
    extra = _one(conn, "SELECT 1 FROM pg_namespace WHERE nspowner=%s AND nspname<>%s UNION ALL SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relowner=%s AND n.nspname<>%s AND n.nspname<>'pg_toast' UNION ALL SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE p.proowner=%s AND n.nspname<>%s LIMIT 1", (owner[0],policy.schema)*3)
    if extra:raise ValueError('harvest registry owner isolation required')
    target = policy.schema+'.'+TABLE
    for role in (policy.publisher,policy.reader):
        privileges = ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER') + (('MAINTAIN',) if conn.info.server_version >= 170000 else ())
        for privilege in privileges:
            actual = _one(conn, 'SELECT has_table_privilege(%s,%s,%s)', (role,target,privilege))[0]
            if actual != (privilege=='SELECT' or role==policy.publisher and privilege=='INSERT'):raise ValueError('harvest registry grants mismatch')
        usage, create, dbcreate, connect = _one(conn, "SELECT has_schema_privilege(%s,%s,'USAGE'),has_schema_privilege(%s,%s,'CREATE'),has_database_privilege(%s,%s,'CREATE'),has_database_privilege(%s,%s,'CONNECT')", (role,policy.schema,role,policy.schema,role,policy.database,role,policy.database))
        if not usage or create or dbcreate or not connect:raise ValueError('harvest registry scope grants mismatch')
        if _one(conn, "SELECT has_function_privilege(%s,%s,'EXECUTE')", (role,policy.schema+'.reject_harvest_result_change()'))[0]:
            raise ValueError('harvest registry routine grants forbidden')
    public = _one(conn, "SELECT 1 FROM pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) a WHERE n.nspname=%s AND a.grantee=0 UNION ALL SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(c.relacl) a WHERE n.nspname=%s AND a.grantee=0 UNION ALL SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE n.nspname=%s AND a.grantee=0 LIMIT 1", (policy.schema,)*3)
    if public:raise ValueError('harvest registry PUBLIC grants forbidden')
    columns = _one(conn, 'SELECT 1 FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=%s AND a.attacl IS NOT NULL LIMIT 1', (policy.schema,))
    if columns:raise ValueError('harvest registry column grants forbidden')
    approved = [row[0] for row in _all(conn, 'SELECT oid FROM pg_roles WHERE rolname=ANY(%s)', (list(roles),))]
    runtime = [row[0] for row in _all(conn, 'SELECT oid FROM pg_roles WHERE rolname=ANY(%s)', ([policy.publisher,policy.reader],))]
    grantable = _one(conn, 'SELECT 1 FROM pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) a WHERE n.nspname=%s AND a.grantee=ANY(%s) AND a.is_grantable UNION ALL SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(c.relacl) a WHERE n.nspname=%s AND a.grantee=ANY(%s) AND a.is_grantable LIMIT 1', (policy.schema,runtime)*2)
    if grantable:raise ValueError('harvest registry runtime grant options forbidden')
    unexpected = _one(conn, "SELECT 1 FROM pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) a WHERE n.nspname=%s AND NOT a.grantee=ANY(%s) UNION ALL SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(c.relacl) a WHERE n.nspname=%s AND NOT a.grantee=ANY(%s) UNION ALL SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE n.nspname=%s AND NOT a.grantee=ANY(%s) LIMIT 1", (policy.schema,approved)*3)
    if unexpected:raise ValueError('harvest registry unexpected ACL identity')
    return {'schema':policy.schema,'table':TABLE,'publisher_rights':['SELECT','INSERT'],'reader_rights':['SELECT'],'owner_login':False}
