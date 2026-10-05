"""Actual SCRAM publication of synthetic signed files; no crop validation gates."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime,timedelta
from hashlib import sha256
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
from time import perf_counter

from psycopg import sql
import pytest

from app import crop_cycle_result_store as storage
from app import crop_cycle_server_custody as custody
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from app.thermal_run_store import _canonical
from app.crop_result_store import _intent_lock_key
from test_crop_cycle_server_custody_farms import server_setup,OwnInputResolver,KEY,BUDGET
from test_crop_cycle_farm_binding import counts
from test_crop_cycle_artifact import PROFILES
from test_crop_startup_result_store import shifted
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database,login_scope

ROOT=Path(__file__).resolve().parents[2]
DB_KEY=b'own-synthetic-cycle-db-HMAC-key-001'
pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,'break_even_calculation':True,
    'crop_cycle_result_storage':True}],indirect=True)


def fresh(store):
    old=store.server
    server=custody.CycleServerCustody(old.binding,old.directory,input_resolver=old.input_resolver,integrity_key=old.integrity_key)
    return storage.CycleCropResultStore(server,integrity_key=DB_KEY)


def forbid_math(monkeypatch):
    def forbidden(*args,**kwargs):pytest.fail('DB publication or read executed crop math')
    monkeypatch.setattr(engine,'advance_chunk',forbidden);monkeypatch.setattr(engine.short._Evaluator,'rhs',forbidden)


def fork_read(store,result_id,farm,queue):
    try:
        restarted=fresh(store);record=restarted.get('tenant-1',result_id,farm)
        page=restarted.page('tenant-1',result_id,farm,'samples',0,64)
        queue.put({'record':record,'samples':page['records']})
    except Exception as exc:queue.put({'error':type(exc).__name__})


def test_short_publication_is_scram_immutable_and_restarted_reads_do_not_calculate(server_setup,monkeypatch):
    server,raw,_,_,expected=server_setup;server.advance('tenant-1',raw,budget=BUDGET)
    store=storage.CycleCropResultStore(server,integrity_key=DB_KEY);before=counts(server.binding);forbid_math(monkeypatch)
    tick=perf_counter();first=store.put('tenant-1',raw);put_seconds=perf_counter()-tick
    packet=json.loads(first['payload_raw']);farm=json.loads(raw)['farm']
    assert packet['artifact']['steps']==120 and packet['artifact']['status']=='completed'
    assert counts(server.binding)==(before[0],before[1],1,0) and before[2:]==(0,0)
    assert store.put('tenant-1',raw)==first
    restarted=fresh(store);tick=perf_counter();assert restarted.get('tenant-1',first['result_id'],farm)==first;get_seconds=perf_counter()-tick
    pages={};times={}
    for kind,limit in (('samples',64),('events',8)):
        tick=perf_counter();page=restarted.page('tenant-1',first['result_id'],farm,kind,0,limit);times[kind]=perf_counter()-tick
        assert _canonical(page['records'])==_canonical(expected[kind]);pages[kind]={'records':len(page['records']),'bytes':len(_canonical(page))}
    process=multiprocessing.get_context('fork');queue=process.Queue();child=process.Process(target=fork_read,args=(store,first['result_id'],farm,queue));child.start()
    try:
        value=queue.get(timeout=90);assert value['record']==first and _canonical(value['samples'])==_canonical(expected['samples'])
        child.join(5);assert not child.is_alive() and child.exitcode==0
    finally:
        if child.is_alive():child.kill();child.join(5)
        queue.close();queue.join_thread()
    with store.jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    Path('/tmp/ossf-cycle-db-farm-reference-20261005.json').write_text(json.dumps({'scope':'synthetic_registered_farm_software_only',
        'actual_scram':True,'payload_bytes':len(first['payload_raw']),'payload_sha256':first['payload_sha256'],
        'code_sha256':storage.CODE_SHA256,'put_seconds':put_seconds,'get_seconds':get_seconds,'pages':pages,'page_seconds':times,
        'immutable_retry_bytes_id_time':True,'fresh_service_and_fork_process_exact':True,'read_and_put_rhs_zero':True,
        'research_row_count':1,'actual_crop_runs':0},indent=2)+'\n')


def test_missing_yielded_result_foreign_tenant_and_invalid_key_cannot_publish(server_setup,monkeypatch):
    server,raw,_,_,_=server_setup;store=storage.CycleCropResultStore(server,integrity_key=DB_KEY)
    with pytest.raises(custody.CycleCustodyHold):store.put('tenant-1',raw)
    with pytest.raises(PermissionError):store.put('foreign',raw)
    assert store.get('tenant-1',storage.VERSION+':'+'0'*64,json.loads(raw)['farm']) is None
    for key in (b'short',KEY):
        with pytest.raises(custody.CycleCustodyHold):storage.CycleCropResultStore(server,integrity_key=key)
    progress=json.loads(server.advance('tenant-1',raw,budget={'max_steps':1,'max_transitions':1}));assert progress['status']=='yielded'
    forbid_math(monkeypatch)
    with pytest.raises(custody.CycleCustodyHold):store.put('tenant-1',raw)
    assert counts(server.binding)[2:]==(0,0)


@pytest.mark.parametrize('kind',['input','source','farm'])
@pytest.mark.parametrize('phase',['before-commit','after-commit'])
def test_actual_commit_boundary_rights_withdrawal_rolls_back_or_keeps_private_audit(server_setup,monkeypatch,kind,phase):
    server,raw,rights,_,_=server_setup;server.advance('tenant-1',raw,budget=BUDGET)
    store=storage.CycleCropResultStore(server,integrity_key=DB_KEY);forbid_math(monkeypatch)
    connect=store.jobs.connect;triggered=False;farm_find=server.binding.farms._find
    source=server.binding.farms.replay.candidates._source._source;source_rights=source.get_input_rights
    def withdraw():
        nonlocal triggered
        triggered=True
        if kind=='input':rights.allowed=False
        elif kind=='source':monkeypatch.setattr(source,'get_input_rights',lambda *_:None)
        else:monkeypatch.setattr(server.binding.farms,'_find',lambda *_:None)
    class PublicationConnection:
        inserted=False
        def __init__(self,conn):self.conn=conn
        def __getattr__(self,name):return getattr(self.conn,name)
        def execute(self,query,*args,**kwargs):
            result=self.conn.execute(query,*args,**kwargs)
            if hasattr(query,'as_string') and query.as_string(self.conn).startswith('INSERT INTO'):
                self.inserted=True
                if phase=='before-commit':withdraw()
            return result
    @contextmanager
    def connected():
        wrapper=None
        with connect() as conn:
            wrapper=PublicationConnection(conn);yield wrapper
        if phase=='after-commit' and wrapper.inserted:withdraw()
    monkeypatch.setattr(store.jobs,'connect',connected)
    with pytest.raises(custody.CycleCustodyHold):store.put('tenant-1',raw)
    assert triggered
    monkeypatch.setattr(store.jobs,'connect',connect)
    assert counts(server.binding)[2:]==(0 if phase=='before-commit' else 1,0)
    with store.jobs.connect() as conn:
        row=conn.execute(sql.SQL('SELECT result_id FROM {}').format(store.jobs._table(storage.schema.TABLE))).fetchone()
    if row:
        with pytest.raises(custody.CycleCustodyHold):store.get('tenant-1',row['result_id'],json.loads(raw)['farm'])
    rights.allowed=True;monkeypatch.setattr(source,'get_input_rights',source_rights);monkeypatch.setattr(server.binding.farms,'_find',farm_find)
    restored=store.put('tenant-1',raw);assert store.get('tenant-1',restored['result_id'],json.loads(raw)['farm'])==restored
    assert counts(server.binding)[2:]==(1,0)


def test_actual_separate_connection_advisory_lock_is_pending_and_read_scope_withdrawal_denies(server_setup,monkeypatch):
    server,raw,_,principal,_=server_setup;server.advance('tenant-1',raw,budget=BUDGET)
    store=storage.CycleCropResultStore(server,integrity_key=DB_KEY);forbid_math(monkeypatch);request=json.loads(raw)
    with store.jobs.connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(%s)',(_intent_lock_key('tenant-1',request['study_id'],request['revision']),))
        with pytest.raises(custody.CycleCustodyPending):store.put('tenant-1',raw)
    assert counts(server.binding)[2:]==(0,0)
    first=store.put('tenant-1',raw);principal['scopes'].remove('crop_result_read')
    with pytest.raises(PermissionError):store.get('tenant-1',first['result_id'],request['farm'])
    principal['scopes'].add('crop_result_read');assert store.get('tenant-1',first['result_id'],request['farm'])==first


def test_registered_25h_result_keeps_original_pages_and_immutable_db_reference(server_setup,tmp_path,monkeypatch):
    base,raw,_,_,_=server_setup
    spec=importlib.util.spec_from_file_location('independent_db_cycle_reference',ROOT/'research/crop-cycle-stream-execution-reference.py')
    reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
    program=reference.long_program();stamp=lambda s:(datetime.fromisoformat(s.replace('Z','+00:00'))+timedelta(days=273)).isoformat().replace('+00:00','Z')
    for segment in program['segments']:
        for k in ('start','end'):segment[k]=stamp(segment[k])
    for event in program['events']:event['at']=stamp(event['at'])
    program['output_times']=[stamp(s) for s in program['output_times']]
    tick=perf_counter();expected,_=reference.independent_control_flow(program,PROFILES);independent_seconds=perf_counter()-tick
    anchors=program.pop('output_times');directory=tmp_path/'long-inputs'
    packet=inputs.write_input_packet(directory,**program,anchors=anchors,outputs=anchors,**PROFILES,program_id='own-db-long-program')
    body=json.loads(raw);body['input'].update(root_sha256=packet['root_sha256'],program_id='own-db-long-program')
    body['rights']['input_root_sha256']=packet['root_sha256'];raw=_canonical(body)
    root=tmp_path/'long-server';root.mkdir(mode=0o700)
    server=custody.CycleServerCustody(base.binding,root,input_resolver=OwnInputResolver(directory,packet['root_sha256']),integrity_key=KEY)
    tick=perf_counter();advances=0
    while True:
        progress=server.advance('tenant-1',raw,budget=BUDGET);advances+=1
        if json.loads(progress)['status']!='yielded':break
    execution_seconds=perf_counter()-tick;assert json.loads(progress)['steps']==11400
    store=storage.CycleCropResultStore(server,integrity_key=DB_KEY);forbid_math(monkeypatch)
    tick=perf_counter();record=store.put('tenant-1',raw);publication_seconds=perf_counter()-tick
    assert json.loads(record['payload_raw'])['policies']['server_progress']==json.loads(progress)
    pages=[];timings=[];tick=perf_counter()
    for kind,limit in (('samples',7),('events',2)):
        actual=[];start=0
        while True:
            before=perf_counter();page=store.page('tenant-1',record['result_id'],body['farm'],kind,start,limit)
            timings.append(perf_counter()-before);pages.append({'kind':kind,'start':start,'records':len(page['records']),'bytes':len(_canonical(page))})
            actual.extend(page['records']);start=page['next']
            if start==page['total']:break
        assert _canonical(actual)==_canonical(expected[kind])
    read_seconds=perf_counter()-tick
    assert fresh(store).get('tenant-1',record['result_id'],body['farm'])==record
    assert store.put('tenant-1',raw)==record and counts(server.binding)[2:]==(1,0)
    Path('/tmp/ossf-cycle-db-long-reference-20261005.json').write_text(json.dumps({'scope':'registered_synthetic_25h_software_only',
        'code_sha256':storage.CODE_SHA256,'actual_steps':11400,'forcing_intervals':300,'samples':27,'events':5,
        'independent_control_flow_shares_frozen_rates':True,'canonical_independent_samples_events_equal':True,
        'actual_advances':advances,'independent_seconds':independent_seconds,'execution_seconds':execution_seconds,
        'publication_seconds':publication_seconds,'reading_seconds':read_seconds,'pages':pages,'page_seconds':timings,
        'payload_bytes':len(record['payload_raw']),'payload_sha256':record['payload_sha256'],
        'immutable_retry_and_fresh_service_exact':True,'publication_and_reads_rhs_zero':True,'research_rows':1,'actual_crop_runs':0},indent=2)+'\n')


def test_registered_numeric_hold_reads_original_reason_and_mid_summary_withdrawal_denies(server_setup,tmp_path,monkeypatch):
    base,raw,rights,_,_=server_setup;p=shifted();p['initial_state']['values']['temperature_sum']['value']=0
    expected=engine.short.physical.integrate_plant_startup(**p,**PROFILES);assert expected['status']=='hold'
    anchors=p.pop('output_times');directory=tmp_path/'hold-inputs'
    packet=inputs.write_input_packet(directory,**p,anchors=anchors,outputs=anchors,**PROFILES,program_id='own-db-hold-program')
    body=json.loads(raw);body['input'].update(root_sha256=packet['root_sha256'],program_id='own-db-hold-program')
    body['rights']['input_root_sha256']=packet['root_sha256'];raw=_canonical(body)
    root=tmp_path/'hold-server';root.mkdir(mode=0o700)
    server=custody.CycleServerCustody(base.binding,root,input_resolver=OwnInputResolver(directory,packet['root_sha256']),integrity_key=KEY)
    assert json.loads(server.advance('tenant-1',raw,budget=BUDGET))['status']=='hold'
    store=storage.CycleCropResultStore(server,integrity_key=DB_KEY);forbid_math(monkeypatch)
    record=store.put('tenant-1',raw);summary=store.summary('tenant-1',record['result_id'],body['farm'])
    for key in ('hold','last_confirmed'):assert _canonical(summary[key])==_canonical(expected[key])
    assert summary['status']=='hold' and counts(server.binding)[2:]==(1,0)
    copied=storage.deepcopy
    def withdrawn(value):
        out=copied(value);rights.allowed=False;return out
    monkeypatch.setattr(storage,'deepcopy',withdrawn)
    with pytest.raises(custody.CycleCustodyHold):store.summary('tenant-1',record['result_id'],body['farm'])


def test_valid_hmac_cannot_replace_selected_proof_or_db_authority_and_key(server_setup,monkeypatch):
    server,raw,_,_,_=server_setup;server.advance('tenant-1',raw,budget=BUDGET)
    store=storage.CycleCropResultStore(server,integrity_key=DB_KEY);forbid_math(monkeypatch)
    first=store.put('tenant-1',raw);farm=json.loads(raw)['farm'];row=store._find('tenant-1',result_id=first['result_id'])
    find=store._find
    for kind in ('signature','authority','proof','code','policies-extra','farm'):
        changed=deepcopy(row);packet=json.loads(row['payload_raw'])
        if kind=='signature':changed['integrity_signature']='0'*64
        elif kind=='authority':changed['registered_by']=store.jobs.runtime_identity[0].roles['worker']
        else:
            if kind=='proof':packet['policies']['server_progress']['proof_sha256']='0'*64
            if kind=='code':packet['code']['storage_code_sha256']='0'*64
            if kind=='policies-extra':packet['policies']['external_file_path']='/tmp/untrusted'
            if kind=='farm':packet['binding']['registration']['floor_area']['value']='12345'
            if kind=='farm':packet['policies']['server_progress']['binding_sha256']=sha256(_canonical(packet['binding'])).hexdigest()
            packet.pop('result_id');packet['result_id']=storage.VERSION+':'+sha256(_canonical(packet)).hexdigest()
            payload=_canonical(packet);changed.update(payload_raw=payload,payload_sha256=sha256(payload).hexdigest(),
                integrity_signature=store._signature(payload),result_id=packet['result_id'])
        monkeypatch.setattr(store,'_find',lambda *a,**k:changed)
        with pytest.raises(custody.CycleCustodyHold):store.get('tenant-1',changed['result_id'],farm)
    monkeypatch.setattr(store,'_find',find)
    other=storage.CycleCropResultStore(server,integrity_key=b'other-own-db-fixture-HMAC-key-00001')
    with pytest.raises(custody.CycleCustodyHold):other.get('tenant-1',first['result_id'],farm)
    assert store.get('tenant-1',first['result_id'],farm)==first and counts(server.binding)[2:]==(1,0)
