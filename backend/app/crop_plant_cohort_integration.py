"""Bounded deterministic research integration of plant and fruit compartments."""
from datetime import datetime, timedelta
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum, isfinite, ulp
from pathlib import Path
import platform
import re

from . import crop_growth_rates as plant
from . import crop_fruit_cohorts as fruit
from . import crop_fruit_allocation as allocation
from . import crop_fruit_transport as transport
from . import crop_plant_cohort_rates as coupled


INTEGRATOR_VERSION = 'crop-plant-cohort-rk4-research-v1'
PLANT = tuple(coupled.PLANT_UNITS)
ARRAY_UNITS = {k:fruit.ARRAY_UNITS[k] for k in ('fruit_number','fruit_carbohydrate')}
FLUX = ('photosynthesis','growth_respiration','maintenance_leaf','maintenance_stem_root','maintenance_fruit',
        'removal_leaf','removal_stem_root','terminal_carbohydrate','terminal_number','entry_number',
        'event_carbohydrate','event_number')
FLUX_UNITS = {k:('fruits_equivalent/m2_floor' if k in ('terminal_number','entry_number','event_number')
                 else plant.MASS_UNIT) for k in FLUX}
CODE_HASHES = {name:sha256(Path(path).read_bytes()).hexdigest() for name,path in (
    ('integrator',__file__),('coupled',coupled.__file__),('plant',plant.__file__),
    ('cohorts',fruit.__file__),('allocation',allocation.__file__),('transport',transport.__file__))}


class PlantCohortIntegrationHold(ValueError):
    """A malformed or unbounded research program rejected before integration."""


class _EvaluationHold(Exception):
    def __init__(self,reason,at,phase):
        self.reason,self.at,self.phase=reason,at,phase


def _need(condition,reason):
    if not condition:raise PlantCohortIntegrationHold(reason)


def _q(value,unit):
    return {'value':value,'unit':unit}


def _hash(document):
    return sha256(json.dumps(document,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _utc(value):
    _need(type(value) is str and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',value),
          'TIME_HOLD: canonical whole-second UTC required')
    try:return datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc:raise PlantCohortIntegrationHold('TIME_HOLD: invalid UTC') from exc


def _stamp(at):
    return at.isoformat().replace('+00:00','Z')


def _quantity(record,unit):
    _need(type(record) is dict and set(record)=={'value','unit'},'INPUT_HOLD: closed quantity required')
    _need(record['unit']==unit,'UNIT_HOLD: unexpected quantity unit')
    _need(type(record['value']) in (int,float),'INPUT_HOLD: numeric value required')
    try:value=float(record['value'])
    except OverflowError as exc:raise PlantCohortIntegrationHold('INPUT_HOLD: unrepresentable input') from exc
    _need(isfinite(value) and value>=0,'INPUT_HOLD: finite nonnegative value required')
    return _q(value,unit)


def _block(block,scalars,arrays=None):
    arrays=arrays or {}
    _need(type(block) is dict and set(block)=={'input_id','origin','values'},'INPUT_HOLD: closed block required')
    _need(type(block['input_id']) is str and 0<len(block['input_id'])<=256 and bool(block['input_id'].strip())
          and type(block['origin']) is str and block['origin'] in ('synthetic','reference_calculation','reference_observation'),
          'INPUT_HOLD: bounded provenance required')
    _need(type(block['values']) is dict and set(block['values'])==set(scalars)|set(arrays),
          'INPUT_HOLD: missing or unexpected quantity')
    values={k:_quantity(block['values'][k],unit) for k,unit in scalars.items()}
    for k,unit in arrays.items():
        raw=block['values'][k]
        _need(type(raw) is list and len(raw)==50,'INPUT_HOLD: exact compartment array required')
        values[k]=[_quantity(q,unit) for q in raw]
        if k=='fruit_fraction':_need(all(q['value']<=1 for q in values[k]),'INPUT_HOLD: fraction exceeds one')
    return {'input_id':block['input_id'],'origin':block['origin'],'values':values}


def _prepare(initial_state,segments,events,output_times,solver):
    for records,limit in ((segments,128),(events,128),(output_times,512)):
        _need(type(records) is list and len(records)<=limit,'RESOURCE_HOLD: bounded lists required')
    _need(bool(segments) and len(output_times)>=2,'INPUT_HOLD: period/output endpoints required')
    _need(type(solver) is dict and set(solver)=={'method','max_step_seconds','max_steps','roundoff_rule'}
          and solver['method']=='rk4-fixed-v1' and solver['roundoff_rule']=='64-ulp-per-operation-v1',
          'SOLVER_HOLD: pinned closed solver required')
    _need(type(solver['max_step_seconds']) is int and 1<=solver['max_step_seconds']<=3600
          and type(solver['max_steps']) is int and 1<=solver['max_steps']<=10000,
          'RESOURCE_HOLD: explicit positive integer budgets required')
    initial=_block(initial_state,coupled.PLANT_UNITS,ARRAY_UNITS)
    normalized=[];previous=None
    for segment in segments:
        _need(type(segment) is dict and set(segment)=={'start','end','forcing','removals','fruit_entry','relative_growth_rate'},
              'INPUT_HOLD: closed interval required')
        begin,end=_utc(segment['start']),_utc(segment['end'])
        _need(begin<end and (previous is None or begin==previous),'TIME_HOLD: noncontinuous intervals')
        normalized.append({'start':segment['start'],'end':segment['end'],
            'forcing':_block(segment['forcing'],plant.FORCING_UNITS),
            'removals':_block(segment['removals'],coupled.REMOVAL_UNITS),
            'fruit_entry':_block(segment['fruit_entry'],coupled.ENTRY_UNITS),
            'relative_growth_rate':_block(segment['relative_growth_rate'],{}, {'fruit_relative_growth_rate':'1/s'})})
        previous=end
    begin,end=_utc(normalized[0]['start']),previous
    _need((end-begin).total_seconds()<=86400,'RESOURCE_HOLD: research period exceeds one day')
    outputs=[_utc(t) for t in output_times]
    _need(outputs[0]==begin and outputs[-1]==end and all(a<b for a,b in zip(outputs,outputs[1:])),
          'TIME_HOLD: ordered outputs must cover exact period')
    pulses=[];prior=None
    for event in events:
        _need(type(event) is dict and set(event)=={'at','removals'},'INPUT_HOLD: closed event required')
        at=_utc(event['at'])
        _need(begin<=at<=end and (prior is None or prior<at),'TIME_HOLD: unordered or external event')
        pulses.append({'at':event['at'],'removals':_block(event['removals'],
            {'leaf':plant.MASS_UNIT,'stem_root':plant.MASS_UNIT},{'fruit_fraction':'1'})});prior=at
    boundaries=sorted(set(outputs)|{_utc(s['end']) for s in normalized}|{_utc(e['at']) for e in pulses})
    h=solver['max_step_seconds']
    planned=sum((int((b-a).total_seconds())+h-1)//h for a,b in zip(boundaries,boundaries[1:]))
    _need(planned<=solver['max_steps'],'RESOURCE_HOLD: planned steps exceed budget')
    return {'initial_state':initial,'segments':normalized,'events':pulses,
            'output_times':list(output_times),'solver':dict(solver)},boundaries,planned


def _state(y):
    return {**{k:_q(v,coupled.PLANT_UNITS[k]) for k,v in zip(PLANT,y[:5],strict=True)},
            **{k:[_q(v,ARRAY_UNITS[k]) for v in values] for k,values in (
                ('fruit_number',y[5:55]),('fruit_carbohydrate',y[55:105]))}}


def _guard(y,at,phase):
    if not all(isfinite(v) for v in y):raise _EvaluationHold('NUMERIC_HOLD: nonfinite state/accumulation',at,phase)
    if any(v<0 for v in y):raise _EvaluationHold('DEPLETED_STATE_HOLD: negative trial state/accumulation',at,phase)
    if any(c>0 and n==0 for n,c in zip(y[5:55],y[55:105],strict=True)):
        raise _EvaluationHold('FRUIT_COHORT_STATE_HOLD: carbohydrate without number',at,phase)


def _ledger(y,seed,operations,at):
    try:
        carbon=fsum([*y[:3],*y[55:105],*[-v for v in seed[:3]],*[-v for v in seed[55:105]],-y[105],*y[106:113],y[115]])
        number=fsum([*y[5:55],*[-v for v in seed[5:55]],-y[114],y[113],y[116]])
        carbon_scale=max(1.0,fsum([*seed[:3],*seed[55:105]]),fsum([*y[:3],*y[55:105]]),*y[105:113],y[115])
        number_scale=max(1.0,fsum(seed[5:55]),fsum(y[5:55]),y[113],y[114],y[116])
        budgets=[64*(operations+1)*ulp(scale) for scale in (carbon_scale,number_scale)]
        if not all(isfinite(v) for v in (carbon,number,*budgets)) or abs(carbon)>budgets[0] or abs(number)>budgets[1]:
            raise _EvaluationHold('BALANCE_HOLD: unresolved accumulated number/carbon',at,'balance')
        return carbon,number,*budgets
    except (OverflowError,ValueError) as exc:
        raise _EvaluationHold('NUMERIC_HOLD: balance arithmetic failed',at,'balance') from exc


def integrate_plant_cohorts(*,initial_state,segments,events,output_times,growth_profile,cohort_profile,transport_profile,solver):
    """Advance an explicit short research program or preserve a diagnostic hold."""
    _need(type(growth_profile) is plant.ReferenceParameters and type(cohort_profile) is fruit.ReferenceFruitCohortParameters
          and type(transport_profile) is transport.ReferenceFruitTransportParameters,'PROFILE_HOLD: pinned profiles required')
    program,boundaries,planned=_prepare(initial_state,segments,events,output_times,solver)
    solver=program['solver']
    profile_hashes={k:p.sha256 for k,p in (('growth_profile',growth_profile),('cohort_profile',cohort_profile),('transport_profile',transport_profile))}
    blocks=[program['initial_state']]+[s[k] for s in program['segments'] for k in ('forcing','removals','fruit_entry','relative_growth_rate')]
    blocks += [e['removals'] for e in program['events']]
    manifest={'integrator_version':INTEGRATOR_VERSION,'rate_model_version':coupled.MODEL_VERSION,
        'profile_sha256':profile_hashes,'policy_sha256':allocation.POLICY_SHA256,'code_sha256':dict(CODE_HASHES),
        'solver':dict(solver),'time_rule':'UTC_POSIX_whole_seconds_v1','python_version':platform.python_version(),
        'temperature_sum_method':'analytic_piecewise_constant_fraction_v1','convergence':'not_evaluated_for_this_program',
        'origins':sorted({b['origin'] for b in blocks}),'input_ids':[b['input_id'] for b in blocks],
        'research_assumptions':list(coupled.ASSUMPTIONS)}
    manifest['input_sha256']=_hash({'program':program,'manifest':manifest})
    initial=program['initial_state']['values']
    y=[initial[k]['value'] for k in PLANT]+[q['value'] for k in ARRAY_UNITS for q in initial[k]]+[0.0]*len(FLUX)
    seed=list(y);at=boundaries[0];active=0;steps=0;event_count=0;frames=[];journal=[];last_confirmed=None
    pulses={_utc(e['at']):e for e in program['events']};requested=set(program['output_times'])
    clocks=[];total=Fraction.from_float(y[4])
    for segment in program['segments']:
        start,end=_utc(segment['start']),_utc(segment['end'])
        slope=Fraction.from_float(segment['forcing']['values']['canopy_temperature']['value'])/Fraction.from_float(growth_profile.values['seconds_per_day'])
        clocks.append((start,total,slope));total+=slope*int((end-start).total_seconds())
    calculated_id='calculated-state:'+_hash(program['initial_state'])

    def clock(vector,time,phase):
        result=list(vector);start,prefix,slope=clocks[active]
        try:result[4]=float(prefix+slope*Fraction.from_float((time-start).total_seconds()))
        except OverflowError as exc:raise _EvaluationHold('NUMERIC_HOLD: temperature sum overflow',time,phase) from exc
        return result

    def rhs(vector,time,phase):
        vector=clock(vector,time,phase);_guard(vector,time,phase);state=_state(vector);segment=program['segments'][active]
        plant_state={'input_id':calculated_id,'origin':'reference_calculation','values':{k:state[k] for k in PLANT}}
        fruit_state={'input_id':calculated_id,'origin':'reference_calculation','values':{
            **{k:state[k] for k in (*ARRAY_UNITS,*fruit.SCALAR_UNITS)},
            **segment['relative_growth_rate']['values']}}
        try:
            result=coupled.calculate_plant_cohort_rates(state=plant_state,cohort_state=fruit_state,
                forcing=segment['forcing'],removals=segment['removals'],fruit_entry=segment['fruit_entry'],
                growth_profile=growth_profile,cohort_profile=cohort_profile,transport_profile=transport_profile)
            if any(vector[j]>0 and result['vegetative_maintenance'][k]['value']==0
                   for j,k in ((1,'leaf'),(2,'stem_root'))):
                raise _EvaluationHold('NUMERIC_HOLD: positive vegetative maintenance underflow',time,phase)
            cohorts=result['cohorts']
            return [result['derivatives'][k]['value'] for k in PLANT]+[
                q['value'] for k in ARRAY_UNITS for q in cohorts['derivatives'][k]]+[
                result['photosynthesis']['value'],result['growth_respiration']['value'],
                result['vegetative_maintenance']['leaf']['value'],result['vegetative_maintenance']['stem_root']['value'],
                result['fruit_maintenance']['value'],result['removals']['leaf']['value'],result['removals']['stem_root']['value'],
                cohorts['terminal_outflow']['fruit_carbohydrate']['value'],cohorts['terminal_outflow']['fruit_number']['value'],
                segment['fruit_entry']['values']['fruit_number_inflow']['value'],0.0,0.0]
        except coupled.PlantCohortHold as exc:raise _EvaluationHold(str(exc),time,phase) from exc

    def snapshot(vector,time,operations):
        carbon,number,cb,nb=_ledger(vector,seed,operations,time)
        return {'at':_stamp(time),'state':_state(vector),
            'cumulative':{k:_q(v,FLUX_UNITS[k]) for k,v in zip(FLUX,vector[105:],strict=True)},
            'lai':_q(growth_profile.values['sla']*vector[1],'m2_leaf/m2_floor'),
            'fruit_carbohydrate_total':_q(fsum(vector[55:105]),plant.MASS_UNIT),
            'carbon_residual':_q(carbon,plant.MASS_UNIT),'carbon_residual_budget':_q(cb,plant.MASS_UNIT),
            'number_residual':_q(number,'fruits_equivalent/m2_floor'),'number_residual_budget':_q(nb,'fruits_equivalent/m2_floor')}

    try:
        for boundary in boundaries:
            while at<boundary:
                h=min(solver['max_step_seconds'],int((boundary-at).total_seconds()));half=at+timedelta(seconds=h/2);end=at+timedelta(seconds=h)
                k1=rhs(y,at,'rk4-k1');k2=rhs([v+h*d/2 for v,d in zip(y,k1,strict=True)],half,'rk4-k2')
                k3=rhs([v+h*d/2 for v,d in zip(y,k2,strict=True)],half,'rk4-k3')
                k4=rhs([v+h*d for v,d in zip(y,k3,strict=True)],end,'rk4-k4')
                try:candidate=[fsum((v,h*fsum((a,2*b,2*c,d))/6)) for v,a,b,c,d in zip(y,k1,k2,k3,k4,strict=True)]
                except (OverflowError,ValueError) as exc:raise _EvaluationHold('NUMERIC_HOLD: RK4 update failed',end,'step-end-arithmetic') from exc
                candidate=clock(candidate,end,'step-end');rhs(candidate,end,'step-end');_ledger(candidate,seed,steps+event_count+1,end)
                y,at=candidate,end;steps+=1;last_confirmed={**snapshot(y,at,steps+event_count),'phase':'step-end'}
            if active+1<len(program['segments']) and at==_utc(program['segments'][active]['end']):active+=1
            _guard(y,at,'boundary');candidate=list(y);event=pulses.get(at);removed=None
            if event:
                values=event['removals']['values'];removed={k:values[k] for k in ('leaf','stem_root')}
                if any(values[k]['value']>candidate[j] for j,k in enumerate(('leaf','stem_root'),start=1)):
                    raise _EvaluationHold('REMOVAL_EXCEEDS_STORAGE_HOLD: event exceeds organ state',at,'event')
                for j,k in enumerate(('leaf','stem_root'),start=1):candidate[j]-=values[k]['value']
                for name,offset in (('fruit_number',5),('fruit_carbohydrate',55)):
                    amounts=[y[offset+j]*f['value'] for j,f in enumerate(values['fruit_fraction'])]
                    if any(y[offset+j]>0 and f['value']>0 and amounts[j]==0 for j,f in enumerate(values['fruit_fraction'])):
                        raise _EvaluationHold('NUMERIC_HOLD: positive event removal underflow',at,'event')
                    for j,value in enumerate(amounts):candidate[offset+j]-=value
                    removed[name]=[_q(v,ARRAY_UNITS[name]) for v in amounts]
                try:
                    candidate[115]=fsum((y[115],values['leaf']['value'],values['stem_root']['value'],
                        *(q['value'] for q in removed['fruit_carbohydrate'])))
                    candidate[116]=fsum((y[116],*(q['value'] for q in removed['fruit_number'])))
                except (OverflowError,ValueError) as exc:raise _EvaluationHold('NUMERIC_HOLD: event accumulation overflow',at,'event') from exc
            rhs(candidate,at,'boundary-after-event' if event else 'boundary');_ledger(candidate,seed,steps+event_count+bool(event),at)
            if event:
                journal.append({'at':_stamp(at),'input_id':event['removals']['input_id'],'before':_state(y),'after':_state(candidate),'removed':removed});event_count+=1
            y=candidate;last_confirmed={**snapshot(y,at,steps+event_count),'phase':'boundary-after-event' if event else 'boundary'}
            if _stamp(at) in requested:frames.append(snapshot(y,at,steps+event_count))
        result={'status':'completed','scope':'software_research_only','manifest':manifest,'steps':steps,
                'planned_steps':planned,'samples':frames,'events':journal}
    except _EvaluationHold as exc:
        result={'status':'hold','scope':'software_research_only','manifest':manifest,'steps':steps,'planned_steps':planned,
                'samples':frames,'events':journal,'hold':{'at':_stamp(exc.at),'phase':exc.phase,'reason':exc.reason},'last_confirmed':last_confirmed}
    result['result_sha256']=_hash(result)
    return result
