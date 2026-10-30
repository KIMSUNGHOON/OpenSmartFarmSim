"""Locate an unconsumed threshold in one genuine forcing interval's dense curve."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import time

from . import crop_supply_forcing_owner as owner
from . import crop_funded_event_time as event

base,kernel=owner.base,owner.kernel
VERSION='supply-forcing-threshold-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
EVENT_CODE_SHA256=event.CODE_SHA256
FLAGS=base.FLAGS
q,x,need,raw,digest=base.q,base.x,base._need,base._raw,base._hash
MAX_BISECTIONS=128


def _code():
    owner._code()
    need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256
         and sha256(Path(event.__file__).read_bytes()).hexdigest()==EVENT_CODE_SHA256,
         'CODE_HOLD: unchanged threshold locator and exact dense arithmetic required')


def _isolate(coefficients,dt,tolerance,interrupt,progress):
    need(type(tolerance)is Fraction and 0<tolerance<=dt,'TOLERANCE_HOLD: positive exact tolerance within interval required')
    need(event._minimum_derivative(coefficients)>0,'MONOTONICITY_HOLD: strictly increasing dense curve required')
    need(event._value(coefficients,Fraction(0))<0<=event._value(coefficients,Fraction(1)),
         'ROOT_HOLD: original unconsumed threshold must be bracketed')
    lower,upper=Fraction(0),Fraction(1)
    while (upper-lower)*dt>tolerance:
        interrupt()
        need(progress['bisections']<MAX_BISECTIONS,'PRECISION_HOLD: bounded exact root isolation exhausted')
        middle=(lower+upper)/2
        if event._value(coefficients,middle)<0:lower=middle
        else:upper=middle
        progress['bisections']+=1
    interrupt()
    return lower,upper


def _order(left,right,active_edge,next_edge,coefficients):
    need(active_edge<=left,'ORDER_HOLD: actual active forcing must precede this interval')
    relation='absent'
    if next_edge is not None:
        need(right<=next_edge,'ORDER_HOLD: pending interval cannot cross the next forcing edge')
        if right<next_edge or event._value(coefficients,Fraction(1))>0:relation='strictly_before'
        else:relation='coincident_dense_endpoint'
    return {'active_forcing_edge_exact':q(active_edge,'s'),'after_active_forcing_edge':True,
            'next_forcing_edge_exact':None if next_edge is None else q(next_edge,'s'),
            'next_forcing_relation':relation,'material_forcing_order_resolved':relation!='coincident_dense_endpoint',
            'scope':'ordering_in_certified_numerical_polynomial_only'}


def _failure(handle,error,progress,authority=None):
    return {**FLAGS,'schema_version':'supply-forcing-threshold-location-v1','model_version':VERSION,
            'code_sha256':CODE_SHA256,'status':'hold','hold':base._reason(error),'failed_stage':progress['stage'],
            'root':None,'progress':deepcopy(progress),'authority_hold':authority,
            'historical_cursor_sha256':handle.cursor_sha256 if type(handle)is owner.Handle else None,
            'checkpoint_issued':False,'history_committed':False,'material_consumed':False}


def locate_threshold(handle,pending_page_sha256,time_tolerance_seconds_exact,*,cancelled=None,wall_seconds=60):
    """Replay only an unconfirmed interval; return a root certificate, never a state."""
    started=time.monotonic()
    progress={'stage':'admission','pending_current_validation_RHS_evaluations':0,'pending_new_RHS_evaluations':0,
              'RHS_quota_reserved':0,'failed_pending_RHS_count_unreported':False,'bisections':0,
              'past_confirmed_intervals_reintegrated':0}
    try:
        _code()
        need(type(wall_seconds)is int and 1<=wall_seconds<=60 and (cancelled is None or callable(cancelled)),
             'BUDGET_HOLD: bounded local wall/cancellation controls required')
        need(type(handle)is owner.Handle and handle._token is owner._TOKEN,'CONTEXT_HOLD: genuine forcing owner handle required')
        with owner._session(handle._definition,handle._workspace)as s:
            try:
                cursor,current=owner._restore(s,handle.cursor_sha256)
                need(raw(cursor,base.CURRENT_MAX)==handle._cursor and raw(current,base.CURRENT_MAX)==handle._current
                     and raw(s.basis)==handle._basis,'CONTEXT_HOLD: unchanged genuine owner bytes required')
                need(owner._switch_index(s,current)is None and current['phase']!='declared_end',
                     'ORDER_HOLD: pending interval requires an already applied forcing')
                page=owner.get(s,pending_page_sha256)
                base.reader._closed(page,{'schema_version','definition_sha256','previous_cursor_sha256','result','reason'})
                need(page['schema_version']=='supply-forcing-pending-page-v1'
                     and page['definition_sha256']==s.definition_ref and page['previous_cursor_sha256']==handle.cursor_sha256,
                     'SOURCE_HOLD: pending page must belong to this actual definition/cursor')
                index=current['span_index'];span=s.spans[index];n=current['numeric']
                left=x(current['at']['elapsed_seconds_exact'],'s');right=owner._right(s,current);dt=right-left
                tolerance=x(time_tolerance_seconds_exact,'s')
                need(0<tolerance<=dt,'TOLERANCE_HOLD: positive exact tolerance within pending interval required')
                controls=base.AdvanceRequest(q(right,'s'),rhs_budget=5,wall_seconds=wall_seconds,cancelled=cancelled)
                def interrupt():base._interrupt(controls,progress,started)
                interrupt();owner._check(s);_code()
                remaining=owner._remaining_wall(controls,started)
                progress['stage']='pending_interval_replay';progress['RHS_quota_reserved']=5
                try:
                    replay=kernel.advance_interval(basis=s.math_basis,current=n,profiles=s.profiles,span=span,
                        end=q(right,'s'),cancelled=cancelled,wall_seconds=remaining)
                except (OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError):
                    progress['failed_pending_RHS_count_unreported']=True;raise
                progress['pending_current_validation_RHS_evaluations']=replay['progress']['current_validation_RHS_evaluations']
                progress['pending_new_RHS_evaluations']=replay['progress']['new_RHS_evaluations']
                reason='EVENT_HOLD: refine material threshold before further integration'
                if right==x(span['end'],'s')and index<len(s.spans)-1:
                    reason='ORDER_HOLD: material bracket reaches forcing edge; refine its order'
                need(replay['status']=='awaiting_material'and replay['current']is None
                     and replay==page['result']and page['reason']==reason,
                     'REPLAY_HOLD: exact stored pending result and canonical active-forcing interval required')
                owner._check(s);interrupt()
                progress['stage']='dense_polynomial'
                age=x(n['schedule']['age_exact'],'degC_day');threshold=x(n['schedule']['next_threshold_exact'],'degC_day')
                trace=replay['interval'];temperatures=tuple(Fraction.from_float(row['state'][104])for row in trace['stages'])
                coefficients=event._thermal_polynomial(temperatures,dt,Fraction(s.math_basis['shoot_base_temperature']),age,threshold)
                certificate=trace['shoot_clock_certificate']
                expected=list(coefficients);expected[0]+=threshold
                need(certificate['shoot_age_coefficients_exact']==[q(v,'degC_day')for v in expected]
                     and x(certificate['minimum_derivative_per_unit_theta_exact'],'degC_day')==event._minimum_derivative(coefficients),
                     'CLOCK_HOLD: exact original shared-stage thermal certificate required')
                progress['stage']='root_bisection'
                lower,upper=_isolate(coefficients,dt,tolerance,interrupt,progress)
                next_edge=x(span['end'],'s')if index<len(s.spans)-1 else None
                order=_order(left,right,x(span['start'],'s'),next_edge,coefficients)
                root={'time_origin_utc':current['at']['time_origin_utc'],
                      'lower_elapsed_seconds_exact':q(left+lower*dt,'s'),'upper_elapsed_seconds_exact':q(left+upper*dt,'s'),
                      'width_seconds_exact':q((upper-lower)*dt,'s'),
                      'lower_thermal_residual_exact':q(event._value(coefficients,lower),'degC_day'),
                      'upper_thermal_residual_exact':q(event._value(coefficients,upper),'degC_day')}
                order_hold=not order['material_forcing_order_resolved']
                progress['stage']='final_source_check';interrupt();owner._check(s);_code()
                result={**FLAGS,'schema_version':'supply-forcing-threshold-location-v1','model_version':VERSION,
                    'code_sha256':CODE_SHA256,'owner_code_sha256':owner.CODE_SHA256,'kernel_code_sha256':kernel.CODE_SHA256,
                    'event_math_code_sha256':EVENT_CODE_SHA256,'status':'hold'if order_hold else'root_located',
                    'hold':'ORDER_HOLD: dense endpoint coincides with next forcing; adoption order unsupported'if order_hold else None,
                    'definition_sha256':s.definition_ref,'cursor_sha256':handle.cursor_sha256,
                    'pending_page_sha256':pending_page_sha256,'numeric_sha256':digest(n),'span_sha256':digest(span),
                    'interval_input_sha256':replay['input_sha256'],'effective_rights':deepcopy(s.rights),
                    'source_schedule':deepcopy(n['schedule']),'interval_left_exact':q(left,'s'),'interval_right_exact':q(right,'s'),
                    'time_tolerance_seconds_exact':q(tolerance,'s'),
                    'polynomial_residual_coefficients_exact':[q(v,'degC_day')for v in coefficients],
                    'minimum_derivative_per_theta_exact':q(event._minimum_derivative(coefficients),'degC_day'),
                    'ideal_cubic_minus_accumulated_endpoint_age_exact':q(event._value(coefficients,Fraction(1))-
                        (x(replay['pending']['right_age_exact'],'degC_day')-threshold),'degC_day'),
                    'method_reference':event.METHOD_REFERENCE,
                    'method':'classical_rk4_third_order_continuous_extension_eq28_exact_rational_bisection',
                    'claim_scope':'root_isolation_in_this_numerical_polynomial_not_physical_time_or_discretization_error',
                    'root':root,'order':order,'progress':deepcopy(progress),'checkpoint_issued':False,
                    'history_committed':False,'material_consumed':False}
                raw(result);interrupt();owner._check(s);_code()
                return result
            except (OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError)as error:
                authority=None
                try:owner._check(s);_code()
                except (OSError,ValueError,TypeError,KeyError)as late:authority=base._reason(late)
                return _failure(handle,error,progress,authority)
    except (OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError)as error:
        return _failure(handle,error,progress)
