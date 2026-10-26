from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from math import fsum, ulp
import os
from pathlib import Path
import shutil

import pytest

from app import crop_funded_internode_lengths as model
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_funded_shoot_clock import sources, profiles, ROOT, snapshot
from test_crop_leaf_carbon_stock_artifact import ACCESS


def calculated(sources,case=0):
    directory,root=sources[2][case]
    return model.calculate_funded_initial_internode_lengths(directory,sources[0],ACCESS,leaf_root_sha256=root,stem_root_sha256=sources[1])


def reference(age,curve):
    with localcontext()as context:
        context.prec=120
        a=Decimal(age['numerator'])/Decimal(age['denominator'])
        m,k,t=(Decimal.from_float(float(curve['values'][key]['value']))for key in ('maximum_length','steepness','inflection_age'))
        return m/(1+(-(a-t)*k).exp())


@pytest.mark.parametrize('case',range(6))
def test_same_air_lengths_preserve_sources_anchors_phases_and_independent_Decimal(sources,case):
    leaf,root=sources[2][case];before=snapshot(leaf),snapshot(sources[0]);result=calculated(sources,case)
    source=json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_bytes())['initial_state']['internodes']
    assert result['G0_G4']=='not_assessed' and result['leaf_artifact_sha256']==root and len(result['frames'])==7
    assert result['original_internodes']==source
    for frame in result['frames']:
        lengths=[]
        for node,original in zip(frame['internodes'],source,strict=True):
            assert node['internode_id']==original['length_state']['clock_state']['internode_id'] and node['sequence']==original['sequence']
            assert node['curve_sha256']==original['length_state']['curve_sha256']
            assert node['initial_state_sha256']==sha256(model._canonical(original['length_state'])).hexdigest()
            assert node['length']['unit']=='m'
            assert node['length']['value']==pytest.approx(float(reference(node['age_exact'],original['length_state']['curve'])),rel=1e-12,abs=0)
            lengths.append(node['length']['value'])
        assert frame['tracked_initial_axis_length']=={'value':fsum(lengths),'unit':'m'}
    assert result['frames'][0]['internodes']==result['frames'][1]['internodes']
    assert result['frames'][3]['internodes']==result['frames'][4]['internodes']
    assert [n['length']for n in result['frames'][0]['internodes']]==[n['length_state']['length']for n in source]
    assert (snapshot(leaf),snapshot(sources[0]))==before


@pytest.mark.parametrize('kind',['length','anchor','curve','id','age-unit','negative-age','backwards-age','code','capacity'])
def test_invalid_initial_source_and_clock_or_capacity_does_not_yield_a_pose(sources,tmp_path,monkeypatch,kind):
    if kind in ('length','anchor','curve'):
        directory=tmp_path/'forged';shutil.copytree(sources[0],directory)
        m=model.clock.stem.read_rational_morphology_manifest(directory,ACCESS,sources[1])
        with MorphologyBlobStore(directory,ACCESS,write=True)as store:
            p=json.loads(store.get(m['program_sha256'],maximum=model.clock.stem.PROGRAM_MAX));state=p['initial_state']['internodes'][0]['length_state']
            if kind=='length':state['length']['value']*=2
            elif kind=='anchor':state['anchor']['canonical_length']['value']*=2
            else:state['curve_sha256']=state['anchor']['curve_sha256']='0'*64
            raw=model._canonical(p);m['program_sha256']=store.put(raw,maximum=model.clock.stem.PROGRAM_MAX);m['program_bytes']=len(raw)
            m['initial_state_sha256']=sha256(model._canonical(p['initial_state'])).hexdigest();m['samples'][0]['input_state_sha256']=m['initial_state_sha256']
            forged=store.put(model._canonical(m),maximum=model.clock.stem.ROOT_MAX)
        model.clock.stem.read_rational_morphology_manifest(directory,ACCESS,forged)
        with pytest.raises(model.FundedInternodeLengthsHold):
            model.calculate_funded_initial_internode_lengths(sources[2][0][0],directory,ACCESS,leaf_root_sha256=sources[2][0][1],stem_root_sha256=forged)
        return
    elif kind in ('id','age-unit','negative-age','backwards-age'):
        derive=model.clock.derive_funded_shoot_clock
        def changed(*a,**k):
            value=derive(*a,**k);node=value['frames'][-1]['initial_internodes'][0]
            if kind=='id':node['internode_id']='wrong'
            elif kind=='age-unit':node['age_exact']['unit']='s'
            elif kind=='negative-age':node['age_exact']['numerator']='-1'
            else:node['age_exact']['numerator']='0';node['age_exact']['denominator']='1'
            return value
        monkeypatch.setattr(model.clock,'derive_funded_shoot_clock',changed)
    elif kind=='code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    else:monkeypatch.setattr(model,'MAX_BYTES',1024)
    with pytest.raises(model.FundedInternodeLengthsHold):calculated(sources)


def test_no_clock_advance_DB_CLI_network_writes_and_detached_results(sources,monkeypatch):
    import subprocess,socket,psycopg
    calls=[]
    def forbidden(*a,**k):calls.append(1);raise AssertionError('no integration or external writes')
    monkeypatch.setattr(model.initial,'advance_rational_internode_length',forbidden)
    monkeypatch.setattr(model.point,'advance_internode_length',forbidden)
    for owner,name in [(subprocess,'Popen'),(socket,'socket'),(psycopg,'connect'),(MorphologyBlobStore,'put')]:monkeypatch.setattr(owner,name,forbidden)
    original_open=os.open
    def readonly(path,flags,*a,**k):
        if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):return forbidden()
        return original_open(path,flags,*a,**k)
    monkeypatch.setattr(os,'open',readonly)
    value=calculated(sources);value['original_internodes'][0]['length_state']['anchor']['requested_length']['value']=0
    assert calculated(sources)['original_internodes'][0]['length_state']['anchor']['requested_length']['value']>0 and calls==[]


@pytest.mark.parametrize('count',[1,512])
def test_actual_producer_minimum_and_maximum_initial_nodes(tmp_path,profiles,count):
    from test_crop_leaf_funded_birth_artifact import calculated_inputs,encoded
    from app.crop_leaf_funded_birth_artifact_producer import produce_funded_leaf_artifact
    from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
    p=json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_bytes());template=p['initial_state']['internodes'][0]
    nodes=[]
    for i in range(count):
        node=deepcopy(template);node['sequence']=i
        for clock in [node['length_state']['clock_state'],node['length_state']['anchor']['clock_state']]:clock['internode_id']=f's{i}'
        nodes.append(node)
    p['initial_state']['internodes']=nodes;p['initial_state']['timeline_state']['next_sequence']=count
    end='2026-10-01T00:00:01Z';p['segments'][0]['end_utc']=end;p['output_times']=[end]
    stem=tmp_path/'stem';sr=produce_rational_morphology_artifact(stem,ACCESS,program_raw=encoded(p))
    inputs,_=calculated_inputs(profiles,steps=(0,),dt=1/3,count=1)
    leaf=tmp_path/'leaf';lr=produce_funded_leaf_artifact(leaf,ACCESS,inputs_raw=encoded(inputs),**profiles)
    before=snapshot(stem),snapshot(leaf)
    result=model.calculate_funded_initial_internode_lengths(leaf,stem,ACCESS,leaf_root_sha256=lr,stem_root_sha256=sr)
    assert len(result['original_internodes'])==count and len(result['frames'])==3 and len(model._canonical(result))<=2*1024**2
    assert all(len(frame['internodes'])==count for frame in result['frames'])
    assert (snapshot(stem),snapshot(leaf))==before


@pytest.mark.parametrize('kind',['code','rights','program'])
def test_late_dependency_or_source_changes_reject_after_point_calculation(sources,monkeypatch,kind):
    if kind=='code':
        pins=model._pins;calls=[]
        def changed():
            value=pins();calls.append(1)
            if len(calls)>1:value[next(iter(value))]='0'*64
            return value
        monkeypatch.setattr(model,'_pins',changed)
    else:
        calculate=model.point.calculate_internode_length_point;started=[]
        def calculated_point(*a,**k):
            result=calculate(*a,**k);started.append(1);return result
        monkeypatch.setattr(model.point,'calculate_internode_length_point',calculated_point)
        if kind=='rights':
            read=model.clock.stem.read_rational_morphology_manifest
            def changed(*a,**k):
                value=read(*a,**k)
                if started:value['program_rights']['display']=False
                return value
            monkeypatch.setattr(model.clock.stem,'read_rational_morphology_manifest',changed)
        else:
            read=MorphologyBlobStore.get;target=model.clock.stem.read_rational_morphology_manifest(sources[0],ACCESS,sources[1])['program_sha256']
            def changed(self,digest,**k):
                raw=read(self,digest,**k);return raw+b' 'if started and digest==target else raw
            monkeypatch.setattr(MorphologyBlobStore,'get',changed)
    with pytest.raises(model.FundedInternodeLengthsHold):calculated(sources)


def test_accepted_requested_length_gap_is_preserved_as_a_receipt_without_growth_offset(sources,tmp_path):
    directory=tmp_path/'requested-gap';shutil.copytree(sources[0],directory)
    m=model.clock.stem.read_rational_morphology_manifest(directory,ACCESS,sources[1])
    with MorphologyBlobStore(directory,ACCESS,write=True)as store:
        p=json.loads(store.get(m['program_sha256'],maximum=model.clock.stem.PROGRAM_MAX));state=p['initial_state']['internodes'][0]['length_state']
        canonical=deepcopy(state['length']);state['anchor']['requested_length']['value']*=1+5e-13
        raw=model._canonical(p);m['program_sha256']=store.put(raw,maximum=model.clock.stem.PROGRAM_MAX);m['program_bytes']=len(raw)
        m['initial_state_sha256']=sha256(model._canonical(p['initial_state'])).hexdigest();m['samples'][0]['input_state_sha256']=m['initial_state_sha256']
        root=store.put(model._canonical(m),maximum=model.clock.stem.ROOT_MAX)
    result=model.calculate_funded_initial_internode_lengths(sources[2][0][0],directory,ACCESS,leaf_root_sha256=sources[2][0][1],stem_root_sha256=root)
    assert result['original_internodes'][0]['length_state']['anchor']==state['anchor']
    assert state['anchor']['requested_length']!=canonical and result['frames'][0]['internodes'][0]['length']==canonical
    last=result['frames'][-1]['internodes'][0];expected=reference(last['age_exact'],state['curve'])
    with localcontext()as context:
        context.prec=120
        assert abs(Decimal.from_float(last['length']['value'])-expected)<=8*Decimal.from_float(ulp(last['length']['value']))
