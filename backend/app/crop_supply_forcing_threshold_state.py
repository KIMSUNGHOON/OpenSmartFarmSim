"""Unpublished all-state/transfer candidates at the admitted dense root upper bound."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import time
from types import SimpleNamespace

from . import crop_supply_forcing_threshold as locator
from . import crop_supply_threshold_state_books as books

owner,base,kernel=locator.owner,locator.base,locator.kernel
VERSION='supply-forcing-threshold-state-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
BOOK_CODE_SHA256=books.CODE_SHA256
FLAGS=base.FLAGS
q,x,need,raw,digest=base.q,base.x,base._need,base._raw,base._hash
old=base.arithmetic.source.candidate.old
REFINEMENTS=(1,2,4)


def _code():
    locator._code()
    need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256
         and sha256(Path(books.__file__).read_bytes()).hexdigest()==BOOK_CODE_SHA256,
         'CODE_HOLD: unchanged threshold state and exact account arithmetic required')


def _rk4(state,totals,rates,flow,h,at,evaluate):
    rows=[{'stage':'k1','at_elapsed_seconds_exact':q(at,'s'),'state':list(state),'rates':list(rates),'flux':list(flow)}]
    previous=rates
    for name,offset in [('k2',h/2),('k3',h/2),('k4',h)]:
        trial=base.combine(state,(previous,),(Fraction(1),),offset)
        previous,values,_=evaluate(trial,name)
        rows.append({'stage':name,'at_elapsed_seconds_exact':q(at+offset,'s'),'state':list(trial),'rates':list(previous),'flux':list(values)})
    weights=(Fraction(1,6),Fraction(1,3),Fraction(1,3),Fraction(1,6))
    end=base.combine(state,tuple(tuple(r['rates'])for r in rows),weights,h)
    cumulative=base.combine(totals,tuple(tuple(r['flux'])for r in rows),weights,h)
    rates,flow,derived=evaluate(end,'endpoint')
    trace={'left_elapsed_seconds_exact':q(at,'s'),'right_elapsed_seconds_exact':q(at+h,'s'),'step_seconds_exact':q(h,'s'),
           'stages':rows,'endpoint':{'state':list(end),'rates':list(rates),'flux':list(flow)}}
    return end,cumulative,rates,flow,derived,trace


def _differences(packets):
    def rows(fields,units):
        return [{'index':i,**{name:q(abs(Fraction(fields[a][i])-Fraction(fields[b][i])),unit)
                for name,a,b in [('dense_to_one_exact',0,1),('one_to_two_exact',1,2),('two_to_four_exact',2,3)]}}
                for i,unit in enumerate(units)]
    states=[r['state']for r in packets];transfers=[[v['value']for v in r['partial_interval_transfers'].values()]for r in packets]
    return states,transfers,rows


def _failure(handle,error,progress,authority=None):
    return {**FLAGS,'schema_version':'supply-forcing-threshold-state-result-v1','model_version':VERSION,
            'code_sha256':CODE_SHA256,'status':'hold','hold':base._reason(error),'failed_stage':progress['stage'],
            'dense_candidate':None,'refinements':[],'progress':deepcopy(progress),'authority_hold':authority,
            'historical_cursor_sha256':handle.cursor_sha256 if type(handle)is owner.Handle else None,
            'checkpoint_issued':False,'history_committed':False,'material_consumed':False}


def calculate_threshold_state(handle,pending_page_sha256,time_tolerance_seconds_exact,*,cancelled=None,wall_seconds=60):
    started=time.monotonic()
    p={'stage':'admission','root_RHS_evaluations':0,'current_validation_RHS_evaluations':0,'new_RHS_evaluations':0,
       'failed_root_RHS_count_unreported':False,'past_confirmed_intervals_reintegrated':0}
    try:
        _code()
        need(type(wall_seconds)is int and 1<=wall_seconds<=60 and(cancelled is None or callable(cancelled)),
             'BUDGET_HOLD: bounded whole calculation controls required')
        tolerance=q(x(time_tolerance_seconds_exact,'s'),'s')
        controls=base.AdvanceRequest(q(0,'s'),rhs_budget=29,wall_seconds=wall_seconds,cancelled=cancelled)
        def interrupt():base._interrupt(controls,p,started)
        interrupt();p['stage']='root_location'
        root=locator.locate_threshold(handle,pending_page_sha256,tolerance,cancelled=cancelled,
                                     wall_seconds=owner._remaining_wall(controls,started))
        rp=root['progress'];p['root_RHS_evaluations']=rp['pending_current_validation_RHS_evaluations']+rp['pending_new_RHS_evaluations']
        p['failed_root_RHS_count_unreported']=rp['failed_pending_RHS_count_unreported']
        need(root['status']=='root_located',root.get('hold')or'ROOT_HOLD: independently located source threshold required')
        with owner._session(handle._definition,handle._workspace)as s:
            try:
                p['stage']='source_recheck';cursor,current=owner._restore(s,handle.cursor_sha256)
                need(raw(cursor,base.CURRENT_MAX)==handle._cursor and raw(current,base.CURRENT_MAX)==handle._current
                     and raw(s.basis)==handle._basis,'CONTEXT_HOLD: unchanged actual source handle bytes required')
                n=current['numeric'];page=owner.get(s,pending_page_sha256);trace=page['result']['interval'];index=current['span_index']
                span=s.spans[index];left=x(current['at']['elapsed_seconds_exact'],'s');at=x(root['root']['upper_elapsed_seconds_exact'],'s')
                need(root['cursor_sha256']==handle.cursor_sha256 and root['definition_sha256']==s.definition_ref
                     and root['pending_page_sha256']==pending_page_sha256 and root['numeric_sha256']==digest(n)
                     and root['span_sha256']==digest(span)and root['interval_input_sha256']==page['result']['input_sha256']
                     and page['previous_cursor_sha256']==handle.cursor_sha256 and page['definition_sha256']==s.definition_ref,
                     'SOURCE_HOLD: located root must bind this held source/pending/active span')
                duration=at-left;dt=x(trace['step_seconds_exact'],'s');theta=duration/dt
                need(0<theta<=1 and at<=x(span['end'],'s'),'TIME_HOLD: root upper bound must remain in the admitted interval/span')
                program=kernel._view(s.math_basis,span);data=kernel._data(s.math_basis,program,s.profiles)
                math=SimpleNamespace(data=data,basis=s.math_basis,profiles=s.profiles,units=base.books.flux_units(program,data['organs']))
                snapshot=raw({'current':current,'basis':s.math_basis,'span':span,'pending':page})
                def fence():
                    owner._check(s);_code();kernel._profiles(s.math_basis,s.profiles)
                    need(snapshot==raw({'current':current,'basis':s.math_basis,'span':span,'pending':page}),
                         'SOURCE_HOLD: unchanged admitted numeric source and pending input required')
                def evaluate(state,label):
                    rhs=base._rhs(math,state,controls,p,started,label)
                    return tuple(rhs['rates']),tuple(base.books.flux(program,state,rhs,data['organs'])),rhs['derived']
                interrupt();fence();state=tuple(n['last_confirmed']['state']);zero=(0.,)*len(math.units)
                rows=trace['stages'];weights=old._weights(theta)
                dense_state=base.combine(state,tuple(tuple(r['rates'])for r in rows),weights,dt)
                dense_transfers=base.combine(zero,tuple(tuple(r['flux'])for r in rows),weights,dt)
                _,_,dense_derived=evaluate(dense_state,'dense_candidate')
                dense=books.packet(math,n,dense_state,dense_transfers,dense_derived,at,1)
                need(dense['represented_threshold_status']=='crossed','ROUNDING_HOLD: represented dense clock must cross without snapping')
                refinements=[]
                for count in REFINEMENTS:
                    interrupt();fence();y=state;totals=zero;rates=tuple(rows[0]['rates']);flow=tuple(rows[0]['flux']);intervals=[];step=duration/count
                    for i in range(count):
                        y,totals,rates,flow,derived,interval=_rk4(y,totals,rates,flow,step,left+i*step,evaluate)
                        packet=books.packet(math,n,y,totals,derived,left+(i+1)*step,i+1);intervals.append(interval)
                    refinements.append({'substeps':count,'step_seconds_exact':q(step,'s'),'intervals':intervals,**packet})
                states,transfers,difference_rows=_differences([dense,*refinements])
                p['stage']='coordinate_projection'
                coordinates=deepcopy(data['seed']['state_layout'])
                layout_data={'initial':{'state_layout':coordinates,'state':state},'program':program}
                # The established pure coordinate builder needs only these numeric fields.
                coordinate_rows=base.arithmetic.resume._coordinates(layout_data)
                state_differences=difference_rows(states,[r['unit']for r in coordinate_rows])
                for row,coordinate in zip(state_differences,coordinate_rows,strict=True):row['coordinate']=coordinate
                transfer_differences=difference_rows(transfers,list(math.units.values()))
                for row,name in zip(transfer_differences,math.units,strict=True):row['name']=name
                p['stage']='final_source_check';interrupt();fence()
                result={**FLAGS,'schema_version':'supply-forcing-threshold-state-result-v1','model_version':VERSION,
                    'code_sha256':CODE_SHA256,'book_code_sha256':BOOK_CODE_SHA256,'status':'candidate_ready','hold':None,
                    'root_certificate':root,'effective_rights':deepcopy(s.rights),'source_current_sha256':digest(current),
                    'source_basis_sha256':digest(s.basis),'source_current':deepcopy(current),'source_interval':deepcopy(trace),
                    'source_schedule':deepcopy(n['schedule']),'state_layout':coordinates,'state_coordinates':coordinate_rows,
                    'at':deepcopy(dense['at']),'selection_policy':'certified_dense_root_upper_bound_no_threshold_snap',
                    'dense_candidate':dense,'refinements':refinements,'state_differences':state_differences,
                    'transfer_differences':transfer_differences,'progress':deepcopy(p),
                    'account_rule':'exact_source_plus_partial_residual_and_unchanged_budget_sum',
                    'diagnostic_scope':'same_time_local_differences_not_certified_ODE_or_agronomic_error',
                    'checkpoint_issued':False,'history_committed':False,'material_consumed':False}
                result['calculation_sha256']=digest(result);raw(result);interrupt();fence();return result
            except(OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError)as error:
                authority=None
                try:owner._check(s);_code()
                except(OSError,ValueError,TypeError,KeyError)as late:authority=base._reason(late)
                return _failure(handle,error,p,authority)
    except(OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError)as error:
        return _failure(handle,error,p)
