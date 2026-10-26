from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest

from app import crop_funded_fractional_stem_binding as model
from app.crop_leaf_funded_birth_artifact_producer import produce_funded_leaf_artifact
from test_crop_funded_event_time import sources,profiles,ACCESS,TOLERANCE
from test_crop_funded_fractional_birth_point import inputs as point_inputs
from test_crop_leaf_carbon_stock_artifact import encoded

ROOT=Path(__file__).resolve().parents[2]
PARENTS=['synthetic-initial-0','synthetic-initial-1','synthetic-initial-2']


def frac(value):return Fraction(int(value['numerator']),int(value['denominator']))


def declaration(context):
    d=context.value;selection=d['source']['candidate']['selection'];directory=context._leaf_directory
    m=json.loads((directory/selection['leaf_root_sha256']).read_bytes())
    return {'schema_version':'funded-fractional-initial-links-v1','input_id':'test-initial-links','origin':'synthetic',
        'context_sha256':context.sha256,'leaf_root_sha256':selection['leaf_root_sha256'],'stem_root_sha256':selection['stem_root_sha256'],
        'root_initial_state_sha256':m['initial_state_sha256'],'model_floor_area':deepcopy(d['program']['model_floor_area']),
        'initial_attachments':[{'leaf_id':leaf,'attachment_internode_id':PARENTS[i]}for i,leaf in enumerate(d['original']['root_leaf_ids'])],
        'rights':deepcopy(m['source_rights']),'reviewer':'native-development-software-QA'}


@pytest.fixture(scope='module')
def prepared(sources,profiles,tmp_path_factory):
    spec=importlib.util.spec_from_file_location('relink',ROOT/'research/relink-funded-stem-fixtures.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    base,sr,lr,_=sources;manifest=json.loads((base/'leaf'/lr).read_bytes());raw=(base/'leaf'/manifest['sources']['inputs']['sha256']).read_bytes()
    original=json.loads(raw);original['step_count']=64;inputs=driver.relink_inputs(original,PARENTS[:2],profiles)
    directory=tmp_path_factory.mktemp('fractional-binding')/'leaf';root=produce_funded_leaf_artifact(directory,ACCESS,inputs_raw=encoded(inputs),**profiles)
    pc=model.crop.birth.prepare_fractional_birth_context(directory,base/'stem',ACCESS,leaf_root_sha256=root,
        stem_root_sha256=sr,stem_start_index=0,bracket_index=0,time_tolerance_seconds_exact=TOLERANCE)
    identity=model.describe_fractional_internode(pc);value=point_inputs(pc);value['events'][0]['attachment_internode_id']=identity['internode_id']
    context=model.crop.prepare_context(point_context=pc,inputs=value);initial=model.crop.start(context)
    mid=model.crop.advance_chunk(context,initial,1)['checkpoint'];final=model.crop.advance_chunk(context,mid,128)['checkpoint']
    return pc,context,initial,mid,final,identity


@pytest.mark.parametrize('place',[2,3,4])
def test_actual_new_parent_shared_clock_old_anchors_leaf_state_and_checkpoint(prepared,place):
    _,context,initial,_,_,identity=prepared;cp=prepared[place];before=context._raw;cp_raw=cp._raw;decl=declaration(context)
    result=model.bind_fractional_crop(context,cp,decl);data=context.value;v=cp.value;nodes=result['shoot']['internodes']
    assert [node['internode_id']for node in nodes[:3]]==PARENTS and nodes[-1]['internode_id']==identity['internode_id']
    assert len(nodes)==4 and len(result['leaves'])==6 and result['leaves'][-1]['attachment_internode_id']==nodes[-1]['internode_id']
    assert result['checkpoint']==v and context._raw==before and cp._raw==cp_raw and result['initial_bindings']==decl
    elapsed=frac(v['at']['elapsed_seconds_exact']);birth=frac(initial.value['at']['elapsed_seconds_exact'])
    integral=Fraction.from_float(v['lifetime_integrated_transfers']['indoor_air_temperature_time']['value']);first=Fraction.from_float(initial.value['lifetime_integrated_transfers']['indoor_air_temperature_time']['value'])
    assert frac(nodes[-1]['age_exact'])==(integral-first-5*(elapsed-birth))/86400
    for node in nodes[:3]:
        assert frac(node['age_exact'])==Fraction(119,24)+(integral-5*elapsed)/86400
        assert node['initial_anchor']['clock_state']['time_origin_utc']=='2026-10-01T00:00:00Z'
    if place==2:assert nodes[-1]['age_exact']['numerator']=='0'and nodes[-1]['length']==nodes[-1]['initial_anchor']['canonical_initial_length']
    assert frac(result['shoot']['birth']['threshold_overshoot_exact'])>0
    assert result['shoot']['birth']['numerical_root_interval']==identity['numerical_root_interval']
    assert result['simulation_start_development_seconds_exact']=={'numerator':'25200','denominator':'1','unit':'s'}
    n=len(result['leaves']);y=v['last_confirmed']['state']
    for i,leaf in enumerate(result['leaves']):assert [leaf[k]['value']for k in ['thermal_age','area','carbohydrate']]==[y[107+i],y[107+n+i],y[107+2*n+i]]
    assert result['G0_G4']=='not_assessed'and result['new_stem_carbon_allocation']=='not_independently_allocated_in_aggregate_stem_pool'


@pytest.mark.parametrize('change',[
    lambda v:v.update(extra=1),lambda v:v.update(context_sha256='0'*64),lambda v:v.update(leaf_root_sha256='0'*64),
    lambda v:v.update(stem_root_sha256='0'*64),lambda v:v.update(root_initial_state_sha256='0'*64),
    lambda v:v['model_floor_area'].update(value=2.),lambda v:v.update(initial_attachments=[]),
    lambda v:v['initial_attachments'][0].update(leaf_id='other'),lambda v:v['initial_attachments'][0].update(attachment_internode_id='unknown'),
    lambda v:v['initial_attachments'][0].update(extra=1),lambda v:v['rights'].update(display=False),
    lambda v:v['rights'].update(redistribute=1),lambda v:v.update(reviewer='')])
def test_closed_explicit_initial_mapping_source_floor_and_rights(prepared,change):
    _,ctx,cp,*_=prepared;v=declaration(ctx);change(v)
    with pytest.raises(model.FractionalStemBindingHold):model.bind_fractional_crop(ctx,cp,v)


def test_preexisting_leaf_cannot_bind_to_new_future_parent(prepared):
    _,ctx,cp,_,_,identity=prepared;v=declaration(ctx);v['initial_attachments'][0]['attachment_internode_id']=identity['internode_id']
    with pytest.raises(model.FractionalStemBindingHold,match='precedes'):model.bind_fractional_crop(ctx,cp,v)


def test_original_placeholder_input_is_held_without_repair(prepared):
    pc,_,_,_,_,_=prepared;v=point_inputs(pc);ctx=model.crop.prepare_context(point_context=pc,inputs=v);cp=model.crop.start(ctx)
    with pytest.raises(model.FractionalStemBindingHold,match='parent absent'):model.bind_fractional_crop(ctx,cp,declaration(ctx))


def test_describe_has_zero_RHS_and_binding_only_current_validation_no_past_work(prepared,monkeypatch):
    import socket,subprocess,psycopg
    pc,ctx,cp,_,_,identity=prepared;evaluate=model.crop.short._evaluate;calls=[]
    def current(*a,**k):calls.append(1);return evaluate(*a,**k)
    def forbidden(*a,**k):raise AssertionError('no old ODE/clock/initialization/external effect')
    monkeypatch.setattr(model.crop.short,'_evaluate',current)
    for owner,name in [(model.crop,'advance_chunk'),(model.crop,'adopt_births'),(model.crop.birth,'prepare_fractional_birth_context'),
        (model.crop.birth,'apply_fractional_births'),(model.crop.old,'advance_chunk'),(model.crop.old.parent,'prepare_context'),
        (model.crop.old.parent,'advance_chunk'),(model.epochs,'project_funded_shoot_from_stored_state'),
        (model.length,'advance_rational_internode_thermal_clock'),(model.length,'initialize_rational_internode_length'),
        (subprocess,'Popen'),(socket,'socket'),(psycopg,'connect')]:monkeypatch.setattr(owner,name,forbidden)
    assert model.describe_fractional_internode(pc)['internode_id']==identity['internode_id']and calls==[]
    result=model.bind_fractional_crop(ctx,cp,declaration(ctx));assert len(calls)==result['checkpoint_validation_RHS_evaluations']==1


def test_late_code_and_bounded_output_hold(prepared,monkeypatch):
    _,ctx,cp,*_=prepared
    value=declaration(ctx);monkeypatch.setattr(model,'MAX_BYTES',len(encoded(value))+16)
    with pytest.raises(model.FractionalStemBindingHold,match='bounded coupled binding output'):model.bind_fractional_crop(ctx,cp,value)
    monkeypatch.setattr(model,'MAX_BYTES',2*1024**2);monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    with pytest.raises(model.FractionalStemBindingHold,match='CODE_HOLD'):model.bind_fractional_crop(ctx,cp,declaration(ctx))


def test_same_time_additional_leaves_preserve_actual_new_parent_and_air_age(prepared):
    from test_crop_funded_fractional_continuation import adoption
    _,ctx,_,cp,_,identity=prepared;before=model.bind_fractional_crop(ctx,cp,declaration(ctx))
    value=adoption(ctx,cp,'bound-additional',2)
    for event in value['events']:event['attachment_internode_id']=identity['internode_id']
    updated=model.crop.adopt_births(ctx,cp,value);after_cp=model.crop.start(updated)
    after=model.bind_fractional_crop(updated,after_cp,declaration(updated))
    assert len(after['leaves'])==8 and after['shoot']==before['shoot']and after['at']==before['at']
    assert after['phase']=='after_birth'and after['output_cursor']==before['output_cursor']+1
    assert all(leaf['attachment_internode_id']==identity['internode_id']for leaf in after['leaves'][-2:])


def test_late_source_display_withdrawal_is_held(prepared,monkeypatch):
    _,ctx,cp,*_=prepared;original=model.stem.read_rational_morphology_manifest;calls=[]
    def withdraw(*a,**k):
        value=original(*a,**k);calls.append(1)
        if len(calls)>=3:value['program_rights']['display']=False
        return value
    monkeypatch.setattr(model.stem,'read_rational_morphology_manifest',withdraw)
    with pytest.raises(model.FractionalStemBindingHold,match='RIGHTS_HOLD'):model.bind_fractional_crop(ctx,cp,declaration(ctx))


def test_changed_selected_stem_epoch_is_held(prepared,monkeypatch):
    _,ctx,cp,*_=prepared;original=model.epochs._selected
    def altered(*a,**k):
        state,digest,result,raw=original(*a,**k);state=deepcopy(state);state['timeline_state']['at']='2026-10-01T06:00:00Z'
        return state,digest,result,raw
    monkeypatch.setattr(model.epochs,'_selected',altered)
    with pytest.raises(model.FractionalStemBindingHold,match='STATE_HOLD: inventory identity/time mismatch'):model.bind_fractional_crop(ctx,cp,declaration(ctx))


def test_stem_source_copy_uses_actual_owned_store_file_policy(tmp_path):
    from stat import S_IMODE
    from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
    spec=importlib.util.spec_from_file_location('copy_stem',ROOT/'research/relink-funded-stem-fixtures.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    program=json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_bytes())
    program['output_times']=['2026-10-01T07:00:00Z'];program['segments'][0]['end_utc']=program['output_times'][-1]
    original=tmp_path/'source';target=tmp_path/'copy';root=produce_rational_morphology_artifact(original,ACCESS,program_raw=encoded(program))
    before={p.name:p.read_bytes()for p in original.iterdir()}
    driver.copy_stem_source(original,target,ACCESS,root)
    assert S_IMODE(target.stat().st_mode)==0o750 and {p.name:p.read_bytes()for p in target.iterdir()}==before
    assert all(S_IMODE(p.stat().st_mode)==0o640 for p in target.iterdir())
