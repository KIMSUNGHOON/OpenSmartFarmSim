"""Actual SCRAM custody for synthetic crop math; no approved crop Run."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta
from hashlib import sha256
import json
import multiprocessing
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import errors, sql
import pytest

from app.crop_result_store import (CropResultStore, CropResultHold, CropResultConflict, CropResultPending,
                                   READ_SCOPES, WRITE_SCOPES, NOTICE_SHA256, MAX_REQUEST_BYTES)
from app.crop_growth_rates import ReferenceParameters
from app.thermal_run_store import _canonical
from app.runtime_roles import RuntimeLoginPolicy, RolePolicyHold, audit_runtime_roles
from app.runtime_login import connect_runtime
from test_farm_authoring_storage import authoring, request
from test_farm_replay_scenario import farm_setup
from login_database import login_database, login_scope


ROOT = Path(__file__).resolve().parents[2]
PROFILE = ReferenceParameters((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes())
NOTICE = (ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()
KEY = b'synthetic-crop-result-test-key-0001'
pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,
    'break_even_calculation':True,'crop_result_storage':True}], indirect=True)


class SyntheticProgramRights:
    policy_version = 'synthetic-crop-rights-test-v1'
    allowed = True
    allowed_uses = ('research_calculation','research_display')

    def __call__(self, tenant, declaration, program_sha256, intended_use):
        return (self.allowed is True and tenant == 'tenant-1' and
                declaration['program_sha256'] == program_sha256 and
                intended_use in self.allowed_uses)


@pytest.fixture
def crop_setup(authoring):
    farms, farm_body, principal = authoring
    registration = farms.submit('tenant-1',request(farm_body))
    principal['scopes'].update(WRITE_SCOPES)
    program = json.loads((ROOT/'fixtures/crop-integration-reference-v1.json').read_bytes())['program']
    offset = timedelta(days=273)
    stamp = lambda value:(datetime.fromisoformat(value.replace('Z','+00:00'))+offset).isoformat().replace('+00:00','Z')
    for segment in program['segments']:
        for field in ('start','end'):segment[field]=stamp(segment[field])
    for event in program['events']:event['at']=stamp(event['at'])
    program['output_times']=[stamp(value) for value in program['output_times']]
    body = {'study_id':'study-1','revision':'r1','farm':{
        'scenario_id':farm_body['farm']['scenario_id'],
        'scenario_revision':farm_body['farm']['scenario_revision'],
        'registration_sha256':registration.scenario_sha256,'crop_id':'crop-1'},
        'program':program,'rights':{'declaration_id':'self-authored-crop-1','revision':'r1',
        'program_sha256':sha256(_canonical(program)).hexdigest(),
        **{name:True for name in ('ownership_asserted','access','store','transform','use','display')},
        'redistribute':False,'available_at':farm_body['farm']['decision_at']}}
    rights = SyntheticProgramRights()
    store = CropResultStore(farms,PROFILE,NOTICE,program_rights=rights,integrity_key=KEY)
    return store,body,principal,rights


def raw(body):
    return _canonical(body)


def count(store):
    with store.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(store.jobs._table('crop_research_results'))).fetchone()['n']


def put(store,body):
    return store.put('tenant-1',raw(body))


def _child_read(store, result_id, farm, queue):
    try:
        fresh = CropResultStore(store.farms,PROFILE,NOTICE,
            program_rights=store.program_rights,integrity_key=KEY)
        record = fresh.get('tenant-1',result_id,farm)
        queue.put({'sha256':record['payload_sha256'],'raw':record['payload_raw']})
    except Exception as exc:
        queue.put({'error':type(exc).__name__})


def test_scram_exact_bytes_profile_notice_replay_and_fresh_process(crop_setup):
    store,body,_,_=crop_setup
    first=put(store,body); packet=json.loads(first['payload_raw'])
    assert packet['status']=='stored_unpublished_research'
    assert packet['claim_scope']=='synthetic_crop_math_only'
    assert packet['request']==body
    assert packet['profile_raw_utf8'].encode()==PROFILE.raw_bytes
    assert sha256(packet['notice_raw_utf8'].encode()).hexdigest()==NOTICE_SHA256
    assert packet['result']['status']=='completed' and len(packet['result']['samples'])==6
    assert packet['binding']['profile_applicability']=='unvalidated_for_registered_crop'
    assert packet['binding']['normalization']=='per_m2_floor'
    assert packet['binding']['floor_area']['unit']=='m²'
    assert packet['binding']['crop']['batch_id']==store.farms.read_registration('tenant-1',
        body['farm']['scenario_id'],body['farm']['scenario_revision'],
        body['farm']['registration_sha256'])['farm'].crops[0].batch_id
    assert 'run_id' not in packet and 'gate_signature' not in packet
    Path('/tmp/ossf-crop-stored-packet-20261004.json').write_bytes(_canonical({
        'evidence_version':'crop-result-storage-reference-v1','scope':'synthetic software custody test only',
        'recorded_at':first['recorded_at'].isoformat(),'payload_sha256':first['payload_sha256'],
        'payload_raw_utf8':first['payload_raw'].decode(),'packet':packet,
        'program_rights_provider':'synthetic-crop-rights-test-v1; not actual consent or G0',
        'postgres_version':'16.15','python_version':'3.12.3'}))
    assert count(store)==1 and put(store,body)==first
    with store.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
        assert audit_runtime_roles(conn,store.jobs.runtime_identity[0])['tables']>=1
    fresh=CropResultStore(store.farms,PROFILE,NOTICE,program_rights=store.program_rights,integrity_key=KEY)
    assert fresh.get('tenant-1',first['result_id'],body['farm'])==first
    context=multiprocessing.get_context('fork'); queue=context.Queue()
    child=context.Process(target=_child_read,args=(store,first['result_id'],body['farm'],queue))
    child.start()
    try:
        child.join(45)
        assert not child.is_alive() and child.exitcode==0
        observed=queue.get(timeout=2)
        assert observed=={'sha256':first['payload_sha256'],'raw':first['payload_raw']}
    finally:
        if child.is_alive():child.kill();child.join(5)
        queue.close();queue.join_thread()
    with store.jobs.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(store.jobs._table('thermal_g1_runs'))).fetchone()['n']==0


def test_retry_does_not_recalculate_conflict_new_revision_and_concurrent_intent(crop_setup,monkeypatch):
    store,body,_,_=crop_setup
    import app.crop_result_store as module
    def attempt(_):
        try:return put(store,deepcopy(body))
        except CropResultPending:return 'pending'
    with ThreadPoolExecutor(max_workers=2) as pool:
        records=list(pool.map(attempt,range(2)))
    completed=[r for r in records if r!='pending']
    assert completed and count(store)==1
    assert all(r==completed[0] for r in completed)
    original=module.integrate_crop
    monkeypatch.setattr(module,'integrate_crop',lambda **_:pytest.fail('read/retry reran integration'))
    assert put(store,body)==completed[0]
    assert store.get('tenant-1',completed[0]['result_id'],body['farm'])==completed[0]
    changed=deepcopy(body); changed['program']['solver']['max_step_seconds']=5
    changed['rights']['program_sha256']=sha256(raw(changed['program'])).hexdigest()
    with pytest.raises(CropResultConflict):put(store,changed)
    monkeypatch.setattr(module,'integrate_crop',original)
    changed['revision']='r2'; second=put(store,changed)
    assert second['result_id']!=completed[0]['result_id'] and count(store)==2
    blocked=deepcopy(body);blocked['revision']='blocked-r1'
    with store.jobs.connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(%s)',
            (module._intent_lock_key('tenant-1',blocked['study_id'],blocked['revision']),))
        with pytest.raises(CropResultPending):put(store,blocked)
        assert count(store)==2
    assert put(store,blocked)['result_id']!=completed[0]['result_id'] and count(store)==3


def test_numerical_hold_is_stored_with_diagnostics_without_completed_frames(crop_setup):
    store,body,_,_=crop_setup
    body['program']['initial_state']['values']['buffer']['value']=0
    body['program']['segments'][0]['forcing']['values']['par_above_canopy']['value']=0
    body['rights']['program_sha256']=sha256(raw(body['program'])).hexdigest()
    record=put(store,body); result=json.loads(record['payload_raw'])['result']
    assert result['status']=='hold' and result['samples']==[] and result['events']==[]
    assert result['hold']['reason'].startswith('DEPLETED_STATE_HOLD')
    assert store.get('tenant-1',record['result_id'],body['farm'])==record


def test_invalid_or_mixed_input_cannot_create_record(crop_setup):
    store,original,_,_=crop_setup
    for kind in ('tenant','result','profile','unit','time','origin','duplicate_input','rights_hash',
                 'rights_use','rights_available','crop','farm_hash','outside_crop','extra_program','extra_rights'):
        body=deepcopy(original)
        if kind=='tenant':body['tenant_id']='foreign'
        elif kind=='result':body['result']={'status':'accepted'}
        elif kind=='profile':body['profile']={'coefficient':1}
        elif kind=='unit':body['program']['initial_state']['values']['leaf']['unit']='kg_fresh/m2'
        elif kind=='time':body['program']['output_times'][0]='bad'
        elif kind=='origin':body['program']['segments'][0]['forcing']['origin']='reference_observation'
        elif kind=='duplicate_input':body['program']['segments'][1]['forcing']['input_id']=body['program']['segments'][0]['forcing']['input_id']
        elif kind=='rights_hash':body['rights']['program_sha256']='a'*64
        elif kind=='rights_use':body['rights']['use']=False
        elif kind=='rights_available':body['rights']['available_at']='2099-01-01T00:00:00Z'
        elif kind=='crop':body['farm']['crop_id']='another-crop'
        elif kind=='farm_hash':body['farm']['registration_sha256']='a'*64
        elif kind=='outside_crop':
            for s in body['program']['segments']:
                for k in ('start','end'):s[k]=s[k].replace('2026-10-01','2026-10-30')
            for e in body['program']['events']:e['at']=e['at'].replace('2026-10-01','2026-10-30')
            body['program']['output_times']=[t.replace('2026-10-01','2026-10-30') for t in body['program']['output_times']]
        elif kind=='extra_program':body['program']['yield_kg']=100
        else:body['rights']['G0_approved']=True
        if kind!='rights_hash':body['rights']['program_sha256']=sha256(raw(body['program'])).hexdigest()
        with pytest.raises((CropResultHold,PermissionError,ValueError)):put(store,body)
        assert count(store)==0,kind


def test_closed_bytes_reject_duplicate_nonfinite_noncanonical_and_oversize(crop_setup):
    store,body,_,_=crop_setup
    document=raw(body)
    for payload in (document+b' ',document.replace(b'"study_id":"study-1"',b'"study_id":"study-1","study_id":"other"'),
                    b'{"invalid":NaN}',b'\xff',b' '*(MAX_REQUEST_BYTES+1)):
        with pytest.raises(CropResultHold):store.put('tenant-1',payload)
    assert count(store)==0


def test_current_scope_farm_and_program_withdrawal_before_return_or_commit(crop_setup,monkeypatch):
    store,body,principal,rights=crop_setup
    first=put(store,body)
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        with pytest.raises(PermissionError):store.get('tenant-1',first['result_id'],body['farm'])
        principal['scopes'].add(scope)
    with pytest.raises(PermissionError):store.get('foreign',first['result_id'],body['farm'])
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm']|{'crop_id':'other'})
    assert store.get('tenant-1','crop-result-v1:'+'0'*64,body['farm']) is None
    rights.allowed=False
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])
    rights.allowed=True
    rights.allowed_uses=('research_calculation',)
    with pytest.raises(CropResultHold):put(store,body|{'revision':'r2'})
    assert count(store)==1
    rights.allowed_uses=('research_calculation','research_display')
    import app.crop_result_store as module
    original=module.integrate_crop
    def late_loss(**args):
        result=original(**args); rights.allowed=False; return result
    monkeypatch.setattr(module,'integrate_crop',late_loss)
    with pytest.raises(CropResultHold):put(store,body|{'revision':'r2'})
    assert count(store)==1
    rights.allowed=True; monkeypatch.setattr(module,'integrate_crop',original)
    original_checked=store._checked
    def post_insert_loss(*args):
        record=original_checked(*args); principal['scopes'].remove('crop_result_write'); return record
    monkeypatch.setattr(store,'_checked',post_insert_loss)
    with pytest.raises(PermissionError):put(store,body|{'revision':'r2'})
    assert count(store)==1
    principal['scopes'].add('crop_result_write'); monkeypatch.setattr(store,'_checked',original_checked)
    def read_loss(*args):
        record=original_checked(*args); rights.allowed=False; return record
    monkeypatch.setattr(store,'_checked',read_loss)
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])
    rights.allowed=True; monkeypatch.setattr(store,'_checked',original_checked)
    monkeypatch.setattr(store.farms.replay.candidates._source._source,'get_input_rights',lambda *_:None)
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])


def test_db_privileges_immutability_fk_and_authenticated_tampering(crop_setup,login_scope,monkeypatch):
    store,body,_,_=crop_setup; base,policy,dsns=login_scope
    first=put(store,body); target=store.jobs._table('crop_research_results')
    for kind in ('request','worker','supervisor'):
        with connect_runtime(dsns[kind],policy,kind) as conn,pytest.raises(errors.InsufficientPrivilege):
            conn.execute(sql.SQL('SELECT * FROM {} LIMIT 0').format(target))
        with connect_runtime(dsns[kind],policy,kind) as conn,pytest.raises(errors.InsufficientPrivilege):
            if kind=='supervisor':conn.execute('SET TRANSACTION READ WRITE')
            conn.execute(sql.SQL('INSERT INTO {} SELECT * FROM {} WHERE false').format(target,target))
    for statement in (sql.SQL('UPDATE {} SET revision=revision').format(target),
                      sql.SQL('DELETE FROM {}').format(target),sql.SQL('TRUNCATE {}').format(target)):
        with store.jobs.connect() as conn,pytest.raises(errors.InsufficientPrivilege):conn.execute(statement)
    for verb in ('UPDATE','DELETE'):
        query=sql.SQL('UPDATE {} SET revision=revision').format(target) if verb=='UPDATE' else sql.SQL('DELETE FROM {}').format(target)
        with base.connect() as conn,pytest.raises(errors.RaiseException,match='immutable'):conn.execute(query)
    # The owner can corrupt custody; validators must still reject bytes with old or recomputed hashes.
    with base.connect() as conn:
        row=conn.execute(sql.SQL('SELECT * FROM {}').format(target)).fetchone()
    foreign=deepcopy(json.loads(row['payload_raw'])); foreign['request']['study_id']='foreign-key-study'
    foreign['binding']['registration_job_id']=str(uuid4())
    foreign['result_id']='crop-result-v1:'+sha256(raw({k:v for k,v in foreign.items() if k!='result_id'})).hexdigest()
    foreign_raw=raw(foreign)
    with store.jobs.connect() as conn,pytest.raises(errors.ForeignKeyViolation):
        conn.execute(sql.SQL('''INSERT INTO {} (tenant_id,study_id,revision,result_id,scenario_id,
            scenario_revision,registration_job_id,registration_sha256,payload_raw,payload_sha256,integrity_signature,registered_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''').format(target),
            ('tenant-1','foreign-key-study',row['revision'],foreign['result_id'],row['scenario_id'],row['scenario_revision'],
             foreign['binding']['registration_job_id'],row['registration_sha256'],foreign_raw,sha256(foreign_raw).hexdigest(),
             store._signature(foreign_raw),row['registered_by']))
    original_find=store._find
    for patch in ({'payload_raw':row['payload_raw']+b' '},{'integrity_signature':'0'*64},
                  {'scenario_id':'other-farm'},{'registered_by':policy.roles['request']}):
        monkeypatch.setattr(store,'_find',lambda *args,patch=patch,**kwargs:{**row,**patch})
        with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])
    packet=json.loads(row['payload_raw']); packet['result']['samples'][-1]['lai']['value']+=1
    changed=raw(packet)
    monkeypatch.setattr(store,'_find',lambda *args,**kwargs:{**row,'payload_raw':changed,'payload_sha256':sha256(changed).hexdigest()})
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])
    monkeypatch.setattr(store,'_find',original_find)
    with base.connect() as conn:
        constraints=conn.execute('SELECT contype FROM pg_constraint WHERE conrelid=%s::regclass',
            (policy.schema+'.crop_research_results',)).fetchall()
    assert any(c['contype']=='f' for c in constraints)
    with base.connect() as conn:
        conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER crop_result_immutable').format(target))
        conn.execute(sql.SQL('UPDATE {} SET payload_raw=%s,payload_sha256=%s').format(target),(changed,sha256(changed).hexdigest()))
        conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER crop_result_immutable').format(target))
    with pytest.raises(CropResultHold):store.get('tenant-1',first['result_id'],body['farm'])


def test_explicit_binding_and_default_disabled_policy(crop_setup):
    store,_,_,_=crop_setup
    assert RuntimeLoginPolicy('test','owner','runtime','postgres').crop_result_storage is False
    with pytest.raises(RolePolicyHold):replace(store.jobs.runtime_identity[0],crop_result_storage=1)
    for notice,key,rights in ((NOTICE+b' ',KEY,store.program_rights),(NOTICE,b'short',store.program_rights),
                             (NOTICE,KEY,None)):
        with pytest.raises(CropResultHold):CropResultStore(store.farms,PROFILE,notice,program_rights=rights,integrity_key=key)
