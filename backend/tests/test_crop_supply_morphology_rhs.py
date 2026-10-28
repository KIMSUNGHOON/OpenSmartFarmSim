from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_organ_repeat as source
from test_crop_organ_repeat import adopt
from test_crop_organ_successor_point import TOLERANCE
from test_crop_organ_fractional_continuation import build_short_event_context
from test_crop_leaf_carbon_stock_artifact import profiles, inputs as crop_inputs, encoded, ACCESS, ROOT
from app.crop_leaf_carbon_stock_artifact_producer import produce_leaf_carbon_stock_artifact
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from app.crop_rational_morphology_artifact_reader import read_rational_morphology_frame


def make_current(directory,profiles,buffer_factor=1.,outflow=0.):
    source_input=crop_inputs(1,dt=.125,count=1);source_input['time_origin_utc']='2026-10-01T07:00:00Z'
    program=source_input['program'];program['capacity_outflow']['value']=outflow
    source_input['input_id']=program['input_id']=program['scenario']['input_id']='own-construction-stage-active-leaf-sinks-v1'
    for index,leaf in enumerate(program['leaves']):leaf['sink_weight']['value']=float(index)
    program['scenario']['plant_state']['buffer']['value']*=buffer_factor
    crop_dir=directory/'crop';crop_root=produce_leaf_carbon_stock_artifact(crop_dir,ACCESS,inputs_raw=encoded(source_input),**profiles)
    stem_program=json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_bytes())
    stem_program['output_times']=['2026-10-01T07:00:00Z'];stem_program['segments'][0]['end_utc']=stem_program['output_times'][-1]
    stem_dir=directory/'stem';stem_root=produce_rational_morphology_artifact(stem_dir,ACCESS,program_raw=encoded(stem_program))
    nodes=read_rational_morphology_frame(stem_dir,ACCESS,stem_root,index=0)['internodes']
    ids=[x['internode_id']for x in nodes]
    amounts={3:[2000.,4000.,6000.,8000.],4:[2000.,4000.,6000.,7000.,1000.]}[len(ids)]
    p=deepcopy(program);p['scenario']['plant_state'].pop('stem_root');p['scenario']['removals'].pop('stem_root')
    p['stem_root_stock_policy']=source.stock.short.stock.POLICY_ID
    p['stem_root_compartments']=[{'compartment_id':identifier,'kind':'root_system'if i==0 else'internode',
        'initial_carbon':{'value':carbon,'unit':'mg_CH2O/m2_floor'},'sink_weight':{'value':i+1.,'unit':'1'},
        'carbon_removal':{'value':0.,'unit':'mg_CH2O/m2_floor/s'}}
        for i,(identifier,carbon)in enumerate(zip(['explicit-root',*ids],amounts,strict=True))]
    root=source.stock.parent.prepare_context(program=p,step_seconds=8.,step_count=64,**profiles)
    short_dir=directory/'short';short_dir.mkdir(mode=0o700)
    captured=build_short_event_context(short_dir,root,crop_dir,crop_root,profiles)
    result=source.legacy.advance_chunk(captured,source.legacy.start(captured),128)
    assert result['pending_event']is not None
    raw=source._canonical(result['last_confirmed']);digest=sha256(raw).hexdigest()
    candidate=source.material.candidate.calculate_successor_candidate(captured,raw,expected_sha256=digest,time_tolerance_seconds_exact=TOLERANCE)
    context=adopt((captured,raw,digest,candidate));cp=source.start(context)
    return context,cp,source.checkpoint_bytes(context,cp)


def parameters(context, checkpoint, leaf_cost=1.e12, stem_cost=1.e12):
    p=context.value['seed']['program']
    return {'schema_version':'supply-morphology-stage-input-v1','input_id':'own-marginal-cost-QA',
        'origin':'synthetic','policy':'marginal-construction-extension-v1','parameter_revision':'own-QA-v1',
        'parameter_source':'own_declared_synthetic_assumptions','reviewer':'native-software-QA-not-cultivar-validation',
        'rights':deepcopy(json.loads(context._receipts[-1])['inputs']['rights']),
        'context_sha256':context.root_sha256,'checkpoint_sha256':checkpoint.sha256,'model_floor_area':deepcopy(p['model_floor_area']),
        'leaves':[{'leaf_id':x['leaf_id'],'construction_cost':{'value':leaf_cost,'unit':'mg_CH2O/m2_leaf'}}for x in p['leaves']],
        'internodes':[{'compartment_id':x['compartment_id'],'construction_cost':{'value':stem_cost,'unit':'mg_CH2O/m_internode'}}
            for x in p['stem_root_compartments']if x['kind']=='internode']}


@pytest.fixture(scope='module')
def current(tmp_path_factory,profiles):
    return make_current(tmp_path_factory.mktemp('zero-capacity-outflow-current'),profiles)


def test_actual_checkpoint_drives_supply_limited_growth_and_material_heat(current):
    from app import crop_supply_morphology_rhs as model
    context,cp,raw=current;value=parameters(context,cp);before=source.context_bytes(context)
    out=model.evaluate_bound_rhs(context,raw,expected_sha256=cp.sha256,inputs=value)
    assert out['state'][:len(cp.value['last_confirmed']['state'])]==cp.value['last_confirmed']['state']
    stage=out['stage'];floor=Fraction.from_float(value['model_floor_area']['value'])
    for item in [*stage['leaves'],*stage['internodes']]:
        cost=Fraction.from_float(item['construction_cost']['value']);potential=Fraction.from_float(item['potential_rate']['value'])
        supply=Fraction.from_float(item['inflow']['value']);extension=min(supply,cost*potential/floor)
        assert item['realized_rate']['value']==float(floor*extension/cost)
        assert item['extension_inflow']['value']==float(extension)
        assert item['unmapped_inflow']['value']==float(supply-extension)
        assert 0<=item['realized_rate']['value']<=item['potential_rate']['value']
    assert any(x['realized_rate']['value']<x['potential_rate']['value']for x in stage['leaves'])
    assert stage['derived']['leaf_area_index_rate']['value']==pytest.approx(sum(x['realized_rate']['value']for x in stage['leaves'])/float(floor))
    assert all(abs(q['value'])<=stage['balance_budgets'][k]['value']for k,q in stage['balance_residuals'].items())
    assert out['old_current_validation_RHS_evaluations']==out['new_shared_stage_RHS_evaluations']==1
    assert out['G0_G4']=='not_assessed'and out['integrator_checkpoint']is None
    assert source.context_bytes(context)==before and source.checkpoint_bytes(context,cp)==raw


@pytest.fixture(scope='module')
def evaluated(current):
    from app import crop_supply_morphology_rhs as model
    ctx,cp,raw=current
    return model.evaluate_bound_rhs(ctx,raw,expected_sha256=cp.sha256,inputs=parameters(ctx,cp))


def test_two_genuine_source_paths_vary_carbon_supply_without_a_caller_allocation_override(current,tmp_path_factory,profiles):
    from app import crop_supply_morphology_rhs as model
    low=make_current(tmp_path_factory.mktemp('low-buffer-current'),profiles,buffer_factor=.05)
    outputs=[model.evaluate_bound_rhs(ctx,raw,expected_sha256=cp.sha256,inputs=parameters(ctx,cp))for ctx,cp,raw in [low,current]]
    left,right=outputs;n=len(left['organs']['leaves']);old=left['state_layout']['original_prefix_length']
    assert left['at']==right['at']and left['state'][103:106+2*n]==right['state'][103:106+2*n]
    assert left['state'][old:]==right['state'][old:]and left['state'][0]!=right['state'][0]
    for kind in ['leaves','internodes']:
        pairs=list(zip(left['stage'][kind],right['stage'][kind],strict=True))
        supplied=[(a,b)for a,b in pairs if a['inflow']['value']>0 and b['inflow']['value']>0]
        assert supplied
        for a,b in supplied:
            assert a['inflow']['value']<b['inflow']['value']
            assert a['realized_rate']['value']<b['realized_rate']['value']
        for a,b in pairs:
            if a['inflow']['value']==b['inflow']['value']==0:
                assert a['realized_rate']['value']==b['realized_rate']['value']==0
    assert left['stage']['capacity_transport']['capacity_rates']['incoming']['value']<right['stage']['capacity_transport']['capacity_rates']['incoming']['value']
    assert left['stage']['derivatives']['climate']['canopy_sensible_energy']!=right['stage']['derivatives']['climate']['canopy_sensible_energy']


def test_demand_limited_costs_leave_unmapped_carbon_without_new_cost_or_forced_thickness(current,evaluated):
    from app import crop_supply_morphology_rhs as model
    ctx,cp,raw=current;out=model.evaluate_bound_rhs(ctx,raw,expected_sha256=cp.sha256,inputs=parameters(ctx,cp,1.e-6,1.e-6))
    for row in [*out['stage']['leaves'],*out['stage']['internodes']]:
        if row['inflow']['value']>0:
            assert row['realized_rate']==row['potential_rate']and row['unmapped_inflow']['value']>0
        else:
            assert row['realized_rate']['value']==row['unmapped_inflow']['value']==0
    assert any(row['unmapped_inflow']['value']>0 for row in out['stage']['leaves'])
    assert out['stage']['derivatives']['plant']==evaluated['stage']['derivatives']['plant']
    assert out['stage']['growth_respiration']==evaluated['stage']['growth_respiration']
    assert out['historical_geometry_carbon_compatibility']=='not_assessed'


def test_lineage_and_clocks_keep_initial_unbound_leaves_and_material_threshold_sequences_distinct(current,evaluated):
    ctx,cp,_=current;organs=evaluated['organs'];parents={x['compartment_id']for x in organs['internodes']}
    assert len(organs['roots'])==1 and organs['roots'][0]['age_exact']is None
    for row in organs['leaves']:
        if row['lineage_kind']=='source_initial_leaf':assert row['parent_internode_id']is None and row['attachment_status']=='unbound_initial_leaf'
        else:assert row['parent_internode_id']in parents
    numerical=[x for x in organs['internodes']if x['lineage_kind']=='numerical_threshold_material']
    assert numerical[-1]['material_event_sequence']==cp.value['event_sequence']
    assert len({x['source_threshold_sequence']for x in numerical})==len(numerical)==2
    assert numerical[-1]['material_event_sequence']!=numerical[-1]['source_threshold_sequence']
    assert evaluated['source_binding']['anchors']==ctx.value['seed']['anchors']


@pytest.mark.parametrize('supply,potential,cost,floor',[(0.,1.,3.,2.),(2.,0.,3.,2.),(1.,1.,3.,2.),(1.5,1.,3.,2.),(3.,1.,3.,2.)])
@pytest.mark.parametrize('unit',['m2/s','m/s'])
def test_independent_exact_boundary_and_floor_arithmetic(supply,potential,cost,floor,unit):
    from app.crop_supply_morphology_stage import _classification
    out=_classification(supply,potential,cost,floor,unit);F=Fraction.from_float
    exact=min(F(supply),F(cost)*F(potential)/F(floor))
    assert out['realized_rate']['value']==float(F(floor)*exact/F(cost))
    assert out['extension_inflow']['value']==float(exact)
    assert out['unmapped_inflow']['value']==float(F(supply)-exact)


def _internal(current,evaluated):
    from app import crop_supply_morphology_rhs as model
    ctx,cp,_=current;p=ctx.value['seed']['program'];costs,_=model._parameters(parameters(ctx,cp),ctx,cp,p)
    return p,deepcopy(evaluated['state']),deepcopy(evaluated['organs']),costs,source.stock.parent._profiles(ctx._source._root)


def test_actual_zero_sink_deferrals_preserve_original_respiration_and_carbon_ledgers(current,evaluated):
    from app import crop_supply_morphology_stage as stage
    p,state,organs,costs,profiles=_internal(current,evaluated)
    for row in [*p['leaves'],*p['stem_root_compartments']]:row['sink_weight']['value']=0.
    out=stage.evaluate(p,state,organs,costs,profiles)
    assert all(row['inflow']['value']==row['realized_rate']['value']==0 for row in [*out['leaves'],*out['internodes']])
    assert out['derived']['leaf_area_index_rate']['value']==0
    assert out['leaf_partition']['growth_respiration']['realized']['value']==out['stem_root_partition']['growth_respiration']['realized']['value']==0
    assert all(abs(q['value'])<=out['balance_budgets'][k]['value']for k,q in out['balance_residuals'].items())


def test_zero_thermal_potential_retains_all_inflow_in_unmapped_structural_account(current,evaluated):
    from app import crop_supply_morphology_stage as stage
    p,state,organs,costs,profiles=_internal(current,evaluated)
    for row in p['leaves']:row['base_temperature']['value']=state[104]
    for row in organs['internodes']:row['baseline']['base_temperature']['value']=state[104]
    out=stage.evaluate(p,state,organs,costs,profiles)
    for row in [*out['leaves'],*out['internodes']]:
        assert row['potential_rate']['value']==row['realized_rate']['value']==row['extension_inflow']['value']==0
        assert row['unmapped_inflow']==row['inflow']


@pytest.mark.parametrize('change',[
    lambda v:v.update(policy='unknown'),lambda v:v.update(origin='measured'),lambda v:v.update(parameter_source='unlicensed_external'),
    lambda v:v.update(context_sha256='0'*64),lambda v:v.update(checkpoint_sha256='0'*64),
    lambda v:v['rights'].update(use=False),lambda v:v['rights'].update(ownership_asserted=False),
    lambda v:v['model_floor_area'].update(value=2.),lambda v:v['model_floor_area'].update(unit='m2_leaf'),
    lambda v:v['leaves'][0]['construction_cost'].update(unit='m2_leaf/mg_CH2O'),
    lambda v:v['internodes'][0]['construction_cost'].update(unit='g_DM/m'),
    lambda v:v['leaves'][0]['construction_cost'].update(value=0.),lambda v:v['leaves'][0]['construction_cost'].update(value=True),
    lambda v:v['leaves'][0]['construction_cost'].update(value=float('nan')),lambda v:v['leaves'].pop(),
    lambda v:v['internodes'].reverse(),lambda v:v['leaves'][0].update(leaf_id='unknown'),lambda v:v.update(extra=1),
])
def test_invalid_cost_authority_rights_units_or_inventory_produce_no_result(current,change):
    from app import crop_supply_morphology_rhs as model
    ctx,cp,raw=current;v=parameters(ctx,cp);change(v)
    with pytest.raises(model.SupplyMorphologyHold):model.evaluate_bound_rhs(ctx,raw,expected_sha256=cp.sha256,inputs=v)


@pytest.mark.parametrize('change',[
    lambda p,y,o:p['capacity_outflow'].update(value=.0001),
    lambda p,y,o:p['leaves'][0]['carbon_removal'].update(value=1.),
    lambda p,y,o:y.__setitem__(106,-1.),lambda p,y,o:y.__setitem__(106+len(p['leaves']),0.),
    lambda p,y,o:y.__setitem__(106+2*len(p['leaves']),-1.),lambda p,y,o:y.__setitem__(104,0.),
    lambda p,y,o:y.__setitem__(-1,-1.),lambda p,y,o:y.__setitem__(105,-1.),
])
def test_unsupported_stage_domains_hold_instead_of_clamping(current,evaluated,change):
    from app import crop_supply_morphology_stage as stage
    args=_internal(current,evaluated);change(*args[:3])
    with pytest.raises(stage.SupplyMorphologyHold):stage.evaluate(*args)


def test_current_checkpoint_trust_and_rehashed_state_do_not_replace_original_authority(current):
    from app import crop_supply_morphology_rhs as model
    ctx,cp,raw=current;v=parameters(ctx,cp)
    with pytest.raises(model.SupplyMorphologyHold):model.evaluate_bound_rhs(ctx,raw,expected_sha256='0'*64,inputs=v)
    forged=json.loads(raw);forged['last_confirmed']['state'][0]+=1.;changed=source._canonical(forged);digest=sha256(changed).hexdigest();v['checkpoint_sha256']=digest
    with pytest.raises(model.SupplyMorphologyHold):model.evaluate_bound_rhs(ctx,changed,expected_sha256=digest,inputs=v)


@pytest.mark.parametrize('target',['inputs','state','costs','profile','runtime'])
def test_late_mutation_and_runtime_failure_cannot_publish_a_stage(current,monkeypatch,target):
    from app import crop_supply_morphology_rhs as model
    ctx,cp,raw=current;v=parameters(ctx,cp);run=model.stage.evaluate
    profile=source.stock.parent._profiles(ctx._source._root)['growth_profile'];original=profile.filtered_temperature_bounds
    def changed(p,y,o,c,profiles):
        out=run(p,y,o,c,profiles)
        if target=='inputs':v['rights']['display']=False
        elif target=='state':y[0]+=1.
        elif target=='costs':c['leaves'][0]*=2
        elif target=='profile':object.__setattr__(profile,'filtered_temperature_bounds',(1.,2.))
        else:raise RuntimeError('unexpected stage failure')
        return out
    monkeypatch.setattr(model.stage,'evaluate',changed)
    try:
        with pytest.raises(RuntimeError if target=='runtime'else model.SupplyMorphologyHold):model.evaluate_bound_rhs(ctx,raw,expected_sha256=cp.sha256,inputs=v)
    finally:object.__setattr__(profile,'filtered_temperature_bounds',original)


def test_code_and_response_caps_do_not_publish_partial_results(current,monkeypatch):
    from app import crop_supply_morphology_rhs as model
    ctx,cp,raw=current;v=parameters(ctx,cp)
    with monkeypatch.context()as patch:
        patch.setattr(model,'CODE_SHA256','0'*64)
        with pytest.raises(model.SupplyMorphologyHold,match='CODE_HOLD'):model.evaluate_bound_rhs(ctx,raw,expected_sha256=cp.sha256,inputs=v)
    original=model._canonical
    def bounded(value,maximum=None):return original(value,32 if maximum is None else maximum)
    monkeypatch.setattr(model,'_canonical',bounded)
    with pytest.raises(model.SupplyMorphologyHold,match='CAPACITY_HOLD'):model.evaluate_bound_rhs(ctx,raw,expected_sha256=cp.sha256,inputs=v)


@pytest.mark.parametrize('when',['before','after'])
def test_actual_source_access_loss_withholds_current_or_late_result(current,monkeypatch,when):
    from pathlib import Path
    from stat import S_IMODE
    from app import crop_supply_morphology_rhs as model
    ctx,cp,raw=current;directory=Path(ctx._source._directories[0]);mode=S_IMODE(directory.stat().st_mode)
    run=model.stage.evaluate;calls=[]
    def revoke(*args,**kw):
        out=run(*args,**kw);calls.append(1);directory.chmod(0)
        return out
    if when=='after':monkeypatch.setattr(model.stage,'evaluate',revoke)
    else:directory.chmod(0)
    try:
        with pytest.raises(model.SupplyMorphologyHold):model.evaluate_bound_rhs(ctx,raw,expected_sha256=cp.sha256,inputs=parameters(ctx,cp))
        assert calls==([1]if when=='after'else[])
    finally:directory.chmod(mode)


def test_late_code_identity_change_withholds_result(current,monkeypatch):
    from app import crop_supply_morphology_rhs as model
    ctx,cp,raw=current;run=model.stage.evaluate
    def changed(*args,**kw):
        out=run(*args,**kw);monkeypatch.setattr(model,'CODE_SHA256','0'*64)
        return out
    monkeypatch.setattr(model.stage,'evaluate',changed)
    with pytest.raises(model.SupplyMorphologyHold,match='CODE_HOLD'):model.evaluate_bound_rhs(ctx,raw,expected_sha256=cp.sha256,inputs=parameters(ctx,cp))
