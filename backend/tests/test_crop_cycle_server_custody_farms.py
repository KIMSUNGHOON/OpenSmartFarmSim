"""Real SCRAM/current farm checks around server-owned synthetic crop execution."""
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter

import pytest

from app import crop_cycle_server_custody as custody
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from app import crop_plant_startup_integration as original
from app.crop_cycle_farm_binding import CycleFarmBinding
from app.thermal_run_store import _canonical
from test_crop_cycle_artifact import PROFILES,NOTICE
from test_crop_cycle_farm_binding import SyntheticInputRights,counts
from test_crop_startup_result_store import shifted
from test_farm_authoring_storage import authoring,request
from test_farm_replay_scenario import farm_setup
from login_database import login_database,login_scope
from app.crop_result_store import READ_SCOPES,WRITE_SCOPES

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,'break_even_calculation':True,
    'crop_cycle_result_storage':True}],indirect=True)
KEY=b'own-synthetic-cycle-server-farm-key-01'
BUDGET={'max_steps':10000,'max_transitions':128}


class OwnInputResolver:
    version='own-synthetic-server-input-resolver-v1'
    def __init__(self,directory,root):self.directory,self.root=directory,root
    def __call__(self,root,**profiles):
        assert root==self.root
        return inputs.open_input_packet(self.directory,root,**profiles)


@pytest.fixture
def server_setup(authoring,tmp_path):
    farms,farm_body,principal=authoring
    registered=farms.submit('tenant-1',request(farm_body));principal['scopes'].update(WRITE_SCOPES)
    p=shifted();expected=original.integrate_plant_startup(**p,**PROFILES)
    anchors=p.pop('output_times');directory=tmp_path/'inputs'
    packet=inputs.write_input_packet(directory,**p,anchors=anchors,outputs=anchors,**PROFILES,program_id='own-server-custody-program')
    body={'study_id':'own-server-study','revision':'r1','farm':{
        'scenario_id':farm_body['farm']['scenario_id'],'scenario_revision':farm_body['farm']['scenario_revision'],
        'registration_sha256':registered.scenario_sha256,'crop_id':'crop-1'},
        'input':{'schema_version':inputs.VERSION,'root_sha256':packet['root_sha256'],'program_id':'own-server-custody-program'},
        'rights':{'schema_version':'crop-cycle-input-rights-v1','declaration_id':'own-server-input','revision':'r1',
            'input_root_sha256':packet['root_sha256'],'available_at':farm_body['farm']['decision_at'],
            **{k:True for k in ('ownership_asserted','access','store','transform','use','display')},'redistribute':False}}
    rights=SyntheticInputRights();binding=CycleFarmBinding(farms,**PROFILES,notice_raw=NOTICE,input_rights=rights)
    root=tmp_path/'server';root.mkdir(mode=0o700);resolver=OwnInputResolver(directory,packet['root_sha256'])
    service=custody.CycleServerCustody(binding,root,input_resolver=resolver,integrity_key=KEY)
    return service,_canonical(body),rights,principal,expected


def test_actual_scram_registered_farm_signed_server_equations_and_no_rhs_read_retry(server_setup,monkeypatch):
    service,raw,rights,principal,expected=server_setup;before=counts(service.binding)
    started=perf_counter();progress=service.advance('tenant-1',raw,budget=BUDGET);advance_seconds=perf_counter()-started
    value=json.loads(progress)
    assert value['status']=='completed' and value['scope']=='synthetic_crop_math_only'
    assert value['steps']==expected['steps'] and value['artifact_sha256'] and value['commit_count']==1
    assert counts(service.binding)==before and before[2:]==(0,0)
    fresh=custody.CycleServerCustody(service.binding,service.directory,input_resolver=service.input_resolver,integrity_key=KEY)
    def forbidden(*args,**kwargs):pytest.fail('completed retry/read must not execute RHS')
    monkeypatch.setattr(engine.short._Evaluator,'rhs',forbidden)
    tick=perf_counter();assert fresh.inspect('tenant-1',raw)==progress;inspect_seconds=perf_counter()-tick
    ticks={}
    for kind,limit in (('samples',64),('events',8)):
        tick=perf_counter();page=fresh.page('tenant-1',raw,progress,kind,0,limit);ticks[kind]=perf_counter()-tick
        assert page['next']==page['total'] and _canonical(page['records'])==_canonical(expected[kind])
    assert fresh.advance('tenant-1',raw,budget=BUDGET)==progress
    with service.binding.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    principal['scopes'].remove('crop_result_read')
    with pytest.raises(PermissionError):fresh.inspect('tenant-1',raw)
    principal['scopes'].add('crop_result_read')
    rights.allowed=False
    with pytest.raises(custody.CycleCustodyHold):fresh.inspect('tenant-1',raw)
    assert counts(service.binding)==before
    Path('/tmp/ossf-cycle-server-farm-reference-20261005.json').write_text(json.dumps({
        'scope':'synthetic_server_farm_custody_software_only','actual_scram':True,
        'progress_bytes':len(progress),'progress_sha256':sha256(progress).hexdigest(),'progress':value,
        'advance_seconds':advance_seconds,'inspect_seconds':inspect_seconds,'page_seconds':ticks,
        'same_fresh_service_bytes':True,'complete_retry_and_reads_rhs_zero':True,
        'current_scope_and_input_withdrawal_held':True,'crop_rows_and_runs':list(before[2:])},indent=2)+'\n')


def test_actual_registered_input_withdrawn_after_equations_does_not_select_new_head(server_setup,monkeypatch):
    service,raw,rights,_,_=server_setup;before=counts(service.binding);advance=engine.advance_chunk;calls=0
    def withdrawn(*args,**kwargs):
        nonlocal calls
        result=advance(*args,**kwargs);calls+=1;rights.allowed=False;return result
    monkeypatch.setattr(engine,'advance_chunk',withdrawn)
    with pytest.raises(custody.CycleCustodyHold):service.advance('tenant-1',raw,budget=BUDGET)
    assert calls==1
    where=service.directory/custody._intent_id('tenant-1',json.loads(raw))
    head=json.loads((where/'artifact'/'HEAD').read_bytes())
    assert head['commit_count']==0 and head['artifact_sha256'] is None
    assert len(list((where/'proofs').glob('*.json')))==1
    rights.allowed=True;monkeypatch.setattr(engine,'advance_chunk',advance)
    zero=json.loads(service.inspect('tenant-1',raw));assert zero['commit_count']==zero['steps']==0
    assert counts(service.binding)==before and before[2:]==(0,0)


def test_foreign_tenant_wrong_expected_progress_and_changed_resolver_are_held(server_setup,monkeypatch):
    service,raw,_,_,_=server_setup
    with pytest.raises(PermissionError):service.inspect('foreign',raw)
    progress=service.advance('tenant-1',raw,budget=BUDGET)
    with pytest.raises(custody.CycleCustodyHold):service.page('tenant-1',raw,progress+b' ','samples',0,1)
    monkeypatch.setattr(service.input_resolver,'version','changed-v2')
    with pytest.raises(custody.CycleCustodyHold):service.inspect('tenant-1',raw)
