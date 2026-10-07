"""Provisioner-only metadata for the explicit verified calculation result version."""
from psycopg import sql

from .crop_cycle_calculation_artifact import LIMITS
from .crop_cycle_input_stream import MAX_RECORDS
from .runtime_roles import NAME

VERSION='crop-cycle-verified-result-v1'
TABLE='crop_cycle_verified_research_results'
MAX_METADATA_BYTES=LIMITS['metadata_bytes']
_DOC=sql.SQL("convert_from(payload_raw,'UTF8')::jsonb")
_RAW_DOC=sql.SQL("convert_from(payload_raw,'UTF8')::json")


def _path(doc,keys,*,text=False):
    return sql.SQL('({} {} {}::text[])').format(doc,sql.SQL('#>>' if text else '#>'),sql.Literal(list(keys)))


def _closed(obj,keys):
    return sql.SQL("(CASE WHEN jsonb_typeof({obj})='object' THEN {obj} ?& {keys}::text[] "
                   "AND ({obj}-{keys}::text[])='{{}}'::jsonb ELSE false END) IS TRUE").format(obj=obj,keys=sql.Literal(list(keys)))


def _pin(column,keys,kind='string'):
    return sql.SQL('(jsonb_typeof({value})={kind} AND {raw}={column}::text) IS TRUE').format(
        value=_path(_DOC,keys),kind=sql.Literal(kind),raw=_path(_RAW_DOC,keys,text=True),column=sql.Identifier(column))


def install_calculation_cycle_crop_result_schema(conn,schema):
    """Create fresh objects atomically; existing tables require a separate migration."""
    if type(schema) is not str or not NAME.fullmatch(schema):raise ValueError('invalid cycle crop schema')
    namespace=sql.Identifier(schema);target=sql.Identifier(schema,TABLE)
    farm_keys=('scenario_id','scenario_revision','registration_job_id','registration_sha256')
    artifact_strings={'ref':'artifact_ref','sha256':'artifact_sha256','header_sha256':'artifact_header_sha256','status':'artifact_status'}
    counters=('steps','planned_steps','sample_count','event_count','commit_count','storage_bytes','file_count')
    top=('schema_version','status','claim_scope','result_id','tenant_id','study_id','revision',
         'farm','input_root_sha256','artifact','binding','policies','code')
    checks=[_closed(_DOC,top),_closed(_path(_DOC,('farm',)),farm_keys),
            _closed(_path(_DOC,('artifact',)),tuple(artifact_strings)+counters)]
    for key,value in (('schema_version',VERSION),('status','stored_unpublished_research'),('claim_scope','synthetic_crop_math_only')):
        checks.append(sql.SQL('({}={}::jsonb) IS TRUE').format(_path(_DOC,(key,)),sql.Literal('"'+value+'"')))
    for key in ('binding','policies','code'):
        checks.append(sql.SQL("(jsonb_typeof({})='object') IS TRUE").format(_path(_DOC,(key,))))
    checks += [_pin(k,(k,)) for k in ('tenant_id','study_id','revision','result_id','input_root_sha256')]
    checks += [_pin(k,('farm',k)) for k in farm_keys]
    checks += [_pin(column,('artifact',key)) for key,column in artifact_strings.items()]
    checks += [_pin(k,('artifact',k),'number') for k in counters]
    constraints=sql.SQL(',').join(sql.SQL('CHECK ({})').format(check) for check in checks)
    with conn.transaction():
        conn.execute(sql.SQL('''
            CREATE TABLE {target} (
                tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
                study_id text NOT NULL CHECK (length(study_id) BETWEEN 1 AND 200),
                revision text NOT NULL CHECK (length(revision) BETWEEN 1 AND 200),
                result_id text NOT NULL CHECK (result_id ~ '^crop-cycle-verified-result-v1:[0-9a-f]{{64}}$'),
                scenario_id text NOT NULL CHECK (length(scenario_id) BETWEEN 1 AND 200),
                scenario_revision text NOT NULL CHECK (length(scenario_revision) BETWEEN 1 AND 200),
                registration_job_id uuid NOT NULL,
                registration_sha256 char(64) NOT NULL CHECK (registration_sha256 ~ '^[0-9a-f]{{64}}$'),
                input_root_sha256 char(64) NOT NULL CHECK (input_root_sha256 ~ '^[0-9a-f]{{64}}$'),
                artifact_sha256 char(64) NOT NULL CHECK (artifact_sha256 ~ '^[0-9a-f]{{64}}$'),
                artifact_header_sha256 char(64) NOT NULL CHECK (artifact_header_sha256 ~ '^[0-9a-f]{{64}}$'),
                artifact_ref text NOT NULL CHECK (artifact_ref='crop-cycle-verified-artifact-v1:' || artifact_sha256),
                artifact_status text NOT NULL CHECK (artifact_status IN ('completed','hold')),
                steps bigint NOT NULL CHECK (steps BETWEEN 0 AND 40000000),
                planned_steps bigint NOT NULL CHECK (planned_steps BETWEEN 1 AND 40000000),
                sample_count integer NOT NULL CHECK (sample_count BETWEEN 0 AND {records}),
                event_count integer NOT NULL CHECK (event_count BETWEEN 0 AND {records}),
                commit_count integer NOT NULL CHECK (commit_count BETWEEN 1 AND {commits}),
                storage_bytes bigint NOT NULL CHECK (storage_bytes BETWEEN 1 AND {bytes}),
                file_count integer NOT NULL CHECK (file_count BETWEEN 1 AND {files}),
                payload_raw bytea NOT NULL CHECK (octet_length(payload_raw) BETWEEN 1 AND {metadata}),
                payload_sha256 char(64) NOT NULL CHECK (payload_sha256=encode(sha256(payload_raw),'hex')),
                integrity_signature char(64) NOT NULL CHECK (integrity_signature ~ '^[0-9a-f]{{64}}$'),
                registered_by text NOT NULL CHECK (length(registered_by) BETWEEN 1 AND 200),
                recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
                PRIMARY KEY (tenant_id,study_id,revision), UNIQUE (tenant_id,result_id),
                FOREIGN KEY (tenant_id,registration_job_id) REFERENCES {namespace}.jobs (tenant_id,job_id),
                CHECK (steps<=planned_steps AND (artifact_status<>'completed' OR steps=planned_steps)),
                CHECK ((convert_from(payload_raw,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS TRUE),
                {constraints}
            )
        ''').format(target=target,namespace=namespace,constraints=constraints,records=sql.Literal(MAX_RECORDS),
                    commits=sql.Literal(LIMITS['commits']),bytes=sql.Literal(LIMITS['directory_bytes']),
                    files=sql.Literal(LIMITS['files']),metadata=sql.Literal(MAX_METADATA_BYTES)))
        routine=sql.Identifier(schema,'reject_verified_cycle_crop_result_change')
        conn.execute(sql.SQL('''
            CREATE FUNCTION {}() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'verified cycle crop research result is immutable'; END $$
        ''').format(routine))
        conn.execute(sql.SQL('''
            CREATE TRIGGER verified_cycle_crop_result_immutable BEFORE UPDATE OR DELETE ON {}
            FOR EACH ROW EXECUTE FUNCTION {}()
        ''').format(target,routine))
        conn.execute(sql.SQL('REVOKE ALL ON TABLE {} FROM PUBLIC').format(target))
        conn.execute(sql.SQL('REVOKE ALL ON FUNCTION {}() FROM PUBLIC').format(routine))
