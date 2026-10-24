from copy import deepcopy
from decimal import Decimal,localcontext
from fractions import Fraction
from hashlib import sha256
import json
from math import nextafter,ulp

import pytest

from app import crop_leaf_carbon_stock_rhs as model
from app import crop_leaf_partition_climate_rhs as source
from test_crop_leaf_partition_climate_rhs import case_inputs,raw
from test_growing_geometry_leaf_removal_point import profiles

STOCKS=((.25,.25,.5),(0.,0.,1.),(.125,.875,0.),(1/3,1/3,1/3))
WEIGHTS=((1.,2.,4.),(0.,0.,0.),(0.,1.,2.))


def inputs(p,case=0,stock=STOCKS[0],weights=WEIGHTS[0]):
    s,l=case_inputs(p,case,weights);carbon=s['plant_state'].pop('leaf')['value'];s['removals'].pop('leaf')
    leaves=[{'leaf_id':i,'carbon':{'value':carbon*share,'unit':'mg_CH2O/m2_floor'},
        'sink_weight':{'value':w,'unit':'1'},'removal':{'value':.001*(j+1)if share else 0.,'unit':'mg_CH2O/m2_floor/s'}}
        for j,(i,share,w)in enumerate(zip(l['leaf_ids'],stock,weights,strict=True))]
    return s,{'input_id':s['input_id'],'origin':'synthetic','policy':model.POLICY_ID,
        'model_floor_area':deepcopy(s['geometry']['model_floor_area']),'leaf_ids':l['leaf_ids'],'leaves':leaves}


def run(s,l,p):return model.evaluate_rhs(scenario=s,leaf_stocks=l,**p)


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('stock',STOCKS)
@pytest.mark.parametrize('weights',WEIGHTS)
def test_independent_individual_maintenance_derivatives_and_whole_C_from_authoritative_stocks(profiles,case,stock,weights):
    s,l=inputs(profiles,case,stock,weights);before=raw([s,l]);r=run(s,l,profiles);stage=r['source_stage'];crop=stage['source_joint']['crop']
    D=lambda x:Decimal.from_float(float(x))
    with localcontext()as ctx:
        ctx.prec=180;cs=[D(x['carbon']['value'])for x in l['leaves']];total=sum(cs);agg=float(total)
        assert r['leaf_totals']['carbon']['value']==agg==stage['inputs']['scenario']['plant_state']['leaf']['value']
        p={k:D(v)for k,v in profiles['growth_profile'].values.items()};temp=D(s['plant_state']['temperature_filtered_24h']['value'])
        phi=(1-(-p['cRgr']*p['rgr']).exp())*(p['q10m'].ln()*(temp-p['maintenance_temperature_reference_c'])/p['q10_temperature_interval_c']).exp()
        independent_M=phi*D(agg)*p['cLeafM'];original_M=D(crop['vegetative_maintenance']['leaf']['value'])
        assert abs(original_M-independent_M)<=max(abs(independent_M)*D(5e-12),D(64*ulp(float(independent_M))))
        allocated=stage['leaf_partition']['allocation'];ds=[];ms=[]
        for row,state,c,g in zip(r['leaf_rates'],l['leaves'],cs,allocated,strict=True):
            want_M=float(original_M*c/total);inflow=g['carbohydrate_inflow']['value'];removal=state['removal']['value']
            assert abs(row['maintenance']['value']-want_M)<=2*ulp(want_M)
            want_d=float(D(inflow)-D(want_M)-D(removal));scale=max(abs(inflow),abs(want_M),abs(removal))
            assert abs(row['derivative']['value']-want_d)<=4*ulp(scale)
            assert row['leaf_id']==state['leaf_id']and row['inflow']==g['carbohydrate_inflow']and row['removal']==state['removal']
            ds.append(D(row['derivative']['value']));ms.append(D(row['maintenance']['value']))
        assert r['derivatives']['plant']['leaf']['value']==float(sum(ds))and r['leaf_totals']['maintenance']['value']==float(sum(ms))
        plant=r['derivatives']['plant'];terms=[D(plant[k]['value'])for k in('buffer','leaf','stem_root')]
        terms += [D(q['value'])for q in r['derivatives']['cohorts']['fruit_carbohydrate']]
        terms += [D(stage['adjusted_carbon']['growth_respiration']['value']),sum(ms),D(crop['vegetative_maintenance']['stem_root']['value']),
            D(crop['fruit_maintenance']['value']),sum(D(x['removal']['value'])for x in l['leaves']),D(crop['removals']['stem_root']['value']),
            D(crop['cohorts']['terminal_outflow']['fruit_carbohydrate']['value']),-D(crop['photosynthesis']['value'])]
        assert abs(sum(terms))<=D(r['balance_budgets']['carbohydrate']['value'])
    assert raw([s,l])==before and 'leaf'not in r['inputs']['scenario']['plant_state']and 'leaf'not in r['inputs']['scenario']['removals']
    for block in('cohorts','climate'):assert r['derivatives'][block]==stage['derivatives'][block]
    for name in('buffer','stem_root','temperature_filtered_24h','temperature_sum'):assert r['derivatives']['plant'][name]==stage['derivatives']['plant'][name]
    assert r['claim_scope']=='synthetic_individual_leaf_carbon_rhs_only'and r['G0_G4']=='not_assessed'
    assert r['calculation_sha256']==sha256(raw({k:v for k,v in r.items()if k!='calculation_sha256'})).hexdigest()
    assert run(s,l,profiles)==r


@pytest.mark.parametrize('change',[
    lambda s,l:l.update(extra=1),lambda s,l:l.update(origin='measured'),lambda s,l:l.update(policy='automatic'),
    lambda s,l:l.update(input_id='other'),lambda s,l:l['model_floor_area'].update(value=2*l['model_floor_area']['value']),
    lambda s,l:l['model_floor_area'].update(unit='m2_leaf'),lambda s,l:l['model_floor_area'].update(value=True),
    lambda s,l:l['leaf_ids'].reverse(),lambda s,l:l['leaves'].reverse(),lambda s,l:l['leaves'].pop(),
    lambda s,l:l['leaves'][0].update(extra=1),lambda s,l:l['leaves'][0]['carbon'].update(unit='mg_CH2O'),
    lambda s,l:l['leaves'][0]['carbon'].update(value=-1),lambda s,l:l['leaves'][0]['carbon'].update(value=float('nan')),
    lambda s,l:l['leaves'][0]['removal'].update(value=-1),lambda s,l:l['leaves'][0]['sink_weight'].update(value=True),
    lambda s,l:l.update(leaves=[]),lambda s,l:l.update(leaves=tuple(l['leaves'])),lambda s,l:l['leaf_ids'].__setitem__(1,l['leaf_ids'][0]),
    lambda s,l:s['plant_state'].update(leaf={'value':100,'unit':'mg_CH2O/m2_floor'}),
    lambda s,l:s['removals'].update(leaf={'value':0,'unit':'mg_CH2O/m2_floor/s'})])
def test_closed_units_identity_basis_and_no_duplicate_aggregate_before_source(profiles,change,monkeypatch):
    s,l=inputs(profiles);change(s,l)
    def forbidden(**kw):raise AssertionError('invalid state must not evaluate source')
    monkeypatch.setattr(source,'evaluate_rhs',forbidden)
    with pytest.raises(model.LeafCarbonStockHold):run(s,l,profiles)


def test_zero_stock_outward_depletion_and_explicit_flow_through(profiles):
    s,l=inputs(profiles,stock=STOCKS[1]);r=run(s,l,profiles);g=r['leaf_rates'][0]['inflow']['value']
    l['leaves'][0]['removal']['value']=g;balanced=run(s,l,profiles);assert balanced['leaf_rates'][0]['derivative']['value']==0
    l['leaves'][0]['removal']['value']=nextafter(g,float('inf'))
    with pytest.raises(model.LeafCarbonStockHold,match='DEPLETED_STATE_HOLD'):run(s,l,profiles)
    for row in l['leaves']:row['carbon']['value']=0
    with pytest.raises(model.LeafCarbonStockHold,match='STATE_HOLD'):run(s,l,profiles)


def test_per_floor_units_are_not_silently_multiplied_by_changed_model_footprint(profiles):
    s,l=inputs(profiles);first=run(s,l,profiles)
    s['geometry']['model_floor_area']['value']*=2;l['model_floor_area']['value']*=2;r=run(s,l,profiles)
    assert r['leaf_totals']==first['leaf_totals']and r['leaf_rates']==first['leaf_rates']


def test_each_source_and_partition_component_once_and_detached(profiles,monkeypatch):
    s,l=inputs(profiles);calls={}
    for module,name,key in((source,'evaluate_rhs','stage'),(source.source,'evaluate_rhs','joint'),(source.partition,'calculate_partition','partition')):
        fn=getattr(module,name)
        def counted(*,_fn=fn,_key=key,**kw):calls[_key]=calls.get(_key,0)+1;return _fn(**kw)
        monkeypatch.setattr(module,name,counted)
    r=run(s,l,profiles);assert calls==dict.fromkeys(('stage','joint','partition'),1)
    original=deepcopy(r['source_stage']);r['derivatives']['plant']['leaf']['value']=12;assert r['source_stage']==original
    r['inputs']['leaf_stocks']['leaves'][0]['carbon']['value']=0;assert l['leaves'][0]['carbon']['value']>0


def test_512_stocks_capacity_and_positive_maintenance_underflow_hold(profiles,monkeypatch):
    s,l=inputs(profiles);carbon=float(sum(Fraction.from_float(x['carbon']['value'])for x in l['leaves']));l['leaf_ids']=[f'l{i}'for i in range(512)]
    l['leaves']=[{'leaf_id':i,'carbon':{'value':carbon/512,'unit':'mg_CH2O/m2_floor'},'sink_weight':{'value':1,'unit':'1'},
        'removal':{'value':0,'unit':'mg_CH2O/m2_floor/s'}}for i in l['leaf_ids']]
    r=run(s,l,profiles);assert len(r['leaf_rates'])==512 and len(raw(r))<=model.MAX_BYTES
    l['leaf_ids'].append('overflow');l['leaves'].append({**deepcopy(l['leaves'][0]),'leaf_id':'overflow'})
    with pytest.raises(model.LeafCarbonStockHold,match='CAPACITY_HOLD'):run(s,l,profiles)
    s,l=inputs(profiles);l['leaves'][0]['carbon']['value']=float.fromhex('0x1.0p-1022')
    with pytest.raises(model.LeafCarbonStockHold,match='NUMERIC_HOLD'):run(s,l,profiles)
    s,l=inputs(profiles)
    for row in l['leaves']:row['carbon']['value']=float.fromhex('0x1.fffffffffffffp+1023')
    with pytest.raises(model.LeafCarbonStockHold):run(s,l,profiles)
    monkeypatch.setattr(model,'MAX_BYTES',100)
    with pytest.raises(model.LeafCarbonStockHold,match='CAPACITY_HOLD'):run(s,l,profiles)


@pytest.mark.parametrize('kind',['own_code','source_code','source_hash','source_failure'])
def test_code_hash_and_component_failure_holds(profiles,kind,monkeypatch):
    s,l=inputs(profiles)
    if kind=='own_code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    elif kind=='source_code':monkeypatch.setitem(model.COMPONENT_CODE_SHA256,source.__name__,'0'*64)
    else:
        fn=source.evaluate_rhs
        def changed(**kw):
            if kind=='source_failure':raise source.LeafPartitionClimateHold('NUMERIC_HOLD: owned fault')
            out=fn(**kw);out['calculation_sha256']='0'*64;return out
        monkeypatch.setattr(source,'evaluate_rhs',changed)
    with pytest.raises(model.LeafCarbonStockHold):run(s,l,profiles)
