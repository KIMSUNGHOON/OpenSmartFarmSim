"""Actual registered retrospective farm and completed stem job for leaf binding."""
from copy import deepcopy
import ctypes
import gc
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter

import psycopg
from psycopg import sql
import pytest

from app import crop_leaf_population_farm_binding as model
from app import crop_morphology_signed_artifact as signed
from app import crop_morphology_execution as execution
from app.crop_morphology_execution_worker import MorphologyExecutionWorker
from app.content_access import ContentAccess
from app.crop_result_store import WRITE_SCOPES
from app.farm_authoring_storage import FarmAuthoringRequest
from login_database import login_database,login_scope
from test_crop_morphology_signed_artifact_native import schema_hash,final_cleanup,KEY
from test_crop_morphology_execution_native import Resolver
import test_crop_leaf_population_input_evidence as leaf_inputs
import test_crop_morphology_input_evidence as stem_inputs
import morphology_farm_factory as factory


pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_cycle_result_storage':True}],indirect=True)


class LeafRights:
    policy_version='owned-leaf-population-input-rights-test-v1'
    allowed=True
    def __call__(self,tenant,declaration,source,use):
        return self.allowed and tenant=='tenant-1' and declaration['schema_version']==model.RIGHTS_VERSION \
            and declaration['input_source_sha256']==source and use in ('research_calculation','research_display')


def registered_leaf_services(login_scope,tmp_path,monkeypatch):
    parent_raw,parent_source=stem_inputs.prepared();parent_review=stem_inputs.review(parent_source)
    parent_authority=stem_inputs.authority(model.evidence.stem,parent_source,lambda _:deepcopy(parent_review))
    parent_args={**stem_inputs.arguments(parent_raw,parent_source),'decision_at':leaf_inputs.DECISION}
    parent_proof=parent_authority.issue(**parent_args)
    parent_packet=dict(program_raw=parent_raw,source_raw=parent_source,evidence_raw=parent_proof)
    farms,farm_body,principal=factory.create_farm(login_scope,monkeypatch,leaf_inputs.DECISION)
    registered=farms.submit('tenant-1',FarmAuthoringRequest.model_validate_json(model.farms.documents._canonical(farm_body)))
    principal['scopes'].update(set(WRITE_SCOPES)|{'simulation_create','cancel'})
    parent_rights=factory.SyntheticMorphologyRights()
    parent_binding=signed.farms.MorphologyFarmBinding(farms,parent_authority,input_rights=parent_rights)
    parent_body=factory.study(farm_body,registered.scenario_sha256,parent_packet,leaf_inputs.DECISION)
    signed_authority=signed.MorphologyArtifactAuthority(parent_binding,directory=tmp_path/'signed',
        access=ContentAccess(os.getuid(),os.getgid()),integrity_key=KEY,issuer_id='owned-native-research',key_id='owned-signed-result-key-v1')
    resolver=Resolver(parent_packet);parent_service=execution.MorphologyExecutionService(signed_authority,input_resolver=resolver)
    worker=MorphologyExecutionWorker(parent_service,tenant_id='tenant-1')
    job=parent_service.submit('tenant-1',model.farms.documents._canonical(parent_body))
    outcome=worker.run_once(str(job['job_id']));assert outcome.state=='succeeded'
    parent_query=model.parent_reads.MorphologyExecutionQuery(parent_service)
    parent=parent_query.read('tenant-1',str(job['job_id']),view='manifest')['manifest']
    raw,source=leaf_inputs.prepared();review=leaf_inputs.review(source)
    authority=model.evidence.LeafPopulationInputEvidenceAuthority(integrity_key=leaf_inputs.KEY,issuer_id='owned-software',
        key_id='owned-leaf-key-v1',review_resolver=lambda _:deepcopy(review),stem_input_authority=parent_authority)
    arguments={'program_raw':raw,'source_raw':source,'expected_program_sha256':sha256(raw).hexdigest(),
        'expected_source_sha256':sha256(source).hexdigest(),'review_id':'owned-leaf-review',
        'decision_at':leaf_inputs.DECISION,'stem_arguments':{**parent_args,'evidence_raw':parent_proof}}
    evidence=authority.issue(**arguments);packet=dict(program_raw=raw,source_raw=source,evidence_raw=evidence)
    rights=LeafRights();service=model.LeafPopulationFarmBinding(parent_query,authority,input_rights=rights)
    body={'study_id':'owned-native-leaf-study','revision':'r1','farm':parent_body['farm'],
        'parent':{'job_id':str(job['job_id']),'result_sha256':parent['result_sha256'],
            'numerical_root_sha256':parent['numerical_root_sha256']},
        'input':{'schema_version':model.evidence.SOURCE_VERSION,'program_id':json.loads(raw)['program_id'],
            'program_sha256':sha256(raw).hexdigest(),'source_sha256':sha256(source).hexdigest(),'evidence_sha256':sha256(evidence).hexdigest()},
        'rights':{'schema_version':model.RIGHTS_VERSION,'declaration_id':'owned-leaf-source','revision':'r1',
            'input_source_sha256':sha256(source).hexdigest(),'available_at':'2026-10-22T00:00:00Z','redistribute':False,
            **{k:True for k in ('ownership_asserted','access','store','transform','use','display')}}}
    return service,body,packet,parent_body,parent_packet,review,parent_review,principal,rights,parent_rights


def forbid_growth(monkeypatch):
    calls=factory.forbid_growth(monkeypatch)
    for name in ('crop_leaf_expansion','crop_leaf_area_change','crop_leaf_area','crop_rational_leaf_area',
                 'crop_leaf_inventory','crop_declared_leaf_births','crop_leaf_population','crop_leaf_stem_binding',
                 'crop_leaf_population_artifact_producer','crop_leaf_artifact_producer'):
        module=__import__('app.'+name,fromlist=['*'])
        for key,fn in vars(module).copy().items():
            if inspect.isfunction(fn) and fn.__module__==module.__name__ and not key.startswith('_'):
                label=name+'.'+key;calls[label]=0
                def fail(*args,_label=label,**kwargs):calls[_label]+=1;raise AssertionError('binding called growth')
                monkeypatch.setattr(module,key,fail)
    return calls


@pytest.fixture
def setup(login_scope,tmp_path,monkeypatch):
    values=registered_leaf_services(login_scope,tmp_path,monkeypatch)
    calls=forbid_growth(monkeypatch)
    yield (*values,calls)
    assert not any(calls.values())


def prepare(value):
    service,body,packet,*_=value
    return service.prepare('tenant-1',model.farms.documents._canonical(body),**packet)


def current(value,raw,*,write=False,body=None,tenant='tenant-1'):
    service,original,packet,*_=value
    return service.current(tenant,model.farms.documents._canonical(original if body is None else body),raw,**packet,write=write)


def test_actual_registered_completed_parent_read_write_and_fresh(setup,login_scope,tmp_path,monkeypatch):
    service,body,packet,parent_body,parent_packet,review,parent_review,principal,_,_,calls=setup
    before=schema_hash(login_scope[0]);writes={k:0 for k in ('submit','publish','record_decision','_insert_publication','_event','_durable_content')}
    sql_writes=[];timings={}
    with monkeypatch.context() as patch:
        for name in writes:
            def blocked(*args,_name=name,**kwargs):writes[_name]+=1;raise AssertionError('binding wrote a job')
            patch.setattr(type(service.jobs),name,blocked)
        original=psycopg.Cursor.execute
        def readonly_execute(self,statement,*args,**kwargs):
            text=statement if type(statement) is str else statement.as_string(self.connection)
            if re.match(r'^\s*(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|COPY|CALL|DO)\b',text,re.I):
                sql_writes.append(text.split()[0]);raise AssertionError('binding persistent SQL write')
            return original(self,statement,*args,**kwargs)
        patch.setattr(psycopg.Cursor,'execute',readonly_execute)
        started=perf_counter();raw=prepare(setup);timings['prepare']=perf_counter()-started
        started=perf_counter();assert current(setup,raw)==raw;timings['read']=perf_counter()-started
        started=perf_counter();assert current(setup,raw,write=True)==raw;timings['write_current']=perf_counter()-started
    assert not any(writes.values()) and not sql_writes
    doc=json.loads(raw)
    assert doc['parent_result_binding_verified'] is True and doc['rights_or_gate_approval'] is False
    assert doc['parent']['job_id']==body['parent']['job_id'] and doc['parent']['numerical_root_sha256']==body['parent']['numerical_root_sha256']
    assert doc['input']['variable_count']==43 and doc['registration']['decision_at']=='2026-10-22T00:00:00Z'
    assert schema_hash(login_scope[0])==before
    parent=service.parent_authority;payload=json.loads((parent.directory/body['parent']['result_sha256']).read_bytes())['payload']
    parent_binding=(parent.directory/payload['binding_sha256']).read_bytes()
    config=factory.fresh_config(parent.farm_binding,principal,parent_body,parent_packet,parent_review,parent_binding,tmp_path/'fresh')
    p=json.loads(Path(config).read_bytes());directory=tmp_path/'fresh'
    p['signed']={'directory':str(parent.directory),'key_file':factory.private_file(directory,'signed-key.private',parent.integrity_key),
        'issuer_id':parent.issuer_id,'key_id':parent.key_id}
    p['execution']={'job_id':body['parent']['job_id'],'resolver_version':service.parent_query.service.input_resolver.version}
    p['leaf']={'packet_files':{k:factory.private_file(directory,'leaf-'+k+'.private',v) for k,v in packet.items()},
        'body':body,'binding_file':factory.private_file(directory,'leaf-binding.private',raw),'review':review,
        'key_file':factory.private_file(directory,'leaf-key.private',service.input_authority.integrity_key),
        'issuer_id':service.input_authority.issuer_id,'key_id':service.input_authority.key_id}
    path=factory.private_file(directory,'leaf-configuration.private.json',model.farms.documents._canonical(p))
    gc.collect();ctypes.CDLL(None).malloc_trim(0)
    done=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('leaf_population_farm_fresh.py')),path],
        stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=180,
        env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1])})
    assert done.returncode==0,done.stderr
    fresh=json.loads(done.stdout);assert fresh['actual_SCRAM'] and fresh['binding_sha256']==sha256(raw).hexdigest()
    assert schema_hash(login_scope[0])==before and not any(calls.values())
    factory.save('leaf-binding-normal.json',{'binding_sha256':sha256(raw).hexdigest(),'binding_bytes':len(raw),
        'parent':doc['parent'],'leaf_program_sha256':doc['input']['program_sha256'],'decision_at':doc['registration']['decision_at'],
        'fresh':fresh,'growth_CLI_calls':calls,'job_write_calls':writes,'persistent_SQL_write_calls':sql_writes,
        'single_operation_seconds':timings,'database_before_after':[before,schema_hash(login_scope[0])],
        'actual_farm_Runs':0,'G0_G4':'not_assessed'})


def test_current_parent_leaf_scopes_registration_and_late_changes(setup,login_scope,monkeypatch):
    service,body,_,parent_body,_,review,parent_review,principal,rights,parent_rights,calls=setup
    raw=prepare(setup);jobs=service.parent_query.service.jobs
    queued_body=deepcopy(parent_body);queued_body['study_id']='owned-queued-parent'
    queued=service.parent_query.service.submit('tenant-1',model.farms.documents._canonical(queued_body))
    canceled_body=deepcopy(parent_body);canceled_body['study_id']='owned-canceled-parent'
    canceled=service.parent_query.service.submit('tenant-1',model.farms.documents._canonical(canceled_body));assert jobs.cancel('tenant-1',canceled['job_id'])
    before=schema_hash(login_scope[0]);cases=[]
    principal['scopes'].remove('crop_result_write');assert current(setup,raw)==raw
    with pytest.raises(PermissionError):current(setup,raw,write=True)
    principal['scopes'].add('crop_result_write')
    for scope in ('crop_result_read','artifact'):
        principal['scopes'].remove(scope)
        with pytest.raises(PermissionError):current(setup,raw)
        principal['scopes'].add(scope);cases.append('scope:'+scope)
    with pytest.raises(PermissionError):current(setup,raw,tenant='foreign')
    for key,value in [('result_sha256','0'*64),('numerical_root_sha256','0'*64),('job_id',str(queued['job_id'])),('job_id',str(canceled['job_id']))]:
        changed=deepcopy(body);changed['parent'][key]=value
        with pytest.raises(model.LeafPopulationFarmBindingHold):current(setup,raw,body=changed)
        cases.append('parent:'+key+':'+value[:8])
    changed=deepcopy(body);changed['farm']['crop_id']='other'
    with pytest.raises(model.LeafPopulationFarmBindingHold):current(setup,raw,body=changed)
    for state in (review,parent_review):
        state['status']='revoked'
        with pytest.raises(model.LeafPopulationFarmBindingHold):current(setup,raw)
        state['status']='accepted_for_software_validation'
    for state in (rights,parent_rights):
        state.allowed=False
        with pytest.raises(model.LeafPopulationFarmBindingHold):current(setup,raw)
        state.allowed=True
    with monkeypatch.context() as patch:
        original=type(parent_rights).__call__
        patch.setattr(type(parent_rights),'__call__',lambda self,t,d,s,use:use!='research_calculation' and original(self,t,d,s,use))
        assert current(setup,raw)==raw
        with pytest.raises(model.LeafPopulationFarmBindingHold):current(setup,raw,write=True)
    for change in ('parent-rights','leaf-review','scope','declaration'):
        with monkeypatch.context() as patch:
            original=LeafRights.__call__;seen=[]
            def late(self,tenant,declaration,source,use):
                answer=original(self,tenant,declaration,source,use);seen.append(1)
                if len(seen)==1:
                    if change=='parent-rights':parent_rights.allowed=False
                    elif change=='leaf-review':review['status']='revoked'
                    elif change=='scope':principal['scopes'].remove('artifact')
                    else:declaration['display']=False
                return answer
            patch.setattr(LeafRights,'__call__',late)
            with pytest.raises((model.LeafPopulationFarmBindingHold,PermissionError)):current(setup,raw,write=True)
        parent_rights.allowed=True;review['status']='accepted_for_software_validation';principal['scopes'].add('artifact');cases.append('late:'+change)
    with monkeypatch.context() as patch:
        original=service.parent_query.read;seen=[]
        def late_parent(*args,**kwargs):
            value=original(*args,**kwargs);seen.append(1)
            if len(seen)==2:review['status']='revoked'
            return value
        patch.setattr(service.parent_query,'read',late_parent)
        with pytest.raises(model.LeafPopulationFarmBindingHold):current(setup,raw)
    review['status']='accepted_for_software_validation';cases.append('late:parent-query-revoked-leaf')
    base,policy,_=login_scope;table=jobs._table('jobs');role=sql.Identifier(policy.roles['authority'])
    with base.connect() as conn:conn.execute(sql.SQL('GRANT DELETE ON {} TO {}').format(table,role))
    try:
        with pytest.raises(model.LeafPopulationFarmBindingHold):current(setup,raw)
    finally:
        with base.connect() as conn:conn.execute(sql.SQL('REVOKE DELETE ON {} FROM {}').format(table,role))
    row=service.farms.farms._find('tenant-1',body['farm']['scenario_id'],body['farm']['scenario_revision'])
    changed=row['input_bytes']+b' '
    with base.connect() as conn:
        conn.execute("SET LOCAL session_replication_role='replica'")
        conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE job_id=%s').format(table),
            (changed,sha256(changed).hexdigest(),row['job_id']))
    try:
        with pytest.raises(model.LeafPopulationFarmBindingHold):current(setup,raw)
    finally:
        with base.connect() as conn:
            conn.execute("SET LOCAL session_replication_role='replica'")
            conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE job_id=%s').format(table),
                (row['input_bytes'],row['input_sha256'],row['job_id']))
    assert current(setup,raw)==raw and schema_hash(base)==before and not any(calls.values())
    factory.save('leaf-binding-fences.json',{'cases':cases,'both_source_reviews_rights_revoked_rejected':True,
        'parent_calculation_right_required':True,'actual_excess_database_grant_rejected':True,
        'rehash_registration_corruption_rejected_in_owned_scratch_DB':True,
        'restored_original_binding':True,'database_before_after':[before,schema_hash(base)],'growth_CLI_calls':calls})
