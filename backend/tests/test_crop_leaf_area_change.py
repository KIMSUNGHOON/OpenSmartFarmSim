from copy import deepcopy
from fractions import Fraction
import json
import math
from pathlib import Path

import pytest

from app.crop_leaf_area_change import LeafAreaChangeHold, calculate_leaf_area_change, normalize_leaf_area_curve
from app.crop_leaf_expansion import calculate_leaf_expansion_rate


REFERENCE = json.loads((Path(__file__).resolve().parents[2] /
    'fixtures/crop-leaf-area-change-reference-v1.json').read_bytes())


def inputs():
    return deepcopy(REFERENCE['cases'][3]['inputs'])


def exact(value):
    v = Fraction(value)
    return {'numerator': str(v.numerator), 'denominator': str(v.denominator), 'unit': 'degC_day'}


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_independent_800_digit_direct_antiderivative_difference(case):
    original = deepcopy(case['inputs']); actual = calculate_leaf_area_change(inputs=case['inputs'])
    assert actual['area_change']['unit'] == 'm2'
    assert actual['area_change']['value'] == pytest.approx(float(case['expected_change_m2']), rel=1e-12, abs=0)
    assert actual['model_version'] == 'leaf-logistic-area-change-research-v1'
    assert actual['scope'] == 'software_research_only' and actual['claim_scope'] == 'synthetic_crop_math_only'
    assert actual['gates'] == 'not_assessed'
    assert actual['start_age_exact'] == case['inputs']['start_age_exact']
    assert actual['end_age_exact'] == case['inputs']['end_age_exact']
    assert len(actual['curve_sha256']) == len(actual['input_sha256']) == 64
    assert set(actual) == {'model_version','scope','claim_scope','gates','input_sha256','curve_sha256',
                           'start_age_exact','end_age_exact','area_change'}
    assert case['inputs'] == original


def test_split_sum_and_identity_do_not_use_endpoint_rate_rectangle():
    p = inputs(); whole = calculate_leaf_area_change(inputs=p); parts=[]
    for start,end in [(0,2),(2,4),(4,6),(6,8)]:
        p['start_age_exact'],p['end_age_exact']=exact(start),exact(end)
        result=calculate_leaf_area_change(inputs=p);parts.append(result['area_change']['value'])
        assert result['curve_sha256']==whole['curve_sha256']
    assert math.fsum(parts)==pytest.approx(whole['area_change']['value'],rel=1e-12,abs=0)
    assert calculate_leaf_area_change(inputs=p)==result
    p['input_id']='distinct-explicit-interval'
    assert calculate_leaf_area_change(inputs=p)['input_sha256']!=result['input_sha256']
    p=inputs(); rate=calculate_leaf_expansion_rate(inputs={'input_id':'rectangle-probe','origin':'synthetic',
        'thermal_age_basis':'since_leaf_emergence','values':{**p['curve']['values'],'thermal_age':{'value':8,'unit':'degC_day'}}})
    assert abs(8*rate['expansion_per_thermal_age']['value']/whole['area_change']['value']-1)>.1


def test_positive_change_when_binary64_endpoint_ages_coincide():
    p=deepcopy(REFERENCE['cases'][8]['inputs'])
    ages=[Fraction(int(p[k]['numerator']),int(p[k]['denominator'])) for k in ('start_age_exact','end_age_exact')]
    assert ages[1]>ages[0] and float(ages[0])==float(ages[1])
    assert calculate_leaf_area_change(inputs=p)['area_change']['value']>0


@pytest.mark.parametrize('change',['reverse','unit','unreduced','denominator-zero','leading-zero','digit-limit','negative',
    'numeric-not-string','age-extra','missing','extra-initial','curve-extra','real-origin','wrong-curve-unit','empty-id'])
def test_closed_exact_interval_and_curve_holds(change):
    p=inputs()
    if change=='reverse':p['start_age_exact'],p['end_age_exact']=p['end_age_exact'],p['start_age_exact']
    elif change=='unit':p['start_age_exact']['unit']='s'
    elif change=='unreduced':p['end_age_exact']={'numerator':'16','denominator':'2','unit':'degC_day'}
    elif change=='denominator-zero':p['start_age_exact']['denominator']='0'
    elif change=='leading-zero':p['end_age_exact']['numerator']='08'
    elif change=='digit-limit':p['end_age_exact']['numerator']='1'*1025
    elif change=='negative':p['start_age_exact']['numerator']='-1'
    elif change=='numeric-not-string':p['start_age_exact']['numerator']=0
    elif change=='age-extra':p['start_age_exact']['at']='2026-10-01T00:00:00Z'
    elif change=='missing':del p['end_age_exact']
    elif change=='extra-initial':p['initial_area']={'value':0,'unit':'m2'}
    elif change=='curve-extra':p['curve']['default']=True
    elif change=='real-origin':p['curve']['origin']='reference_observation'
    elif change=='wrong-curve-unit':p['curve']['values']['maximum_area']['unit']='cm2'
    elif change=='empty-id':p['input_id']=''
    with pytest.raises(LeafAreaChangeHold):calculate_leaf_area_change(inputs=p)


@pytest.mark.parametrize('case',['exponent-overflow','positive-underflow','positive-subnormal'])
def test_unsupported_numeric_intervals_hold(case):
    p=inputs()
    if case=='exponent-overflow':
        p['end_age_exact']=exact(10**400)
    elif case=='positive-underflow':
        p['start_age_exact'],p['end_age_exact']=exact(100000),exact(100001)
    else:
        p['curve']['values']['maximum_area']['value']=1e-308
    with pytest.raises(LeafAreaChangeHold,match='NUMERIC_HOLD'):calculate_leaf_area_change(inputs=p)


def test_curve_normalization_is_bound_to_leaf_rate_version():
    p=inputs(); before=deepcopy(p['curve']);normalized=normalize_leaf_area_curve(curve=p['curve'])
    assert set(normalized)=={'curve','curve_sha256'} and p['curve']==before
    assert normalized['curve']['origin']=='synthetic'
    assert normalize_leaf_area_curve(curve=normalized['curve'])==normalized
