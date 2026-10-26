from copy import deepcopy
from fractions import Fraction
from math import fsum
import json
from pathlib import Path

import pytest

from app import crop_funded_shoot_epochs as model
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from app.crop_leaf_funded_birth_artifact_producer import produce_funded_leaf_artifact
from test_crop_leaf_funded_birth_artifact import calculated_inputs, profiles
from test_crop_leaf_carbon_stock_artifact import ACCESS,encoded
from test_crop_funded_internode_lengths import reference
from test_crop_funded_shoot_clock import snapshot

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def sources(tmp_path_factory,profiles):
    base=tmp_path_factory.mktemp('shoot-epochs');program=json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_bytes())
    program['output_times']=['2026-10-01T07:00:00Z','2026-10-01T08:00:00Z'];program['segments'][0]['end_utc']=program['output_times'][-1]
    sr=produce_rational_morphology_artifact(base/'stem',ACCESS,program_raw=encoded(program));cases={}
    for label,origin,case,dt,count in [('initial','2026-10-01T00:00:00Z',0,1/3,4),
        ('later','2026-10-01T08:00:00Z',0,1/3,4),('crossing','2026-10-01T07:00:00Z',0,8,32),
        *[(f'case-{i}','2026-10-01T07:00:00Z',i,2,16)for i in range(6)]]:
        inputs,_=calculated_inputs(profiles,case,steps=(0,count//2),dt=dt,count=count)
        inputs['time_origin_utc']=origin;directory=base/label
        root=produce_funded_leaf_artifact(directory,ACCESS,inputs_raw=encoded(inputs),**profiles);cases[label]=(directory,root)
    return base/'stem',sr,cases


def projected(sources,label='later',index=1):
    directory,root=sources[2][label]
    return model.project_funded_shoot_from_stored_state(directory,sources[0],ACCESS,leaf_root_sha256=root,stem_root_sha256=sources[1],stem_start_index=index)


def frac(q):return Fraction(int(q['numerator']),int(q['denominator']))


@pytest.mark.parametrize('label,index,offset',[('initial',-1,0),('later',1,28800),*[(f'case-{i}',0,25200)for i in range(6)]])
def test_original_stored_initial_history_exact_epoch_map_and_independent_ages_lengths(sources,label,index,offset):
    before=snapshot(sources[0]);result=projected(sources,label,index);source=result['stem_source_state'];t=source['timeline_state']
    assert result['G0_G4']=='not_assessed' and result['stem_start_index']==index
    assert result['development_origin_utc']=='2026-10-01T00:00:00Z' and result['simulation_origin_utc']==t['at']
    assert frac(result['simulation_start_development_elapsed_seconds_exact'])==offset
    initial_age=frac(t['age_exact']);initial_nodes=source['internodes']
    for frame in result['frames']:
        elapsed=frac(frame['at']['elapsed_seconds_exact']);integral=Fraction.from_float(frame['air_temperature_integral']['value'])
        change=(integral-Fraction(5)*elapsed)/86400
        assert frac(frame['development_elapsed_seconds_exact'])==offset+elapsed
        assert frac(frame['shoot_age_exact'])==initial_age+change
        assert len(frame['internodes'])==len(initial_nodes)
        for node,original in zip(frame['internodes'],initial_nodes,strict=True):
            state=original['length_state'];assert node['internode_id']==state['clock_state']['internode_id']
            assert node['emerged_development_seconds_exact']==state['clock_state']['emerged_elapsed_seconds_exact']
            assert frac(node['age_exact'])==frac(state['clock_state']['age_exact'])+change
            assert node['length']['value']==pytest.approx(float(reference(node['age_exact'],state['curve'])),rel=1e-12,abs=0)
        assert frame['tracked_source_axis_length']=={'value':fsum(n['length']['value']for n in frame['internodes']),'unit':'m'}
    assert [n['length']for n in result['frames'][0]['internodes']]==[n['length_state']['length']for n in initial_nodes]
    assert result['frames'][0]['internodes']==result['frames'][1]['internodes']
    assert snapshot(sources[0])==before


def test_actual_near_threshold_state_produces_only_a_source_bracket_not_an_invented_birth(sources):
    result=projected(sources,'crossing',0);brackets=result['event_brackets'];assert len(brackets)==1
    event=brackets[0];assert event['sequence']==3 and frac(event['thermal_age_exact'])==5
    left,right=(result['frames'][event[k]]for k in ('left_frame_index','right_frame_index'))
    assert frac(left['shoot_age_exact'])<5<=frac(right['shoot_age_exact'])
    assert event['start_at']==left['at'] and event['end_at']==right['at']
    assert event['time_status']=='within_step_time_unresolved' and 'occurred_at'not in event
    assert result['new_internodes']=='not_created' and all(len(f['internodes'])==3 for f in result['frames'])


@pytest.mark.parametrize('index',[-2,2,True,.5,'0'])
def test_invalid_source_index_rejected(sources,index):
    with pytest.raises(model.FundedShootEpochHold):projected(sources,index=index)


def test_simulation_origin_must_equal_actual_selected_source_time(sources):
    with pytest.raises(model.FundedShootEpochHold):projected(sources,'case-0',1)


@pytest.mark.parametrize('kind',['code','capacity'])
def test_model_and_response_fences(sources,monkeypatch,kind):
    monkeypatch.setattr(model,'CODE_SHA256'if kind=='code'else'MAX_BYTES','0'*64 if kind=='code'else 1024)
    with pytest.raises(model.FundedShootEpochHold):projected(sources)


def test_same_origin_numeric_values_match_existing_version_without_changing_it(sources):
    from app.crop_funded_internode_lengths import calculate_funded_initial_internode_lengths
    directory,root=sources[2]['initial'];old=calculate_funded_initial_internode_lengths(directory,sources[0],ACCESS,leaf_root_sha256=root,stem_root_sha256=sources[1])
    new=projected(sources,'initial',-1)
    for a,b in zip(old['frames'],new['frames'],strict=True):
        assert a['at']==b['at'] and a['shoot_age_exact']==b['shoot_age_exact']
        assert a['tracked_initial_axis_length']==b['tracked_source_axis_length']
        for left,right in zip(a['internodes'],b['internodes'],strict=True):
            assert {k:left[k]for k in ('sequence','internode_id','age_exact','length','curve_sha256')}=={k:right[k]for k in ('sequence','internode_id','age_exact','length','curve_sha256')}


@pytest.mark.parametrize('kind',['code','rights','program','selected-result'])
def test_late_source_changes_after_length_calculation_are_rejected(sources,monkeypatch,kind):
    from app.crop_morphology_artifact_io import MorphologyBlobStore
    if kind=='code':
        pins=model._pins;calls=[]
        def changed():
            value=pins();calls.append(1)
            if len(calls)>1:value[next(iter(value))]='0'*64
            return value
        monkeypatch.setattr(model,'_pins',changed)
    else:
        calculate=model.point.calculate_internode_length_point;started=[]
        def counted(*a,**k):
            value=calculate(*a,**k);started.append(1);return value
        monkeypatch.setattr(model.point,'calculate_internode_length_point',counted)
        if kind=='rights':
            read=model.stem.read_rational_morphology_manifest
            def changed(*a,**k):
                value=read(*a,**k)
                if started:value['program_rights']['display']=False
                return value
            monkeypatch.setattr(model.stem,'read_rational_morphology_manifest',changed)
        else:
            manifest=model.stem.read_rational_morphology_manifest(sources[0],ACCESS,sources[1]);target=manifest['program_sha256']if kind=='program'else manifest['samples'][1]['result_sha256']
            read=MorphologyBlobStore.get
            def changed(self,digest,**k):
                value=read(self,digest,**k);return value+b' 'if started and digest==target else value
            monkeypatch.setattr(MorphologyBlobStore,'get',changed)
    with pytest.raises(model.FundedShootEpochHold):projected(sources)


def test_projection_does_not_reintegrate_history_use_old_forcing_or_write_external_state(sources,monkeypatch):
    import os,subprocess,socket,psycopg
    from app.crop_morphology_artifact_io import MorphologyBlobStore
    calls=[]
    def forbidden(*a,**k):calls.append(1);raise AssertionError('no old integration or external writes')
    for owner,name in [(model.initial,'advance_rational_internode_length'),(model.point,'advance_internode_length'),(subprocess,'Popen'),(socket,'socket'),(psycopg,'connect'),(MorphologyBlobStore,'put')]:monkeypatch.setattr(owner,name,forbidden)
    original=os.open
    def readonly(path,flags,*a,**k):
        if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):return forbidden()
        return original(path,flags,*a,**k)
    monkeypatch.setattr(os,'open',readonly)
    value=projected(sources);value['stem_source_state']['internodes'][0]['length_state']['anchor']['requested_length']['value']=0
    assert projected(sources)['stem_source_state']['internodes'][0]['length_state']['anchor']['requested_length']['value']>0 and calls==[]


@pytest.mark.parametrize('count',[1,512])
def test_actual_initial_node_count_boundaries(tmp_path,profiles,count):
    program=json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_bytes());template=program['initial_state']['internodes'][0];nodes=[]
    for i in range(count):
        node=deepcopy(template);node['sequence']=i
        for clock in (node['length_state']['clock_state'],node['length_state']['anchor']['clock_state']):clock['internode_id']=f's{i}'
        nodes.append(node)
    program['initial_state']['internodes']=nodes;program['initial_state']['timeline_state']['next_sequence']=count
    end='2026-10-01T00:00:01Z';program['segments'][0]['end_utc']=end;program['output_times']=[end]
    sr=produce_rational_morphology_artifact(tmp_path/'stem',ACCESS,program_raw=encoded(program))
    inputs,_=calculated_inputs(profiles,steps=(0,),dt=1/3,count=1)
    lr=produce_funded_leaf_artifact(tmp_path/'leaf',ACCESS,inputs_raw=encoded(inputs),**profiles)
    value=model.project_funded_shoot_from_stored_state(tmp_path/'leaf',tmp_path/'stem',ACCESS,leaf_root_sha256=lr,stem_root_sha256=sr,stem_start_index=-1)
    assert all(len(f['internodes'])==count for f in value['frames'])and len(model._canonical(value))<=2*1024**2
