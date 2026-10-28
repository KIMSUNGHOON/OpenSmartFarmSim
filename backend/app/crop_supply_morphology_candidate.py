"""Read-only first-event candidates on the genuine supply-limited trajectory."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from . import crop_supply_morphology_resume as resume
from . import crop_supply_morphology_candidate_books as accounts

source=resume.source
Q,X,F=resume.Q,resume.X,resume.F
old=source.candidate.old
event=source.candidate.interval.event
VERSION='supply-morphology-next-event-candidate-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
BOOK_SHA256=sha256(Path(accounts.__file__).read_bytes()).hexdigest()
MAX_BYTES=2*1024**2


class SupplyCandidateHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise SupplyCandidateHold(reason)


def _pins():
    pins={**resume._pins(),'backend/app/crop_supply_morphology_candidate.py':CODE_SHA256,'backend/app/crop_supply_morphology_candidate_books.py':BOOK_SHA256}
    root=Path(__file__).resolve().parents[2]
    _need(all(sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in pins.items()),'CODE_HOLD: original supply candidate sources required')
    return pins


def _tolerance(value,step):
    source.stock.arithmetic._closed(value,{'numerator','denominator','unit'})
    _need(value['unit']=='s'and all(type(value[k])is str and 1<=len(value[k])<=128 for k in ['numerator','denominator']),
        'TOLERANCE_HOLD: bounded exact rational seconds required')
    number=X(value)
    _need(0<number<=step and Q(number,'s')==value,'TOLERANCE_HOLD: canonical positive tolerance within actual interval required')
    return number


def _refine(context,data,cp,state,rhs,duration,count,progress):
    units=resume.books.flux_units(data['program'],data['initial']['organs']);totals=(0.,)*len(units)
    at=X(cp['at']['elapsed_seconds_exact']);traces=[];y,r=state,rhs
    for i in range(count):
        y,totals,r,trace=resume._step(context,data,y,totals,r,at+i*duration/count,duration/count,progress);traces.append(trace)
        packet=accounts.packet(context,data,cp,y,totals,r,duration*(i+1)/count,i+1)
    return {'substeps':count,'step_seconds_exact':Q(duration/count,'s'),'intervals':traces,**packet}


def calculate_next_event_candidate(context,raw_checkpoint,*,expected_sha256,time_tolerance_seconds_exact):
    try:
        pins=_pins();data=resume._context(context);cp=resume._parse(raw_checkpoint,expected_sha256,resume.MAX_CP)
        at=X(cp['at']['elapsed_seconds_exact']);right=resume._time(data,cp['branch_steps']+1);step=right-at
        tolerance=_tolerance(time_tolerance_seconds_exact,step)
        tolerance_input=deepcopy(time_tolerance_seconds_exact)
        _need(_tolerance(tolerance_input,step)==tolerance,'SOURCE_HOLD: stable caller tolerance required')
        progress={'stage':'current_validation','current_validation_RHS_evaluations':0,'new_RHS_evaluations':0}
        state,totals,rhs=resume._validate(context,data,cp,progress)
        endpoint,cumulative,end,trace=resume._step(context,data,state,totals,rhs,at,step,progress)
        clock=resume._clock(data,cumulative,right);trace['shoot_clock_certificate']=resume._interval_clock(data,cp,trace,clock)
        _need(X(clock['age_exact'])>=X(clock['next_threshold_exact']),'THRESHOLD_HOLD: actual new-law next interval must bracket first pending event')
        coefficients=[X(q)for q in trace['shoot_clock_certificate']['shoot_age_coefficients_exact']];coefficients[0]-=X(cp['schedule']['next_threshold_exact'])
        lower,upper,iterations=event._root_interval(tuple(coefficients),step,tolerance)
        duration=step*upper;selected=at+duration;weights=old._weights(upper)
        dense_state=old._combine(state,tuple(row['rates']for row in trace['stages']),weights,step)
        partial=old._combine((0.,)*len(totals),tuple(row['flux']for row in trace['stages']),weights,step)
        dense_rhs=resume._rhs(context,data,dense_state,progress,'dense_candidate')
        dense=accounts.packet(context,data,cp,dense_state,partial,dense_rhs,duration,1)
        _need(dense['represented_threshold_status']=='crossed','ROUNDING_HOLD: represented new-law air integral has not crossed the pending threshold')
        refinements=[_refine(context,data,cp,state,rhs,duration,count,progress)for count in (1,2,4)]
        coordinates=resume._coordinates(data);differences=[]
        for i,coordinate in enumerate(coordinates):
            unit=coordinate['unit'];values=[F(row['state'][i])for row in refinements]
            differences.append({'coordinate':coordinate,'dense_to_one_exact':Q(abs(F(dense_state[i])-values[0]),unit),
                'one_to_two_exact':Q(abs(values[0]-values[1]),unit),'two_to_four_exact':Q(abs(values[1]-values[2]),unit)})
        root={'lower_elapsed_seconds_exact':Q(at+step*lower,'s'),'upper_elapsed_seconds_exact':Q(selected,'s'),
            'time_tolerance_seconds_exact':tolerance_input,'lower_threshold_residual_exact':Q(event._value(coefficients,lower),'degC_day'),
            'upper_threshold_residual_exact':Q(event._value(coefficients,upper),'degC_day'),'bisections':iterations}
        out={'model_version':VERSION,'source_code_sha256':pins,'scope':'software_research_only','time_kind':'synthetic_model_clock_not_observation','G0_G4':'not_assessed',
            'context_sha256':context.root_sha256,'checkpoint_sha256':expected_sha256,'source_prefix':deepcopy(cp),'source_interval':trace,
            'source_stage_sha256':[resume._hash(row)for row in trace['stages']],'numerical_root_interval':root,
            'at':{'time_origin_utc':cp['at']['time_origin_utc'],'elapsed_seconds_exact':Q(selected,'s')},'partial_interval_seconds_exact':Q(duration,'s'),
            'state_layout':deepcopy(data['initial']['state_layout']),'state_coordinates':coordinates,'dense_candidate':dense,'refinements':refinements,'state_differences':differences,
            'source_next_sequence':cp['schedule']['next_sequence'],'threshold_exact':deepcopy(cp['schedule']['next_threshold_exact']),
            'redistribution_authorized':cp['redistribution_authorized'],'selection_policy':'original_new_law_cubic_upper_bound_no_threshold_snap',
            'refinement_scope':'readonly_same_time_local_differences_not_certified_ODE_or_agronomic_error_bounds',
            'ledger_rule':'exact_current_plus_partial_residual_and_original_budget_sum','past_intervals_reintegrated':0,
            'schedule_consumed':False,'new_organs_created':False,'integrator_checkpoint':None,**progress}
        out['calculation_sha256']=resume._hash(out)
        resume._fence(context,data);_need(_pins()==pins,'CODE_HOLD: current candidate sources required before return')
        _need(time_tolerance_seconds_exact==tolerance_input,'SOURCE_HOLD: caller tolerance changed during calculation')
        _need(resume._canonical(cp,resume.MAX_CP)==raw_checkpoint,'SOURCE_HOLD: unchanged original caller checkpoint required')
        resume._canonical(out,MAX_BYTES);return deepcopy(out)
    except SupplyCandidateHold:raise
    except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:
        raise SupplyCandidateHold(str(error))from None
