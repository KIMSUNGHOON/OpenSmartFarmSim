from copy import deepcopy
from decimal import Decimal, localcontext
import json
from math import fsum, nextafter, ulp
from pathlib import Path
import sys

import pytest

from app import crop_leaf_carbon_partition as partition
from app.crop_growth_rates import ReferenceParameters, RATE_UNIT
from test_growing_geometry_leaf_removal_point import CASES, profiles
from app import crop_growing_geometry_continuation as parent

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def profile():return ReferenceParameters((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes())


def inputs(growth=4.0,weights=(1.0,3.0)):
    return {'input_id':'own-leaf-partition','origin':'synthetic','policy':partition.POLICY_ID,
        'requested_leaf_growth':{'value':growth,'unit':RATE_UNIT},
        'leaves':[{'leaf_id':f'leaf-{i}','sink_weight':{'value':w,'unit':'1'}}for i,w in enumerate(weights)]}


def reference(g,weights,c):
    with localcontext()as ctx:
        ctx.prec=180;g=Decimal.from_float(float(g));c=Decimal.from_float(c)
        w=[Decimal.from_float(float(x))for x in weights];total=sum(w);realized=g if total else Decimal(0);deferred=g-realized
        flows=[float(g*x/total)if total else 0.0 for x in w]
        return flows,float(c*g),float(c*realized),float(c*deferred),float(deferred+c*deferred)


@pytest.mark.parametrize('growth,weights',[(4.,(1.,3.)),(0.,(1.,3.)),(4.,(0.,0.)),(0.,(0.,0.)),
    (2.,(1.,)),(30.,(1.,2.)),(.125,(0.,1.,0.,3.)),(1e80,(1e-30,1.,3.)),(1e-80,(.25,.5,.25)),
    (nextafter(1.,2.),(1.,7.,13.)),(10.,tuple(float(i%7)for i in range(512)))])
def test_independent_Decimal_flows_respiration_refund_and_input_preservation(profile,growth,weights):
    v=inputs(growth,weights);before=deepcopy(v);r=partition.calculate_partition(inputs=v,growth_profile=profile)
    expected=reference(growth,weights,profile.values['cLeafG'])
    for actual,want in zip([q['carbohydrate_inflow']['value']for q in r['allocation']],expected[0],strict=True):
        assert abs(actual-want)<=2*ulp(want)
    for key,want in zip(('requested','realized','avoided'),expected[1:4],strict=True):assert r['growth_respiration'][key]=={'value':want,'unit':RATE_UNIT}
    assert abs(r['derivative_adjustments']['buffer']['value']-expected[4])<=2*ulp(expected[4])
    assert r['effective_leaf_growth']['value']==(growth if any(weights)else 0.)
    assert r['deferred_leaf_growth']['value']==(0. if any(weights)else growth)
    assert [x['leaf_id']for x in r['allocation']]==[x['leaf_id']for x in v['leaves']]
    assert all(x['carbohydrate_inflow']['unit']==RATE_UNIT for x in r['allocation'])
    assert r['profile_sha256']==profile.sha256 and r['G0_G4']=='not_assessed'
    assert r['claim_scope']=='synthetic_leaf_carbon_partition_math_only'
    for k,q in r['balance_residuals'].items():assert abs(q['value'])<=r['balance_budgets'][k]['value']
    assert v==before and partition.calculate_partition(inputs=v,growth_profile=profile)==r


def test_relative_weights_are_not_a_mass_demand_cap_or_default_equal_shares(profile):
    r=partition.calculate_partition(inputs=inputs(30.,(1.,2.)),growth_profile=profile)
    assert [q['carbohydrate_inflow']['value']for q in r['allocation']]==[10.,20.]
    assert r['derivative_adjustments']['buffer']['value']==0 and r['deferred_leaf_growth']['value']==0


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('weights',[(1.,2.,4.),(0.,0.,0.)])
def test_actual_parent_RHS_budget_requires_atomic_leaf_buffer_respiration_adjustments(profiles,case,weights):
    context=parent.prepare_context(program=CASES[case]['program'],step_seconds=.125,step_count=1,**profiles)
    p,seed,m=parent._context(context);current=seed['evaluation']['joint']['crop'];g=current['allocation']['leaf']['value']
    r=partition.calculate_partition(inputs=inputs(g,weights),growth_profile=profiles['growth_profile']);a=r['derivative_adjustments']
    y=fsum((current['derivatives']['leaf']['value'],a['leaf']['value']))
    assert abs(fsum((y,current['vegetative_maintenance']['leaf']['value'],current['removals']['leaf']['value'],
        *(-q['carbohydrate_inflow']['value']for q in r['allocation']))))<=r['balance_budgets']['allocation']['value']+64*ulp(g)
    original=current['balance_residual']['carbohydrate']['value']
    adjusted=fsum((original,*(q['value']for q in a.values())))
    assert abs(adjusted)<=current['balance_budget']['carbohydrate']['value']+r['balance_budgets']['adjustments']['value']
    if not any(weights):
        assert a['buffer']['value']>g and a['leaf']['value']==-g and a['growth_respiration']['value']<0
        assert abs(fsum((a['buffer']['value'],a['leaf']['value'])))>r['balance_budgets']['adjustments']['value']
    assert parent._context(context)==(p,seed,m)


@pytest.mark.parametrize('change',[
    lambda v:v.update(extra=1),lambda v:v.update(origin='measured'),lambda v:v.update(policy='automatic'),
    lambda v:v.update(input_id=''),lambda v:v.update(input_id='bad id'),lambda v:v.pop('policy'),
    lambda v:v.update(leaves=[]),lambda v:v.update(leaves=tuple(v['leaves'])),lambda v:v['leaves'].append(deepcopy(v['leaves'][0])),
    lambda v:v['leaves'][0].update(extra=1),lambda v:v['leaves'][0].update(leaf_id='bad id'),
    lambda v:v['requested_leaf_growth'].update(value=-1),lambda v:v['requested_leaf_growth'].update(value=True),
    lambda v:v['requested_leaf_growth'].update(value=float('inf')),lambda v:v['requested_leaf_growth'].update(value=float('nan')),
    lambda v:v['requested_leaf_growth'].update(unit='mg_CH2O/s'),lambda v:v['requested_leaf_growth'].update(extra=1),
    lambda v:v['leaves'][0]['sink_weight'].update(value=-1),lambda v:v['leaves'][0]['sink_weight'].update(value=True),
    lambda v:v['leaves'][0]['sink_weight'].update(value=float('nan')),lambda v:v['leaves'][0]['sink_weight'].update(unit='mg_CH2O'),
])
def test_rejects_missing_or_invalid_declared_budget_scope_units_or_inventory(profile,change):
    v=inputs();change(v)
    with pytest.raises(partition.LeafCarbonPartitionHold):partition.calculate_partition(inputs=v,growth_profile=profile)


@pytest.mark.parametrize('g,weights',[(1.,tuple(1. for _ in range(513))),(1.,(1e308,1e308)),(sys.float_info.max,(0.,)),
    (sys.float_info.min,(1.,)),(1.,(sys.float_info.min,1e308)),(1.,(5e-324,1.))])
def test_rejects_capacity_overflow_and_lost_positive_flows(profile,g,weights):
    with pytest.raises(partition.LeafCarbonPartitionHold):partition.calculate_partition(inputs=inputs(g,weights),growth_profile=profile)


def test_bounds_input_and_output_and_returns_copied_views(profile):
    v=inputs();v['input_id']='x'*140000
    with pytest.raises(partition.LeafCarbonPartitionHold):partition.calculate_partition(inputs=v,growth_profile=profile)
    v=inputs();r=partition.calculate_partition(inputs=v,growth_profile=profile);r['inputs']['leaves'][0]['sink_weight']['value']=0
    assert v['leaves'][0]['sink_weight']['value']==1.
    assert len(json.dumps(partition.calculate_partition(inputs=inputs(1.,tuple(1. for _ in range(512))),growth_profile=profile)).encode())<128*1024


def test_rejects_unreviewed_profile_and_changed_code(profile,monkeypatch):
    with pytest.raises(partition.LeafCarbonPartitionHold):partition.calculate_partition(inputs=inputs(),growth_profile=object())
    monkeypatch.setattr(partition,'CODE_SHA256','0'*64)
    with pytest.raises(partition.LeafCarbonPartitionHold,match='CODE_HOLD'):partition.calculate_partition(inputs=inputs(),growth_profile=profile)


def test_partition_does_not_recalculate_growth_or_advance_state(profile,monkeypatch):
    from app import crop_growth_rates
    def forbidden(*args,**kwargs):raise AssertionError('partition must not repeat photosynthesis or time advance')
    monkeypatch.setattr(crop_growth_rates,'calculate_rates',forbidden);monkeypatch.setattr(crop_growth_rates,'_photosynthesis',forbidden)
    monkeypatch.setattr(parent,'prepare_context',forbidden);monkeypatch.setattr(parent,'advance_chunk',forbidden)
    assert partition.calculate_partition(inputs=inputs(),growth_profile=profile)['effective_leaf_growth']['value']==4.
