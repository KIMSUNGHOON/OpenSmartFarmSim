"""Real SCRAM custody of synthetic startup artifacts, without an approved Run."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from datetime import datetime,timedelta
from hashlib import sha256
import json
import hmac
import multiprocessing
from pathlib import Path
from uuid import uuid4

from psycopg import errors,sql
import pytest

from app.crop_startup_result_store import (StartupCropResultStore,install_startup_crop_result_schema,
    CropResultHold,CropResultConflict,CropResultPending,READ_SCOPES,WRITE_SCOPES,
    MAX_REQUEST_BYTES,MAX_PACKET_BYTES,_intent_lock_key)
from app.crop_startup_artifact import read_startup_artifact
from app.runtime_roles import RuntimeLoginPolicy,RolePolicyHold,audit_runtime_roles,_tables,CROP_RESULT_TABLES,CROP_COUPLED_RESULT_TABLES
from app.runtime_login import connect_runtime
from app.thermal_run_store import _canonical
from test_crop_plant_startup_integration import ROOT,PROFILES,program
from test_crop_result_store import SyntheticProgramRights
from test_farm_authoring_storage import authoring,request
from test_farm_replay_scenario import farm_setup
from login_database import login_database,login_scope


NOTICE=(ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()
KEY=b'synthetic-startup-custody-test-key-01'
pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,'break_even_calculation':True,
    'crop_startup_result_storage':True}],indirect=True)


def shifted(pattern='empty-entry'):
    value=program(pattern)
    stamp=lambda s:(datetime.fromisoformat(s.replace('Z','+00:00'))+timedelta(days=273)).isoformat().replace('+00:00','Z')
    for segment in value['segments']:
        for k in ('start','end'):segment[k]=stamp(segment[k])
    for event in value['events']:event['at']=stamp(event['at'])
    value['output_times']=[stamp(s) for s in value['output_times']]
    return value


@pytest.fixture
def startup_setup(authoring):
    farms,farm_body,principal=authoring
    registered=farms.submit('tenant-1',request(farm_body));principal['scopes'].update(WRITE_SCOPES)
    body={'study_id':'startup-study-1','revision':'r1','farm':{
        'scenario_id':farm_body['farm']['scenario_id'],'scenario_revision':farm_body['farm']['scenario_revision'],
        'registration_sha256':registered.scenario_sha256,'crop_id':'crop-1'},'program':shifted(),
        'rights':{'declaration_id':'synthetic-startup-program-1','revision':'r1',
            **{k:True for k in ('ownership_asserted','access','store','transform','use','display')},
            'redistribute':False,'available_at':farm_body['farm']['decision_at']}}
    update_rights(body);rights=SyntheticProgramRights()
    return StartupCropResultStore(farms,**PROFILES,notice_raw=NOTICE,program_rights=rights,integrity_key=KEY),body,principal,rights


def update_rights(body):
    body['rights']['program_sha256']=sha256(_canonical(body['program'])).hexdigest()


def put(store,body):
    return store.put('tenant-1',_canonical(body))


def count(store):
    with store.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
            store.jobs._table('crop_startup_research_results'))).fetchone()['n']


def fresh(store):
    from app.farm_authoring_storage import FarmAuthoringService
    return StartupCropResultStore(FarmAuthoringService(store.farms.replay),**PROFILES,
        notice_raw=NOTICE,program_rights=store.program_rights,integrity_key=KEY)


def child_read(store,result_id,farm,queue):
    try:queue.put(fresh(store).get('tenant-1',result_id,farm))
    except Exception as exc:queue.put({'error':type(exc).__name__})


@pytest.mark.parametrize('pattern',['empty-no-entry','empty-entry','first-only',
    'full-removal-reentry','positive-tail','night-smooth'])
def test_real_scram_exact_artifact_farm_binding_and_restarted_store(startup_setup,pattern,monkeypatch):
    store,body,_,_=startup_setup;body['program']=shifted(pattern);update_rights(body)
    first=put(store,body);packet=json.loads(first['payload_raw']);artifact=packet['artifact']
    assert packet['schema_version']=='crop-result-v3' and packet['status']=='stored_unpublished_research'
    assert packet['claim_scope']=='synthetic_crop_math_only' and packet['request']==body
    assert artifact['program_raw_utf8'].encode()==_canonical(body['program'])
    assert read_startup_artifact(_canonical(artifact),expected_sha256=packet['artifact_sha256'],
        **PROFILES,notice_raw=NOTICE)==artifact
    assert len(artifact['result']['samples'])==len(body['program']['output_times'])
    assert artifact['result']['status']=='completed'
    binding=packet['binding'];assert binding['normalization']=='per_m2_floor'
    assert binding['profile_applicability']=='unvalidated_for_registered_crop'
    assert binding['crop']['crop_id']=='crop-1' and binding['crop']['batch_id']
    assert binding['zone_id'] and binding['floor_area']['unit']=='m²'
    assert count(store)==1 and put(store,body)==first
    assert fresh(store).get('tenant-1',first['result_id'],body['farm'])==first
    with store.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
        row=conn.execute(sql.SQL('SELECT * FROM {}').format(store.jobs._table('crop_startup_research_results'))).fetchone()
        assert row['integrity_signature']==hmac.new(KEY,b'ossf-crop-startup-research-custody-v3\0'+first['payload_raw'],'sha256').hexdigest()
        assert row['payload_raw']==first['payload_raw'] and row['recorded_at']==first['recorded_at']
        assert audit_runtime_roles(conn,store.jobs.runtime_identity[0])['tables']>=1
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
            store.jobs._table('thermal_g1_runs'))).fetchone()['n']==0
    import app.crop_startup_result_store as module
    monkeypatch.setattr(module,'calculate_startup_artifact',lambda *a,**k:pytest.fail('restart read recalculated'))
    context=multiprocessing.get_context('fork');queue=context.Queue()
    child=context.Process(target=child_read,args=(store,first['result_id'],body['farm'],queue));child.start()
    try:
        assert queue.get(timeout=45)==first
        child.join(5);assert not child.is_alive() and child.exitcode==0
    finally:
        if child.is_alive():child.kill();child.join(5)
        queue.close();queue.join_thread()
    assert not any(k in packet for k in ('run_id','gate_signature','harvest_kg','ranking'))
    Path('/tmp/ossf-crop-startup-stored-case-'+pattern+'-20261005.json').write_bytes(_canonical({
        'scope':'synthetic SCRAM custody software test; fake rights/source provider; not G0/G1',
        'recorded_at':first['recorded_at'].isoformat(),'payload_sha256':first['payload_sha256'],
        'packet':packet,'same_fresh_process_bytes':True,'actual_scram':True}))


def test_concurrent_retry_conflict_revision_lock_and_no_reintegration(startup_setup,monkeypatch):
    store,body,_,_=startup_setup
    def attempt(_):
        try:return put(store,deepcopy(body))
        except CropResultPending:return None
    with ThreadPoolExecutor(max_workers=2) as pool:records=list(pool.map(attempt,range(2)))
    completed=[r for r in records if r is not None];assert completed and count(store)==1
    assert all(r==completed[0] for r in completed)
    import app.crop_startup_result_store as module
    original=module.calculate_startup_artifact
    monkeypatch.setattr(module,'calculate_startup_artifact',lambda *a,**k:pytest.fail('read/retry recalculated'))
    assert put(store,body)==completed[0] and store.get('tenant-1',completed[0]['result_id'],body['farm'])==completed[0]
    changed=deepcopy(body);changed['program']['solver']['max_step_seconds']=5;update_rights(changed)
    with pytest.raises(CropResultConflict):put(store,changed)
    monkeypatch.setattr(module,'calculate_startup_artifact',original);changed['revision']='r2'
    assert put(store,changed)['result_id']!=completed[0]['result_id'] and count(store)==2
    pending=deepcopy(body);pending['revision']='pending'
    with store.jobs.connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(%s)',(_intent_lock_key('tenant-1',pending['study_id'],pending['revision']),))
        with pytest.raises(CropResultPending):put(store,pending)
    assert count(store)==2 and put(store,pending)['result_id'] and count(store)==3


def test_numeric_hold_keeps_only_confirmed_past(startup_setup):
    store,body,_,_=startup_setup
    body['program']=shifted('positive-tail')
    body['program']['events'][1]['removals']['values']['leaf']['value']=1e7;update_rights(body)
    record=put(store,body);result=json.loads(record['payload_raw'])['artifact']['result']
    assert result['status']=='hold' and result['hold']['phase']=='event'
    assert len(result['samples'])==3 and all(s['at']<result['hold']['at'] for s in result['samples'])
    assert store.get('tenant-1',record['result_id'],body['farm'])==record


def test_invalid_input_and_canonical_bytes_never_saved(startup_setup,monkeypatch):
    store,original,_,_=startup_setup
    import app.crop_startup_result_store as module
    monkeypatch.setattr(module,'calculate_startup_artifact',lambda *a,**k:pytest.fail('invalid input calculated'))
    for kind in ('result','coefficient','unit','origin','id','rights_hash','rights_use','available','crop','farm','time','extra_rights','calendar','revision'):
        body=deepcopy(original)
        if kind=='result':body['artifact']={}
        if kind=='coefficient':body['cohort_profile']={}
        if kind=='unit':body['program']['initial_state']['values']['fruit_number'][0]['unit']='kg'
        if kind=='origin':body['program']['segments'][0]['fruit_entry']['origin']='reference_observation'
        if kind=='id':body['program']['segments'][1]['forcing']['input_id']=body['program']['segments'][0]['forcing']['input_id']
        if kind=='rights_use':body['rights']['store']=False
        if kind=='available':body['rights']['available_at']='2099-01-01T00:00:00Z'
        if kind=='crop':body['farm']['crop_id']='other'
        if kind=='farm':body['farm']['registration_sha256']='0'*64
        if kind=='time':body['program']['output_times'][0]='bad'
        if kind=='extra_rights':body['rights']['G0']=True
        if kind=='calendar':
            for segment in body['program']['segments']:
                for k in ('start','end'):segment[k]=segment[k].replace('2026-10-01','2027-10-01')
            body['program']['output_times']=[s.replace('2026-10-01','2027-10-01') for s in body['program']['output_times']]
        if kind=='revision':body['revision']='r'*201
        update_rights(body)
        if kind=='rights_hash':body['rights']['program_sha256']='0'*64
        with pytest.raises((CropResultHold,PermissionError)):put(store,body)
        assert count(store)==0,kind
    good=_canonical(original)
    for bad in (good+b' ',b'{"a":1,"a":1}',b'{"a":NaN}',b'\xff',b' '*(MAX_REQUEST_BYTES+1)):
        with pytest.raises(CropResultHold):store.put('tenant-1',bad)
    assert count(store)==0


def test_scope_rights_source_revocation_and_late_rollback(startup_setup,monkeypatch):
    store,body,principal,rights=startup_setup;first=put(store,body)
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        with pytest.raises(PermissionError):store.get('tenant-1',first['result_id'],body['farm'])
        principal['scopes'].add(scope)
    with pytest.raises(PermissionError):store.get('foreign',first['result_id'],body['farm'])
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm']|{'crop_id':'other'})
    assert store.get('tenant-1','crop-result-v3:'+'0'*64,body['farm']) is None
    rights.allowed=False
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])
    rights.allowed=True;rights.allowed_uses=('research_calculation',)
    with pytest.raises(CropResultHold):put(store,body|{'revision':'r2'})
    rights.allowed_uses=('research_calculation','research_display')
    import app.crop_startup_result_store as module
    original=module.calculate_startup_artifact
    def during_calculation(*args,**kwargs):
        raw=original(*args,**kwargs);rights.allowed=False;return raw
    monkeypatch.setattr(module,'calculate_startup_artifact',during_calculation)
    with pytest.raises(CropResultHold):put(store,body|{'revision':'r2'})
    assert count(store)==1;rights.allowed=True;monkeypatch.setattr(module,'calculate_startup_artifact',original)
    checked=store._checked
    def before_commit(*args,**kwargs):
        record=checked(*args,**kwargs);principal['scopes'].remove('crop_result_write');return record
    monkeypatch.setattr(store,'_checked',before_commit)
    with pytest.raises(PermissionError):put(store,body|{'revision':'r2'})
    assert count(store)==1;principal['scopes'].add('crop_result_write');monkeypatch.setattr(store,'_checked',checked)
    def before_return(*args,**kwargs):
        record=checked(*args,**kwargs);rights.allowed=False;return record
    monkeypatch.setattr(store,'_checked',before_return)
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])
    rights.allowed=True;monkeypatch.setattr(store,'_checked',checked)
    monkeypatch.setattr(store.farms.replay.candidates._source._source,'get_input_rights',lambda *_:None)
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])


def test_actual_roles_immutable_rows_fk_and_owner_corruption(startup_setup,login_scope,monkeypatch):
    store,body,_,_=startup_setup;base,policy,dsns=login_scope;first=put(store,body)
    target=store.jobs._table('crop_startup_research_results')
    for kind in ('request','worker','supervisor'):
        for write in (False,True):
            with connect_runtime(dsns[kind],policy,kind) as conn,pytest.raises(errors.InsufficientPrivilege):
                if write:
                    if kind=='supervisor':conn.execute('SET TRANSACTION READ WRITE')
                    conn.execute(sql.SQL('INSERT INTO {} SELECT * FROM {} WHERE false').format(target,target))
                else:conn.execute(sql.SQL('SELECT * FROM {} LIMIT 0').format(target))
    for query in (sql.SQL('UPDATE {} SET revision=revision').format(target),sql.SQL('DELETE FROM {}').format(target),
                  sql.SQL('TRUNCATE {}').format(target)):
        with store.jobs.connect() as conn,pytest.raises(errors.InsufficientPrivilege):conn.execute(query)
    for query in (sql.SQL('UPDATE {} SET revision=revision').format(target),sql.SQL('DELETE FROM {}').format(target)):
        with base.connect() as conn,pytest.raises(errors.RaiseException,match='immutable'):conn.execute(query)
    with base.connect() as conn:row=conn.execute(sql.SQL('SELECT * FROM {}').format(target)).fetchone()
    original_find=store._find
    for changes in ({'payload_raw':row['payload_raw']+b' '},{'integrity_signature':'0'*64},
        {'scenario_id':'other'},{'registered_by':policy.roles['request']}):
        monkeypatch.setattr(store,'_find',lambda *a,changes=changes,**k:{**row,**changes})
        with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])
    monkeypatch.setattr(store,'_find',original_find)
    bad=json.loads(row['payload_raw']);bad['artifact']['result']['samples'][0]['lai']['value']+=1
    changed=_canonical(bad)
    with base.connect() as conn:
        conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER crop_startup_result_immutable').format(target))
        conn.execute(sql.SQL('UPDATE {} SET payload_raw=%s,payload_sha256=%s').format(target),(changed,sha256(changed).hexdigest()))
        conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER crop_startup_result_immutable').format(target))
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])
    # Even an authenticated INSERT must refer to an actual tenant registration job.
    bad=json.loads(row['payload_raw']);bad['request']['study_id']='foreign-job';bad['binding']['registration_job_id']=str(uuid4())
    bad['result_id']='crop-result-v3:'+sha256(_canonical({k:v for k,v in bad.items() if k!='result_id'})).hexdigest()
    payload=_canonical(bad)
    with store.jobs.connect() as conn,pytest.raises(errors.ForeignKeyViolation):
        conn.execute(sql.SQL('''INSERT INTO {} (tenant_id,study_id,revision,result_id,scenario_id,scenario_revision,
            registration_job_id,registration_sha256,payload_raw,payload_sha256,integrity_signature,registered_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''').format(target),
            ('tenant-1','foreign-job',row['revision'],bad['result_id'],row['scenario_id'],row['scenario_revision'],
             bad['binding']['registration_job_id'],row['registration_sha256'],payload,sha256(payload).hexdigest(),
             store._signature(payload),row['registered_by']))


def test_default_flag_old_grants_and_strict_constructor(startup_setup):
    store,_,_,rights=startup_setup
    plain=RuntimeLoginPolicy('test','owner','runtime','postgres')
    assert plain.crop_startup_result_storage is False
    assert _tables(plain)==_tables(replace(plain,crop_startup_result_storage=False))
    assert not set(CROP_RESULT_TABLES+CROP_COUPLED_RESULT_TABLES)&set(_tables(store.jobs.runtime_identity[0]))
    with pytest.raises(RolePolicyHold):replace(plain,crop_startup_result_storage=1)
    for patch in ({'cohort_profile':{}},{'transport_profile':{}},{'notice_raw':NOTICE+b' '},
                  {'integrity_key':b'short'},{'program_rights':None}):
        args={**PROFILES,'notice_raw':NOTICE,'program_rights':rights,'integrity_key':KEY,**patch}
        with pytest.raises(CropResultHold):StartupCropResultStore(store.farms,**args)
    assert MAX_PACKET_BYTES==20*1024*1024


def test_authenticated_packets_still_require_current_bindings_and_artifact(startup_setup,monkeypatch):
    store,body,_,_=startup_setup;first=put(store,body)
    with store.jobs.connect() as conn:
        row=conn.execute(sql.SQL('SELECT * FROM {}').format(
            store.jobs._table('crop_startup_research_results'))).fetchone()
    original=json.loads(row['payload_raw'])
    for kind in ('schema','scope','tenant','rights_policy','storage_code','binding_code','extra',
                 'zone','area','crop','batch','normalization','applicability','farm_hash','source_hash',
                 'registration','program','model','sample','artifact_hash','header_revision','authority'):
        packet=deepcopy(original);changed=dict(row)
        if kind=='schema':packet['schema_version']='crop-result-v2'
        if kind=='scope':packet['claim_scope']='validated_production'
        if kind=='tenant':packet['tenant_id']='foreign'
        if kind=='rights_policy':packet['rights_policy_version']='other'
        if kind=='storage_code':packet['storage_code_sha256']='0'*64
        if kind=='binding_code':packet['binding_code_sha256']='0'*64
        if kind=='extra':packet['G1']=True
        if kind=='zone':packet['binding']['zone_id']='foreign'
        if kind=='area':packet['binding']['floor_area']['value']='12345'
        if kind=='crop':packet['binding']['crop']['crop_id']='foreign'
        if kind=='batch':packet['binding']['crop']['batch_id']='foreign'
        if kind=='normalization':packet['binding']['normalization']='per_plant'
        if kind=='applicability':packet['binding']['profile_applicability']='validated_for_registered_crop'
        if kind=='farm_hash':packet['binding']['farm_sha256']='0'*64
        if kind=='source_hash':packet['binding']['source_binding_sha256']='0'*64
        if kind=='registration':packet['binding']['registration_job_id']=str(uuid4())
        if kind=='program':
            packet['request']['program']['solver']['max_step_seconds']=2;update_rights(packet['request'])
        if kind=='model':packet['artifact']['result']['manifest']['rate_model_version']='old-model'
        if kind=='sample':packet['artifact']['result']['samples'][0]['lai']['value']+=1
        if kind=='artifact_hash':packet['artifact_sha256']='0'*64
        if kind=='header_revision':changed['revision']='other'
        if kind=='authority':changed['registered_by']=store.jobs.runtime_identity[0].roles['worker']
        if kind in ('model','sample'):
            from test_crop_startup_artifact import rehash
            packet['artifact']=json.loads(rehash(packet['artifact']))
            packet['artifact_sha256']=sha256(_canonical(packet['artifact'])).hexdigest()
        packet['result_id']='crop-result-v3:'+sha256(_canonical(
            {k:v for k,v in packet.items() if k!='result_id'})).hexdigest()
        payload=_canonical(packet)
        changed.update(payload_raw=payload,payload_sha256=sha256(payload).hexdigest(),
                       integrity_signature=store._signature(payload),result_id=packet['result_id'])
        monkeypatch.setattr(store,'_find',lambda *a,**k:changed)
        with pytest.raises(CropResultHold):store.get('tenant-1',changed['result_id'],body['farm'])


def test_late_program_source_and_scope_revocation_roll_back_new_rows(startup_setup,monkeypatch):
    store,body,principal,rights=startup_setup;first=put(store,body);checked=store._checked
    source=store.farms.replay.candidates._source._source
    get_rights=source.get_input_rights
    for kind in ('program','source','scope'):
        def before_commit(*args,**kwargs):
            record=checked(*args,**kwargs)
            if kind=='program':rights.allowed=False
            if kind=='source':monkeypatch.setattr(source,'get_input_rights',lambda *_:None)
            if kind=='scope':principal['scopes'].remove('crop_result_write')
            return record
        monkeypatch.setattr(store,'_checked',before_commit)
        with pytest.raises((CropResultHold,PermissionError)):put(store,body|{'revision':'late-'+kind})
        assert count(store)==1
        rights.allowed=True;principal['scopes'].add('crop_result_write')
        monkeypatch.setattr(source,'get_input_rights',get_rights)
    monkeypatch.setattr(store,'_checked',checked)
    assert store.get('tenant-1',first['result_id'],body['farm'])==first


def test_provider_or_role_binding_replacement_denies_read_and_write(startup_setup,monkeypatch):
    store,body,_,_=startup_setup;first=put(store,body)
    original=store.program_rights
    monkeypatch.setattr(store,'program_rights',SyntheticProgramRights())
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])
    with pytest.raises(CropResultHold):put(store,body|{'revision':'other'})
    monkeypatch.setattr(store,'program_rights',original)
    policy,kind=store.jobs.runtime_identity
    monkeypatch.setattr(store.jobs,'runtime_identity',(replace(policy,crop_startup_result_storage=False),kind))
    with pytest.raises(CropResultHold):
        StartupCropResultStore(store.farms,**PROFILES,notice_raw=NOTICE,
            program_rights=original,integrity_key=KEY)
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])
    with pytest.raises(CropResultHold):put(store,body|{'revision':'other'})
    monkeypatch.setattr(store.jobs,'runtime_identity',(policy,kind))
    assert count(store)==1


@pytest.mark.parametrize('kind',['program','source','scope'])
def test_revocation_after_actual_commit_withholds_returned_result(startup_setup,monkeypatch,kind):
    store,body,principal,rights=startup_setup
    source=store.farms.replay.candidates._source._source
    original=store.jobs.connect;get_rights=source.get_input_rights
    class CommitProbe:
        def __init__(self,conn):self.conn,self.inserted=conn,False
        def __getattr__(self,name):return getattr(self.conn,name)
        def execute(self,query,*args,**kwargs):
            rendered=query.as_string(self.conn) if isinstance(query,sql.Composable) else query
            if rendered.lstrip().startswith('INSERT INTO') and 'crop_startup_research_results' in rendered:
                self.inserted=True
            return self.conn.execute(query,*args,**kwargs)
    @contextmanager
    def observed_connect():
        with original() as conn:
            probe=CommitProbe(conn);yield probe
        if probe.inserted:
            if kind=='program':rights.allowed=False
            if kind=='source':monkeypatch.setattr(source,'get_input_rights',lambda *_:None)
            if kind=='scope':principal['scopes'].remove('crop_result_write')
    monkeypatch.setattr(store.jobs,'connect',observed_connect)
    with pytest.raises((CropResultHold,PermissionError)):put(store,body)
    monkeypatch.setattr(store.jobs,'connect',original)
    assert count(store)==1  # A complete committed packet stays immutable, never a partial row.
    rights.allowed=True;principal['scopes'].add('crop_result_write')
    monkeypatch.setattr(source,'get_input_rights',get_rights)
    record=put(store,body)
    assert store.get('tenant-1',record['result_id'],body['farm'])==record
