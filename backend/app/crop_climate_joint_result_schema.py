"""Provisioner-only references to immutable joint crop/climate research results."""
from psycopg import sql

from .crop_climate_joint_storage import LIMITS, VERSION as ARTIFACT_VERSION
from .runtime_roles import NAME

VERSION = 'joint-crop-climate-result-v1'
TABLE = 'crop_climate_joint_research_results'
MAX_METADATA_BYTES = LIMITS['metadata_bytes']
FARM_KEYS = ('scenario_id', 'scenario_revision', 'registration_job_id', 'registration_sha256',
             'crop_id', 'batch_id', 'zone_id')
INPUT_KEYS = ('program_id', 'source_sha256', 'context_sha256', 'time_binding_sha256',
              'evidence_sha256', 'start_utc', 'end_utc')
ARTIFACT_STRINGS = {'ref': 'artifact_ref', 'sha256': 'artifact_sha256',
    'header_sha256': 'artifact_header_sha256', 'status': 'artifact_status',
    **{key: key for key in ('intent_sha256', 'farm_binding_sha256', 'head_sha256', 'proof_sha256')}}
COUNTER_BOUNDS = {'steps': (0, 4096), 'planned_steps': (1, 4096), 'sample_count': (0, 512),
    'event_count': (0, 128), 'commit_count': (1, LIMITS['commits']),
    'storage_bytes': (1, LIMITS['directory_bytes']), 'file_count': (1, LIMITS['files'])}
_DOC = sql.SQL("convert_from(payload_raw,'UTF8')::jsonb")
_RAW_DOC = sql.SQL("convert_from(payload_raw,'UTF8')::json")
_UTC = r'^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9][.][0-9]{6}Z$'


def _path(doc, keys, *, text=False):
    return sql.SQL('({} {} {}::text[])').format(doc, sql.SQL('#>>' if text else '#>'), sql.Literal(list(keys)))


def _closed(obj, keys):
    return sql.SQL("(CASE WHEN jsonb_typeof({obj})='object' THEN {obj} ?& {keys}::text[] "
                   "AND ({obj}-{keys}::text[])='{{}}'::jsonb ELSE false END) IS TRUE").format(
                       obj=obj, keys=sql.Literal(list(keys)))


def _pin(column, keys, kind='string'):
    return sql.SQL('(jsonb_typeof({value})={kind} AND {raw}={column}::text) IS TRUE').format(
        value=_path(_DOC, keys), kind=sql.Literal(kind), raw=_path(_RAW_DOC, keys, text=True),
        column=sql.Identifier(column))


def install_joint_crop_climate_result_schema(conn, schema):
    """Create fresh objects atomically; an existing installation needs a migration."""
    if type(schema) is not str or not NAME.fullmatch(schema):
        raise ValueError('invalid joint crop climate schema')
    top = ('schema_version', 'status', 'claim_scope', 'G0_G4', 'result_id', 'tenant_id',
           'study_id', 'revision', 'farm', 'input', 'artifact', 'binding', 'policies', 'code')
    checks = [_closed(_DOC, top), _closed(_path(_DOC, ('farm',)), FARM_KEYS),
              _closed(_path(_DOC, ('input',)), INPUT_KEYS),
              _closed(_path(_DOC, ('artifact',)), (*ARTIFACT_STRINGS, *COUNTER_BOUNDS))]
    for key, value in (('schema_version', VERSION), ('status', 'stored_unpublished_research'),
                       ('claim_scope', 'synthetic_joint_crop_climate_math_only'), ('G0_G4', 'not_assessed')):
        checks.append(sql.SQL('({}={}::jsonb) IS TRUE').format(_path(_DOC, (key,)), sql.Literal('"'+value+'"')))
    for key in ('binding', 'policies', 'code'):
        checks.append(sql.SQL("(jsonb_typeof({})='object') IS TRUE").format(_path(_DOC, (key,))))
    checks += [_pin(k, (k,)) for k in ('tenant_id', 'study_id', 'revision', 'result_id')]
    checks += [_pin(k, ('farm', k)) for k in FARM_KEYS]
    checks += [_pin(k, ('input', k)) for k in INPUT_KEYS]
    checks += [_pin(column, ('artifact', key)) for key, column in ARTIFACT_STRINGS.items()]
    checks += [_pin(k, ('artifact', k), 'number') for k in COUNTER_BOUNDS]
    identifiers = ('tenant_id', 'study_id', 'revision', 'scenario_id', 'scenario_revision',
                   'crop_id', 'batch_id', 'zone_id', 'program_id', 'registered_by')
    hashes = ('registration_sha256', 'source_sha256', 'context_sha256', 'time_binding_sha256',
              'evidence_sha256', 'artifact_sha256', 'artifact_header_sha256', 'intent_sha256',
              'farm_binding_sha256', 'head_sha256', 'proof_sha256', 'integrity_signature')
    columns = [sql.SQL('{} text NOT NULL CHECK ({} ~ {})').format(sql.Identifier(k), sql.Identifier(k),
               sql.Literal(r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$')) for k in identifiers]
    columns += [sql.SQL('{} text NOT NULL CHECK ({} ~ {})').format(sql.Identifier(k), sql.Identifier(k),
                sql.Literal(r'^[0-9a-f]{64}$')) for k in hashes]
    columns += [sql.SQL('{} bigint NOT NULL CHECK ({} BETWEEN {} AND {})').format(
        sql.Identifier(k), sql.Identifier(k), sql.Literal(bounds[0]), sql.Literal(bounds[1]))
        for k, bounds in COUNTER_BOUNDS.items()]
    columns += [sql.SQL('{} text NOT NULL CHECK ({} ~ {})').format(sql.Identifier(k), sql.Identifier(k),
                sql.Literal(_UTC)) for k in ('start_utc', 'end_utc')]
    target = sql.Identifier(schema, TABLE)
    routine = sql.Identifier(schema, 'reject_joint_crop_climate_result_change')
    with conn.transaction():
        conn.execute(sql.SQL('''CREATE TABLE {target} (
            {columns}, registration_job_id uuid NOT NULL,
            result_id text NOT NULL CHECK (result_id ~ {result_pattern}),
            artifact_ref text NOT NULL CHECK (artifact_ref={artifact_prefix} || artifact_sha256),
            artifact_status text NOT NULL CHECK (artifact_status IN ('completed','hold')),
            payload_raw bytea NOT NULL CHECK (octet_length(payload_raw) BETWEEN 1 AND {metadata}),
            payload_sha256 text NOT NULL CHECK (payload_sha256=encode(sha256(payload_raw),'hex')),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id,study_id,revision), UNIQUE (tenant_id,result_id),
            UNIQUE (tenant_id,intent_sha256),
            FOREIGN KEY (tenant_id,registration_job_id) REFERENCES {jobs} (tenant_id,job_id),
            CHECK (steps<=planned_steps AND (artifact_status<>'completed' OR steps=planned_steps)),
            CHECK (start_utc::timestamptz < end_utc::timestamptz
                AND end_utc::timestamptz-start_utc::timestamptz<=interval '600 seconds'),
            CHECK ((convert_from(payload_raw,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS TRUE),
            {checks}
        )''').format(target=target, columns=sql.SQL(',').join(columns),
            result_pattern=sql.Literal('^'+VERSION+r':[0-9a-f]{64}$'),
            artifact_prefix=sql.Literal(ARTIFACT_VERSION+':'), metadata=sql.Literal(MAX_METADATA_BYTES),
            jobs=sql.Identifier(schema, 'jobs'), checks=sql.SQL(',').join(
                sql.SQL('CHECK ({})').format(check) for check in checks)))
        conn.execute(sql.SQL('''CREATE FUNCTION {}() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'joint crop climate research result is immutable'; END $$''').format(routine))
        conn.execute(sql.SQL('''CREATE TRIGGER joint_crop_climate_result_immutable
            BEFORE UPDATE OR DELETE ON {} FOR EACH ROW EXECUTE FUNCTION {}()''').format(target, routine))
        conn.execute(sql.SQL('REVOKE ALL ON TABLE {} FROM PUBLIC').format(target))
        conn.execute(sql.SQL('REVOKE ALL ON FUNCTION {}() FROM PUBLIC').format(routine))
