"""Current synthetic input/farm binding over actual SCRAM; no crop execution."""
from copy import deepcopy
from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path

from psycopg import sql
import pytest

from app.crop_cycle_farm_binding import CycleFarmBinding,CycleFarmBindingHold,MAX_BINDING_BYTES
from app import crop_cycle_input_stream as inputs
from app.runtime_roles import audit_runtime_roles
from app.thermal_run_store import _canonical
from test_crop_cycle_artifact import PROFILES,NOTICE
from test_crop_startup_result_store import shifted
from test_farm_authoring_storage import authoring,request
from test_farm_replay_scenario import farm_setup
from login_database import login_database,login_scope
from app.crop_result_store import READ_SCOPES,WRITE_SCOPES

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,'break_even_calculation':True,
    'crop_cycle_result_storage':True}],indirect=True)


class SyntheticInputRights:
    policy_version='synthetic-cycle-input-rights-test-v1'
    allowed=True
    uses=('research_calculation','research_display')
    def __init__(self):self.calls=[]
    def __call__(self,tenant,declaration,root,intended_use):
        self.calls.append((tenant,deepcopy(declaration),root,intended_use))
        return (self.allowed is True and tenant=='tenant-1'
            and declaration['schema_version']=='crop-cycle-input-rights-v1'
            and declaration['input_root_sha256']==root and intended_use in self.uses)


@pytest.fixture(autouse=True)
def no_crop_execution(monkeypatch):
    from app import crop_cycle_stream_execution as engine
    def forbidden(*args,**kwargs):pytest.fail('farm binding must not calculate a crop result')
    monkeypatch.setattr(engine,'advance_chunk',forbidden)
    monkeypatch.setattr(engine.short._Evaluator,'rhs',forbidden)


@pytest.fixture
def binding_setup(authoring,tmp_path):
    farms,farm_body,principal=authoring
    registered=farms.submit('tenant-1',request(farm_body));principal['scopes'].update(WRITE_SCOPES)
    p=shifted();anchors=p.pop('output_times');directory=tmp_path/'cycle-inputs'
    proof=inputs.write_input_packet(directory,**p,anchors=anchors,outputs=anchors,**PROFILES,
        program_id='own-cycle-binding-fixture')
    body={'study_id':'cycle-study-1','revision':'r1','farm':{
        'scenario_id':farm_body['farm']['scenario_id'],'scenario_revision':farm_body['farm']['scenario_revision'],
        'registration_sha256':registered.scenario_sha256,'crop_id':'crop-1'},
        'input':{'schema_version':inputs.VERSION,'root_sha256':proof['root_sha256'],'program_id':'own-cycle-binding-fixture'},
        'rights':{'schema_version':'crop-cycle-input-rights-v1','declaration_id':'own-cycle-input-1','revision':'r1',
            'input_root_sha256':proof['root_sha256'],'available_at':farm_body['farm']['decision_at'],
            **{k:True for k in ('ownership_asserted','access','store','transform','use','display')},'redistribute':False}}
    rights=SyntheticInputRights();service=CycleFarmBinding(farms,**PROFILES,notice_raw=NOTICE,input_rights=rights)
    with inputs.open_input_packet(directory,proof['root_sha256'],**PROFILES) as reader:
        yield service,body,reader,principal,rights,directory


def prepare(setup):
    service,body,reader,*_=setup
    return service.prepare('tenant-1',_canonical(body),reader)


def counts(service):
    with service.jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(service.jobs._table(table))).fetchone()['n']
            for table in ('jobs','job_events','crop_cycle_research_results','thermal_g1_runs'))


def test_actual_scram_registered_crop_and_input_binding_current_read_without_rows(binding_setup):
    service,body,reader,_,rights,_=binding_setup;before=counts(service);raw=prepare(binding_setup)
    value=json.loads(raw);assert _canonical(value)==raw and len(raw)<=MAX_BINDING_BYTES
    assert value['version']=='crop-cycle-farm-binding-v1' and value['scope']=='synthetic_crop_math_only'
    assert value['tenant_id']=='tenant-1' and value['request']==body
    assert value['input']['root_sha256']==reader.root_sha256
    assert value['input']['calculation_sha256']==reader.calculation_sha256
    assert value['input']['period']==reader.manifest['period'] and value['input']['plan']==reader.plan
    assert value['registration']['normalization']=='per_m2_floor'
    assert value['registration']['profile_applicability']=='unvalidated_for_registered_crop'
    assert value['registration']['crop']['crop_id']=='crop-1' and value['registration']['crop']['batch_id']
    assert value['registration']['floor_area']['unit']=='m²' and value['registration']['zone_id']
    assert [c[-1] for c in rights.calls]==['research_calculation','research_display']
    rights.calls.clear()
    assert service.current('tenant-1',_canonical(body),reader,raw)==raw
    assert [c[-1] for c in rights.calls]==['research_display']
    assert counts(service)==before and before[2:]==(0,0)
    with service.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
        audit_runtime_roles(conn,service.jobs.runtime_identity[0])


@pytest.mark.parametrize('kind',['extra','missing','version','root','program','rights-version','rights-root',
    'available','crop','farm','revision','identifier','declaration','rights-type','null','redistribute'])
def test_closed_root_request_and_current_registration_reject_wrong_inputs(binding_setup,kind):
    service,original,reader,_,_,_=binding_setup;body=deepcopy(original);before=counts(service)
    if kind=='extra':body['filesystem_path']='/tmp/untrusted'
    if kind=='missing':del body['input']['root_sha256']
    if kind=='version':body['input']['schema_version']='crop-program-v3'
    if kind=='root':body['input']['root_sha256']='0'*64
    if kind=='program':body['input']['program_id']='other-program'
    if kind=='rights-version':body['rights']['schema_version']='inline-program-rights-v1'
    if kind=='rights-root':body['rights']['input_root_sha256']='0'*64
    if kind=='available':body['rights']['available_at']='2099-01-01T00:00:00Z'
    if kind=='crop':body['farm']['crop_id']='other-crop'
    if kind=='farm':body['farm']['registration_sha256']='0'*64
    if kind=='revision':body['farm']['scenario_revision']='other-revision'
    if kind=='identifier':body['study_id']='unsafe id'
    if kind=='declaration':body['rights']['program_sha256']=body['input']['root_sha256']
    if kind=='rights-type':body['rights']['display']=1
    if kind=='null':body['input']=None
    if kind=='redistribute':body['rights']['redistribute']=True
    with pytest.raises(CycleFarmBindingHold):service.prepare('tenant-1',_canonical(body),reader)
    assert counts(service)==before


@pytest.mark.parametrize('kind',['space','duplicate','nan','utf8','empty','oversize'])
def test_raw_request_is_canonical_and_bounded(binding_setup,kind):
    service,body,reader,*_=binding_setup
    raw={'space':_canonical(body)+b' ','duplicate':b'{"x":1,"x":2}','nan':b'{"x":NaN}',
        'utf8':b'\xff','empty':b'','oversize':b' '*(MAX_BINDING_BYTES+1)}[kind]
    with pytest.raises(CycleFarmBindingHold):service.prepare('tenant-1',raw,reader)


@pytest.mark.parametrize('kind',['rights','source','read-scopes','write-scope','foreign','late-source','late-scope','late-rights'])
def test_current_rights_and_callback_interruption_reject_revocation(binding_setup,monkeypatch,kind):
    service,body,reader,principal,rights,_=binding_setup;raw=prepare(binding_setup);before=counts(service)
    source=service.farms.replay.candidates._source._source
    if kind=='rights':rights.allowed=False
    if kind=='source':monkeypatch.setattr(source,'get_input_rights',lambda *_:None)
    if kind=='read-scopes':
        for scope in READ_SCOPES:
            principal['scopes'].remove(scope)
            with pytest.raises(PermissionError):service.current('tenant-1',_canonical(body),reader,raw)
            principal['scopes'].add(scope)
        return
    if kind=='write-scope':
        principal['scopes'].remove('crop_result_write')
        assert service.current('tenant-1',_canonical(body),reader,raw)==raw
        with pytest.raises(PermissionError):service.current('tenant-1',_canonical(body),reader,raw,write=True)
        return
    if kind=='foreign':
        with pytest.raises(PermissionError):service.current('foreign',_canonical(body),reader,raw)
        return
    if kind.startswith('late-'):
        original=rights.__class__.__call__
        calls=0
        def changed(self,*args):
            nonlocal calls
            answer=original(self,*args);calls+=1
            if calls==1:
                if kind=='late-source':monkeypatch.setattr(source,'get_input_rights',lambda *_:None)
                if kind=='late-scope':principal['scopes'].remove('crop_result_read')
                if kind=='late-rights':self.allowed=False
            return answer
        monkeypatch.setattr(rights.__class__,'__call__',changed)
    with pytest.raises((CycleFarmBindingHold,PermissionError)):
        service.current('tenant-1',_canonical(body),reader,raw,write=True)
    assert counts(service)==before


@pytest.mark.parametrize('kind',['profile','policy-version','provider','farm','identity','code','notice','closed','root-file','block-file','expected'])
def test_fixed_runtime_reader_files_and_expected_binding_cannot_change(binding_setup,monkeypatch,kind):
    service,body,reader,_,rights,directory=binding_setup;raw=prepare(binding_setup)
    if kind=='profile':service.growth_profile=object()
    if kind=='policy-version':rights.policy_version='other-version'
    if kind=='provider':service.input_rights=SyntheticInputRights()
    if kind=='farm':service.farms=object()
    if kind=='identity':service.jobs.runtime_identity=(service.jobs.runtime_identity[0],'request')
    if kind=='code':
        from app import crop_cycle_farm_binding as module
        monkeypatch.setattr(module,'CODE_SHA256','0'*64)
    if kind=='notice':service.notice_raw=b'not-the-notice'
    if kind=='closed':reader.close()
    if kind=='root-file':(directory/'root.json').write_bytes((directory/'root.json').read_bytes()+b' ')
    if kind=='block-file':
        name=reader.manifest['streams']['segments']['blocks'][0]['sha256']+'.json'
        (directory/name).write_bytes((directory/name).read_bytes()+b' ')
    if kind=='expected':raw=_canonical({**json.loads(raw),'tenant_id':'foreign'})
    with pytest.raises(CycleFarmBindingHold):service.current('tenant-1',_canonical(body),reader,raw)


@pytest.mark.parametrize('answer',[1,'true',None,{},False])
def test_callback_requires_exact_true_and_cannot_change_declaration(binding_setup,monkeypatch,answer):
    service,body,reader,_,rights,_=binding_setup
    monkeypatch.setattr(rights.__class__,'__call__',lambda *args:answer)
    with pytest.raises(CycleFarmBindingHold):service.prepare('tenant-1',_canonical(body),reader)


def test_period_outside_registered_occupancy_is_rejected(binding_setup,tmp_path):
    service,body,_,*_=binding_setup;p=shifted();p['segments']=[p['segments'][0]];p['segments'][0]['start']='2026-01-01T00:00:00Z'
    p['segments'][-1]['end']='2026-01-01T00:05:00Z';p['events']=[]
    anchors=['2026-01-01T00:00:00Z','2026-01-01T00:05:00Z'];p.pop('output_times')
    assert len(p['segments'])==1
    path=tmp_path/'outside-input';proof=inputs.write_input_packet(path,**p,anchors=anchors,outputs=anchors,**PROFILES,program_id='outside-period')
    body=deepcopy(body);body['input'].update(root_sha256=proof['root_sha256'],program_id='outside-period')
    body['rights']['input_root_sha256']=proof['root_sha256']
    with inputs.open_input_packet(path,proof['root_sha256'],**PROFILES) as reader,pytest.raises(CycleFarmBindingHold):
        service.prepare('tenant-1',_canonical(body),reader)


def child_binding(service,body,directory,expected,queue):
    try:
        fresh=CycleFarmBinding(service.farms,**PROFILES,notice_raw=NOTICE,input_rights=SyntheticInputRights())
        with inputs.open_input_packet(directory,body['input']['root_sha256'],**PROFILES) as reader:
            queue.put(fresh.current('tenant-1',_canonical(body),reader,expected))
    except Exception as exc:queue.put({'error':type(exc).__name__})


def test_fresh_process_reconnection_preserves_binding_bytes_and_fd_cleanup(binding_setup):
    service,body,reader,_,_,directory=binding_setup;raw=prepare(binding_setup)
    context=multiprocessing.get_context('fork');queue=context.Queue()
    child=context.Process(target=child_binding,args=(service,body,directory,raw,queue));child.start()
    try:
        assert queue.get(timeout=45)==raw
        child.join(5);assert not child.is_alive() and child.exitcode==0
    finally:
        if child.is_alive():child.kill();child.join(5)
        queue.close();queue.join_thread()
    fds=len(os.listdir('/proc/self/fd'))
    for _ in range(3):assert service.current('tenant-1',_canonical(body),reader,raw)==raw
    assert len(os.listdir('/proc/self/fd'))==fds


@pytest.mark.parametrize('kind',['root-after-policy','block-after-policy','reader-memory','mutable-declaration'])
def test_policy_callback_and_reader_memory_cannot_change_preflighted_input(binding_setup,monkeypatch,kind):
    service,body,reader,_,rights,directory=binding_setup;original_body=deepcopy(body)
    if kind=='reader-memory':reader._root['program_id']='another-private-root'
    else:
        original=rights.__class__.__call__;calls=0
        def changed(self,tenant,declaration,root,use):
            nonlocal calls
            answer=original(self,tenant,declaration,root,use);calls+=1
            if calls==1:
                if kind=='mutable-declaration':declaration['display']=False
                else:
                    name='root.json' if kind=='root-after-policy' else reader.manifest['streams']['segments']['blocks'][0]['sha256']+'.json'
                    path=directory/name;path.write_bytes(path.read_bytes()+b' ')
            return answer
        monkeypatch.setattr(rights.__class__,'__call__',changed)
    with pytest.raises(CycleFarmBindingHold):service.prepare('tenant-1',_canonical(body),reader)
    assert body==original_body
