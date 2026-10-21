from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path

import pytest

from app.crop_rational_leaf_area import (RationalLeafAreaHold,normalize_leaf_thermal_clock_state,
    advance_leaf_thermal_clock,initialize_rational_leaf_area,normalize_rational_leaf_area_state,advance_rational_leaf_area)
from app import crop_rational_morphology_clock as internode_clock
from test_crop_leaf_area_change import exact


REFERENCE=json.loads((Path(__file__).resolve().parents[2]/'fixtures/crop-rational-leaf-area-reference-v1.json').read_bytes())


def example(index=2):
    return deepcopy(REFERENCE['cases'][index])


def seconds(v):
    return {**exact(v),'unit':'s'}


@pytest.mark.parametrize('case',REFERENCE['cases'],ids=lambda c:c['case_id'])
def test_independent_clock_area_and_original_fractional_birth(case):
    p=deepcopy(case);original=deepcopy(p)
    initialized=initialize_rational_leaf_area(inputs=p['initialization']);state=initialized['state']
    assert state['area_state']['area']['value']==pytest.approx(float(p['expected_initial_area_m2']),rel=1e-12,abs=0)
    result=advance_rational_leaf_area(inputs={'input_id':p['case_id'],'state':state,'segments':p['segments']})
    out=result['state'];clock=out['clock_state'];area=out['area_state']
    assert clock['age_exact']==area['age_exact']==p['expected_age_exact']
    assert clock['at_elapsed_seconds_exact']==p['expected_at_seconds_exact']
    assert clock['emerged_elapsed_seconds_exact']==p['initialization']['clock_state']['emerged_elapsed_seconds_exact']
    assert clock['time_origin_utc']=='2026-10-01T00:00:00Z'
    assert area['leaf_id']==clock['leaf_id'] and area['area']['value']==pytest.approx(float(p['expected_area_m2']),rel=1e-12,abs=0)
    assert result['area_change']['value']==pytest.approx(float(p['expected_change_m2']),rel=1e-12,abs=0)
    assert normalize_rational_leaf_area_state(state=out)==out and p==original
    assert result['scope']=='software_research_only' and result['claim_scope']=='synthetic_crop_math_only' and result['gates']=='not_assessed'


def test_split_same_state_no_internode_clock_calls(monkeypatch):
    def forbidden(**_):raise AssertionError('internode state is not a leaf clock')
    monkeypatch.setattr(internode_clock,'advance_rational_internode_thermal_clock',forbidden)
    monkeypatch.setattr(internode_clock,'normalize_rational_internode_clock_state',forbidden)
    p=example();initial=initialize_rational_leaf_area(inputs=p['initialization'])['state'];original=deepcopy(initial)
    whole=advance_rational_leaf_area(inputs={'input_id':'whole','state':initial,'segments':p['segments']})
    state=initial;changes=[]
    for i,segment in enumerate(p['segments']):
        part=advance_rational_leaf_area(inputs={'input_id':'part-'+str(i),'state':state,'segments':[segment]})
        state=part['state'];changes.append(part['area_change']['value'])
    assert state==whole['state'] and initial==original and state['clock_anchor']==initial['clock_anchor']
    assert sum(changes)==pytest.approx(whole['area_change']['value'],rel=1e-12,abs=0)


@pytest.mark.parametrize('change',['leaf-id','age','origin','base','birth','anchor-age','anchor-at','area-leaf','extra'])
def test_clock_and_area_cannot_be_mixed(change):
    p=example();state=initialize_rational_leaf_area(inputs=p['initialization'])['state']
    if change=='leaf-id':state['clock_state']['leaf_id']='other-leaf'
    elif change=='age':state['clock_state']['age_exact']=exact(1)
    elif change=='origin':state['clock_state']['time_origin_utc']='2026-10-02T00:00:00Z'
    elif change=='base':state['clock_state']['base_temperature']['value']+=1
    elif change=='birth':state['clock_state']['emerged_elapsed_seconds_exact']=seconds(1)
    elif change=='anchor-age':state['clock_anchor']['age_exact']=exact(1)
    elif change=='anchor-at':state['clock_anchor']['at_elapsed_seconds_exact']=seconds(1)
    elif change=='area-leaf':state['area_state']['leaf_id']='other-leaf'
    elif change=='extra':state['previous_temperature']='unverified'
    with pytest.raises(RationalLeafAreaHold):normalize_rational_leaf_area_state(state=state)


@pytest.mark.parametrize('change',['gap','overlap','reverse','wrong-unit','below-base','missing','extra','empty','over-limit'])
def test_invalid_forcing_holds(change):
    p=example();state=initialize_rational_leaf_area(inputs=p['initialization'])['state'];segments=p['segments']
    if change=='gap':segments[0]['start_elapsed_seconds_exact']=seconds(1)
    elif change=='overlap':segments[1]['start_elapsed_seconds_exact']=seconds(0)
    elif change=='reverse':segments[0]['end_elapsed_seconds_exact']=seconds(0)
    elif change=='wrong-unit':segments[0]['air_temperature']['unit']='K'
    elif change=='below-base':segments[0]['air_temperature']['value']=4
    elif change=='missing':del segments[0]['air_temperature']
    elif change=='extra':segments[0]['leaf_temperature']=22
    elif change=='empty':segments=[]
    elif change=='over-limit':segments=[segments[0]]*513
    with pytest.raises(RationalLeafAreaHold):advance_rational_leaf_area(inputs={'input_id':'bad','state':state,'segments':segments})


def test_512_segments_current_clock_does_not_reset_age():
    p=example(3);clock=p['initialization']['clock_state'];clock['at_elapsed_seconds_exact']=seconds(3600)
    segments=[{'start_elapsed_seconds_exact':seconds(3600+i),'end_elapsed_seconds_exact':seconds(3601+i),
               'air_temperature':{'value':18,'unit':'degC'}} for i in range(512)]
    result=advance_leaf_thermal_clock(inputs={'input_id':'512','state':clock,'segments':segments})
    assert result['checkpoint']['at_elapsed_seconds_exact']==seconds(4112)
    assert result['checkpoint']['age_exact']==exact(Fraction(3)+Fraction(512,10800))


@pytest.mark.parametrize('change',['internode-basis','bad-UTC','unreduced-seconds','birth-after-current','age-at-birth','bad-temperature'])
def test_closed_leaf_clock_boundary(change):
    clock=example(0)['initialization']['clock_state']
    if change=='internode-basis':clock['age_basis']='since_internode_emergence'
    elif change=='bad-UTC':clock['time_origin_utc']='2026-02-30T00:00:00Z'
    elif change=='unreduced-seconds':clock['at_elapsed_seconds_exact']={'numerator':'2','denominator':'2','unit':'s'}
    elif change=='birth-after-current':clock['emerged_elapsed_seconds_exact']=seconds(1)
    elif change=='age-at-birth':clock['age_exact']=exact(1)
    elif change=='bad-temperature':clock['base_temperature']['value']=True
    with pytest.raises(RationalLeafAreaHold):normalize_leaf_thermal_clock_state(state=clock)
