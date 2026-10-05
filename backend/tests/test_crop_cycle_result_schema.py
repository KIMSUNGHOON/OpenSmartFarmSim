"""Real SCRAM schema fixtures, before current farm rights or result custody."""
from copy import deepcopy
from hashlib import sha256
import json
from uuid import uuid4

from psycopg import errors,sql
import pytest

from app.runtime_login import connect_runtime
from app.runtime_roles import audit_runtime_roles,RolePolicyHold
from app.thermal_run_store import _canonical
from login_database import login_database,login_scope


@pytest.fixture(autouse=True)
def forbid_crop_execution(monkeypatch):
    from app import crop_cycle_stream_execution as engine
    def forbidden(*args,**kwargs):raise AssertionError('schema must not calculate a crop result')
    monkeypatch.setattr(engine,'advance_chunk',forbidden)
    monkeypatch.setattr(engine.short._Evaluator,'rhs',forbidden)


def install(conn,schema):
    from app.crop_cycle_result_schema import install_cycle_crop_result_schema
    install_cycle_crop_result_schema(conn,schema)


@pytest.mark.parametrize('schema',[None,True,12,'bad-name','x;DROP SCHEMA public','a'*64,'Mixed',''])
def test_invalid_identifier_is_rejected_before_sql(schema):
    with pytest.raises(ValueError):install(None,schema)


def metadata(row):
    return {'schema_version':'crop-cycle-result-v1','status':'stored_unpublished_research',
        'claim_scope':'synthetic_crop_math_only',
        **{k:row[k] for k in ('tenant_id','study_id','revision','result_id','input_root_sha256')},
        'farm':{k:str(row[k]) for k in ('scenario_id','scenario_revision','registration_job_id','registration_sha256')},
        'artifact':{'ref':row['artifact_ref'],'sha256':row['artifact_sha256'],
            'header_sha256':row['artifact_header_sha256'],'status':row['artifact_status'],
            **{k:row[k] for k in ('steps','planned_steps','sample_count','event_count','commit_count','storage_bytes','file_count')}},
        'binding':{},'policies':{},'code':{}}


def with_payload(row,value=None,raw=None):
    row=dict(row);raw=_canonical(value if value is not None else metadata(row)) if raw is None else raw
    return {**row,'payload_raw':raw,'payload_sha256':sha256(raw).hexdigest()}


def fixture_row(base,policy):
    job=base.submit('tenant-a','research',{'fixture':'synthetic_cycle_schema_only'},uuid4().hex)
    return with_payload({'tenant_id':'tenant-a','study_id':'schema-study','revision':'r1',
        'result_id':'crop-cycle-result-v1:'+'1'*64,'scenario_id':'synthetic-schema-farm','scenario_revision':'r1',
        'registration_job_id':job['job_id'],'registration_sha256':job['input_sha256'],
        'input_root_sha256':'2'*64,'artifact_sha256':'3'*64,'artifact_header_sha256':'4'*64,
        'artifact_ref':'crop-cycle-artifact-v1:'+'3'*64,'artifact_status':'completed',
        'steps':120,'planned_steps':120,'sample_count':3,'event_count':0,'commit_count':1,
        'storage_bytes':1,'file_count':1,'integrity_signature':'5'*64,'registered_by':policy.roles['authority']})


def target(policy):return sql.Identifier(policy.schema,'crop_cycle_research_results')


def insert(conn,policy,row):
    keys=list(row)
    conn.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(target(policy),
        sql.SQL(',').join(map(sql.Identifier,keys)),sql.SQL(',').join(sql.Placeholder() for _ in keys)),
        tuple(row[k] for k in keys))


def owner(conn,policy):conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))


@pytest.fixture
def cycle_schema(login_scope):
    base,policy,dsns=login_scope
    with base.connect() as conn:
        assert conn.pgconn.used_password
        owner(conn,policy);install(conn,policy.schema)
    return base,policy,dsns,fixture_row(base,policy)


def test_actual_scram_owner_row_roundtrip_and_default_runtime_grants_remain_zero(cycle_schema):
    base,policy,dsns,row=cycle_schema
    with base.connect() as conn:
        owner(conn,policy);insert(conn,policy,row)
        actual=conn.execute(sql.SQL('SELECT * FROM {}').format(target(policy))).fetchone()
        assert bytes(actual['payload_raw'])==row['payload_raw']
        assert actual['payload_sha256']==row['payload_sha256'] and actual['recorded_at'].tzinfo
        assert str(actual['registration_job_id'])==str(row['registration_job_id'])
    with base.connect() as conn:assert audit_runtime_roles(conn,policy)['tables']>0
    for kind,dsn in dsns.items():
        for query in (sql.SQL('SELECT * FROM {} LIMIT 0').format(target(policy)),
                      sql.SQL('INSERT INTO {} SELECT * FROM {} WHERE false').format(target(policy),target(policy)),
                      sql.SQL('UPDATE {} SET revision=revision').format(target(policy)),
                      sql.SQL('DELETE FROM {}').format(target(policy)),sql.SQL('TRUNCATE {}').format(target(policy))):
            with connect_runtime(dsn,policy,kind) as conn,pytest.raises(errors.InsufficientPrivilege):
                assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
                if kind=='supervisor':conn.execute('SET TRANSACTION READ WRITE')
                conn.execute(query)


def test_owner_update_delete_are_immutable_and_reinstall_preserves_original_row(cycle_schema):
    base,policy,_,row=cycle_schema
    with base.connect() as conn:owner(conn,policy);insert(conn,policy,row)
    for query in (sql.SQL('UPDATE {} SET revision=revision').format(target(policy)),sql.SQL('DELETE FROM {}').format(target(policy))):
        with base.connect() as conn,pytest.raises(errors.RaiseException,match='immutable'):
            owner(conn,policy);conn.execute(query)
    with base.connect() as conn:
        owner(conn,policy)
        with pytest.raises(errors.DuplicateTable):install(conn,policy.schema)
        assert bytes(conn.execute(sql.SQL('SELECT payload_raw FROM {}').format(target(policy))).fetchone()['payload_raw'])==row['payload_raw']


BAD_COLUMNS=[('tenant_id',''),('study_id',''),('revision',''),('scenario_id',''),('scenario_revision',''),
    ('registered_by',''),('result_id','crop-result-v3:'+'1'*64),('input_root_sha256','x'*64),
    ('artifact_sha256','G'*64),('artifact_header_sha256','x'),('registration_sha256','z'*64),
    ('artifact_ref','/tmp/unsafe-result'),('artifact_status','approved'),('steps',-1),('steps',121),
    ('planned_steps',0),('planned_steps',40000001),('sample_count',-1),('sample_count',131073),
    ('event_count',131073),('commit_count',0),('commit_count',16385),('storage_bytes',0),
    ('storage_bytes',536870913),('file_count',0),('file_count',65537),('integrity_signature','x'*64),
    ('payload_sha256','0'*64)]


@pytest.mark.parametrize('key,value',BAD_COLUMNS,ids=[k+'-'+str(v) for k,v in BAD_COLUMNS])
def test_matching_metadata_cannot_bypass_column_ranges_ids_or_hash(cycle_schema,key,value):
    base,policy,_,row=cycle_schema
    changed=with_payload({**row,key:value})
    if key=='payload_sha256':changed['payload_sha256']=value
    with base.connect() as conn,pytest.raises(errors.CheckViolation):owner(conn,policy);insert(conn,policy,changed)


@pytest.mark.parametrize('kind',['cross-tenant','missing-job'])
def test_registration_fk_requires_same_tenant_existing_job(cycle_schema,kind):
    base,policy,_,row=cycle_schema
    changed=with_payload({**row,**({'tenant_id':'tenant-b'} if kind=='cross-tenant' else {'registration_job_id':uuid4()})})
    with base.connect() as conn,pytest.raises(errors.ForeignKeyViolation):owner(conn,policy);insert(conn,policy,changed)


@pytest.mark.parametrize('kind',['version','status','scope','root','farm','missing','null','extra','artifact-extra',
    'farm-extra','binding-type','code-type','counter-bool','counter-float','counter-string','counter-null','counter-exponent'])
def test_rehashed_metadata_identity_shape_or_counter_type_is_rejected(cycle_schema,kind):
    base,policy,_,row=cycle_schema;packet=metadata(row)
    if kind=='version':packet['schema_version']='crop-result-v3'
    if kind=='status':packet['status']='approved'
    if kind=='scope':packet['claim_scope']='production_prediction'
    if kind=='root':packet['artifact']['sha256']='6'*64
    if kind=='farm':packet['farm']['scenario_id']='another-farm'
    if kind=='missing':del packet['artifact']['sample_count']
    if kind=='null':packet['input_root_sha256']=None
    if kind=='extra':packet['filesystem_path']='/tmp/unsafe-result'
    if kind=='artifact-extra':packet['artifact']['filesystem_path']='/tmp/unsafe-result'
    if kind=='farm-extra':packet['farm']['tenant_id']='tenant-b'
    if kind=='binding-type':packet['binding']=[]
    if kind=='code-type':packet['code']=None
    if kind.startswith('counter-'):
        packet['artifact']['steps']={'counter-bool':True,'counter-float':120.0,'counter-string':'120',
            'counter-null':None,'counter-exponent':120}[kind]
    raw=_canonical(packet)
    if kind=='counter-exponent':raw=raw.replace(b'"steps":120',b'"steps":1.2e2')
    changed=with_payload(row,raw=raw)
    with base.connect() as conn,pytest.raises(errors.CheckViolation):owner(conn,policy);insert(conn,policy,changed)


@pytest.mark.parametrize('raw',[b'[]',b'null',b'{}',b'{"x":1,"x":2}',b'{"binding":{"x":1,"x":2}}',
    b'{"x":NaN}',b'not-json',b'\xff',b' '*(131072+1)],
    ids=['array','null','missing','duplicate','nested-duplicate','nan','not-json','utf8','oversize'])
def test_malformed_or_oversize_raw_metadata_never_creates_row(cycle_schema,raw):
    base,policy,_,row=cycle_schema
    with base.connect() as conn,pytest.raises((errors.CheckViolation,errors.InvalidTextRepresentation,
            errors.CharacterNotInRepertoire,errors.UntranslatableCharacter)):
        owner(conn,policy);insert(conn,policy,with_payload(row,raw=raw))


def test_duplicates_conflict_and_correction_uses_new_revision_without_rewriting(cycle_schema):
    base,policy,_,row=cycle_schema
    with base.connect() as conn:owner(conn,policy);insert(conn,policy,row)
    for changes in ({},{'revision':'r2'},{'result_id':'crop-cycle-result-v1:'+'7'*64}):
        with base.connect() as conn,pytest.raises(errors.UniqueViolation):
            owner(conn,policy);insert(conn,policy,with_payload({**row,**changes}))
    corrected=with_payload({**row,'revision':'r2','result_id':'crop-cycle-result-v1:'+'7'*64})
    with base.connect() as conn:
        owner(conn,policy);insert(conn,policy,corrected)
        found=conn.execute(sql.SQL('SELECT revision,payload_raw FROM {} ORDER BY revision').format(target(policy))).fetchall()
        assert [(r['revision'],bytes(r['payload_raw'])) for r in found]==[('r1',row['payload_raw']),('r2',corrected['payload_raw'])]


@pytest.mark.parametrize('drift',['public-select','public-execute'])
def test_extra_privilege_on_new_objects_fails_existing_whole_role_audit(cycle_schema,drift):
    base,policy,_,_=cycle_schema
    with base.connect() as conn:
        owner(conn,policy)
        if drift=='public-select':conn.execute(sql.SQL('GRANT SELECT ON {} TO PUBLIC').format(target(policy)))
        else:conn.execute(sql.SQL('GRANT EXECUTE ON FUNCTION {}() TO PUBLIC').format(
            sql.Identifier(policy.schema,'reject_cycle_crop_result_change')))
    with base.connect() as conn,pytest.raises(RolePolicyHold):audit_runtime_roles(conn,policy)


def test_failed_fresh_install_rolls_back_new_objects_when_parent_is_missing(login_scope):
    base,policy,_=login_scope;schema=policy.schema+'_extra'
    with base.connect() as conn:conn.execute(sql.SQL('CREATE SCHEMA {} AUTHORIZATION {}').format(sql.Identifier(schema),sql.Identifier(policy.owner)))
    try:
        with base.connect() as conn:
            owner(conn,policy)
            with pytest.raises(errors.UndefinedTable):install(conn,schema)
            assert conn.execute('SELECT to_regclass(%s) AS relation',(schema+'.crop_cycle_research_results',)).fetchone()['relation'] is None
            assert conn.execute('SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname=%s',(schema,)).fetchone() is None
    finally:
        with base.connect() as conn:conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def test_existing_startup_table_row_and_default_policy_are_preserved(login_scope):
    from app.crop_startup_result_store import install_startup_crop_result_schema
    from test_runtime_roles import startup_schema_row,insert_startup_schema_row
    base,policy,_=login_scope;old=startup_schema_row(base,policy)
    with base.connect() as conn:
        owner(conn,policy);install_startup_crop_result_schema(conn,policy.schema);insert_startup_schema_row(conn,policy,old)
        install(conn,policy.schema)
        table=sql.Identifier(policy.schema,'crop_startup_research_results')
        actual=conn.execute(sql.SQL('SELECT payload_raw,payload_sha256 FROM {}').format(table)).fetchone()
        assert bytes(actual['payload_raw'])==old['payload_raw'] and actual['payload_sha256']==old['payload_sha256']
    with base.connect() as conn:audit_runtime_roles(conn,policy)


def test_hold_can_preserve_empty_past_but_completed_requires_all_planned_steps(cycle_schema):
    base,policy,_,row=cycle_schema
    hold=with_payload({**row,'artifact_status':'hold','steps':0,'sample_count':0,'event_count':0})
    with base.connect() as conn:owner(conn,policy);insert(conn,policy,hold)
    completed=with_payload({**row,'revision':'r2','result_id':'crop-cycle-result-v1:'+'7'*64,'steps':0})
    with base.connect() as conn,pytest.raises(errors.CheckViolation):owner(conn,policy);insert(conn,policy,completed)


def test_valid_json_exact_metadata_byte_limit_roundtrips_and_one_byte_over_is_rejected(cycle_schema):
    from app.crop_cycle_result_schema import MAX_METADATA_BYTES
    base,policy,_,row=cycle_schema;packet=metadata(row);packet['binding']['padding']=''
    packet['binding']['padding']='x'*(MAX_METADATA_BYTES-len(_canonical(packet)))
    exact=with_payload(row,packet);assert len(exact['payload_raw'])==MAX_METADATA_BYTES
    with base.connect() as conn:
        owner(conn,policy);insert(conn,policy,exact)
        assert bytes(conn.execute(sql.SQL('SELECT payload_raw FROM {}').format(target(policy))).fetchone()['payload_raw'])==exact['payload_raw']
    packet['revision']='r2';packet['result_id']='crop-cycle-result-v1:'+'7'*64;packet['binding']['padding']+='x'
    oversized=with_payload({**row,'revision':'r2','result_id':packet['result_id']},packet)
    assert len(oversized['payload_raw'])==MAX_METADATA_BYTES+1
    with base.connect() as conn,pytest.raises(errors.CheckViolation):owner(conn,policy);insert(conn,policy,oversized)
    with base.connect() as conn:assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(target(policy))).fetchone()['n']==1


def test_empty_metadata_bytes_never_create_row(cycle_schema):
    base,policy,_,row=cycle_schema
    with base.connect() as conn,pytest.raises((errors.CheckViolation,errors.InvalidTextRepresentation)):
        owner(conn,policy);insert(conn,policy,with_payload(row,raw=b''))
    with base.connect() as conn:assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(target(policy))).fetchone()['n']==0
