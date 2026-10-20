"""Independent piecewise CO2/Solar programs and confirmed-boundary failures."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
from importlib import import_module
import json
from math import fsum
from pathlib import Path

import pytest

from app import crop_greenhouse_co2_integration as short
from app import crop_climate_joint_management as old_management
from test_crop_greenhouse_co2_management import profiles, state
from test_crop_greenhouse_co2_integration import metrics, fine_metrics
from test_crop_climate_joint_boundary import independent_balances
from test_crop_greenhouse_solar_program import radiation_balances

ROOT=Path(__file__).resolve().parents[2]
DOCUMENT=json.loads((ROOT/'fixtures/crop-greenhouse-co2-program-reference-cases-v1.json').read_bytes())
CASES=DOCUMENT['cases'];BY_ID={c['case_id']:c for c in CASES}


@pytest.fixture(scope='module')
def model():return import_module('app.crop_greenhouse_co2_program')


def run(model,profiles,case=None,dt=2,**changes):
    c=BY_ID['weather-multiple'] if case is None else case
    scale=lambda n:int(n*c['step_seconds']/dt)
    forcing=deepcopy(c['forcing_program']);events=deepcopy(c['events'])
    if dt!=c['step_seconds']:
        for row in forcing+events:row['step_index']=scale(row['step_index'])
    args=dict(scenario=c['scenario'],forcing_program=forcing,events=events,
        output_steps=[scale(i) for i in c['output_steps']],step_seconds=dt,step_count=scale(c['step_count']),**profiles)
    args.update(changes);return model.integrate_events(**args)


@pytest.fixture(scope='module')
def results(model,profiles):return {c['case_id']:run(model,profiles,c) for c in CASES}


def compare_state(actual,expected):
    for a,b in zip(state(actual),expected,strict=True):assert a==pytest.approx(float(b),rel=5e-12,abs=5e-14)


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['case_id'])
def test_independent_program_states_transfers_events_and17_global_balances(results,profiles,case):
    r=results[case['case_id']];a=state(case['scenario']);carbon=lambda y:fsum((*y[:3],*y[5:55]))
    for sample,wanted in zip(r['samples'],case['expected_decimal']['samples'],strict=True):
        assert sample['step_index']==wanted['step_index'] and sample['elapsed_seconds']==float(wanted['elapsed_seconds'])
        assert sample['forcing_step_index']==wanted['forcing_step_index'] and sample['event_count']==wanted['event_count']
        compare_state(sample,wanted['state'])
        for block in ('integrated_transfers','event_totals','derived'):
            for key,value in wanted[block].items():assert sample[block][key]['value']==pytest.approx(float(value),rel=5e-12,abs=5e-14),(case['case_id'],block,key)
        assert abs(sample['derived']['canopy_temperature']['value']-float(wanted['derived']['canopy_temperature']))<=2e-10
        assert len(sample['balance_residuals'])==17
        for key,q in sample['balance_residuals'].items():assert abs(q['value'])<=sample['balance_budgets'][key]['value']
        for key,value in independent_balances(profiles,case,sample).items():
            assert abs(value)<={'number':1e-12,'vapor_and_water_boundaries':1e-13,'crop_capacity':1e-8}.get(key,1e-7)
        t={k:q['value'] for k,q in sample['integrated_transfers'].items()};e=sample['event_totals'];b=state(sample)
        assert abs(fsum((b[108],-a[108],*(-t[k] for k in short.CO2_FIELDS))))<=1e-7
        removed=fsum(e[k]['value'] for k in ('leaf','stem_root','fruit_carbohydrate'))
        assert abs(fsum((b[108],-a[108],44/30*fsum((carbon(b),-carbon(a),removed,t['removal_leaf'],t['removal_stem_root'],t['terminal_fruit_carbohydrate'])),-t['co2_ventilation_to_air'],-t['co2_external_to_air'])))<=1e-7
        assert max(map(abs,radiation_balances(sample['integrated_transfers'])))<=1e-7
        elapsed=sample['elapsed_seconds'];forcing=case['forcing_program'];external=0
        for i,row in enumerate(forcing):
            start=row['step_index']*case['step_seconds'];end=forcing[i+1]['step_index']*case['step_seconds'] if i+1<len(forcing) else elapsed
            external+=max(0,min(elapsed,end)-start)*row['co2']['forcing']['external_co2_flux']['value']
        assert abs(t['co2_external_to_air']-external)<=1e-12
    for event,wanted in zip(r['events'],case['expected_decimal']['events'],strict=True):
        compare_state(event['management']['before']['scenario'],wanted['before'])
        compare_state(event['management']['after']['scenario'],wanted['after'])
        for key,value in wanted['removed_totals'].items():
            q=event['management']['removed'][key];found=fsum(v['value'] for v in q) if isinstance(q,list) else q['value']
            assert found==pytest.approx(float(value),rel=5e-12,abs=5e-14)
        assert event['management']['before']['derived']['crop_co2_ppm']==event['management']['after']['derived']['crop_co2_ppm']
    assert r['G0_G4']=='not_assessed' and r['scope']=='software_research_only'


@pytest.mark.parametrize('name',['weather-mid','weather-multiple','weather-no-events'])
def test_all96_registered_step_halving_ratios_above8(model,profiles,results,name):
    c=BY_ID[name]
    with localcontext() as context:
        context.prec=80;target=fine_metrics(c['fine_32s_dt0_25_decimal']['samples'][-1])
        rows=[run(model,profiles,c,dt=8),run(model,profiles,c,dt=4),results[name]]
        errors=[[abs(Decimal(str(v))-wanted) for v,wanted in zip(metrics(r['last_confirmed'],r['integrated_transfers']),target,strict=True)] for r in rows]
        for column in range(16):
            a,b,d=(row[column] for row in errors)
            assert a>b>d>0 and a/b>8 and b/d>8,(name,column,a,b,d)


def test_independent_reference_pins():
    assert DOCUMENT['generator_sha256']==sha256((ROOT/'research/crop-greenhouse-co2-program-reference.py').read_bytes()).hexdigest()
    for name,digest in DOCUMENT['input_sha256'].items():assert sha256((ROOT/name).read_bytes()).hexdigest()==digest


def test_actual_calls_order_boundary_forcing_and_unchanged_source(model,profiles,monkeypatch):
    original=model.stage.rhs.evaluate_rhs;apply=model.management.apply_management;calls=[];events=[]
    def rhs(**args):
        result=original(**args);calls.append(({k:deepcopy(args[k]) for k in ('scenario','solar','ventilation','co2')},result));return result
    def event(**args):
        events.append({k:deepcopy(args[k]) for k in ('scenario','solar','ventilation','co2','event')});return apply(**args)
    def forbidden(**args):raise AssertionError('old fixed-ppm management')
    monkeypatch.setattr(model.stage.rhs,'evaluate_rhs',rhs);monkeypatch.setattr(model.management,'apply_management',event)
    monkeypatch.setattr(old_management,'apply_management',forbidden)
    c=deepcopy(BY_ID['weather-multiple']);saved=deepcopy(c);r=run(model,profiles,c)
    assert c==saved and r['scenario']['forcing']==c['scenario']['forcing']
    assert len(calls)==r['numerical']['coupled_rhs_evaluations']==1+5*16+2*3+3
    assert len(events)==3 and r['numerical']['extra_validation_RHS_evaluations']==0
    assert all(a['scenario']['forcing']==c['scenario']['forcing'] for a,_ in calls)
    for e,index in zip(events,(0,8,16),strict=True):
        active=next(row for row in reversed(c['forcing_program']) if row['step_index']<=index)
        assert all(e[k]==active[k] for k in ('solar','ventilation','co2'))
    for row in c['forcing_program'][1:]:
        i=next(i for i,(a,_) in enumerate(calls) if a['solar']['input_id']==row['solar']['input_id'])
        assert calls[i][0]['scenario']['climate_state']==calls[i-1][1]['scenario']['climate_state']
    assert r['last_confirmed']['forcing_step_index']==16


def test_no_event_constant_program_matches_accepted_short(model,profiles,results):
    c=BY_ID['no-events'];r=results['no-events'];f=c['forcing_program'][0]
    old=short.integrate(scenario=c['scenario'],**{k:f[k] for k in ('solar','ventilation','co2')},step_seconds=2,step_count=16,**profiles)
    assert state(r['last_confirmed'])==state(old['samples'][-1])
    assert r['integrated_transfers']==old['integrated_transfers']


def test_output_selection_replay_and_identity(model,profiles,results):
    a=results['weather-multiple'];b=run(model,profiles,output_steps=[0,16])
    assert a==run(model,profiles) and a['calculation_sha256']!=b['calculation_sha256']
    for key in ('last_confirmed','integrated_transfers','event_totals','events'):assert a[key]==b[key]


def test_version2_journal_keeps_post_rhs_identity_without_transient_payload(results):
    r=results['weather-multiple']
    assert r['model_version']=='joint-co2-solar-forcing-management-program-research-v2'
    assert r['journal_schema_version']=='joint-co2-solar-event-journal-v2'
    for row in r['events']:
        m=row['management'];assert 'after_rhs' not in m
        assert m['after_calculation_sha256']==m['after']['calculation_sha256']
        assert m['before_calculation_sha256']==m['before']['calculation_sha256']


@pytest.mark.parametrize('failure',['initial','forcing','event','step-balance','event-balance','interval'])
def test_failures_preserve_detached_confirmed_prefix(model,profiles,monkeypatch,failure):
    c=deepcopy(BY_ID['weather-multiple']);p=dict(profiles)
    if failure=='initial':p['growth_profile']=None
    elif failure=='forcing':c['forcing_program'][2]['solar']['values']['outdoor_global_radiation']['value']=-1
    elif failure=='event':c['events'][1]['event']['values']['leaf']['value']=1e15
    elif failure=='interval':c['forcing_program'][0]['co2']['forcing']['external_co2_flux']['value']=-10000
    else:
        original=model._balances
        def fail(*args):
            if args[6]==8 and args[8]==(1 if failure=='step-balance' else 2):raise model.ProgramHold('BALANCE_HOLD: injected global failure')
            return original(*args)
        monkeypatch.setattr(model,'_balances',fail)
    saved=deepcopy(c)
    with pytest.raises(model.ProgramHold) as caught:run(model,p,c)
    held=caught.value;assert c==saved
    if failure=='initial':assert held.last_confirmed is None and held.samples==held.events==[];return
    assert held.failed_phase=={'forcing':'forcing','event':'event','step-balance':'global-step-balance',
        'event-balance':'global-event-balance','interval':'interval'}[failure]
    index={'interval':0,'step-balance':7}.get(failure,8)
    assert held.last_confirmed['step_index']==index and held.last_confirmed['event_count']==1
    assert len(held.events)==1
    if failure=='forcing':assert held.last_confirmed['forcing_step_index']==4
    if failure in ('event','event-balance'):assert held.last_confirmed['forcing_step_index']==8
    if failure=='interval':assert held.inner_failed_stage=='k2'
    assert all(row['step_index']<8 for row in held.samples)
    saved_event=deepcopy(held.events[0]);saved_state=deepcopy(held.last_confirmed)
    held.samples[0]['plant_state']['leaf']['value']=-1
    assert held.events[0]==saved_event and held.last_confirmed==saved_state


@pytest.mark.parametrize('fault',['empty','first','duplicate','reverse','bool','outside','too-many','extra','block','origin','missing','events','outputs'])
def test_closed_forcing_schedule_and_existing_limits(model,profiles,fault):
    c=deepcopy(BY_ID['weather-multiple']);f=c['forcing_program']
    if fault=='empty':f.clear()
    elif fault=='first':f[0]['step_index']=1
    elif fault=='duplicate':f[1]['step_index']=0
    elif fault=='reverse':f.reverse()
    elif fault=='bool':f[1]['step_index']=True
    elif fault=='outside':f[-1]['step_index']=17
    elif fault=='too-many':f[:]=[deepcopy(f[0]) for _ in range(513)]
    elif fault=='extra':f[0]['unused']=0
    elif fault=='block':f[0]['solar']=[]
    elif fault=='origin':f[-1]['co2']['origin']='reference_calculation'
    elif fault=='missing':del f[0]['co2']
    elif fault=='events':c['events']=[deepcopy(c['events'][0]) for _ in range(129)]
    else:c['output_steps']=[0]*513
    saved=deepcopy(c)
    with pytest.raises(model.ProgramHold) as caught:run(model,profiles,c)
    assert caught.value.last_confirmed is None and c==saved


def test_maximum512_forcing_rows_outputs_and128_events(model,profiles):
    c=deepcopy(BY_ID['weather-multiple']);events=[];forcing=[];indices=[*range(511),512]
    for i in range(128):
        e=deepcopy(c['events'][0]);e['step_index']=i;e['event']['input_id']='co2-max-event-'+str(i)
        v=e['event']['values'];v['leaf']['value']=v['stem_root']['value']=0
        for q in v['fruit_fraction']:q['value']=0
        events.append(e)
    for i in indices:
        row=deepcopy(c['forcing_program'][0]);row['step_index']=i;forcing.append(row)
    r=run(model,profiles,forcing_program=forcing,events=events,output_steps=indices,step_seconds=.0625,step_count=512)
    assert len(r['samples'])==len(r['forcing_program'])==512 and len(r['events'])==128
    assert r['last_confirmed']['elapsed_seconds']==32 and r['last_confirmed']['forcing_step_index']==512
    assert all(q['value']==0 for q in r['event_totals'].values())
    assert r['numerical']['coupled_rhs_evaluations']==3328
