from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path

import pytest

from app.crop_leaf_population import (LeafPopulationHold,initialize_leaf_population,normalize_leaf_population_state,advance_leaf_population)
from test_crop_rational_leaf_area import seconds

REFERENCE=json.loads((Path(__file__).resolve().parents[2]/'fixtures/crop-leaf-population-reference-v1.json').read_bytes())


def example(index=0):return deepcopy(REFERENCE['cases'][index])


def fraction(value):return Fraction(int(value['numerator']),int(value['denominator']))


def advance(p,state=None):
    if state is None:state=initialize_leaf_population(inputs=p['initialization'])['state']
    return advance_leaf_population(inputs={'input_id':p['case_id'],'state':state,'segments':p['segments'],'births':p['births']})


def states(result):
    state=result['state'];return [e['state'] for e in state['initial_inventory_state']['leaves']]+[e['state'] for e in state['new_leaves']]


@pytest.mark.parametrize('case',REFERENCE['cases'],ids=lambda p:p['case_id'])
def test_independent_existing_and_new_areas_clocks_counts_totals(case):
    p=deepcopy(case);before=deepcopy(p);result=advance(p)
    assert result['tracked_leaf_count']==len(p['expected']) and result['new_leaf_count']==len(p['births'])
    assert result['tracked_leaf_area']['unit']=='m2' and result['tracked_leaf_area']['value']==pytest.approx(float(p['expected_sum_m2']),rel=1e-12,abs=0)
    for state,expected in zip(states(result),p['expected']):
        assert state['clock_state']['leaf_id']==expected['leaf_id'] and state['clock_state']['age_exact']==expected['age_exact']
        assert state['area_state']['area']['value']==pytest.approx(float(expected['area_m2']),rel=1e-12,abs=0)
        assert state['clock_state']['at_elapsed_seconds_exact']==p['segments'][-1]['end_elapsed_seconds_exact']
    assert result['scope']=='software_research_only' and result['claim_scope']=='synthetic_crop_math_only' and result['gates']=='not_assessed'
    assert normalize_leaf_population_state(state=result['state'])==result['state'] and p==before


def clipped(segments,start,end):
    return [{**s,'start_elapsed_seconds_exact':seconds(max(start,fraction(s['start_elapsed_seconds_exact']))),
             'end_elapsed_seconds_exact':seconds(min(end,fraction(s['end_elapsed_seconds_exact'])))}
            for s in segments if fraction(s['end_elapsed_seconds_exact'])>start and fraction(s['start_elapsed_seconds_exact'])<end]


@pytest.mark.parametrize('cut',[Fraction(1,3),Fraction(1),Fraction(37,5),Fraction(1200),Fraction(43200),Fraction(86399)])
def test_split_same_population_with_boundary_event_once(cut):
    p=example();whole=advance(p);initial=initialize_leaf_population(inputs=p['initialization'])['state']
    left={**p,'segments':clipped(p['segments'],Fraction(0),cut),'births':[e for e in p['births'] if fraction(e['emerged_elapsed_seconds_exact'])<=cut]}
    right={**p,'segments':clipped(p['segments'],cut,Fraction(86400)),'births':[e for e in p['births'] if fraction(e['emerged_elapsed_seconds_exact'])>cut]}
    a=advance(left,initial);b=advance(right,a['state'])
    assert b['state']==whole['state'] and a['new_leaf_count']+b['new_leaf_count']==whole['new_leaf_count']


@pytest.mark.parametrize('change',['duplicate-initial-ID','duplicate-old-new-ID','old-event-again','gap','wrong-unit','below-base','extra','too-many'])
def test_incoming_scope_and_population_identity_hold(change):
    p=example();initial=initialize_leaf_population(inputs=p['initialization'])['state']
    if change=='duplicate-initial-ID':p['births'][0]['leaf_id']='leaf-0'
    elif change=='duplicate-old-new-ID':
        partial={**p,'segments':clipped(p['segments'],Fraction(0),Fraction(43200)),'births':p['births'][:2]};initial=advance(partial,initial)['state']
        p={**p,'segments':clipped(p['segments'],Fraction(43200),Fraction(86400)),'births':deepcopy(p['births'][-1:])};p['births'][0]['leaf_id']='declared-birth-0'
    elif change=='old-event-again':initial=advance(p,initial)['state']
    elif change=='gap':p['segments'][0]['start_elapsed_seconds_exact']=seconds(1)
    elif change=='wrong-unit':p['segments'][0]['air_temperature']['unit']='K'
    elif change=='below-base':p['segments'][0]['air_temperature']['value']=9
    elif change=='extra':initial['pruning']='unreviewed'
    elif change=='too-many':p['births']*=200
    with pytest.raises(LeafPopulationHold):advance(p,initial)


@pytest.mark.parametrize('change',['outer-time','origin','declaration-hash','attachment','removed','reordered','future-birth','curve','base','initial-area','new-leaf-ID','initial-order'])
def test_mutated_population_declarations_and_anchors_hold(change):
    state=advance(example())['state']
    if change=='outer-time':state['at_elapsed_seconds_exact']=seconds(1)
    elif change=='origin':state['time_origin_utc']='2026-10-02T00:00:00Z'
    elif change=='declaration-hash':state['new_leaves'][0]['declaration_sha256']='0'*64
    elif change=='attachment':state['new_leaves'][0]['declaration']['attachment_internode_id']='other'
    elif change=='removed':state['new_leaves'][0].pop('declaration')
    elif change=='reordered':state['new_leaves'].reverse()
    elif change=='future-birth':state['new_leaves'][0]['declaration']['emerged_elapsed_seconds_exact']=seconds(86401)
    elif change=='curve':state['new_leaves'][0]['state']['area_state']['curve']['values']['maximum_area']['value']=.1
    elif change=='base':state['new_leaves'][0]['state']['clock_anchor']['base_temperature']['value']=0
    elif change=='initial-area':state['new_leaves'][0]['declaration']['initial_area']['value']=0
    elif change=='new-leaf-ID':state['new_leaves'][0]['state']['clock_state']['leaf_id']='other'
    elif change=='initial-order':state['initial_inventory_state']['leaves'].reverse()
    with pytest.raises(LeafPopulationHold):normalize_leaf_population_state(state=state)


def test_empty_new_leaves_and_no_output_input_alias():
    p=example(4);before=deepcopy(p);result=advance(p)
    assert result['new_leaf_count']==0 and result['tracked_leaf_count']==3
    result['state']['initial_inventory_state']['leaves'][0]['state']['clock_anchor']['base_temperature']['value']=0
    assert p==before


@pytest.mark.parametrize('change',['remove-leaf','add-leaf','remove-birth-receipt'])
def test_published_birth_inventory_cannot_change_independently(change):
    state=advance(example())['state']
    if change=='remove-leaf':state['new_leaves'].pop()
    elif change=='add-leaf':state['new_leaves'].append(deepcopy(state['new_leaves'][-1]))
    elif change=='remove-birth-receipt':state['birth_inventory'].pop()
    with pytest.raises(LeafPopulationHold):normalize_leaf_population_state(state=state)


def test_512_total_population_leaves_and_513_hold():
    p=example(2);prototype=p['births'][0];p['births']=[]
    for i in range(509):
        event=deepcopy(prototype);event['leaf_id']='new-leaf-'+str(i);p['births'].append(event)
    assert advance(p)['tracked_leaf_count']==512
    event=deepcopy(prototype);event['leaf_id']='new-leaf-overflow';p['births'].append(event)
    with pytest.raises(LeafPopulationHold,match='CAPACITY_HOLD'):advance(p)


def test_population_input_payload_bound():
    p=example();state=initialize_leaf_population(inputs=p['initialization'])['state']
    state['unapproved_padding']='x'*(2*1024**2)
    with pytest.raises(LeafPopulationHold,match='CAPACITY_HOLD'):normalize_leaf_population_state(state=state)


@pytest.mark.parametrize('case_index,cut',[(1,Fraction(3600)),(1,Fraction(7200)),(2,Fraction(37,5)),(3,Fraction(1)),(4,Fraction(37,5))])
def test_temperature_simultaneous_flat_and_no_event_boundaries(case_index,cut):
    p=example(case_index);end=fraction(p['segments'][-1]['end_elapsed_seconds_exact']);whole=advance(p)
    left={**p,'segments':clipped(p['segments'],Fraction(0),cut),'births':[e for e in p['births'] if fraction(e['emerged_elapsed_seconds_exact'])<=cut]}
    right={**p,'segments':clipped(p['segments'],cut,end),'births':[e for e in p['births'] if fraction(e['emerged_elapsed_seconds_exact'])>cut]}
    assert advance(right,advance(left)['state'])['state']==whole['state']


def test_total_area_overflow_between_initial_and_new_cohorts_holds():
    p=example(3)
    for item in p['initialization']['initial_inventory']['leaves']:
        init=item['initialization'];init['curve']['values']['maximum_area']['value']=6e307
        init['curve']['values']['inflection_age']['value']=0;init['initial_area']['value']=3e307
    p['births']=p['births'][:1]*2
    for i in range(2):
        p['births'][i]=deepcopy(p['births'][i]);event=p['births'][i];event['leaf_id']='overflow-new-'+str(i)
        event['emerged_elapsed_seconds_exact']=seconds(86400);event['curve']['values']['maximum_area']['value']=1.2e308
        event['curve']['values']['inflection_age']['value']=0;event['initial_area']['value']=6e307
    with pytest.raises(LeafPopulationHold,match='NUMERIC_HOLD'):advance(p)
