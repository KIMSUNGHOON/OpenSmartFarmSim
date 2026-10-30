"""Cold algebraic proofs for locally produced material receipts and RK4 traces."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

from . import crop_supply_material_point as point

forcing,base,kernel=point.owner,point.base,point.kernel
locator=point.candidate.locator
q,x,need,raw,digest=base.q,base.x,base._need,base._raw,base._hash
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


def math_view(basis,span,profiles):
    program=kernel._view(basis,span);data=kernel._data(basis,program,profiles)
    return SimpleNamespace(data=data,basis=basis,profiles=profiles,units=base.books.flux_units(program,data['organs']))


def trace_values(math,before,trace,right):
    left=x(before['at']['elapsed_seconds_exact'],'s');h=right-left;y=tuple(before['last_confirmed']['state'])
    base.reader._closed(trace,{'left_elapsed_seconds_exact','right_elapsed_seconds_exact','step_seconds_exact','stages','endpoint','flux_order','shoot_clock_certificate'})
    need(h>0 and trace['left_elapsed_seconds_exact']==q(left,'s')and trace['right_elapsed_seconds_exact']==q(right,'s')
         and trace['step_seconds_exact']==q(h,'s'),'TIME_HOLD: exact canonical interval required')
    need(type(trace['stages'])is list and len(trace['stages'])==4,'TRACE_HOLD: four actual RK4 stages required')
    rows=trace['stages'];previous=None;rates=[];flows=[];p=math.data['program'];names=list(math.units)
    forced={'canopy_external':p['scenario']['forcing']['canopy_external_heat']['value'],
            'air_external':p['scenario']['forcing']['air_external_sensible_heat']['value'],
            'external_vapor':p['scenario']['forcing']['air_external_vapor']['value'],
            'entry_number':p['scenario']['fruit_entry']['fruit_number_inflow']['value']}
    for label,offset,row in zip(('k1','k2','k3','k4'),(Fraction(0),h/2,h/2,h),rows,strict=True):
        base.reader._closed(row,{'stage','at_elapsed_seconds_exact','state','rates','flux'})
        expected=y if previous is None else base.combine(y,(previous,),(Fraction(1),),offset)
        need(row['stage']==label and row['at_elapsed_seconds_exact']==q(left+offset,'s')
             and base._vector(row['state'],len(y))==expected,'TRACE_HOLD: exact stage state/time order required')
        previous=base._vector(row['rates'],len(y));rates.append(previous);flow=base._vector(row['flux'],len(math.units));flows.append(flow)
        need(all(flow[names.index(k)]==v for k,v in forced.items()),'FORCING_HOLD: active external fluxes required')
    weights=(Fraction(1,6),Fraction(1,3),Fraction(1,3),Fraction(1,6))
    state=base.combine(y,tuple(rates),weights,h)
    totals=base.combine(tuple(before['branch_integrated_transfers'][k]['value']for k in math.units),tuple(flows),weights,h)
    base.reader._closed(trace['endpoint'],{'state','rates','flux'})
    need(base._vector(trace['endpoint']['state'],len(y))==state
         and trace['flux_order']==[{'name':k,'unit':v}for k,v in math.units.items()],
         'TRACE_HOLD: exact endpoint/flux inventory required')
    base._vector(trace['endpoint']['rates'],len(y));base._vector(trace['endpoint']['flux'],len(math.units))
    schedule=base._clock(math,totals,right)
    need(trace['shoot_clock_certificate']==base.arithmetic._interval_clock(math.data,before,trace,schedule),
         'CLOCK_HOLD: exact shared-stage certificate required')
    return state,totals,schedule


def verify(s,current,source,definition,value):
    """Verify saved local producer witnesses without evaluating any past RHS."""
    point._head(s,current,source,definition['inputs'],definition['pending_page_sha256'])
    need(value['calculation_sha256']==definition['expected_point_sha256']
         and value['calculation_sha256']==digest({k:v for k,v in value.items()if k!='calculation_sha256'})
         and value['code_sha256']==point.CODE_SHA256 and value['model_version']==point.VERSION
         and value['status']=='point_ready'and value['inputs']==definition['inputs']
         and value['source_current_sha256']==digest(current)and value['source_schedule']==current['numeric']['schedule']
         and value['source_transfer_origins']==current['numeric']['transfer_origins']
         and value['input_sha256']==digest(definition['inputs'])
         and value['cursor_sha256']==definition['source']['cursor_sha256']
         and value['definition_sha256']==s.definition_ref and value['pending_page_sha256']==definition['pending_page_sha256']
         and value['initial_binding_sha256']==source['initial_binding_sha256']
         and value['source_event']==source['event']and value['candidate_sha256']==definition['inputs']['candidate_sha256'],
         'POINT_HOLD: exact locally produced source-bound receipt required')
    need(all(value[k]==v for k,v in base.FLAGS.items())and value['checkpoint_issued']is False
         and value['history_committed']is False and value['material_consumed']is False
         and value['schedule_adoption']=='not_performed'and value['elapsed_seconds_advanced']==q(0,'s'),
         'SCOPE_HOLD: original unadopted point scope required')
    n=current['numeric'];index=current['span_index'];span=s.spans[index];right=forcing._right(s,current)
    page=forcing.get(s,definition['pending_page_sha256']);trace=page['result']['interval'];m=math_view(s.math_basis,span,s.profiles)
    _,_,schedule=trace_values(m,n,trace,right)
    need(x(schedule['age_exact'],'degC_day')>=x(schedule['next_threshold_exact'],'degC_day'),
         'EVENT_HOLD: original pending threshold must be bracketed')
    expected=forcing._interval_evidence(s,current,trace)
    expected.update(status='awaiting_material',current=None,pending={
        'left_at':deepcopy(n['at']['elapsed_seconds_exact']),'right_at':q(right,'s'),
        'left_age_exact':deepcopy(n['schedule']['age_exact']),'right_age_exact':schedule['age_exact'],
        'threshold_exact':schedule['next_threshold_exact'],'schedule_consumed':False,
        'forcing_material_order_resolved':False,'candidate_or_checkpoint_issued':False})
    reason='EVENT_HOLD: refine material threshold before further integration'
    if right==x(span['end'],'s')and index<len(s.spans)-1:reason='ORDER_HOLD: material bracket reaches forcing edge; refine its order'
    need(page=={'schema_version':'supply-forcing-pending-page-v1','definition_sha256':s.definition_ref,
        'previous_cursor_sha256':definition['source']['cursor_sha256'],'result':expected,'reason':reason},
        'REPLAY_HOLD: exact stored pending page required')
    left=x(n['at']['elapsed_seconds_exact'],'s');dt=right-left;threshold=x(n['schedule']['next_threshold_exact'],'degC_day')
    coefficients=locator.event._thermal_polynomial(tuple(Fraction(row['state'][104])for row in trace['stages']),dt,
        Fraction(s.math_basis['shoot_base_temperature']),x(n['schedule']['age_exact'],'degC_day'),threshold)
    progress={'bisections':0};lo,hi=locator._isolate(coefficients,dt,x(definition['time_tolerance_seconds_exact'],'s'),lambda:None,progress)
    root=value['root_certificate'];at=left+hi*dt
    expected_root={'time_origin_utc':n['at']['time_origin_utc'],'lower_elapsed_seconds_exact':q(left+lo*dt,'s'),
        'upper_elapsed_seconds_exact':q(at,'s'),'width_seconds_exact':q((hi-lo)*dt,'s'),
        'lower_thermal_residual_exact':q(locator.event._value(coefficients,lo),'degC_day'),
        'upper_thermal_residual_exact':q(locator.event._value(coefficients,hi),'degC_day')}
    order=locator._order(left,right,x(span['start'],'s'),x(span['end'],'s')if index<len(s.spans)-1 else None,coefficients)
    checks={'root':expected_root,'order':order,'status':'root_located','hold':None,'code_sha256':locator.CODE_SHA256,
        'owner_code_sha256':forcing.CODE_SHA256,'kernel_code_sha256':kernel.CODE_SHA256,
        'event_math_code_sha256':locator.EVENT_CODE_SHA256,'definition_sha256':s.definition_ref,
        'cursor_sha256':definition['source']['cursor_sha256'],'pending_page_sha256':definition['pending_page_sha256'],
        'numeric_sha256':digest(n),'span_sha256':digest(span),'interval_input_sha256':expected['input_sha256'],
        'source_schedule':n['schedule'],'effective_rights':s.rights,'time_tolerance_seconds_exact':definition['time_tolerance_seconds_exact'],
        'polynomial_residual_coefficients_exact':[q(v,'degC_day')for v in coefficients]}
    checks.update({**base.FLAGS,'schema_version':'supply-forcing-threshold-location-v1','model_version':locator.VERSION,
        'interval_left_exact':q(left,'s'),'interval_right_exact':q(right,'s'),
        'minimum_derivative_per_theta_exact':q(locator.event._minimum_derivative(coefficients),'degC_day'),
        'ideal_cubic_minus_accumulated_endpoint_age_exact':q(locator.event._value(coefficients,Fraction(1))-(x(schedule['age_exact'],'degC_day')-threshold),'degC_day'),
        'method_reference':locator.event.METHOD_REFERENCE,
        'method':'classical_rk4_third_order_continuous_extension_eq28_exact_rational_bisection',
        'claim_scope':'root_isolation_in_this_numerical_polynomial_not_physical_time_or_discretization_error',
        'progress':{'stage':'final_source_check','pending_current_validation_RHS_evaluations':1,'pending_new_RHS_evaluations':4,
            'RHS_quota_reserved':5,'failed_pending_RHS_count_unreported':False,'bisections':progress['bisections'],'past_confirmed_intervals_reintegrated':0},
        'checkpoint_issued':False,'history_committed':False,'material_consumed':False})
    need(raw(root)==raw(checks)and order['material_forcing_order_resolved']
         and (index==len(s.spans)-1 or at<x(span['end'],'s')),'ROOT_HOLD: actual root and strict material ordering required')
    need(value['at']=={'time_origin_utc':n['at']['time_origin_utc'],'elapsed_seconds_exact':q(at,'s')}
         and value['at']['elapsed_seconds_exact']==definition['inputs']['at_elapsed_seconds_exact'],
         'TIME_HOLD: exact chosen material time required')
    weights=point.candidate.old._weights(hi)
    state=base.combine(tuple(n['last_confirmed']['state']),tuple(tuple(r['rates'])for r in trace['stages']),weights,dt)
    partial=base.combine((0.,)*len(m.units),tuple(tuple(r['flux'])for r in trace['stages']),weights,dt)
    dense=point.candidate.books.packet(m,n,state,partial,value['before_dense']['derived'],at,1)
    need(raw(dense)==raw(value['before_dense'])and dense['represented_threshold_status']=='crossed',
         'STATE_HOLD: exact whole dense state and partial accounts required')
    spacing=x(source['timeline']['phyllochron_exact'],'degC_day')
    need(threshold<=x(dense['shoot_age_exact'],'degC_day')<threshold+spacing,'EVENT_HOLD: only first pending event can be adopted')
    data=m.data;data['initial']={'organs':data['seed']['organs'],'state_layout':data['seed']['state_layout']}
    numbers={'dense_candidate':{**deepcopy(dense),'global_ledgers':deepcopy(dense['pending_global_ledgers'])},
             'at':deepcopy(value['at']),'source_prefix':{'event_sequence':n['event_sequence']}}
    seeds=point._seeds(s,source,definition['inputs'])
    count=2 if seeds['leaf']is not None else 1
    need(value['schema_version']=='supply-season-material-point-result-v1'and value['hold']is None and value['policy']==point.POLICY
         and value['candidate_RHS_evaluations']==34 and value['point_stage_RHS_evaluations']==count
         and value['point_order']==(['internode','leaf']if count==2 else['internode'])
         and raw(value['progress'])==raw({'stage':'final_source_check','candidate_RHS_evaluations':34,'point_RHS_evaluations':count,
             'candidate_failed_RHS_count_unreported':False,'past_confirmed_intervals_reintegrated':0}),
         'POINT_HOLD: exact original point scope and work witness required')
    for derived in [dense['derived'],value['after_derived']]:
        base.reader._closed(derived,set(n['last_confirmed']['derived']))
        for name,v in derived.items():
            base.reader._closed(v,{'value','unit'});base._vector([v['value']],1)
            need(v['unit']==n['last_confirmed']['derived'][name]['unit'],'UNIT_HOLD: actual source-derived unit required')
    jump=point.material.apply(None,data,numbers,definition['inputs'],source['event'],seeds,lambda *a:deepcopy(value['after_stage']))
    preview=point.point_books.calculate(None,data,numbers,jump)
    layout={**deepcopy(data['seed']['state_layout']),'original':point.material.source.stock.short._layout(jump['program']),
        'original_prefix_length':106+3*len(jump['program']['leaves'])+len(jump['program']['stem_root_compartments']),
        'internode_ids':[row['compartment_id']for row in jump['organs']['internodes']]}
    expected_fields={**preview,'after_program':jump['program'],'after_state':jump['state'],'after_organs':jump['organs'],
        'after_costs':jump['costs'],'after_state_layout':layout,'after_rates':jump['evaluation']['rates'],
        'after_derived':jump['evaluation']['derived'],'seed_compatibility':seeds['compatibility'],
        'new_birth_baselines':jump['new_birth_baselines'],'flow_components':jump['components'],
        'growth_costs':jump['growth_costs'],'leaf_receipts':jump['leaf_receipts'],
        'effective_rights':{k:s.rights[k]and definition['inputs']['rights'][k]for k in s.rights}}
    need(all(raw(value[k])==raw(v)for k,v in expected_fields.items()),'POINT_HOLD: exact source-derived material arithmetic and accounts required')
    base._vector(value['after_rates'],len(jump['state']))
    return jump,preview
