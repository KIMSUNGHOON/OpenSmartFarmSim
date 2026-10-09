"""Bounded versioned startup integration; existing stored models remain unchanged."""
from datetime import timedelta
from fractions import Fraction
from hashlib import sha256
from math import fsum, isfinite, ulp
from pathlib import Path
import platform

from . import crop_growth_rates as plant
from . import crop_fruit_cohorts as fruit
from . import crop_fruit_allocation as allocation
from . import crop_fruit_transport as transport
from . import crop_fruit_startup as startup
from . import crop_plant_startup_rates as coupled
from . import crop_plant_cohort_integration as legacy

PROGRAM_VERSION = 'crop-plant-startup-program-v1'
INTEGRATOR_VERSION = 'crop-plant-startup-rk4-research-v1'
PLANT, ARRAY_UNITS = legacy.PLANT, legacy.ARRAY_UNITS
STARTUP_FLUX = ('requested_fruit_carbohydrate','realized_fruit_carbohydrate',
                'deferred_fruit_carbohydrate','fruit_growth_respiration')
FLUX = (*legacy.FLUX, *STARTUP_FLUX)
FLUX_UNITS = {**legacy.FLUX_UNITS, **{k:plant.MASS_UNIT for k in STARTUP_FLUX}}
CODE_HASHES = {name:sha256(Path(path).read_bytes()).hexdigest() for name,path in (
    ('integrator',__file__),('coupled',coupled.__file__),('startup',startup.__file__),
    ('plant',plant.__file__),('cohorts',fruit.__file__),('allocation',allocation.__file__),
    ('transport',transport.__file__),('legacy_helpers',legacy.__file__),('original_rates',legacy.coupled.__file__))}
_q, _hash, _utc, _stamp = legacy._q, legacy._hash, legacy._utc, legacy._stamp
_state, _guard, _EvaluationHold = legacy._state, legacy._guard, legacy._EvaluationHold


class PlantStartupIntegrationHold(ValueError):
    """Malformed or unbounded programs rejected before startup integration."""


def _need(condition, reason):
    if not condition:raise PlantStartupIntegrationHold(reason)


def _ledger(y, seed, operations, at, cg):
    external = legacy._ledger(y, seed, operations, at)
    try:
        expected_growth = cg*y[118]
        if not isfinite(expected_growth) or (y[118]>0 and cg>0 and expected_growth==0):
            raise _EvaluationHold('NUMERIC_HOLD: startup growth accumulation underflow/overflow',at,'balance')
        residuals = (fsum((y[117],-y[118],-y[119])),fsum((y[120],-expected_growth)))
        scales = (max(y[117:120]),max(y[120],expected_growth))
        budgets = [64*(operations+1)*ulp(scale) for scale in scales]
        if not all(isfinite(v) for v in (*residuals,*budgets)) or any(abs(r)>b for r,b in zip(residuals,budgets,strict=True)):
            raise _EvaluationHold('BALANCE_HOLD: unresolved startup request/respiration accumulations',at,'balance')
        diagnostics = {k:_q(v,plant.MASS_UNIT) for k,v in (
            ('requested_residual',residuals[0]),('requested_budget',budgets[0]),
            ('growth_respiration_residual',residuals[1]),('growth_respiration_budget',budgets[1]))}
        return (*external,diagnostics)
    except (OverflowError,ValueError) as exc:
        raise _EvaluationHold('NUMERIC_HOLD: startup balance arithmetic failed',at,'balance') from exc


def _advance(y, rates, h, at):
    try:
        increments = [h*fsum((a,2*b,2*c,d))/6 for a,b,c,d in zip(*rates,strict=True)]
        if any(increments[j]==0 and any(k[j]>0 for k in rates) for j in range(117,121)):
            raise _EvaluationHold('NUMERIC_HOLD: positive startup accumulation underflow',at,'step-end-arithmetic')
        return [fsum((v,delta)) for v,delta in zip(y,increments,strict=True)]
    except (OverflowError,ValueError) as exc:
        raise _EvaluationHold('NUMERIC_HOLD: RK4 update failed',at,'step-end-arithmetic') from exc


def integrate_plant_startup(*,initial_state,segments,events,output_times,growth_profile,cohort_profile,transport_profile,solver):
    """Advance an explicit short research program or preserve a diagnostic hold."""
    _need(type(growth_profile) is plant.ReferenceParameters and type(cohort_profile) is fruit.ReferenceFruitCohortParameters
          and type(transport_profile) is transport.ReferenceFruitTransportParameters,'PROFILE_HOLD: pinned profiles required')
    try:
        program,boundaries,planned=legacy._prepare(initial_state,segments,events,output_times,solver)
    except legacy.PlantCohortIntegrationHold as exc:
        raise PlantStartupIntegrationHold(str(exc)) from exc
    solver=program['solver']
    profile_hashes={k:p.sha256 for k,p in (('growth_profile',growth_profile),('cohort_profile',cohort_profile),('transport_profile',transport_profile))}
    blocks=[program['initial_state']]+[s[k] for s in program['segments'] for k in ('forcing','removals','fruit_entry','relative_growth_rate')]
    blocks += [e['removals'] for e in program['events']]
    manifest={'program_version':PROGRAM_VERSION,'integrator_version':INTEGRATOR_VERSION,'rate_model_version':coupled.MODEL_VERSION,
        'profile_sha256':profile_hashes,'policy_sha256':startup.POLICY_SHA256,
        'allocation_policy_sha256':allocation.POLICY_SHA256,'code_sha256':dict(CODE_HASHES),
        'solver':dict(solver),'time_rule':'UTC_POSIX_whole_seconds_v1','python_version':platform.python_version(),
        'temperature_sum_method':'analytic_piecewise_constant_fraction_v1','convergence':'not_evaluated_for_this_program',
        'origins':sorted({b['origin'] for b in blocks}),'input_ids':[b['input_id'] for b in blocks],
        'research_assumptions':list(legacy.coupled.ASSUMPTIONS),
        'startup_transition':'zero_or_positive_tail_research_only_not_validated_sink_capacity',
        'startup_balance_rule':'64-ulp-per-operation-without-absolute-floor-v1'}
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
            result=coupled.calculate_plant_startup_rates(state=plant_state,cohort_state=fruit_state,
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
                segment['fruit_entry']['values']['fruit_number_inflow']['value'],0.0,0.0,
                result['fruit_startup']['requested_carbohydrate_inflow']['value'],
                result['fruit_startup']['effective_carbohydrate_inflow']['value'],
                result['fruit_startup']['deferred_carbohydrate_inflow']['value'],
                result['fruit_startup']['realized_growth_respiration']['value']]
        except coupled.PlantStartupHold as exc:raise _EvaluationHold(str(exc),time,phase) from exc

    def snapshot(vector,time,operations):
        carbon,number,cb,nb,diagnostics=_ledger(vector,seed,operations,time,growth_profile.values['cFruitG'])
        return {'at':_stamp(time),'state':_state(vector),'startup_diagnostics':diagnostics,
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
                candidate=_advance(y,(k1,k2,k3,k4),h,end)
                candidate=clock(candidate,end,'step-end');rhs(candidate,end,'step-end');_ledger(candidate,seed,steps+event_count+1,end,growth_profile.values['cFruitG'])
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
            rhs(candidate,at,'boundary-after-event' if event else 'boundary');_ledger(candidate,seed,steps+event_count+bool(event),at,growth_profile.values['cFruitG'])
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
