"""Automatic shared grid, atomic boundaries and global inventory prefixes."""
from copy import deepcopy
from decimal import Decimal,localcontext
from hashlib import sha256
import json
from math import fsum
from pathlib import Path

import pytest

from app import crop_climate_joint_boundary as model
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT=Path(__file__).resolve().parents[2]
PREVIOUS=json.loads((ROOT/'fixtures/crop-climate-joint-management-reference-cases-v1.json').read_bytes())
REFERENCE=json.loads((ROOT/'fixtures/crop-climate-joint-boundary-reference-cases-v1.json').read_bytes())


@pytest.fixture(scope='module')
def profiles():
    return {name:kind((ROOT/'fixtures'/filename).read_bytes()) for name,kind,filename in (
        ('growth_profile',Growth,'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile',Cohort,'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile',Transport,'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile',Exchange,'crop-canopy-exchange-reference-parameters-v1.json'))}


def run(profiles,scenario=None,events=None,outputs=None,dt=2,count=16):
    row=PREVIOUS['programs'][0]
    return model.integrate_events(scenario=row['scenario'] if scenario is None else scenario,
        events=[{'step_index':8,'event':row['event']}] if events is None else events,
        output_steps=[0,8,16] if outputs is None else outputs,step_seconds=dt,step_count=count,**profiles)


def test_automatic_boundary_order_global_ledgers_and_input_preservation(profiles,monkeypatch):
    original=model.joint.evaluate_rhs;calls=[]
    def record(**kw):calls.append(deepcopy(kw['scenario']));return original(**kw)
    monkeypatch.setattr(model.joint,'evaluate_rhs',record)
    source=PREVIOUS['programs'][0];s,e=deepcopy(source['scenario']),[{'step_index':8,'event':deepcopy(source['event'])}]
    saved_s,saved_e=deepcopy(s),deepcopy(e);r=run(profiles,s,e)
    assert s==saved_s and e==saved_e
    assert len(calls)==83==r['numerical']['rhs_evaluations']==1+5*16+2
    assert [v['step_index'] for v in r['samples']]==[0,8,16]
    assert len(r['events'])==1 and r['events'][0]['elapsed_seconds']==16
    at=r['samples'][1];event=r['events'][0]['management']
    assert at['phase']=='boundary-after-event' and at['plant_state']==event['after']['scenario']['plant_state']
    assert at['plant_state']!=event['before']['scenario']['plant_state']
    assert len(r['integrated_transfers'])==22 and len(r['event_totals'])==6
    for sample in r['samples']:
        for k,q in sample['balance_residuals'].items():assert abs(q['value'])<=sample['balance_budgets'][k]['value']
    assert r['scope']=='software_research_only' and r['G0_G4']=='not_assessed'


def test_no_event_matches_accepted_shared_short_kernel_exactly(profiles):
    r=run(profiles,events=[]);old=model.short.integrate(scenario=r['scenario'],step_seconds=2,step_count=16,**profiles)
    for k in ('plant_state','cohort_state','climate_state','derived'):
        assert r['last_confirmed'][k]==old['samples'][-1][k]
    assert r['integrated_transfers']==old['integrated_transfers']
    assert all(q['value']==0 for q in r['event_totals'].values())


def case_run(profiles,case,dt=2,outputs=None):
    scale=lambda i:int(i*case['step_seconds']/dt)
    return run(profiles,case['scenario'],[{'step_index':scale(row['step_index']),'event':row['event']} for row in case['events']],
        [scale(i) for i in case['output_steps']] if outputs is None else outputs,dt,scale(case['step_count']))


def state(sample):return list(model.short._state(sample))
def approx(x,y):assert x==pytest.approx(float(y),rel=5e-12,abs=5e-14)
def state_equal(found,wanted):
    for i,(x,y) in enumerate(zip(found,wanted,strict=True)):
        if i in (3,4,106):assert abs(x-float(y))<=2e-10
        else:approx(x,y)


def independent_balances(profiles,case,sample):
    a,b=state(case['scenario']),state(sample);t={k:q['value'] for k,q in sample['integrated_transfers'].items()}
    e={k:q['value'] for k,q in sample['event_totals'].items()};p=case['scenario']['parameters']
    ca=p['air_volume_per_floor_area']['value']*p['air_capacity_density']['value']*profiles['exchange_profile'].values['air_heat_capacity']
    latent=profiles['exchange_profile'].values['latent_heat'];carbon=lambda y:fsum((*y[:3],*y[5:55]))
    material=(-t['incoming_capacity_heat'],t['maintenance_capacity_heat'],t['removal_capacity_heat'],e['canopy_sensible_energy'])
    out={
        'carbohydrate':fsum((carbon(b)-carbon(a),-t['photosynthesis'],*[t[k] for k in tuple(model.short.FLUX_UNITS)[1:8]],e['leaf'],e['stem_root'],e['fruit_carbohydrate'])),
        'number':fsum((fsum(b[55:105])-fsum(a[55:105]),-t['fruit_number_inflow'],t['terminal_fruit_number'],e['fruit_number'])),
        'canopy_sensible':fsum((b[105]-a[105],-t['canopy_external_heat'],t['canopy_to_air_sensible'],t['canopy_to_vapor_latent'],*material)),
        'air_sensible':fsum((ca*(b[106]-a[106]),-t['air_external_sensible_heat'],-t['canopy_to_air_sensible'])),
        'vapor_and_water_boundaries':fsum((b[107]-a[107],-t['canopy_to_air_vapor'],-t['air_external_vapor'])),
        'crop_capacity':fsum((p['leaf_heat_capacity']['value']*profiles['growth_profile'].values['sla']*(b[1]-a[1]),-t['capacity_allocation'],t['capacity_maintenance'],t['capacity_removal'],e['canopy_capacity'])),
        'reduced_energy':fsum((b[105]-a[105],ca*(b[106]-a[106]),latent*(b[107]-a[107]),-t['canopy_external_heat'],-t['air_external_sensible_heat'],-latent*t['air_external_vapor'],*material))}
    return out


@pytest.mark.parametrize('index',range(9))
def test_independent_decimal_automatic_trajectories_event_journals_and_seven_global_balances(profiles,index):
    case=REFERENCE['cases'][index];r=case_run(profiles,case);expected=case['expected_decimal']
    for actual,wanted in zip(r['samples'],expected['samples'],strict=True):
        assert actual['step_index']==wanted['step_index'] and actual['elapsed_seconds']==float(wanted['elapsed_seconds'])
        assert actual['event_count']==wanted['event_count'];state_equal(state(actual),wanted['state'])
        for key in ('integrated_transfers','event_totals','derived'):
            for k,y in wanted[key].items():approx(actual[key][k]['value'],y)
        assert abs(actual['derived']['canopy_temperature']['value']-float(wanted['derived']['canopy_temperature']))<=2e-10
        for k,v in independent_balances(profiles,case,actual).items():
            limit={'carbohydrate':1e-7,'number':1e-12,'vapor_and_water_boundaries':1e-13,'crop_capacity':1e-8}.get(k,1e-7)
            assert abs(v)<=limit,(case['case_id'],k,v)
            assert abs(actual['balance_residuals'][k]['value'])<=actual['balance_budgets'][k]['value']
    for actual,wanted in zip(r['events'],expected['events'],strict=True):
        assert actual['step_index']==wanted['step_index'] and actual['elapsed_seconds']==float(wanted['elapsed_seconds'])
        m=actual['management'];state_equal(state(m['before']['scenario']),wanted['before']);state_equal(state(m['after']['scenario']),wanted['after'])
        for k,v in wanted['removed_totals'].items():
            q=m['removed'][k];approx(fsum(x['value'] for x in q) if isinstance(q,list) else q['value'],v)


def metrics(sample):
    d=lambda v:Decimal(str(v));y=sample['state'] if 'state' in sample else state(sample)
    value=lambda q:q['value'] if isinstance(q,dict) else q
    return {'canopy_temperature':d(value(sample['derived']['canopy_temperature'])),'air_temperature':d(y[106]),
        'air_vapor_mass':d(y[107]),'temperature_filtered_24h':d(y[3]),'temperature_sum':d(y[4]),
        'buffer':d(y[0]),'fruit_carbohydrate':sum(map(d,y[5:55])),
        **{k:d(value(sample['integrated_transfers'][k])) for k in ('canopy_to_air_sensible','canopy_to_vapor_latent','canopy_to_air_vapor')}}


@pytest.mark.parametrize('index',(1,2,3))
def test_step_halving_against_independent_fine_trajectory_keeps_event_time(profiles,index):
    case=REFERENCE['cases'][index]
    with localcontext() as context:
        context.prec=80;target=metrics(case['fine_32s_dt0_25_decimal']['samples'][-1]);errors=[]
        for dt in (8,4,2):
            r=case_run(profiles,case,dt);assert r['events'][0]['elapsed_seconds']==16
            actual=metrics(r['samples'][-1]);errors.append({k:abs(v-target[k]) for k,v in actual.items()})
        for k in target:
            for coarse,fine in zip(errors,errors[1:]):assert coarse[k]>8*fine[k]>0,(case['case_id'],k)


def test_selection_changes_only_outputs_not_state_or_inventory(profiles):
    a=run(profiles);b=run(profiles,outputs=list(range(17)))
    for k in ('last_confirmed','events','integrated_transfers','event_totals'):assert a[k]==b[k]
    assert a['input_sha256']!=b['input_sha256'] and a['calculation_sha256']!=b['calculation_sha256']


def test_actual_kernel_calls_use_constant_inputs_and_dynamic_shared_clock(profiles,monkeypatch):
    rhs=model.joint.evaluate_rhs;seen=[]
    def record(**kw):seen.append(deepcopy(kw['scenario']));return rhs(**kw)
    monkeypatch.setattr(model.joint,'evaluate_rhs',record);r=run(profiles)
    for s in seen:
        for k in ('forcing','relative_growth_rate','parameters','removals','fruit_entry'):assert s[k]==r['scenario'][k]
    assert seen[-1]['plant_state']['temperature_sum']['value']>seen[0]['plant_state']['temperature_sum']['value']
    assert seen[-1]['plant_state']['temperature_filtered_24h']!=seen[0]['plant_state']['temperature_filtered_24h']
    assert seen[-1]['plant_state']['leaf']!=seen[0]['plant_state']['leaf']


@pytest.mark.parametrize('dt,count',[(True,1),('2',1),(None,1),(0,1),(-1,1),(float('nan'),1),(float('inf'),1),
    (10**400,1),(2,True),(2,0),(2,4097),(2,1.5),(601,1),(300.1,2)])
def test_preflight_step_and_horizon_limits(profiles,dt,count):
    with pytest.raises(model.BoundaryHold) as held:run(profiles,events=[],outputs=[0,count],dt=dt,count=count)
    assert held.value.last_confirmed is None and held.value.failed_phase=='input'


@pytest.mark.parametrize('outputs',[None,(),[],[0],[0,True,16],[0,8.0,16],[0,16,8],[0,8,8,16],[-1,16],[0,17],[1,16],[0,8]])
def test_preflight_output_grid_shape(profiles,outputs):
    with pytest.raises(model.BoundaryHold) as held:
        model.integrate_events(scenario=PREVIOUS['programs'][0]['scenario'],events=[],output_steps=outputs,step_seconds=2,step_count=16,**profiles)
    assert held.value.last_confirmed is None and held.value.samples==held.value.events==[]


@pytest.mark.parametrize('mutation',('type','closed','negative','late','boolean','fractional','unordered','duplicate-index','duplicate-id','event-unit','event-closed','event-origin','event-fraction','too-many'))
def test_preflight_scheduled_event_shape_identity_and_quantities(profiles,mutation,monkeypatch):
    e=deepcopy(PREVIOUS['programs'][0]['event']);events=[{'step_index':8,'event':e}]
    if mutation=='type':events=tuple(events)
    elif mutation=='closed':events[0]['time']=16
    elif mutation=='negative':events[0]['step_index']=-1
    elif mutation=='late':events[0]['step_index']=17
    elif mutation=='boolean':events[0]['step_index']=True
    elif mutation=='fractional':events[0]['step_index']=8.5
    elif mutation in ('unordered','duplicate-index','duplicate-id'):
        other=deepcopy(events[0]);other['step_index']={'unordered':7,'duplicate-index':8,'duplicate-id':9}[mutation]
        if mutation!='duplicate-id':other['event']['input_id']+='-other'
        events.append(other)
    elif mutation=='event-unit':e['values']['leaf']['unit']='g'
    elif mutation=='event-closed':e['extra']=0
    elif mutation=='event-origin':e['origin']='farm_observation'
    elif mutation=='event-fraction':e['values']['fruit_fraction'][0]['value']=1.1
    elif mutation=='too-many':events*=129
    def forbidden(**kw):pytest.fail('malformed schedule reached RHS')
    monkeypatch.setattr(model.joint,'evaluate_rhs',forbidden)
    with pytest.raises(model.BoundaryHold) as held:run(profiles,events=events)
    assert held.value.failed_phase=='input' and held.value.last_confirmed is None


@pytest.mark.parametrize('name',('growth_profile','cohort_profile','transport_profile','exchange_profile'))
def test_wrong_profile_has_no_confirmed_prefix(profiles,name):
    with pytest.raises(model.BoundaryHold) as held:run({**profiles,name:None})
    assert held.value.failed_phase=='initial' and held.value.last_confirmed is None


@pytest.mark.parametrize('amount',(50000,50001,49999))
def test_actual_leaf_event_failure_preserves_boundary_state_without_failed_journal(profiles,amount):
    e=deepcopy(PREVIOUS['programs'][0]['event']);e['values']['leaf']['value']=amount
    with pytest.raises(model.BoundaryHold) as held:run(profiles,events=[{'step_index':0,'event':e}])
    assert held.value.failed_phase=='event' and held.value.last_confirmed['phase']=='initial'
    assert held.value.last_confirmed_elapsed_seconds==0 and held.value.samples==held.value.events==[]


def test_late_real_overdraw_keeps_confirmed_outputs_and_prior_event(profiles):
    case=deepcopy(REFERENCE['cases'][6]);case['events'][-1]['event']['values']['leaf']['value']=50000
    original=deepcopy(case)
    with pytest.raises(model.BoundaryHold) as held:case_run(profiles,case)
    h=held.value;assert h.failed_phase=='event' and h.step_index==16 and h.last_confirmed_elapsed_seconds==32
    assert h.last_confirmed['phase']=='step-end' and h.last_confirmed['event_count']==2
    assert [s['step_index'] for s in h.samples]==[0,8] and [e['step_index'] for e in h.events]==[0,8]
    assert case==original


def test_actual_trial_temperature_domain_failure_keeps_initial_output(profiles):
    s=deepcopy(PREVIOUS['programs'][0]['scenario']);s['forcing']['canopy_external_heat']['value']=1e7
    with pytest.raises(model.BoundaryHold,match='TEMPERATURE_HOLD') as held:run(profiles,s,events=[])
    assert held.value.step_index==1 and held.value.failed_phase=='interval'
    assert held.value.last_confirmed_elapsed_seconds==0 and len(held.value.samples)==1


@pytest.mark.parametrize('dt',(5e-324,1e-200))
def test_real_lost_or_underflow_step_is_not_clamped(profiles,dt):
    with pytest.raises(model.BoundaryHold,match='NUMERIC_HOLD') as held:run(profiles,events=[],outputs=[0,1],dt=dt,count=1)
    assert held.value.failed_phase=='interval' and held.value.last_confirmed_elapsed_seconds==0


@pytest.mark.parametrize('target',('step','event'))
def test_global_inventory_failure_does_not_publish_a_trial_or_failed_event(profiles,monkeypatch,target):
    if target=='step':
        original=model.short.integrate
        def corrupt(**kw):
            r=original(**kw);r['integrated_transfers']['photosynthesis']['value']+=1;return r
        monkeypatch.setattr(model.short,'integrate',corrupt)
    else:
        original=model.management.apply_management
        def corrupt(**kw):
            r=original(**kw);r['removed']['canopy_sensible_energy']['value']+=1;return r
        monkeypatch.setattr(model.management,'apply_management',corrupt)
    with pytest.raises(model.BoundaryHold,match='BALANCE_HOLD') as held:run(profiles)
    h=held.value;assert h.failed_phase=='global-'+target+'-balance' and h.events==[]
    assert h.last_confirmed_elapsed_seconds==(0 if target=='step' else 16)
    assert len(h.samples)==1 and h.last_confirmed['event_count']==0


def test_nonzero_cumulative_increment_lost_to_rounding_is_a_hold():
    with pytest.raises(model.BoundaryHold,match='NUMERIC_HOLD'):
        model._add({'x':{'value':1e100,'unit':'1'}},{'x':{'value':1,'unit':'1'}},{'x':'1'})


def test_maximum_selected_outputs_and_events_are_bounded_and_ordered(profiles):
    zero=deepcopy(PREVIOUS['cases'][0]['event']);events=[]
    for i in range(128):
        e=deepcopy(zero);e['input_id']=f'synthetic-max-event-{i}';events.append({'step_index':i,'event':e})
    outputs=[*range(511),512];r=run(profiles,events=events,outputs=outputs,dt=.0625,count=512)
    assert len(r['samples'])==512 and len(r['events'])==128 and r['last_confirmed']['event_count']==128
    assert r['numerical']['rhs_evaluations']==2817 and r['last_confirmed']['elapsed_seconds']==32
    assert all(q['value']==0 for q in r['event_totals'].values())
    assert [e['step_index'] for e in r['events']]==list(range(128))
    with pytest.raises(model.BoundaryHold,match='TIME_HOLD'):run(profiles,events=[],outputs=list(range(513)),dt=.0625,count=512)


def test_deterministic_identity_binds_profiles_code_numerics_selection_and_payload(profiles):
    r=run(profiles);assert r==run(profiles)
    assert r['code_sha256']==sha256((ROOT/'backend/app/crop_climate_joint_boundary.py').read_bytes()).hexdigest()
    assert r['short_code_sha256']==model.short.CODE_SHA256 and r['management_code_sha256']==model.management.CODE_SHA256
    assert r['rhs_code_sha256']==model.joint.CODE_SHA256 and r['component_code_sha256']==dict(model.joint.COMPONENT_CODE_SHA256)
    first=model.joint.evaluate_rhs(scenario=r['scenario'],**profiles)
    assert r['profile_sha256']==first['profile_sha256'] and r['policy_sha256']==first['policy_sha256']
    bound={k:r[k] for k in ('model_version','code_sha256','short_code_sha256','management_code_sha256','rhs_code_sha256',
        'component_code_sha256','input_sha256','initial_rhs_calculation_sha256','numerical')}
    assert r['calculation_sha256']==model._hash(bound)
    payload={k:r[k] for k in ('samples','events','last_confirmed','integrated_transfers','event_totals')}
    assert r['result_sha256']==model._hash(payload)
    assert r['input_sha256']==model._hash({'scenario':r['scenario'],'events':r['scheduled_events'],'output_steps':r['output_steps'],'numerical':r['numerical']})
    s=deepcopy(r['scenario']);s['forcing']['canopy_external_heat']['value']+=1
    assert run(profiles,s)['calculation_sha256']!=r['calculation_sha256']
    assert run(profiles,dt=1,count=32,outputs=[0,16,32],events=[{'step_index':16,'event':PREVIOUS['programs'][0]['event']}])['calculation_sha256']!=r['calculation_sha256']
    assert r['clock_contract']=='elapsed-grid-shared-rk4-events-v1' and r['claim_scope']=='synthetic_joint_crop_climate_boundary_driver_only'
