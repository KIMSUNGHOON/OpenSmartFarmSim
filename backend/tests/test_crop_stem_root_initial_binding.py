from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from dataclasses import replace
import json
from math import nextafter
from pathlib import Path

import pytest

from app import crop_stem_root_initial_binding as model
from app.crop_leaf_carbon_stock_artifact_producer import produce_leaf_carbon_stock_artifact
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from test_crop_leaf_carbon_stock_artifact import inputs as crop_inputs, profiles, ACCESS, encoded

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def stored(tmp_path_factory,profiles):
    base=tmp_path_factory.mktemp('initial-carbon-binding');p=json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_bytes())
    p['output_times']=['2026-10-01T07:00:00Z','2026-10-01T08:00:00Z'];p['segments'][0]['end_utc']=p['output_times'][-1]
    sr=produce_rational_morphology_artifact(base/'stem',ACCESS,program_raw=encoded(p));rows=[]
    for case in range(6):
        index=[-1,0,1][case%3];origin=['2026-10-01T00:00:00Z',*p['output_times']][case%3]
        source=crop_inputs(case,dt=.125,count=1);source['time_origin_utc']=origin;directory=base/f'crop-{case}'
        cr=produce_leaf_carbon_stock_artifact(directory,ACCESS,inputs_raw=encoded(source),**profiles)
        ids=[n['length_state']['clock_state']['internode_id']for n in p['initial_state']['internodes']]if index==-1 else[
            n['internode_id']for n in model.stem.read_rational_morphology_frame(base/'stem',ACCESS,sr,index=index)['internodes']]
        amounts={3:[2000.,4000.,6000.,8000.],4:[2000.,4000.,6000.,7000.,1000.]}[len(ids)]
        p2=deepcopy(source['program']);p2['scenario']['plant_state'].pop('stem_root');p2['scenario']['removals'].pop('stem_root')
        p2['stem_root_stock_policy']=model.crop.short.stock.POLICY_ID
        p2['stem_root_compartments']=[{'compartment_id':identifier,
            'kind':'root_system'if i==0 else'internode','initial_carbon':{'value':C,'unit':'mg_CH2O/m2_floor'},
            'sink_weight':{'value':i+1.,'unit':'1'},'carbon_removal':{'value':0.,'unit':'mg_CH2O/m2_floor/s'}}
            for i,(identifier,C)in enumerate(zip(['explicit-root',*ids],amounts,strict=True))]
        ctx=model.crop.prepare_context(program=p2,step_seconds=.125,step_count=1,**profiles)
        rows.append((ctx,directory,base/'stem',cr,sr,index))
    return rows


def declaration(row):
    ctx,cd,sd,cr,sr,index=row;cm=model.carbon.read_leaf_carbon_stock_manifest(cd,ACCESS,cr)
    sm=model.stem.read_rational_morphology_manifest(sd,ACCESS,sr)
    state_sha=sm['initial_state_sha256']if index==-1 else sm['samples'][index]['state_sha256']
    return {'schema_version':'stem-root-initial-source-binding-input-v1','input_id':'explicit-initial-link','origin':'synthetic',
        'context_sha256':ctx.root_sha256,'crop_root_sha256':cr,'crop_initial_state_sha256':cm['initial_state_sha256'],
        'stem_root_sha256':sr,'stem_start_index':index,'stem_source_state_sha256':state_sha,
        'time_origin_utc':cm['time_origin_utc'],'model_floor_area':deepcopy(ctx.program['model_floor_area']),
        'tracking_basis':{'kind':'one_tracked_shoot_on_declared_model_floor_research_v1','shoot_id':'synthetic-shoot',
            'model_floor_area':deepcopy(ctx.program['model_floor_area']),'tracked_shoot_count':{'value':1,'unit':'tracked_shoot'}},
        'rights':deepcopy(cm['source_rights']),'reviewer':'native-software-QA-not-agricultural-validation'}


def bind(row,decl=None):
    ctx,cd,sd,cr,sr,index=row
    return model.bind_initial_stem_carbon(ctx,cd,sd,ACCESS,crop_root_sha256=cr,stem_root_sha256=sr,
        stem_start_index=index,declaration=declaration(row)if decl is None else decl)


@pytest.mark.parametrize('case',range(6))
def test_actual_selected_sources_complete_inventory_and_original_initial_state(stored,case):
    row=stored[case];ctx,cd,sd,cr,sr,index=row;before=(ctx._request,ctx._program,ctx._seed,ctx._manifest)
    r=bind(row);p=json.loads(ctx._program)
    assert r['context_sha256']==ctx.root_sha256 and r['stem_selection']['index']==index
    assert r['stem_selection']['state_sha256']==declaration(row)['stem_source_state_sha256']
    expected=[n['length_state']['clock_state']['internode_id']for n in r['stem_selection']['source_state']['internodes']]
    assert [n['compartment_id']for n in r['initial_inventory']if n['kind']=='internode']==expected
    assert len(expected)==(4 if index==1 else 3)
    assert r['initial_inventory']==p['stem_root_compartments']and r['source_rights']['crop']['redistribute']is False
    assert r['redistribution_authorized']is False and r['basis_receipt']['native_stem_floor_basis']is False
    assert r['basis_receipt']['tracking_declaration']==declaration(row)['tracking_basis']
    assert r['G0_G4']=='not_assessed'and r['claim_scope']=='synthetic_initial_stored_source_identity_and_declared_footprint_binding_only'
    assert r['balance']['carbon']['source']=={'value':20000.,'unit':'mg_CH2O/m2_floor'}
    assert r['balance']['carbon']['declared_once_rounded_sum']==r['balance']['carbon']['source']
    assert Fraction(int(r['balance']['carbon']['exact_signed_residual']['numerator']),int(r['balance']['carbon']['exact_signed_residual']['denominator']))==0
    assert before==(ctx._request,ctx._program,ctx._seed,ctx._manifest)and bind(row)==r
    assert r['calculation_sha256']==sha256(encoded({k:v for k,v in r.items()if k!='calculation_sha256'})).hexdigest()


@pytest.mark.parametrize('change',[
    lambda d:d.update(extra=1),lambda d:d.update(origin='observed'),lambda d:d.update(context_sha256='0'*64),
    lambda d:d.update(crop_root_sha256='0'*64),lambda d:d.update(crop_initial_state_sha256='0'*64),
    lambda d:d.update(stem_source_state_sha256='0'*64),lambda d:d.update(stem_start_index=True),
    lambda d:d.update(time_origin_utc='2026-10-02T00:00:00Z'),lambda d:d['model_floor_area'].update(value=2),
    lambda d:d['tracking_basis'].update(shoot_id='invented'),lambda d:d['tracking_basis'].update(kind='inferred_density'),
    lambda d:d['tracking_basis']['tracked_shoot_count'].update(value=True),lambda d:d['tracking_basis']['tracked_shoot_count'].update(value=2),
    lambda d:d['tracking_basis']['model_floor_area'].update(value=2),lambda d:d['rights'].update(use=False),
    lambda d:d['rights'].update(redistribute=1),lambda d:d.update(reviewer='')])
def test_closed_source_time_basis_and_rights_declaration(stored,change):
    row=stored[0];d=declaration(row);change(d)
    with pytest.raises(model.InitialStemCarbonBindingHold):bind(row,d)


@pytest.mark.parametrize('change',[
    lambda p:p['stem_root_compartments'][1].update(compartment_id='placeholder'),
    lambda p:p['stem_root_compartments'].reverse(),
    lambda p:p['leaves'][0]['initial_carbon'].update(value=1.),
    lambda p:p['leaves'][0]['thermal_age'].update(value=101.),
    lambda p:p['scenario']['forcing']['co2'].update(value=500.),
    lambda p:p['model_floor_area'].update(value=1.125)])
def test_matching_aggregate_alone_cannot_replace_original_state_or_order(stored,profiles,change):
    original=stored[0];p=original[0].program;change(p)
    if p['leaves'][0]['thermal_age']['value']==101.:
        p['leaves'][0]['initial_area']['value']=.5/(1+__import__('math').exp(-.02))
    ctx=model.crop.prepare_context(program=p,step_seconds=.125,step_count=1,**profiles);row=(ctx,*original[1:])
    with pytest.raises(model.InitialStemCarbonBindingHold):bind(row)


@pytest.mark.parametrize('difference',[1000.,-1000.])
def test_unassigned_or_overallocated_carbon_is_explicit_hold_without_root_repair(stored,profiles,difference):
    original=stored[0];p=original[0].program;p['stem_root_compartments'][-1]['initial_carbon']['value']-=difference
    ctx=model.crop.prepare_context(program=p,step_seconds=.125,step_count=1,**profiles);row=(ctx,*original[1:]);before=ctx._program
    with pytest.raises(model.InitialStemCarbonBindingHold,match='CARBON_BALANCE_HOLD')as caught:bind(row)
    q=caught.value.hold_evidence['carbon']['exact_signed_residual']
    assert Fraction(int(q['numerator']),int(q['denominator']))==Fraction.from_float(difference)
    assert ctx._program==before and json.loads(ctx._program)['stem_root_compartments'][0]['initial_carbon']['value']==2000.


def test_later_actual_new_node_cannot_be_omitted_despite_matching_total(stored,profiles):
    original=stored[2];p=original[0].program;assert len(p['stem_root_compartments'])==5
    p['stem_root_compartments'].pop();p['stem_root_compartments'][-1]['initial_carbon']['value']=8000.
    ctx=model.crop.prepare_context(program=p,step_seconds=.125,step_count=1,**profiles);row=(ctx,*original[1:]);before=ctx._program
    with pytest.raises(model.InitialStemCarbonBindingHold,match='INVENTORY_HOLD'):bind(row)
    assert ctx._program==before


def test_binding_result_explicitly_identifies_the_synthetic_clock(stored):
    r=bind(stored[0])
    assert r['time_kind']=='synthetic_model_clock_not_observation'


def test_same_once_rounded_carbon_preserves_exact_signed_roundoff(stored,profiles):
    original=stored[0];p=original[0].program;p['stem_root_compartments'][0]['initial_carbon']['value']=nextafter(2000.,float('inf'))
    ctx=model.crop.prepare_context(program=p,step_seconds=.125,step_count=1,**profiles);r=bind((ctx,*original[1:]))
    q=r['balance']['carbon']['exact_signed_residual']
    assert Fraction(int(q['numerator']),int(q['denominator']))==Fraction(2000)-Fraction.from_float(nextafter(2000.,float('inf')))
    assert r['balance']['carbon']['once_rounded_matches_source']is True


def test_zero_root_stock_is_explicit_and_removal_mismatch_is_not_discarded(stored,profiles):
    original=stored[0];p=original[0].program
    for row,C in zip(p['stem_root_compartments'],[0.,6000.,6000.,8000.],strict=True):row['initial_carbon']['value']=C
    ctx=model.crop.prepare_context(program=p,step_seconds=.125,step_count=1,**profiles)
    assert bind((ctx,*original[1:]))['initial_inventory'][0]['initial_carbon']['value']==0.
    p=original[0].program;p['stem_root_compartments'][0]['carbon_removal']['value']=.001
    ctx=model.crop.prepare_context(program=p,step_seconds=.125,step_count=1,**profiles)
    with pytest.raises(model.InitialStemCarbonBindingHold,match='CARBON_BALANCE_HOLD')as caught:bind((ctx,*original[1:]))
    assert caught.value.hold_evidence['removal']['once_rounded_matches_source']is False


def test_binding_has_no_growth_renormalization_external_connections_or_write(stored,monkeypatch):
    import os,socket,subprocess,psycopg
    row=stored[1];d=declaration(row);calls=[]
    def forbidden(*a,**k):calls.append(1);raise AssertionError('no growth/replay/external side effect')
    from app import crop_leaf_carbon_stock_continuation as old
    from app import crop_rational_internode_length as length
    for owner,name in [(model.crop,'prepare_context'),(model.crop,'advance_chunk'),(model.crop.short,'_prepare'),
        (model.crop.short,'_evaluate'),(model.crop.short,'integrate'),(old,'prepare_context'),(old,'advance_chunk'),
        (length,'advance_rational_internode_length'),(length,'initialize_rational_internode_length'),
        (socket,'socket'),(subprocess,'Popen'),(psycopg,'connect'),(model.MorphologyBlobStore,'put')]:monkeypatch.setattr(owner,name,forbidden)
    original=os.open
    def readonly(path,flags,*a,**k):
        if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):return forbidden()
        return original(path,flags,*a,**k)
    monkeypatch.setattr(os,'open',readonly)
    r=bind(row,d);assert r['growth_RHS_evaluations']==0 and calls==[]


@pytest.mark.parametrize('kind',['own_code','late_code','late_crop_input','late_stem_program','late_selected_result','late_stem_rights'])
def test_current_and_late_source_code_rights_and_original_bytes_hold(stored,monkeypatch,kind):
    row=stored[1];d=declaration(row);started=[];balance=model._balance
    def counted(*a,**k):value=balance(*a,**k);started.append(1);return value
    monkeypatch.setattr(model,'_balance',counted)
    if kind=='own_code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    elif kind=='late_code':
        pins=model._pins
        def changed():
            value=pins()
            if started:value['backend/app/crop_stem_root_initial_binding.py']='0'*64
            return value
        monkeypatch.setattr(model,'_pins',changed)
    elif kind=='late_stem_rights':
        load=model.stem._load_manifest
        def withdraw(*a,**k):
            value=load(*a,**k)
            if started:value['program_rights']['display']=False
            return value
        monkeypatch.setattr(model.stem,'_load_manifest',withdraw)
    else:
        cm=model.carbon.read_leaf_carbon_stock_manifest(row[1],ACCESS,row[3]);sm=model.stem.read_rational_morphology_manifest(row[2],ACCESS,row[4])
        target=cm['sources']['inputs']['sha256']if kind=='late_crop_input'else sm['program_sha256']if kind=='late_stem_program'else sm['samples'][row[5]]['result_sha256']
        get=model.MorphologyBlobStore.get
        def altered(self,digest,**k):
            value=get(self,digest,**k)
            return value+b' 'if started and digest==target else value
        monkeypatch.setattr(model.MorphologyBlobStore,'get',altered)
    with pytest.raises(model.InitialStemCarbonBindingHold):bind(row,d)


def test_actual_directory_replacement_is_rejected_with_handles_held(stored,monkeypatch):
    import shutil
    row=stored[0];directory=row[1];moved=directory.with_name(directory.name+'-held-original');balance=model._balance;changed=[]
    d=declaration(row)
    def replace_directory(*a,**k):
        value=balance(*a,**k)
        if not changed:directory.rename(moved);shutil.copytree(moved,directory);changed.append(1)
        return value
    monkeypatch.setattr(model,'_balance',replace_directory)
    try:
        with pytest.raises(model.InitialStemCarbonBindingHold,match='STORAGE_HOLD'):bind(row,d)
    finally:
        if changed:shutil.rmtree(directory);moved.rename(directory)


@pytest.mark.parametrize('kind',['state','receipt'])
def test_self_rehashed_seed_cannot_replace_independent_original_state(stored,kind):
    original=stored[0];ctx=original[0];seed=json.loads(ctx._seed)
    if kind=='state':seed['state'][0]+=1.
    else:seed['initial_area_receipts'][0]['requested_area']['value']*=1.0001
    raw_seed=encoded(seed);m=ctx.manifest;m['seed_sha256']=sha256(raw_seed).hexdigest();raw_m=encoded(m)
    changed=replace(ctx,_seed=raw_seed,_manifest=raw_m,root_sha256=sha256(raw_m).hexdigest())
    with pytest.raises(model.InitialStemCarbonBindingHold,match='STATE_HOLD'):bind((changed,*original[1:]))


def test_returned_copies_and_output_size_hold(stored,monkeypatch):
    row=stored[0];r=bind(row);r['initial_inventory'][0]['initial_carbon']['value']=0
    r['stem_selection']['source_state']['internodes'][0]['length_state']['length']['value']=0
    again=bind(row);assert again['initial_inventory'][0]['initial_carbon']['value']==2000.
    assert again['stem_selection']['source_state']['internodes'][0]['length_state']['length']['value']>0
    monkeypatch.setattr(model,'MAX_BYTES',len(encoded(declaration(row)))+50)
    with pytest.raises(model.InitialStemCarbonBindingHold,match='CAPACITY_HOLD'):bind(row)
