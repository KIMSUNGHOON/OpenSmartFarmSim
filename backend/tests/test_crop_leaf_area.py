from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.crop_leaf_area import (LeafAreaHold,calculate_leaf_area_point,initialize_leaf_area,
                               normalize_leaf_area_state,advance_leaf_area)
from test_crop_leaf_area_change import exact


REFERENCE=json.loads((Path(__file__).resolve().parents[2]/'fixtures/crop-leaf-area-state-reference-v1.json').read_bytes())


def inputs():
    row=REFERENCE['cases'][0]
    return {**deepcopy(row['inputs']),'leaf_id':'leaf-1',
            'initial_area':{'value':float(row['expected_area_m2']),'unit':'m2'}}


@pytest.mark.parametrize('case',REFERENCE['cases'],ids=lambda c:c['case_id'])
def test_independent_point_and_explicit_initial_area(case):
    original=deepcopy(case['inputs']);p=case['inputs'];point=calculate_leaf_area_point(inputs=p)
    assert point['model_version']=='leaf-logistic-canonical-area-point-research-v1'
    assert point['area']['unit']=='m2' and point['area']['value']==pytest.approx(float(case['expected_area_m2']),rel=1e-12,abs=0)
    initialized=initialize_leaf_area(inputs={**p,'leaf_id':'leaf-probe','initial_area':{'value':float(case['expected_area_m2']),'unit':'m2'}})
    state=initialized['state'];assert state['area']==point['area'] and state['age_exact']==p['age_exact']
    assert normalize_leaf_area_state(state=state)==state
    assert initialized['scope']=='software_research_only' and initialized['claim_scope']=='synthetic_crop_math_only'
    assert initialized['gates']=='not_assessed' and case['inputs']==original


def test_split_resume_same_state_anchor_and_independent_interval():
    p=inputs();initial=initialize_leaf_area(inputs=p)['state'];original=deepcopy(initial)
    whole=advance_leaf_area(inputs={'input_id':'whole','state':initial,'end_age_exact':exact(8)})
    state=initial;parts=[]
    for end in (2,4,6,8):
        out=advance_leaf_area(inputs={'input_id':'part-'+str(end),'state':state,'end_age_exact':exact(end)})
        state=out['state'];parts.append(out['area_change']['value'])
    assert state==whole['state'] and state['anchor']==initial['anchor'] and initial==original
    assert state['area']['value']==pytest.approx(float(REFERENCE['cases'][4]['expected_area_m2']),rel=1e-12)
    assert sum(parts)==pytest.approx(whole['area_change']['value'],rel=1e-12,abs=0)
    unchanged=advance_leaf_area(inputs={'input_id':'same-age','state':state,'end_age_exact':exact(8)})
    assert unchanged['state']==state and unchanged['area_change']=={'value':0.0,'unit':'m2'}


def test_small_exact_age_change_retains_positive_increment_and_exact_age():
    p=inputs();p['age_exact']=exact(4);p['initial_area']['value']=.02
    state=initialize_leaf_area(inputs=p)['state']
    end={'numerator':str(4*10**20+1),'denominator':str(10**20),'unit':'degC_day'}
    advanced=advance_leaf_area(inputs={'input_id':'small-step','state':state,'end_age_exact':end})
    assert advanced['state']['age_exact']==end and advanced['state']['area']==state['area']
    assert advanced['area_change']['value']>0
    underflow={'numerator':str(4*10**400+1),'denominator':str(10**400),'unit':'degC_day'}
    with pytest.raises(LeafAreaHold,match='NUMERIC_HOLD'):
        advance_leaf_area(inputs={'input_id':'unrepresentable','state':state,'end_age_exact':underflow})


def test_requested_initial_receipt_is_preserved_separately_from_canonical_area():
    p=inputs();p['initial_area']['value']*=1+1e-13
    state=initialize_leaf_area(inputs=p)['state']
    assert state['anchor']['requested_area']==p['initial_area'] and state['area']!=p['initial_area']
    assert state['anchor']['canonical_area']==state['area']


@pytest.mark.parametrize('change',['missing-normalization','other-normalization','zero-initial','offset-initial',
    'wrong-unit','actual-origin','wrong-clock','bad-leaf-id','extra','missing-area'])
def test_no_implicit_initial_policy_or_units(change):
    p=inputs()
    if change=='missing-normalization':del p['normalization']
    elif change=='other-normalization':p['normalization']='zero_at_emergence'
    elif change=='zero-initial':p['initial_area']['value']=0
    elif change=='offset-initial':p['initial_area']['value']*=2
    elif change=='wrong-unit':p['initial_area']['unit']='cm2'
    elif change=='actual-origin':p['origin']='reference_observation'
    elif change=='wrong-clock':p['thermal_age_basis']='since_internode_emergence'
    elif change=='bad-leaf-id':p['leaf_id']=''
    elif change=='extra':p['actual_cultivar']='Axiany'
    elif change=='missing-area':del p['initial_area']
    with pytest.raises(LeafAreaHold):initialize_leaf_area(inputs=p)


@pytest.mark.parametrize('change',['current-area','anchor-area','requested-area','curve-hash','curve-value',
    'anchor-leaf','leaf-id','anchor-age-after','anchor-extra','policy','state-version'])
def test_current_state_and_anchor_single_mutations_hold(change):
    state=initialize_leaf_area(inputs=inputs())['state']
    if change=='current-area':state['area']['value']*=2
    elif change=='anchor-area':state['anchor']['canonical_area']['value']*=2
    elif change=='requested-area':state['anchor']['requested_area']['value']*=2
    elif change=='curve-hash':state['curve_sha256']='0'*64
    elif change=='curve-value':state['curve']['values']['maximum_area']['value']*=2
    elif change=='anchor-leaf':state['anchor']['leaf_id']='other-leaf'
    elif change=='leaf-id':state['leaf_id']='other-leaf'
    elif change=='anchor-age-after':state['anchor']['age_exact']=exact(4)
    elif change=='anchor-extra':state['anchor']['at']='unverified'
    elif change=='policy':state['normalization']='automatic'
    elif change=='state-version':state['model_version']='future-unreviewed'
    with pytest.raises(LeafAreaHold):normalize_leaf_area_state(state=state)


def test_reverse_age_and_point_numeric_holds():
    state=initialize_leaf_area(inputs=inputs())['state'];state=advance_leaf_area(inputs={'input_id':'to4','state':state,'end_age_exact':exact(4)})['state']
    with pytest.raises(LeafAreaHold):advance_leaf_area(inputs={'input_id':'reverse','state':state,'end_age_exact':exact(2)})
    p=deepcopy(REFERENCE['cases'][0]['inputs']);p['age_exact']=exact(10**400)
    with pytest.raises(LeafAreaHold,match='NUMERIC_HOLD'):calculate_leaf_area_point(inputs=p)
