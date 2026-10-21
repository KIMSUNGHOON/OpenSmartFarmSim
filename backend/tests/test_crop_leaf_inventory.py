from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.crop_leaf_inventory import (LeafInventoryHold,initialize_leaf_inventory,normalize_leaf_inventory_state,advance_leaf_inventory)
from test_crop_rational_leaf_area import seconds


REFERENCE=json.loads((Path(__file__).resolve().parents[2]/'fixtures/crop-leaf-inventory-reference-v1.json').read_bytes())


def example(index=1):return deepcopy(REFERENCE['cases'][index])


@pytest.mark.parametrize('case',REFERENCE['cases'],ids=lambda c:c['case_id'])
def test_independent_areas_totals_exact_ages_and_declared_references(case):
    p=deepcopy(case);original=deepcopy(p);initial=initialize_leaf_inventory(inputs=p['initialization'])
    assert initial['tracked_leaf_count']==3 and initial['tracked_leaf_area']['unit']=='m2'
    assert initial['tracked_leaf_area']['value']==pytest.approx(float(p['expected_initial_sum_m2']),rel=1e-12,abs=0)
    result=advance_leaf_inventory(inputs={'input_id':'whole','state':initial['state'],'segments':p['segments']})
    assert result['tracked_leaf_count']==3 and result['tracked_leaf_area']['value']==pytest.approx(float(p['expected_final_sum_m2']),rel=1e-12,abs=0)
    assert result['tracked_area_change']['value']==pytest.approx(float(p['expected_total_change_m2']),rel=1e-12,abs=0)
    for i,leaf in enumerate(result['state']['leaves']):
        assert leaf['attachment_internode_id']=='internode-'+str(i)
        assert leaf['state']['clock_state']['age_exact']==p['expected_ages_exact'][i]
        assert leaf['state']['area_state']['area']['value']==pytest.approx(float(p['expected_final_areas_m2'][i]),rel=1e-12,abs=0)
    assert normalize_leaf_inventory_state(state=result['state'])==result['state'] and p==original
    assert result['scope']=='software_research_only' and result['claim_scope']=='synthetic_crop_math_only' and result['gates']=='not_assessed'


def test_split_same_inventory_and_changes():
    p=example();initial=initialize_leaf_inventory(inputs=p['initialization'])['state'];original=deepcopy(initial)
    whole=advance_leaf_inventory(inputs={'input_id':'whole','state':initial,'segments':p['segments']});state=initial;changes=[]
    for i,segment in enumerate(p['segments']):
        result=advance_leaf_inventory(inputs={'input_id':'part-'+str(i),'state':state,'segments':[segment]})
        state=result['state'];changes.append(result['tracked_area_change']['value'])
    assert state==whole['state'] and state['initial_inventory']==initial['initial_inventory'] and initial==original
    assert sum(changes)==pytest.approx(whole['tracked_area_change']['value'],rel=1e-12,abs=0)


@pytest.mark.parametrize('change',['duplicate-id','different-origin','different-at','empty','over-limit','unknown-field','bad-attachment'])
def test_closed_initial_declared_inventory(change):
    p=example()['initialization']
    if change=='duplicate-id':p['leaves'][1]['initialization']['clock_state']['leaf_id']='leaf-0'
    elif change=='different-origin':p['leaves'][1]['initialization']['clock_state']['time_origin_utc']='2026-10-02T00:00:00Z'
    elif change=='different-at':p['leaves'][1]['initialization']['clock_state']['at_elapsed_seconds_exact']=seconds(1)
    elif change=='empty':p['leaves']=[]
    elif change=='over-limit':p['leaves']=[p['leaves'][0]]*513
    elif change=='unknown-field':p['predict_new_leaves']=True
    elif change=='bad-attachment':p['leaves'][0]['attachment_internode_id']=''
    with pytest.raises(LeafInventoryHold):initialize_leaf_inventory(inputs=p)


@pytest.mark.parametrize('change',['removed','added','reordered','attachment','current-at','origin','anchor-at','extra'])
def test_immutable_declared_list_and_current_scope(change):
    state=initialize_leaf_inventory(inputs=example()['initialization'])['state']
    if change=='removed':state['leaves'].pop()
    elif change=='added':state['leaves'].append(deepcopy(state['leaves'][0]))
    elif change=='reordered':state['leaves'].reverse()
    elif change=='attachment':state['leaves'][0]['attachment_internode_id']='other-internode'
    elif change=='current-at':state['at_elapsed_seconds_exact']=seconds(1)
    elif change=='origin':state['time_origin_utc']='2026-10-02T00:00:00Z'
    elif change=='anchor-at':state['initial_inventory']['at_elapsed_seconds_exact']=seconds(1)
    elif change=='extra':state['management']='unreviewed'
    with pytest.raises(LeafInventoryHold):normalize_leaf_inventory_state(state=state)


def test_512_leaves_supported_and_aggregate_overflow_holds():
    p=example(0)['initialization'];leaf=p['leaves'][0];p['leaves']=[]
    for i in range(512):
        item=deepcopy(leaf);item['initialization']['clock_state']['leaf_id']='leaf-'+str(i);item['attachment_internode_id']='internode-'+str(i);p['leaves'].append(item)
    result=initialize_leaf_inventory(inputs=p);assert result['tracked_leaf_count']==512
    assert normalize_leaf_inventory_state(state=result['state'])==result['state']
    p=example(0)['initialization'];p['at_elapsed_seconds_exact']=seconds(1)
    for item in p['leaves']:
        init=item['initialization'];init['clock_state']['at_elapsed_seconds_exact']=seconds(1)
        init['clock_state']['age_exact']={'numerator':'100','denominator':'1','unit':'degC_day'}
        init['curve']['values']['maximum_area']['value']=1e308;init['curve']['values']['steepness']['value']=1
        init['curve']['values']['inflection_age']['value']=0;init['initial_area']['value']=1e308
    with pytest.raises(LeafInventoryHold,match='NUMERIC_HOLD'):initialize_leaf_inventory(inputs=p)


def test_large_exact_initial_ages_exceeding_payload_bound_hold():
    p=example(0)['initialization'];template=deepcopy(p['leaves'][0]);p['leaves']=[];p['at_elapsed_seconds_exact']=seconds(1)
    for i in range(512):
        item=deepcopy(template);clock=item['initialization']['clock_state'];clock['leaf_id']='large-leaf-'+str(i)
        clock['at_elapsed_seconds_exact']=seconds(1)
        clock['age_exact']={'numerator':'1','denominator':str(10**1000),'unit':'degC_day'}
        p['leaves'].append(item)
    with pytest.raises(LeafInventoryHold,match='CAPACITY_HOLD'):initialize_leaf_inventory(inputs=p)
