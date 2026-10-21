from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path

import pytest

from app.crop_declared_leaf_births import DeclaredLeafBirthHold,create_declared_leaves
from app import crop_rational_leaf_area as leaf
from test_crop_rational_leaf_area import seconds


REFERENCE=json.loads((Path(__file__).resolve().parents[2]/'fixtures/crop-declared-leaf-births-reference-v1.json').read_bytes())


def example(index=0):return deepcopy(REFERENCE['cases'][index]['inputs'])


@pytest.mark.parametrize('case',REFERENCE['cases'],ids=lambda v:v['case_id'])
def test_independent_birth_clock_area_and_input_immutability(case):
    p=deepcopy(case['inputs']);before=deepcopy(p);result=create_declared_leaves(inputs=p)
    assert result['scope']=='software_research_only' and result['gates']=='not_assessed'
    assert result['claim_scope']=='synthetic_crop_math_only' and result['time_origin_utc']==p['time_origin_utc']
    assert len(result['new_leaves'])==len(p['births'])
    for original,item,expected in zip(p['births'],result['new_leaves'],case['expected']):
        state=item['state'];clock=state['clock_state'];anchor=state['clock_anchor']
        assert item['attachment_internode_id']==original['attachment_internode_id']
        assert clock['leaf_id']==original['leaf_id'] and clock['emerged_elapsed_seconds_exact']==original['emerged_elapsed_seconds_exact']
        assert clock['at_elapsed_seconds_exact']==p['segments'][-1]['end_elapsed_seconds_exact']
        assert anchor['at_elapsed_seconds_exact']==original['emerged_elapsed_seconds_exact'] and anchor['age_exact']['numerator']=='0'
        assert clock['age_exact']==expected['age_exact']
        assert state['area_state']['area']['value']==pytest.approx(float(expected['final_area_m2']),rel=1e-12,abs=0)
        assert state['area_state']['anchor']['canonical_area']['value']==pytest.approx(float(expected['initial_area_m2']),rel=1e-12,abs=0)
    assert result['new_leaf_area']['value']==pytest.approx(sum(float(e['final_area_m2']) for e in case['expected']),rel=1e-12,abs=0)
    assert result['new_leaf_area']['unit']=='m2' and p==before
    assert result==create_declared_leaves(inputs=p)


def test_split_same_newborn_states_and_event_at_boundary_once():
    p=example();whole=create_declared_leaves(inputs=p);cut=Fraction(43200)
    left=deepcopy(p);left['segments'][0]['end_elapsed_seconds_exact']=seconds(cut)
    left['births']=[e for e in p['births'] if Fraction(int(e['emerged_elapsed_seconds_exact']['numerator']),int(e['emerged_elapsed_seconds_exact']['denominator']))<=cut]
    right=deepcopy(p);right['segments'][0]['start_elapsed_seconds_exact']=seconds(cut)
    right['births']=[e for e in p['births'] if e not in left['births']]
    first=create_declared_leaves(inputs=left);second=create_declared_leaves(inputs=right);actual=[]
    for item in first['new_leaves']:
        advanced=leaf.advance_rational_leaf_area(inputs={'input_id':'resume','state':item['state'],'segments':right['segments']})
        actual.append({**item,'state':advanced['state']})
    actual+=second['new_leaves']
    assert [e['state'] for e in actual]==[e['state'] for e in whole['new_leaves']]
    assert len(actual)==3


def test_end_boundary_initializes_without_advance(monkeypatch):
    p=example();p['births']=[p['births'][-1]]
    def forbidden(**_):raise AssertionError('birth at end has no remaining interval')
    monkeypatch.setattr(leaf,'advance_rational_leaf_area',forbidden)
    item=create_declared_leaves(inputs=p)['new_leaves'][0]
    assert item['advancement_input_sha256'] is None and item['state']['clock_state']['age_exact']['numerator']=='0'


@pytest.mark.parametrize('change',['duplicate','reversed-events','at-start','before-start','after-end','missing','extra','wrong-origin','wrong-UTC','bad-ID','bad-attachment','initial-zero','wrong-initial-unit','wrong-base-unit','gap','overlap','reverse','temperature-unit','below-base','no-forcing','too-many-segments','too-many-events'])
def test_invalid_closed_inputs_and_event_scope_hold(change):
    p=example(1)
    if change=='duplicate':p['births'][1]['leaf_id']=p['births'][0]['leaf_id']
    elif change=='reversed-events':p['births'].reverse()
    elif change=='at-start':p['births'][0]['emerged_elapsed_seconds_exact']=seconds(0)
    elif change=='before-start':p['segments'][0]['start_elapsed_seconds_exact']=seconds(1500)
    elif change=='after-end':p['births'][-1]['emerged_elapsed_seconds_exact']=seconds(86401)
    elif change=='missing':del p['births'][0]['initial_area']
    elif change=='extra':p['predict_leaf_count']=True
    elif change=='wrong-origin':p['origin']='measured'
    elif change=='wrong-UTC':p['time_origin_utc']='2026-02-30T00:00:00Z'
    elif change=='bad-ID':p['births'][0]['leaf_id']=''
    elif change=='bad-attachment':p['births'][0]['attachment_internode_id']=' '
    elif change=='initial-zero':p['births'][0]['initial_area']['value']=0
    elif change=='wrong-initial-unit':p['births'][0]['initial_area']['unit']='cm2'
    elif change=='wrong-base-unit':p['births'][0]['base_temperature']['unit']='K'
    elif change=='gap':p['segments'][1]['start_elapsed_seconds_exact']=seconds(3601)
    elif change=='overlap':p['segments'][1]['start_elapsed_seconds_exact']=seconds(3599)
    elif change=='reverse':p['segments'][0]['end_elapsed_seconds_exact']=seconds(0)
    elif change=='temperature-unit':p['segments'][0]['air_temperature']['unit']='K'
    elif change=='below-base':p['segments'][-1]['air_temperature']['value']=9
    elif change=='no-forcing':p['segments']=[]
    elif change=='too-many-segments':p['segments']*=513
    elif change=='too-many-events':p['births']*=513
    with pytest.raises(DeclaredLeafBirthHold):create_declared_leaves(inputs=p)


def test_pre_birth_cold_is_not_post_birth_age():
    p=example(1);p['births']=p['births'][1:];p['segments'][0]['air_temperature']['value']=-5
    assert len(create_declared_leaves(inputs=p)['new_leaves'])==2


def test_512_events_and_payload_bound():
    p=example(2);prototype=p['births'][0];p['births']=[]
    for i in range(512):
        event=deepcopy(prototype);event['leaf_id']='leaf-'+str(i);p['births'].append(event)
    assert len(create_declared_leaves(inputs=p)['new_leaves'])==512
    p=example();p['unused_padding']='x'*(2*1024**2)
    with pytest.raises(DeclaredLeafBirthHold,match='CAPACITY_HOLD'):create_declared_leaves(inputs=p)


def test_output_capacity_holds_even_when_original_input_is_small():
    p=example(2);prototype=p['births'][0];p['births']=[]
    prototype['emerged_elapsed_seconds_exact']=seconds(Fraction(1,10**1000))
    for i in range(512):
        event=deepcopy(prototype);event['leaf_id']='large-leaf-'+str(i);p['births'].append(event)
    assert len(json.dumps(p).encode())<2*1024**2
    with pytest.raises(DeclaredLeafBirthHold,match='CAPACITY_HOLD'):create_declared_leaves(inputs=p)


@pytest.mark.parametrize('bad',[None,True,float('inf'),float('nan'),'22'])
def test_non_numeric_temperatures_are_not_accepted_without_births(bad):
    p=example(4);p['segments'][0]['air_temperature']['value']=bad
    with pytest.raises(DeclaredLeafBirthHold):create_declared_leaves(inputs=p)


def test_512_forcing_segments_and_output_does_not_alias_original_input():
    p=example(2);p['births']=p['births'][:1];p['births'][0]['emerged_elapsed_seconds_exact']=seconds(Fraction(1,3))
    p['segments']=[{'start_elapsed_seconds_exact':seconds(i),'end_elapsed_seconds_exact':seconds(i+1),
                    'air_temperature':{'value':22,'unit':'degC'}} for i in range(512)]
    original=deepcopy(p);result=create_declared_leaves(inputs=p)
    assert result['new_leaves'][0]['state']['clock_state']['age_exact']=={**seconds(Fraction(12)*(512-Fraction(1,3))/86400),'unit':'degC_day'}
    result['new_leaves'][0]['state']['clock_anchor']['base_temperature']['value']=0
    result['new_leaves'][0]['state']['area_state']['curve']['values']['maximum_area']['value']=2
    assert p==original
