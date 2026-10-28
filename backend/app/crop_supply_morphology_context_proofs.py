"""Read-only arithmetic checks of original new-law point receipts; no replay."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path

from . import crop_supply_morphology_point as point

core,resume=point.core,point.resume
source=point.source
F,Q,X=resume.F,resume.Q,resume.X
need=resume._need
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
POINT_FIELDS=frozenset(['G0_G4', 'after_birth_baselines', 'after_costs', 'after_derived', 'after_organs', 'after_program', 'after_rates', 'after_stage', 'after_state', 'after_state_layout', 'at', 'before_candidate', 'before_candidate_sha256', 'birth_stage_version', 'calculation_sha256', 'candidate_new_RHS_evaluations', 'checkpoint_sha256', 'context_sha256', 'current_validation_RHS_evaluations', 'effects', 'elapsed_seconds_advanced', 'flow_components', 'global_prefix_adoption', 'growth_costs', 'initialization_scope', 'input_sha256', 'inputs', 'integrator_checkpoint', 'leaf_receipts', 'model_version', 'new_birth_baselines', 'past_intervals_reintegrated', 'point_balances', 'point_flows_exact', 'point_order', 'point_stage_RHS_evaluations', 'policy', 'post_point_global_ledgers_preview', 'post_point_lifetime_transfers_exact_preview', 'post_point_point_totals_exact_preview', 'preview_scope', 'redistribution_authorized', 'schedule_adoption', 'scope', 'seed_compatibility', 'source_code_sha256', 'source_event', 'time_kind'])
CANDIDATE_FIELDS=frozenset(['G0_G4', 'at', 'calculation_sha256', 'checkpoint_sha256', 'context_sha256', 'current_validation_RHS_evaluations', 'dense_candidate', 'integrator_checkpoint', 'ledger_rule', 'model_version', 'new_RHS_evaluations', 'new_organs_created', 'numerical_root_interval', 'partial_interval_seconds_exact', 'past_intervals_reintegrated', 'redistribution_authorized', 'refinement_scope', 'refinements', 'schedule_consumed', 'scope', 'selection_policy', 'source_code_sha256', 'source_interval', 'source_next_sequence', 'source_prefix', 'source_stage_sha256', 'stage', 'state_coordinates', 'state_differences', 'state_layout', 'threshold_exact', 'time_kind'])
STAGE_FIELDS=frozenset(['balance_budgets', 'balance_residuals', 'canopy_water_boundary', 'capacity_transport', 'crop', 'derivatives', 'derived', 'exchange', 'growth_respiration', 'internodes', 'leaf_partition', 'leaves', 'rates', 'stem_root_partition', 'stem_root_stocks'])


def _hash(value):return resume._hash(value)


def _calculation(value,version,pins):
    core.arithmetic._closed(value,POINT_FIELDS if version==point.VERSION else CANDIDATE_FIELDS)
    need(value['model_version']==version and value['source_code_sha256']==pins
        and value['calculation_sha256']==_hash({k:v for k,v in value.items()if k!='calculation_sha256'}),
        'PROOF_HOLD: original version/code/calculation bytes required')


def _trace(data,state,totals,trace):
    core.arithmetic._closed(trace,{'left_elapsed_seconds_exact','right_elapsed_seconds_exact','step_seconds_exact','stages','endpoint','flux_order'}|({'shoot_clock_certificate'}if 'shoot_clock_certificate'in trace else set()))
    core.arithmetic._closed(trace['endpoint'],{'state','rates','flux'})
    rows=trace['stages'];h=X(trace['step_seconds_exact']);at=X(trace['left_elapsed_seconds_exact']);combine=core.candidate.old._combine
    need(h>0 and X(trace['right_elapsed_seconds_exact'])==at+h and len(rows)==4,'PROOF_HOLD: actual interval required')
    units=resume.books.flux_units(data['program'],data['initial']['organs'])
    need(trace['flux_order']==[{'name':k,'unit':unit}for k,unit in units.items()]and rows[0]['state']==list(state),'PROOF_HOLD: actual original stage layout/left state required')
    for i,(row,name,offset)in enumerate(zip(rows,['k1','k2','k3','k4'],[Fraction(0),h/2,h/2,h],strict=True)):
        core.arithmetic._closed(row,{'stage','at_elapsed_seconds_exact','state','rates','flux'})
        need(row['stage']==name and row['at_elapsed_seconds_exact']==Q(at+offset,'s')and len(row['rates'])==len(state)and len(row['flux'])==len(units),
            'PROOF_HOLD: actual four stage times/arrays required')
        need(all(type(v)is float and isfinite(v)for v in row['state']+row['rates']+row['flux']),'PROOF_HOLD: finite binary64 stages required')
        if i:need(row['state']==list(combine(state,(tuple(rows[i-1]['rates']),),(Fraction(1),),offset)),'PROOF_HOLD: original stage arithmetic required')
    weights=(Fraction(1,6),Fraction(1,3),Fraction(1,3),Fraction(1,6))
    end=combine(state,tuple(tuple(r['rates'])for r in rows),weights,h)
    transfer=combine(totals,tuple(tuple(r['flux'])for r in rows),weights,h)
    need(trace['endpoint']['state']==list(end),'PROOF_HOLD: original RK4 endpoint required')
    return end,transfer


def _candidate(origin,data,result):
    candidate=point.candidate;before=result['before_candidate'];_calculation(before,candidate.VERSION,candidate._pins())
    cp=before['source_prefix'];need(before['context_sha256']==origin.root_sha256 and before['checkpoint_sha256']==_hash(cp),'PROOF_HOLD: actual source context and CP required')
    state,totals=resume._shape(origin,data,cp);at=X(cp['at']['elapsed_seconds_exact']);right=resume._time(data,cp['branch_steps']+1);trace=before['source_interval']
    need(X(trace['left_elapsed_seconds_exact'])==at and X(trace['right_elapsed_seconds_exact'])==right,'PROOF_HOLD: actual next original interval required')
    end,cumulative=_trace(data,state,totals,trace);clock=resume._clock(data,cumulative,right);cert=resume._interval_clock(data,cp,trace,clock)
    need(trace['shoot_clock_certificate']==cert and before['source_stage_sha256']==[_hash(r)for r in trace['stages']],'PROOF_HOLD: original monotone certificate/stage hashes required')
    root=before['numerical_root_interval'];tolerance=candidate._tolerance(root['time_tolerance_seconds_exact'],right-at)
    coefficients=[X(q)for q in cert['shoot_age_coefficients_exact']];coefficients[0]-=X(cp['schedule']['next_threshold_exact'])
    lo,hi,iterations=candidate.event._root_interval(tuple(coefficients),right-at,tolerance);duration=(right-at)*hi;weights=candidate.old._weights(hi)
    need(root=={'lower_elapsed_seconds_exact':Q(at+(right-at)*lo,'s'),'upper_elapsed_seconds_exact':Q(at+duration,'s'),
        'time_tolerance_seconds_exact':root['time_tolerance_seconds_exact'],'lower_threshold_residual_exact':Q(candidate.event._value(coefficients,lo),'degC_day'),
        'upper_threshold_residual_exact':Q(candidate.event._value(coefficients,hi),'degC_day'),'bisections':iterations},'PROOF_HOLD: exact first root interval required')
    dense=before['dense_candidate'];y=candidate.old._combine(state,tuple(tuple(r['rates'])for r in trace['stages']),weights,right-at)
    partial=candidate.old._combine((0.,)*len(totals),tuple(tuple(r['flux'])for r in trace['stages']),weights,right-at)
    checked=candidate.accounts.packet(origin,data,cp,y,partial,{'derived':dense['derived']},duration,1)
    need(dense==checked and dense['represented_threshold_status']=='crossed'and before['at']==dense['at']and before['partial_interval_seconds_exact']==Q(duration,'s'),
        'PROOF_HOLD: original dense state/flows/accounts/time required')
    need(before['state_layout']==data['initial']['state_layout']and before['state_coordinates']==resume._coordinates(data)
        and before['source_next_sequence']==cp['schedule']['next_sequence']and before['threshold_exact']==cp['schedule']['next_threshold_exact'],
        'PROOF_HOLD: original inventory and first event required')
    need(before['schedule_consumed']is False and before['new_organs_created']is False and before['integrator_checkpoint']is None
        and before['past_intervals_reintegrated']==0 and before['current_validation_RHS_evaluations']==1 and before['new_RHS_evaluations']==33,
        'PROOF_HOLD: original unadopted candidate scope required')
    for count,row in zip([1,2,4],before['refinements'],strict=True):
        y0=tuple(state);t=(0.,)*len(totals)
        need(row['substeps']==count and len(row['intervals'])==count and row['step_seconds_exact']==Q(duration/count,'s'),'PROOF_HOLD: original same-time refinement count required')
        for i,tr in enumerate(row['intervals']):
            need(X(tr['left_elapsed_seconds_exact'])==at+i*duration/count and X(tr['step_seconds_exact'])==duration/count,'PROOF_HOLD: exact refinement times required')
            y0,t=_trace(data,y0,t,tr)
        packet=candidate.accounts.packet(origin,data,cp,y0,t,{'derived':row['derived']},duration,count)
        need(all(row[k]==v for k,v in packet.items()),'PROOF_HOLD: original refined state/flows/accounts required')
    need(len(before['state_differences'])==len(before['state_coordinates'])==len(state),'PROOF_HOLD: complete original coordinate diagnostics required')
    need(before['scope']=='software_research_only'and before['G0_G4']=='not_assessed'and before['time_kind']=='synthetic_model_clock_not_observation'and before['redistribution_authorized']is data['initial']['redistribution_authorized'],'PROOF_HOLD: original candidate claim/rights scope required')
    for i,row in enumerate(before['state_differences']):
        unit=before['state_coordinates'][i]['unit'];a,b,c=[F(r['state'][i])for r in before['refinements']]
        need(row=={'coordinate':before['state_coordinates'][i],'dense_to_one_exact':Q(abs(F(y[i])-a),unit),'one_to_two_exact':Q(abs(a-b),unit),'two_to_four_exact':Q(abs(b-c),unit)},'PROOF_HOLD: actual same-time differences required')
    return before


def _component(mass,cost,capacity=0.,energy=0.):
    # Verify saved arithmetic without executing the funding/material operation.
    return {k:core.numeric._q(v,unit)for k,v,unit in [('structural_carbon',mass,core.MASS),
        ('growth_respiration',core.arithmetic._rounded(F(mass)*F(cost)),core.MASS),
        ('buffer_debit',core.arithmetic._rounded(F(mass)*(1+F(cost))),core.MASS),
        ('capacity_in',capacity,core.numeric.CAPACITY),('sensible_in',energy,core.numeric.ENERGY)]}


def validate(origin,result):
    data=resume._context(origin);_calculation(result,point.VERSION,point._pins());before=_candidate(origin,data,result)
    v=result['inputs'];core.arithmetic._closed(v,point.FIELDS);core.stem._rights(v['rights']);p=data['program'];event=core.source_event(data,before)
    need(result['source_event']==event and result['context_sha256']==v['context_sha256']==origin.root_sha256
        and result['checkpoint_sha256']==v['checkpoint_sha256']==before['checkpoint_sha256']and v['candidate_sha256']==result['before_candidate_sha256']==before['calculation_sha256']
        and v['initial_binding_sha256']==data['source_data']['source_snapshot']['manifest']['initial_binding_sha256']and result['input_sha256']==_hash(v),
        'PROOF_HOLD: actual original point inputs/source/candidate required')
    need(v['schema_version']=='supply-morphology-material-point-input-v1'and v['origin']=='synthetic'and v['policy']==point.POLICY
        and v['parameter_source']=='own_declared_synthetic_assumptions'and result['policy']==point.POLICY,'PROOF_HOLD: original synthetic construction policy required')
    part=source.stock.short.stock.part
    for name in ['input_id','reviewer','parent_internode_id','parameter_revision']:part._id(v[name])
    need(v['model_floor_area']==p['model_floor_area']and v['at_elapsed_seconds_exact']==before['at']['elapsed_seconds_exact']==result['at']['elapsed_seconds_exact']
        and result['at']==before['at']and type(v['source_threshold_sequence'])is int and v['source_threshold_sequence']==event['sequence']
        and v['source_threshold_exact']==event['threshold_exact']and v['source_event_id']==event['source_event_id'],'PROOF_HOLD: original point floor/time/event required')
    parents={r['compartment_id']for r in p['stem_root_compartments']if r['kind']=='internode'}
    need(v['parent_internode_id']in parents and event['internode_id']not in {r['compartment_id']for r in p['stem_root_compartments']}and event['leaf_id']not in {r['leaf_id']for r in p['leaves']},'PROOF_HOLD: actual current parent and unique child IDs required')
    node=v['internode'];core.arithmetic._closed(node,{'declaration','initial_length','construction_cost'});decl=node['declaration']
    core.arithmetic._closed(decl,{'compartment_id','kind',*source.stock.short.STOCK_FIELDS})
    values={k:core.arithmetic._quantity(decl[k],unit)for k,unit in source.stock.short.STOCK_FIELDS.items()}
    need(decl['compartment_id']==event['internode_id']and decl['kind']=='internode'and values['initial_carbon']>0 and values['sink_weight']>=0 and values['carbon_removal']==0,'PROOF_HOLD: original supported stem seed required')
    norm={**decl,**{k:core.numeric._q(value,source.stock.short.STOCK_FIELDS[k])for k,value in values.items()}}
    length=core.arithmetic._quantity(node['initial_length'],'m');cost=core.arithmetic._quantity(node['construction_cost'],'mg_CH2O/m_internode')
    binding=source.stock._source(origin._source._source);profile=binding['stem_selection']['source_state']['emergence_profile'];timeline=data['source_data']['point']['before_candidate']['source_root_certificate']['source_timeline']
    need(0<=length<=profile['curve']['values']['maximum_length']['value'],'PROOF_HOLD: original bounded seed length required')
    compatibility={'internode':core.compatibility(values['initial_carbon'],cost,length,p['model_floor_area']['value'],'m')}
    expected_program=deepcopy(p);expected_program['stem_root_compartments'].append(norm)
    y=before['dense_candidate']['state'];n=len(p['leaves']);m=len(p['stem_root_compartments']);h=len(data['initial']['organs']['internodes']);size=106+3*n+m
    stem_cost=core.stem._cost(data['profiles']);components={'internode':_component(values['initial_carbon'],stem_cost)}
    buffer=core.arithmetic._rounded(F(y[0])-F(components['internode']['buffer_debit']['value']));need(buffer>0 and buffer!=y[0],'PROOF_HOLD: original supported remaining stem buffer required')
    state=[*y[:size],values['initial_carbon'],*y[size:size+h],0.,*y[size+h:],length];state[0]=buffer
    bases={'leaf':[],'stem_root':[core.baseline(event['internode_id'],'internode',values['initial_carbon'],timeline['base_temperature'],before)]}
    meta=core._metadata(event['internode_id'],'internode',v['parent_internode_id'],event,bases['stem_root'][0],before)
    meta.update(curve=deepcopy(profile['curve']),seed_length=core.numeric._q(length,'m'),source_emergence_initial_length=deepcopy(profile['initial_length']))
    organs=deepcopy(data['initial']['organs']);organs['internodes'].append(meta);costs=deepcopy(data['costs']);costs['internodes'].append(cost);receipts=[];leaf_cost=None
    if v['leaf']is not None:
        packet=v['leaf'];core.arithmetic._closed(packet,{'declaration','incoming_temperature','construction_cost'});item=result['after_program']['leaves'][-1]
        source.stock.legacy._leaf_declaration(item,packet['declaration']);need(item['leaf_id']==event['leaf_id']and item['carbon_removal']['value']==0,'PROOF_HOLD: actual new leaf required')
        leaf_area=core.arithmetic.resume.short.old.leaf_area;area=leaf_area._area_at(Fraction(0),item['curve'])
        need(len(result['leaf_receipts'])==1,'PROOF_HOLD: one original leaf receipt required');receipt=result['leaf_receipts'][0];initial=receipt['initialization']
        need(leaf_area.normalize_leaf_area_state(state=initial['state'])==initial['state']and initial['state']['area']==area and initial['state']['leaf_id']==item['leaf_id']and X(initial['state']['age_exact'])==0,
            'PROOF_HOLD: original canonical leaf initialization evidence required')
        need(initial==leaf_area._envelope(initial['state'],{'operation':'initialize','input_id':item['leaf_id'],'state':initial['state']})and initial['state']['curve']==item['curve']and initial['state']['anchor']['requested_area']==item['initial_area'],'PROOF_HOLD: original complete initialization envelope/declaration required')
        leaf_cost=core.leaf._cost(data['profiles']);incoming=core.arithmetic._quantity(packet['incoming_temperature'],'degC');core.numeric._temperature(incoming)
        leaf_k=core.arithmetic._quantity(packet['construction_cost'],'mg_CH2O/m2_leaf')
        compatibility['leaf']=core.compatibility(item['initial_carbon']['value'],leaf_k,area['value'],p['model_floor_area']['value'],'m2')
        params=p['scenario']['parameters'];cap=core.arithmetic._rounded(F(params['leaf_heat_capacity']['value'])*F(area['value'])/F(p['model_floor_area']['value']))
        heat=core.arithmetic._rounded(F(cap)*(F(incoming)-F(params['reference_temperature']['value'])));need(cap>0,'PROOF_HOLD: original positive leaf capacity required')
        components['leaf']=_component(item['initial_carbon']['value'],leaf_cost,cap,heat);buffer=core.arithmetic._rounded(F(state[0])-F(components['leaf']['buffer_debit']['value']))
        need(buffer>0 and buffer!=state[0],'PROOF_HOLD: original remaining leaf buffer required');scalar=state[:106];scalar[0]=buffer;scalar[103]=core.arithmetic._rounded(F(state[103])+F(heat))
        state=[*scalar,*state[106:106+n],0.,*state[106+n:106+2*n],area['value'],*state[106+2*n:106+3*n],item['initial_carbon']['value'],*state[106+3*n:]]
        expected_program['leaves'].append(item);costs['leaves'].append(leaf_k)
        base=core.baseline(event['leaf_id'],'leaf',item['initial_carbon']['value'],item['base_temperature'],before);bases['leaf'].append(base)
        meta=core._metadata(event['leaf_id'],'leaf',event['internode_id'],event,base,before);meta.update(attachment_status='declared_material_parent_not_validated_anatomy',seed_area=area);organs['leaves'].append(meta)
        receipts=[{'event_id':event['leaf_event_id'],'parent_internode_id':event['internode_id'],'initialization':initial,'capacity_in':core.numeric._q(cap,core.numeric.CAPACITY),'sensible_in':core.numeric._q(heat,core.numeric.ENERGY)}]
    need(result['after_program']==expected_program and result['after_state']==state and result['after_costs']==costs and result['flow_components']==components
        and result['new_birth_baselines']==bases and result['leaf_receipts']==receipts and result['seed_compatibility']==compatibility,'PROOF_HOLD: original direct material state/parameters/receipts required')
    stage=result['after_stage'];core.arithmetic._closed(stage,STAGE_FIELDS);need(result['after_rates']==stage['rates']and result['after_derived']==stage['derived']and len(stage['rates'])==len(state),'PROOF_HOLD: original post-point stage required')
    jump={'program':expected_program,'state':state,'evaluation':stage,'components':components,'new_birth_baselines':bases,'organs':organs}
    preview=point.books.calculate(origin,data,before,jump)
    need(all(result[k]==v for k,v in preview.items())and result['after_organs']==organs,'PROOF_HOLD: original global/clock preview required')
    layout={**deepcopy(data['initial']['state_layout']),'original':source.stock.short._layout(expected_program),'original_prefix_length':106+3*len(expected_program['leaves'])+len(expected_program['stem_root_compartments']),
        'internode_ids':[r['compartment_id']for r in organs['internodes']]}
    need(result['after_state_layout']==layout and result['growth_costs']=={'cStemG':stem_cost,'cLeafG':leaf_cost,'unit':'mg_CH2O/mg_CH2O','profile_sha256':data['profiles']['growth_profile'].sha256},'PROOF_HOLD: original layout/growth profile costs required')
    need(result['redistribution_authorized']is (before['redistribution_authorized']and v['rights']['redistribute'])and result['point_order']==(['internode','leaf']if v['leaf']is not None else['internode'])
        and result['point_stage_RHS_evaluations']==1+(v['leaf']is not None)and result['current_validation_RHS_evaluations']==1 and result['candidate_new_RHS_evaluations']==33,
        'PROOF_HOLD: original rights and measured preparation work required')
    need(result['scope']=='software_research_only'and result['G0_G4']=='not_assessed'and result['schedule_adoption']=='not_performed'and result['integrator_checkpoint']is None
        and result['global_prefix_adoption']=='not_performed'and result['elapsed_seconds_advanced']==Q(Fraction(0),'s')and result['birth_stage_version']==core.stage.VERSION,'PROOF_HOLD: original unadopted point scope required')
    resume._fence(origin,data);return data
