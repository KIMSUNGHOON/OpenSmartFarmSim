from copy import deepcopy
from decimal import Decimal,localcontext
from hashlib import sha256
import json
from math import fsum,ulp

import pytest

from app import crop_leaf_partition_climate_rhs as model
from app import crop_growing_geometry_continuation as parent
from app import crop_explicit_lai_climate_rhs as base
from app import crop_leaf_carbon_partition as partition
from test_growing_geometry_leaf_removal_point import CASES,profiles

WEIGHTS=((1.,1.,1.),(0.,0.,0.),(1.,0.,3.),(.25,.5,.25),(1e-30,1.,3.),(13.,7.,1.),(0.,0.,1.))


def raw(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def case_inputs(profiles,case=0,weights=WEIGHTS[0]):
    ctx=parent.prepare_context(program=CASES[case]['program'],step_seconds=.125,step_count=1,**profiles)
    p,seed,_=parent._context(ctx);scenario=deepcopy(seed['evaluation']['joint']['scenario'])
    ids=[x['leaf_id']for x in p['leaves']]
    return scenario,{'input_id':scenario['input_id'],'origin':'synthetic','policy':partition.POLICY_ID,'leaf_ids':ids,
        'sinks':[{'leaf_id':i,'sink_weight':{'value':w,'unit':'1'}}for i,w in zip(ids,weights,strict=True)]}


def run(s,l,p):return model.evaluate_rhs(scenario=s,leaf_stage=l,**p)


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('weights',WEIGHTS)
def test_independent_Decimal_adjustments_whole_carbon_leaf_and_original_components(profiles,case,weights):
    s,l=case_inputs(profiles,case,weights);saved=raw([s,l]);old=base.evaluate_rhs(scenario=s,**profiles);r=run(s,l,profiles)
    c=old['crop'];a=r['adjusted_carbon'];d=r['derivatives']['plant'];D=lambda x:Decimal.from_float(float(x))
    with localcontext()as ctx:
        ctx.prec=180;g=D(c['allocation']['leaf']['value']);cg=D(profiles['growth_profile'].values['cLeafG'])
        w=list(map(D,weights));total=sum(w);effective=g if total else Decimal(0);deferred=g-effective
        for name,original,change in [('buffer',c['derivatives']['buffer']['value'],deferred+cg*deferred),
            ('leaf',c['derivatives']['leaf']['value'],-deferred),('growth',c['growth_respiration']['value'],-cg*deferred)]:
            actual=a['growth_respiration']['value']if name=='growth'else d[name]['value'];want=float(D(original)+change)
            assert abs(actual-want)<=4*ulp(max(abs(original),abs(float(change)),abs(want))),name
        flows=[q['carbohydrate_inflow']['value']for q in r['leaf_partition']['allocation']]
        for actual,weight in zip(flows,w,strict=True):
            want=float(g*weight/total)if total else 0.;assert abs(actual-want)<=2*ulp(want)
        assert a['allocation']['leaf']['value']==float(effective)and a['requested_allocation']['leaf']==c['allocation']['leaf']
        terms=[D(d[k]['value'])for k in ('buffer','leaf','stem_root')]
        terms += [D(q['value'])for q in r['derivatives']['cohorts']['fruit_carbohydrate']]
        terms += [D(a['growth_respiration']['value']),*(D(q['value'])for q in c['vegetative_maintenance'].values()),
            D(c['fruit_maintenance']['value']),*(D(q['value'])for q in c['removals'].values()),
            D(c['cohorts']['terminal_outflow']['fruit_carbohydrate']['value']),-D(c['photosynthesis']['value'])]
        assert abs(sum(terms))<=D(r['balance_budgets']['carbohydrate']['value'])
        leaf=D(d['leaf']['value'])+D(c['vegetative_maintenance']['leaf']['value'])+D(c['removals']['leaf']['value'])-sum(map(D,flows))
        assert abs(leaf)<=D(r['balance_budgets']['leaf_compartment']['value'])
    assert r['source_joint']==old and raw([s,l])==saved
    assert r['derivatives']['cohorts']==old['derivatives']['cohorts']and r['derivatives']['climate']==old['derivatives']['climate']
    for name in ('stem_root','temperature_filtered_24h','temperature_sum'):assert d[name]==old['derivatives']['plant'][name]
    assert a['allocation']['fruit']==c['allocation']['fruit']and a['allocation']['stem_root']==c['allocation']['stem_root']
    for name,value in old['balance_residuals'].items():
        if name!='carbohydrate':assert r['balance_residuals'][name]==value
    assert r['claim_scope']=='synthetic_leaf_partition_joint_rhs_only'and r['G0_G4']=='not_assessed'
    assert r['calculation_sha256']==sha256(raw({k:v for k,v in r.items()if k!='calculation_sha256'})).hexdigest()
    assert run(s,l,profiles)==r


def test_each_real_component_called_once_and_original_results_detached(profiles,monkeypatch):
    s,l=case_inputs(profiles,weights=WEIGHTS[1]);seen={};originals={}
    for module,name,key in [(base,'evaluate_rhs','joint'),(partition,'calculate_partition','partition'),
        (base.carbon,'calculate_plant_rates','carbon'),(base.carbon.optical,'calculate_photosynthesis','optical'),
        (base.exchange,'calculate_exchange','exchange'),(base.area,'calculate_area_energy','area')]:
        fn=getattr(module,name)
        def traced(*,_fn=fn,_key=key,**kw):
            seen[_key]=seen.get(_key,0)+1;out=_fn(**kw);originals[_key]=deepcopy(out);return out
        monkeypatch.setattr(module,name,traced)
    r=run(s,l,profiles);assert seen==dict.fromkeys(('joint','partition','carbon','optical','exchange','area'),1)
    assert r['source_joint']==originals['joint']and r['leaf_partition']==originals['partition']
    r['adjusted_carbon']['derivatives']['leaf']['value']=123
    assert r['source_joint']==originals['joint']and r['derivatives']['plant']['leaf']['value']!=123
    r['source_joint']['scenario']['plant_state']['leaf']['value']=0
    assert r['inputs']['scenario']['plant_state']['leaf']==s['plant_state']['leaf']


@pytest.mark.parametrize('change',[
    lambda l:l.update(extra=1),lambda l:l.pop('policy'),lambda l:l.update(input_id='other-stage'),
    lambda l:l.update(origin='measured'),lambda l:l.update(policy='automatic'),lambda l:l.update(leaf_ids=[]),
    lambda l:l.update(leaf_ids=tuple(l['leaf_ids'])),lambda l:l['leaf_ids'].reverse(),
    lambda l:l['sinks'].reverse(),lambda l:l['sinks'].pop(),lambda l:l['sinks'].append(deepcopy(l['sinks'][0])),
    lambda l:l['leaf_ids'].__setitem__(1,l['leaf_ids'][0]),lambda l:l['sinks'][0].update(extra=1),
    lambda l:l['sinks'][0]['sink_weight'].update(unit='mg_CH2O/s'),lambda l:l['sinks'][0]['sink_weight'].update(value=True),
    lambda l:l['sinks'][0]['sink_weight'].update(value=-1),lambda l:l['sinks'][0]['sink_weight'].update(value=float('nan')),
    lambda l:l['sinks'][0]['sink_weight'].update(value=float('inf')),lambda l:l['leaf_ids'].__setitem__(0,'bad id'),
    lambda l:l['sinks'][0].update(leaf_id='unknown'),lambda l:l.update(requested_leaf_growth={'value':0,'unit':'mg_CH2O/m2_floor/s'})])
def test_invalid_stage_identity_order_scope_and_weights_hold_before_original_rhs(profiles,change,monkeypatch):
    s,l=case_inputs(profiles);change(l)
    def forbidden(**kw):raise AssertionError('invalid leaf input must not evaluate old RHS')
    monkeypatch.setattr(base,'evaluate_rhs',forbidden)
    with pytest.raises(model.LeafPartitionClimateHold):run(s,l,profiles)


def test_512_declared_ids_and_bounded_input_output(profiles,monkeypatch):
    s,l=case_inputs(profiles);l['leaf_ids']=[f'l{i}'for i in range(512)]
    l['sinks']=[{'leaf_id':i,'sink_weight':{'value':1.,'unit':'1'}}for i in l['leaf_ids']]
    r=run(s,l,profiles);assert len(r['leaf_partition']['allocation'])==512 and len(raw(r))<=model.MAX_BYTES
    l['leaf_ids'].append('overflow');l['sinks'].append({'leaf_id':'overflow','sink_weight':{'value':1,'unit':'1'}})
    with pytest.raises(model.LeafPartitionClimateHold,match='CAPACITY_HOLD'):run(s,l,profiles)
    s,l=case_inputs(profiles);monkeypatch.setattr(model,'MAX_BYTES',100)
    with pytest.raises(model.LeafPartitionClimateHold,match='CAPACITY_HOLD'):run(s,l,profiles)


def test_source_depletion_hold_is_preserved_and_partition_not_called(profiles,monkeypatch):
    s,l=case_inputs(profiles);s['plant_state']['buffer']['value']=0;s['forcing']['par_above_canopy']['value']=0
    for name in ('fruit_number_inflow','fruit_entry_carbohydrate'):s['fruit_entry'][name]['value']=0
    def forbidden(**kw):raise AssertionError('no partition after source hold')
    monkeypatch.setattr(partition,'calculate_partition',forbidden)
    with pytest.raises(model.LeafPartitionClimateHold,match='DEPLETED_STATE_HOLD'):run(s,l,profiles)


@pytest.mark.parametrize('which',['own','source','partition','original_hash'])
def test_code_or_source_result_change_holds(profiles,which,monkeypatch):
    s,l=case_inputs(profiles)
    if which=='own':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    elif which in('source','partition'):
        module=base if which=='source'else partition;monkeypatch.setitem(model.COMPONENT_CODE_SHA256,module.__name__,'0'*64)
    else:
        fn=base.evaluate_rhs
        def changed(**kw):out=fn(**kw);out['derivatives']['plant']['leaf']['value']+=1;return out
        monkeypatch.setattr(base,'evaluate_rhs',changed)
    with pytest.raises(model.LeafPartitionClimateHold):run(s,l,profiles)


def test_changed_partition_hash_is_rejected(profiles,monkeypatch):
    s,l=case_inputs(profiles);fn=partition.calculate_partition
    def changed(**kw):out=fn(**kw);out['calculation_sha256']='0'*64;return out
    monkeypatch.setattr(partition,'calculate_partition',changed)
    with pytest.raises(model.LeafPartitionClimateHold,match='SOURCE_HOLD'):run(s,l,profiles)


@pytest.mark.parametrize('which',['source','partition'])
def test_late_code_change_and_component_failure_return_no_partial_result(profiles,which,monkeypatch):
    s,l=case_inputs(profiles);module=base if which=='source'else partition;name='evaluate_rhs'if which=='source'else'calculate_partition'
    fn=getattr(module,name)
    def late(**kw):
        out=fn(**kw);monkeypatch.setitem(model.COMPONENT_CODE_SHA256,module.__name__,'0'*64);return out
    monkeypatch.setattr(module,name,late)
    with pytest.raises(model.LeafPartitionClimateHold):run(s,l,profiles)


@pytest.mark.parametrize('profile',['growth_profile','cohort_profile','transport_profile','exchange_profile'])
def test_original_profile_hold_is_preserved(profiles,profile):
    s,l=case_inputs(profiles)
    with pytest.raises(model.LeafPartitionClimateHold,match='PROFILE_HOLD'):run(s,l,{**profiles,profile:object()})


@pytest.mark.parametrize('which',['source','partition'])
def test_component_failure_returns_no_partial_result(profiles,which,monkeypatch):
    s,l=case_inputs(profiles);module=base if which=='source'else partition;name='evaluate_rhs'if which=='source'else'calculate_partition'
    kind=base.ExplicitLaiClimateHold if which=='source'else partition.LeafCarbonPartitionHold
    def failed(**kw):raise kind('NUMERIC_HOLD: owned injected component failure')
    monkeypatch.setattr(module,name,failed)
    with pytest.raises(model.LeafPartitionClimateHold,match='NUMERIC_HOLD'):run(s,l,profiles)
