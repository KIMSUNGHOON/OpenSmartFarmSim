"""Pure leaf binding controls; production parent job/DB proof is separate."""
from copy import deepcopy
from hashlib import sha256
import importlib
import json

import pytest

import test_crop_leaf_appearance_input_evidence as inputs


@pytest.fixture
def model():
    return importlib.import_module('app.crop_leaf_appearance_farm_binding')


def prepared(model):
    raw, source=inputs.prepared();authority,args=inputs.configured(model.evidence,raw,source)
    evidence=authority.issue(**args);parent=args['stem_arguments'];program=json.loads(raw)
    farm={'scenario_id':'farm-1','scenario_revision':'r1','registration_sha256':'1'*64,'crop_id':'crop-1'}
    body={'study_id':'owned-leaf-binding-study','revision':'r1','farm':farm,
        'input':{'schema_version':model.evidence.SOURCE_VERSION,'program_id':program['program_id'],
            'program_sha256':sha256(raw).hexdigest(),'source_sha256':sha256(source).hexdigest(),
            'evidence_sha256':sha256(evidence).hexdigest()},
        'parent':{'job_id':'87e432b9-f361-4195-8512-6c932832c870','result_sha256':'2'*64,
            'numerical_root_sha256':program['stem']['artifact_sha256']},
        'rights':{'schema_version':model.RIGHTS_VERSION,'declaration_id':'owned-leaf-rights','revision':'r1',
            'input_source_sha256':sha256(source).hexdigest(),'available_at':'2026-10-23T16:00:00Z',
            'redistribute':False,**{k:True for k in ('ownership_asserted','access','store','transform','use','display')}}}
    registration={'decision_at':'2026-10-23T16:00:00Z','crop':{'occupancy':{
        'start':'2026-10-01T00:00:00Z','end':'2026-10-02T00:00:00Z'}},
        'calendar_utc':{'start':'2026-09-30T15:00:00Z','end':'2026-10-02T15:00:00Z'}}
    parent_data={'packet':{k:parent[k] for k in ('program_raw','source_raw','evidence_raw')},
        'proof':{'numerical_root_sha256':program['stem']['artifact_sha256'],
            'program_sha256':parent['expected_program_sha256'],'source_sha256':parent['expected_source_sha256'],
            'input_evidence_sha256':sha256(parent['evidence_raw']).hexdigest()},
        'binding':{'registration':registration,'input':{'period':{'start':'2026-10-01T00:00:00Z',
            'end':'2026-10-02T00:00:00Z'},'time_origin_utc':'2026-10-01T00:00:00Z','shoot_id':'owned-shoot'}}}
    shell=object.__new__(model.LeafAppearanceFarmBinding);shell.input_authority=authority
    return shell,body,parent_data,{'program_raw':raw,'source_raw':source,'evidence_raw':evidence}


def test_original_source_parent_identity_and_period_without_scaling(model):
    shell,body,parent,packet=prepared(model)
    assert shell._request(inputs.canonical(body))==body
    source=shell._input(body,parent,packet);shell._scope(body,parent['binding']['registration'],source)
    assert source['source_record']==json.loads(packet['source_raw'])['provenance']
    assert source['parent_stem_evidence_sha256']==parent['proof']['input_evidence_sha256']
    assert source['period']==parent['binding']['input']['period'] and source['normalization']=='per_tracked_shoot'
    assert source['variable_count']==32
    for key in ['policy','initialization','leaf_profile']:
        assert source[key+'_sha256']==sha256(inputs.canonical(json.loads(packet['program_raw'])[key])).hexdigest()
    assert source['numerical_initial_state_validation'] is False and source['stem_artifact_root_verified'] is False
    assert 'plant_count' not in source and 'yield' not in source


@pytest.mark.parametrize('change',['extra','study','farm-extra','crop','farm-sha','source-schema','source-extra',
    'source-sha','rights-schema','rights-source','rights-use','rights-bool','rights-redistribute','rights-time',
    'parent-extra','parent-uuid','parent-result','parent-root','size'])
def test_closed_request_identity_and_limits(model,change):
    shell,body,_,_=prepared(model)
    if change=='extra':body['path']='/not-permitted'
    elif change=='study':body['study_id']=''
    elif change=='farm-extra':body['farm']['approved']=True
    elif change=='crop':body['farm']['crop_id']=True
    elif change=='farm-sha':body['farm']['registration_sha256']='invalid'
    elif change=='source-schema':body['input']['schema_version']='leaf-population-input-source-v1'
    elif change=='source-extra':body['input']['path']='/not-permitted'
    elif change=='source-sha':body['input']['program_sha256']='invalid'
    elif change=='rights-schema':body['rights']['schema_version']='morphology-input-rights-v1'
    elif change=='rights-source':body['rights']['input_source_sha256']='0'*64
    elif change=='rights-use':body['rights']['use']=False
    elif change=='rights-bool':body['rights']['display']=1
    elif change=='rights-redistribute':body['rights']['redistribute']=True
    elif change=='rights-time':body['rights']['available_at']='2026-10-23T16:00:00+09:00'
    elif change=='parent-extra':body['parent']['path']='/not-permitted'
    elif change=='parent-uuid':body['parent']['job_id']='not-a-job'
    elif change=='parent-result':body['parent']['result_sha256']='invalid'
    elif change=='parent-root':body['parent']['numerical_root_sha256']='invalid'
    raw=b'x'*(128*1024+1) if change=='size' else inputs.canonical(body)
    with pytest.raises(model.LeafAppearanceFarmBindingHold):shell._request(raw)


@pytest.mark.parametrize('change',['program','source','evidence','program-id','decision','parent-evidence','parent-root'])
def test_original_leaf_and_parent_proof_identity(model,change):
    shell,body,parent,packet=prepared(model)
    if change in ('program','source','evidence'):packet[change+'_raw']+=b' '
    elif change=='program-id':body['input']['program_id']='other'
    elif change=='decision':parent['binding']['registration']['decision_at']='2026-10-23T16:00:00.000001Z'
    elif change=='parent-evidence':parent['proof']['input_evidence_sha256']='0'*64
    elif change=='parent-root':parent['proof']['numerical_root_sha256']='0'*64
    with pytest.raises(model.LeafAppearanceFarmBindingHold):shell._input(body,parent,packet)


@pytest.mark.parametrize('change',['rights-late','source-late','crop-start','crop-end','calendar-start','calendar-end'])
def test_scope_one_microsecond_boundaries(model,change):
    shell,body,parent,packet=prepared(model);source=shell._input(body,parent,packet);registration=parent['binding']['registration']
    if change=='rights-late':body['rights']['available_at']='2026-10-23T16:00:00.000001Z'
    elif change=='source-late':source['source_record']['available_at']='2026-10-23T16:00:00.000001Z'
    elif change=='crop-start':registration['crop']['occupancy']['start']='2026-10-01T00:00:00.000001Z'
    elif change=='crop-end':registration['crop']['occupancy']['end']='2026-10-01T23:59:59.999999Z'
    elif change=='calendar-start':registration['calendar_utc']['start']='2026-10-01T00:00:00.000001Z'
    elif change=='calendar-end':registration['calendar_utc']['end']='2026-10-01T23:59:59.999999Z'
    with pytest.raises(model.LeafAppearanceFarmBindingHold):shell._scope(body,registration,source)
