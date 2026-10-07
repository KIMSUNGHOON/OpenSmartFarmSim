"""Projection grammar over real synthetic artifacts; no farm/HTTP authority."""
from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

from jsonschema import Draft202012Validator
import pytest

from app.api_crop_cycle_calculation_replay import CalculationCycleCropReplay,project_calculation_cycle_result,_public_bytes
from app import crop_cycle_calculation_result_store as storage
from app import crop_cycle_calculation_farm_binding as farms
from app import crop_cycle_calculation_server_custody as server
from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_context as engine
from app.thermal_run_store import _canonical
from test_crop_cycle_artifact import program,PROFILES,NOTICE,ROOT


def save_reference(name,value):
    root=os.environ.get('OSSF_CALCULATION_PROJECTION_EVIDENCE')
    if root:
        phase=os.environ.get('OSSF_CALCULATION_PROJECTION_PHASE','reference')
        with (Path(root)/(phase+'-'+name)).open('x') as handle:
            os.fchmod(handle.fileno(),0o400);json.dump(value,handle,sort_keys=True,indent=2)
            handle.write('\n');handle.flush();os.fsync(handle.fileno())


def forbid_computation(monkeypatch):
    def forbidden(*a,**k):pytest.fail('public projection repeated parser/context/QC/RHS')
    for module,name in ((engine.inputs,'open_input_packet'),(engine.legacy,'prepare_context'),
            (engine,'open_calculation_context'),(engine,'advance_chunk'),(artifact,'open_artifact'),
            (artifact._Files,'_load_prefix'),(artifact,'_validate_delta'),(engine.short._Evaluator,'rhs')):
        monkeypatch.setattr(module,name,forbidden)


def saved(path,p,*,outputs=None):
    p=deepcopy(p);anchors=p.pop('output_times')
    receipt=engine.inputs.write_input_packet(path/'inputs',**p,anchors=anchors,
        outputs=anchors if outputs is None else outputs,**PROFILES,program_id='own-projection-input')
    from test_crop_cycle_input_evidence import authority
    for file in (path/'inputs').iterdir():file.chmod(0o400)
    issuer=authority();input_raw=issuer.issue(path/'inputs',receipt['root_sha256'])
    ctx=engine.open_calculation_context(path/'inputs',receipt['root_sha256'],input_raw,authority=issuer)
    with ctx:
        source=ctx.reader
        with artifact.create_writer(path/'artifact',ctx,notice_raw=NOTICE) as writer:
            while writer.advance({'max_steps':10000,'max_transitions':128})['status']=='yielded':pass
            receipt=writer.finalize();header=writer._head()[0]['header_sha256']
            terminal={**deepcopy(writer._summary),'manifest':ctx.manifest}
        with artifact.open_artifact(path/'artifact',receipt['artifact_sha256'],ctx,notice_raw=NOTICE) as reader:
            data={k:reader.page(k,0,64 if k=='samples' else 8) for k in ('samples','events')}
            counts=reader.summary['counts']
        farm={'scenario_id':'own-projection-farm','scenario_revision':'r1',
            'registration_sha256':'2'*64,'crop_id':'crop-1'}
        request={'study_id':'own-projection-study','revision':'r1','farm':farm,
            'input':{'schema_version':engine.inputs.VERSION,'root_sha256':source.root_sha256,'program_id':source.manifest['program_id']},
            'rights':{'schema_version':farms.original.RIGHTS_VERSION,'declaration_id':'own-projection-rights','revision':'r1',
                'input_root_sha256':source.root_sha256,'available_at':'2020-01-01T00:00:00Z','redistribute':False,
                **{k:True for k in ('ownership_asserted','access','store','transform','use','display')}}}
        binding={'version':farms.VERSION,'scope':server.SCOPE,'tenant_id':'own-projection-tenant',
            'request':request,'registration':{'registration_job_id':'00000000-0000-0000-0000-000000000001',
                'registration_sha256':farm['registration_sha256'],'farm_sha256':'3'*64,'source_binding_sha256':'4'*64,
                'crop':{'crop_id':'crop-1','batch_id':'batch-1'},'zone_id':'zone-1','floor_area':{'value':'100.0','unit':'m²'},
                'normalization':'per_m2_floor','profile_applicability':'unvalidated_for_registered_crop'},
            'input':{'root_sha256':source.root_sha256,'calculation_sha256':source.calculation_sha256,
                'program_id':source.manifest['program_id'],'period':source.manifest['period'],
                'plan':source.plan,'profile_sha256':source.manifest['profile_sha256'],
                'normalization_sha256':source.manifest['normalization_sha256'],'python_version':source.manifest['python_version'],'input_validation':{
                    'context_sha256':ctx.root_sha256,'evidence_sha256':sha256(input_raw).hexdigest(),
                    'validated_context_sha256':ctx.manifest['input_validation']['validated_context_sha256'],
                    'engine_version':engine.VERSION,'input_evidence_version':farms.evidence.VERSION,
                    'calculation_code_sha256':engine.CODE_SHA256,'input_evidence_code_sha256':farms.evidence.CODE_SHA256,
                    'input_evidence_dependency_sha256':dict(farms.evidence.DEPENDENCY_SHA256)}},
            'rights_policy_version':'own-projection-policy-v1','binding_code_sha256':farms.CODE_SHA256,'binding_dependency_sha256':farms.DEPENDENCY_SHA256}
        progress={'version':server.VERSION,'scope':server.SCOPE,'intent_sha256':'5'*64,
            'binding_sha256':sha256(_canonical(binding)).hexdigest(),'input_root_sha256':source.root_sha256,
            'context_sha256':ctx.root_sha256,'custody_code_sha256':server.CODE_SHA256,'head_sha256':receipt['head_sha256'],
            'proof_sha256':'6'*64,'header_sha256':header,'artifact_sha256':receipt['artifact_sha256'],
            'status':terminal['status'],'commit_count':receipt['commit_count'],'steps':terminal['steps'],
            'planned_steps':terminal['planned_steps'],'counts':counts,
            'storage_bytes':sum(f.stat().st_size for f in (path/'artifact').iterdir()),
            'file_count':len(list((path/'artifact').iterdir()))}
        raw=storage._packet(_canonical(binding),_canonical(progress),'own-projection-resolver-v1',NOTICE)
    return {'result_id':json.loads(raw)['result_id'],'payload_raw':raw,'payload_sha256':sha256(raw).hexdigest(),
        'recorded_at':datetime(2026,10,6,0,0,tzinfo=timezone.utc)},terminal,data


@pytest.fixture(scope='module')
def original(tmp_path_factory):
    path=tmp_path_factory.mktemp('verified-cycle-public-projection');return saved(path,program('full-removal-reentry'))


def project(case,view='summary',offset=0,limit=None):
    record,terminal,data=case
    if view=='summary':return project_calculation_cycle_result(record,terminal).model_dump(mode='json')
    page=deepcopy(data[view]);maximum=64 if view=='samples' else 8;limit=maximum if limit is None else limit
    page['start']=offset;page['records']=page['records'][offset:offset+limit];page['next']=offset+len(page['records'])
    return project_calculation_cycle_result(record,terminal,view=view,page=page,limit=limit).model_dump(mode='json')


def test_original_closed_summary_pages_preserve_quantities_and_hide_private_fields(original,monkeypatch):
    record,terminal,data=original
    before=deepcopy(original);fd_before=len(os.listdir('/proc/self/fd'));forbid_computation(monkeypatch)
    started=perf_counter()
    summary=project(original);assert summary['summary']['manifest']==terminal['manifest'] and summary['page'] is None
    assert summary['reference']['claim_scope']=='synthetic_crop_math_only' and summary['reference']['gates']=='not_assessed'
    packet=json.loads(record['payload_raw']);validation=packet['binding']['input']['input_validation'];responses={}
    assert summary['schema_version']=='crop-cycle-calculation-replay-v1'
    assert summary['result_id'].startswith('crop-cycle-verified-result-v1:')
    assert summary['reference']['artifact_ref'].startswith('crop-cycle-verified-artifact-v1:')
    assert validation['context_sha256']!=validation['validated_context_sha256']
    assert summary['reference']['input_validation']==validation
    assert summary['reference']['runtime_roles_code_sha256']==storage.ROLE_SHA256
    assert summary['reference']['server_dependency_sha256']==server.DEPENDENCY_SHA256
    for view in ('samples','events'):
        value=project(original,view);assert value['summary'] is None and value['page']['total']==data[view]['total']
        assert value['reference']['input_validation']==validation
        expected=data[view]['records'] if view=='samples' else [{k:e[k] for k in ('at','before','after','removed')} for e in data[view]['records']]
        assert _canonical(value['page']['records'])==_canonical(expected)
        Draft202012Validator(CalculationCycleCropReplay.model_json_schema()).validate(value)
        raw=_canonical(value);responses[view]={'bytes':len(raw),'sha256':sha256(raw).hexdigest()}
    raw=_public_bytes(project_calculation_cycle_result(record,terminal))
    for field in (b'"tenant_id":',b'"registration_job_id":',b'"checkpoint":',b'"input_id":',
            b'"rights":',b'"initial_state":',b'"notice_raw":',b'"integrity_key":'):
        assert field not in raw
    assert len(raw)<=2*1024*1024
    assert original==before and len(os.listdir('/proc/self/fd'))==fd_before
    save_reference('normal-public.json',{'schema_version':summary['schema_version'],'steps':terminal['steps'],
        'sample_count':summary['reference']['sample_count'],'event_count':summary['reference']['event_count'],
        'summary_bytes':len(raw),'summary_sha256':sha256(raw).hexdigest(),'page_responses':responses,
        'manifest':summary['summary']['manifest'],'reference_input_validation':validation,
        'projection_and_checks_seconds':perf_counter()-started,'inputs_unchanged':True,
        'parser_context_QC_RHS_forbidden':True,'fd_before':fd_before,'fd_after':len(os.listdir('/proc/self/fd'))})


@pytest.mark.parametrize('name',['empty-no-entry','empty-entry','first-only','full-removal-reentry','positive-tail','night-smooth'])
def test_six_actual_artifacts_keep_all_original_sample_and_event_values(tmp_path,name,monkeypatch):
    case=saved(tmp_path,program(name));assert project(case)['reference']['status']=='completed'
    forbid_computation(monkeypatch)
    for kind in ('samples','events'):
        value=project(case,kind);expected=case[2][kind]['records']
        if kind=='events':expected=[{k:e[k] for k in ('at','before','after','removed')} for e in expected]
        assert _canonical(value['page']['records'])==_canonical(expected)


@pytest.mark.parametrize('fault',['id','payload-hash','record-extra','naive-time','manifest-hash','manifest-extra','code',
    'scope','steps','future-period','farm-crop','profile','terminal-extra','checkpoint','status','private-field'])
def test_mixed_rehashed_reference_and_terminal_shape_are_denied(original,fault):
    record,terminal,data=deepcopy(original);p=json.loads(record['payload_raw'])
    if fault=='id':record['result_id']=storage.VERSION+':'+'0'*64
    elif fault=='payload-hash':record['payload_sha256']='0'*64
    elif fault=='record-extra':record['external_path']='/tmp/untrusted'
    elif fault=='naive-time':record['recorded_at']=datetime(2026,10,6)
    elif fault=='manifest-hash':terminal['manifest']['grid_index_sha256']='0'*64
    elif fault=='manifest-extra':terminal['manifest']['coefficients']={}
    elif fault=='code':terminal['manifest']['code_sha256']['stream_execution']='0'*64
    elif fault=='scope':terminal['scope']='crop_forecast'
    elif fault=='steps':terminal['steps']=True
    elif fault=='terminal-extra':terminal['private_input']={}
    elif fault=='checkpoint':terminal['checkpoint']['output_cursor']+=1
    elif fault=='status':terminal['status']='yielded'
    else:
        if fault=='future-period':p['binding']['input']['period']['end']='2020-01-01T00:00:00Z'
        if fault=='farm-crop':p['binding']['registration']['crop']['crop_id']='foreign-crop'
        if fault=='profile':p['binding']['input']['profile_sha256']['growth_profile']='0'*64
        if fault=='private-field':p['code']['hmac_key']='private'
        p['policies']['server_progress']['binding_sha256']=sha256(_canonical(p['binding'])).hexdigest()
        p.pop('result_id');p['result_id']=storage.VERSION+':'+sha256(_canonical(p)).hexdigest()
        raw=_canonical(p);record.update(result_id=p['result_id'],payload_raw=raw,payload_sha256=sha256(raw).hexdigest())
    with pytest.raises(server.CalculationCustodyHold):project_calculation_cycle_result(record,terminal)


@pytest.mark.parametrize('fault',['extra','kind','offset-bool','next','total','limit-bool','limit-large','duplicate',
    'future','nonfinite','unit','sample-extra','integer-quantity','balance'])
def test_bad_page_identity_time_shape_and_raw_quantities_are_denied(original,fault):
    record,terminal,data=deepcopy(original);page=data['samples'];limit=64
    if fault=='extra':page['filepath']='untrusted'
    elif fault=='kind':page['kind']='events'
    elif fault=='offset-bool':page['start']=False
    elif fault=='next':page['next']+=1
    elif fault=='total':page['total']+=1
    elif fault=='limit-bool':limit=True
    elif fault=='limit-large':limit=65
    elif fault=='duplicate':page['records'][1]=deepcopy(page['records'][0])
    elif fault=='future':page['records'][-1]['at']='2030-01-01T00:00:00Z'
    elif fault=='nonfinite':page['records'][0]['state']['leaf']['value']=float('inf')
    elif fault=='unit':page['records'][0]['state']['leaf']['unit']='kg_fresh'
    elif fault=='sample-extra':page['records'][0]['forecast_margin']=0.9
    elif fault=='integer-quantity':page['records'][0]['state']['leaf']['value']=100000
    elif fault=='balance':page['records'][0]['carbon_residual']['value']=page['records'][0]['carbon_residual_budget']['value']+1
    with pytest.raises(server.CalculationCustodyHold):project_calculation_cycle_result(record,terminal,view='samples',page=page,limit=limit)


def test_empty_last_page_and_short_byte_bounded_page_use_original_next(original):
    record,terminal,data=original;page=deepcopy(data['samples']);page['records']=page['records'][:1];page['next']=1
    value=project_calculation_cycle_result(record,terminal,view='samples',page=page,limit=64).model_dump(mode='json')
    assert value['page']['next_offset']==1 and len(value['page']['records'])==1
    total=data['samples']['total'];empty=project(original,'samples',offset=total)
    assert empty['page']['records']==[] and empty['page']['next_offset'] is None
    with pytest.raises(server.CalculationCustodyHold):project_calculation_cycle_result(record,terminal,page=page)


@pytest.mark.parametrize('kind',['pre-onset','event','fractional'])
def test_actual_hold_only_exposes_confirmed_past_and_original_diagnostic(tmp_path,kind,monkeypatch):
    p=program('full-removal-reentry' if kind=='event' else 'night-smooth' if kind=='fractional' else 'empty-entry')
    if kind=='pre-onset':p['initial_state']['values']['temperature_sum']['value']=0
    elif kind=='event':p['events'][1]['removals']['values']['leaf']['value']=1e6
    else:
        p['initial_state']['values']['buffer']['value']=1;p['output_times']=[p['output_times'][0],p['output_times'][-1]]
        p['solver']['max_step_seconds']=3599
    case=saved(tmp_path,p);forbid_computation(monkeypatch);before=len(os.listdir('/proc/self/fd'))
    value=project(case);hold=value['summary']['hold'];original=case[1]
    assert original['status']==value['reference']['status']=='hold'
    assert hold['at']==original['hold']['at'] and hold['phase']==original['hold']['phase']
    assert _canonical(hold['last_confirmed'])==_canonical(original['last_confirmed'])
    for view in ('samples','events'):assert project(case,view)['page']['total']==case[2][view]['total']
    if original['last_confirmed'] is None:assert hold['last_confirmed'] is None
    assert len(os.listdir('/proc/self/fd'))==before
    save_reference('hold-'+kind+'.json',{'status':original['status'],'steps':original['steps'],
        'samples':case[2]['samples']['total'],'events':case[2]['events']['total'],
        'same_original_confirmed_past_and_diagnostic':True,'parser_context_QC_RHS_forbidden':True,
        'public_bytes':len(_public_bytes(project_calculation_cycle_result(case[0],case[1]))),
        'fd_before':before,'fd_after':len(os.listdir('/proc/self/fd'))})


def test_completed_program_without_output_does_not_invent_samples(tmp_path):
    case=saved(tmp_path,program(),outputs=[])
    assert project(case)['reference']['status']=='completed' and project(case)['reference']['sample_count']==0
    assert project(case,'samples')['page']['records']==[]


def test_real_25h_over10000_step_artifact_projects_all_original_pages_without_rhs(tmp_path,monkeypatch):
    spec=importlib.util.spec_from_file_location('cycle_public_long_reference',ROOT/'research/crop-cycle-stream-execution-reference.py')
    reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
    case=saved(tmp_path,reference.long_program());assert case[1]['steps']==11400
    forbid_computation(monkeypatch);fd_before=len(os.listdir('/proc/self/fd'));started=perf_counter();pages=0
    value=project(case);assert value['reference']['sample_count']==27 and value['reference']['event_count']==5
    for kind in ('samples','events'):
        actual=[];start=0
        while True:
            page=project(case,kind,start,7 if kind=='samples' else 2)['page'];actual.extend(page['records']);pages+=1
            if page['next_offset'] is None:break
            start=page['next_offset']
        expected=case[2][kind]['records']
        if kind=='events':expected=[{k:e[k] for k in ('at','before','after','removed')} for e in expected]
        assert _canonical(actual)==_canonical(expected)
    assert len(os.listdir('/proc/self/fd'))==fd_before
    save_reference('long-public.json',{'steps':case[1]['steps'],'samples':value['reference']['sample_count'],
        'events':value['reference']['event_count'],'pages':pages,'same_original_rows_and_UTC':True,
        'parser_context_QC_RHS_forbidden':True,'summary_bytes':len(_public_bytes(project_calculation_cycle_result(case[0],case[1]))),
        'projection_seconds':perf_counter()-started,'fd_before':fd_before,'fd_after':len(os.listdir('/proc/self/fd'))})


def repack(record,packet):
    packet['policies']['server_progress']['binding_sha256']=sha256(_canonical(packet['binding'])).hexdigest()
    packet['result_id']=storage.VERSION+':'+sha256(_canonical({k:v for k,v in packet.items() if k!='result_id'})).hexdigest()
    raw=_canonical(packet);record.update(result_id=packet['result_id'],payload_raw=raw,payload_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('fault', ['missing', 'changed', 'extra'])
def test_rehashed_server_prefix_dependency_cannot_change_public_provenance(original, fault, monkeypatch):
    record, terminal, _ = deepcopy(original)
    packet = json.loads(record['payload_raw'])
    dependencies = packet['code']['server_dependency_sha256']
    if fault == 'missing': del dependencies['prefix']
    elif fault == 'changed': dependencies['prefix'] = '0' * 64
    else: dependencies['unknown'] = '0' * 64
    repack(record, packet)
    forbid_computation(monkeypatch)
    with pytest.raises(server.CalculationCustodyHold):
        project_calculation_cycle_result(record, terminal)


@pytest.mark.parametrize('field',['context_sha256','evidence_sha256','validated_context_sha256','engine_version',
    'input_evidence_version','calculation_code_sha256','input_evidence_code_sha256','input_evidence_dependency_sha256'])
def test_rehashed_DB_validation_mixing_never_becomes_public(original,field,monkeypatch):
    record,terminal,_=deepcopy(original);packet=json.loads(record['payload_raw']);v=packet['binding']['input']['input_validation']
    if field=='input_evidence_dependency_sha256':v[field]['input_stream']='0'*64
    else:v[field]='0'*64
    if field=='context_sha256':packet['policies']['server_progress']['context_sha256']=v[field]
    repack(record,packet);forbid_computation(monkeypatch)
    with pytest.raises(server.CalculationCustodyHold):project_calculation_cycle_result(record,terminal)


@pytest.mark.parametrize('field',['version','evidence_sha256','validated_context_sha256','validation_engine_version',
    'validation_code_sha256','input_evidence_code_sha256','input_evidence_dependency_sha256'])
def test_rehashed_calculation_manifest_validation_cannot_mix_with_original_source(original,field,monkeypatch):
    record,terminal,_=deepcopy(original);packet=json.loads(record['payload_raw']);v=terminal['manifest']['input_validation']
    if field=='validation_code_sha256':v[field]['stream_execution']='0'*64
    elif field=='input_evidence_dependency_sha256':v[field]['input_stream']='0'*64
    else:v[field]='0'*64
    context=sha256(_canonical(terminal['manifest'])).hexdigest()
    packet['policies']['server_progress']['context_sha256']=context
    packet['binding']['input']['input_validation']['context_sha256']=context
    terminal['checkpoint']['root_sha256']=context;repack(record,packet);forbid_computation(monkeypatch)
    with pytest.raises(server.CalculationCustodyHold):project_calculation_cycle_result(record,terminal)


def test_coherently_rehashed_original_validation_digest_is_checked_against_original_manifest(original,monkeypatch):
    record,terminal,_=deepcopy(original);packet=json.loads(record['payload_raw'])
    terminal['manifest']['input_validation']['validated_context_sha256']='0'*64
    packet['binding']['input']['input_validation']['validated_context_sha256']='0'*64
    context=sha256(_canonical(terminal['manifest'])).hexdigest()
    packet['binding']['input']['input_validation']['context_sha256']=context
    packet['policies']['server_progress']['context_sha256']=context;terminal['checkpoint']['root_sha256']=context
    repack(record,packet);assert storage._decode(record['payload_raw'])==packet;forbid_computation(monkeypatch)
    with pytest.raises(server.CalculationCustodyHold):project_calculation_cycle_result(record,terminal)


def test_public_byte_boundary_and_copy_preserve_the_entire_original_response(original,monkeypatch):
    from app import api_crop_cycle_calculation_replay as api
    projected=project_calculation_cycle_result(original[0],original[1]);before=projected.model_dump(mode='json')
    raw=api._public_bytes(projected);assert api.MAX_RESPONSE_BYTES==2*1024*1024
    monkeypatch.setattr(api,'MAX_RESPONSE_BYTES',len(raw));assert api._public_bytes(projected)==raw
    monkeypatch.setattr(api,'MAX_RESPONSE_BYTES',len(raw)-1)
    with pytest.raises(server.CalculationCustodyHold):api._public_bytes(projected)
    assert projected.model_dump(mode='json')==before


@pytest.mark.parametrize('first',['app.api_crop_cycle_calculation_replay','app.operator_config','app.api'])
def test_three_fresh_import_orders_do_not_construct_calculation_or_authority(first):
    code='''import importlib,json,os,secrets,sys
before=len(os.listdir('/proc/self/fd'))
for name in [sys.argv[1],'app.api_crop_cycle_calculation_replay','app.operator_config','app.api']:importlib.import_module(name)
print(json.dumps({'fd_before':before,'fd_after':len(os.listdir('/proc/self/fd')),'first':sys.argv[1]}))
'''
    child=subprocess.run([sys.executable,'-c',code,first],capture_output=True,text=True,timeout=30)
    assert child.returncode==0 and child.stderr==''
    value=json.loads(child.stdout);assert value['fd_before']==value['fd_after']
    save_reference('import-'+first.rsplit('.',1)[-1]+'.json',{'exit_code':child.returncode,**value,
        'fresh_python_exec':True,'stdlib_secrets_preinitialized':True,
        'calculation_and_authority_construction_not_requested':True})
