"""Genuine construction-limited Context/CP and original-grid shared RK4."""
from copy import deepcopy
from dataclasses import dataclass,field
from fractions import Fraction
from functools import wraps
from hashlib import sha256
from math import isfinite
from pathlib import Path
import json

from . import crop_supply_morphology_rhs as bound
from . import crop_supply_morphology_books as books

source=bound.source
numeric=source.numeric
Q,X=source.Q,source.X
F=Fraction.from_float
VERSION='supply-morphology-shared-stage-continuation-research-v1'
CONTEXT_VERSION='supply-morphology-context-v1'
CHECKPOINT_VERSION='supply-morphology-checkpoint-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
BOOK_SHA256=sha256(Path(books.__file__).read_bytes()).hexdigest()
MAX_BYTES=2*1024**2
MAX_CP=512*1024
_TOKEN=object()


class SupplyResumeHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise SupplyResumeHold(reason)


def _public(fn):
    @wraps(fn)
    def checked(*args,**kw):
        try:return fn(*args,**kw)
        except SupplyResumeHold:raise
        except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:
            raise SupplyResumeHold(str(error))from None
    return checked


def _canonical(value,maximum=MAX_BYTES):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    _need(len(raw)<=maximum,'CAPACITY_HOLD: bounded supply continuation bytes required')
    return raw


def _hash(value):return sha256(_canonical(value)).hexdigest()


def _parse(raw,expected,maximum=MAX_BYTES):
    _need(type(raw)is bytes and 0<len(raw)<=maximum and type(expected)is str and len(expected)==64 and sha256(raw).hexdigest()==expected,
        'HASH_HOLD: actual bounded bytes and trusted SHA required')
    value=json.loads(raw);_need(_canonical(value,maximum)==raw,'INPUT_HOLD: original canonical bytes required');return value


def _pins():
    pins={**bound._pins(),'backend/app/crop_supply_morphology_resume.py':CODE_SHA256,'backend/app/crop_supply_morphology_books.py':BOOK_SHA256}
    root=Path(__file__).resolve().parents[2]
    _need(all(sha256((root/name).read_bytes()).hexdigest()==h for name,h in pins.items()),'CODE_HOLD: original supply continuation sources required')
    return pins


@dataclass(frozen=True,eq=False)
class Context:
    _source:source.Context=field(repr=False)
    _parent:bytes=field(repr=False)
    _inputs:bytes=field(repr=False)
    _initial:bytes=field(repr=False)
    _raw:bytes=field(repr=False)
    root_sha256:str
    _token:object=field(repr=False)
    @property
    def value(self):return json.loads(self._raw)


@dataclass(frozen=True)
class Checkpoint:
    _raw:bytes=field(repr=False)
    sha256:str
    context_sha256:str
    _token:object=field(repr=False)
    @property
    def value(self):return json.loads(self._raw)


def _costs(context,parent,raw,p):
    v=json.loads(raw);part=source.stock.short.stock.part
    part._closed(v,{'schema_version','input_id','origin','policy','parameter_revision','parameter_source','reviewer','rights',
        'context_sha256','checkpoint_sha256','model_floor_area','leaves','internodes'})
    _need(v['schema_version']=='supply-morphology-stage-input-v1'and v['origin']=='synthetic'and v['policy']==bound.POLICY
        and v['parameter_source']=='own_declared_synthetic_assumptions','POLICY_HOLD: original explicit synthetic assumptions required')
    for key in ['input_id','parameter_revision','reviewer']:part._id(v[key])
    source.material.stem._rights(v['rights'])
    _need(v['context_sha256']==context.root_sha256 and v['checkpoint_sha256']==_hash(parent),'SOURCE_HOLD: actual original parameter source pair required')
    floor=part._number(v['model_floor_area'],'m2_floor');_need(floor>0 and part._q(floor,'m2_floor')==p['model_floor_area'],'BASIS_HOLD: original common floor required')
    normalized=deepcopy(v);normalized['model_floor_area']=part._q(floor,'m2_floor');costs={}
    for name,key,unit,ids in [('leaves','leaf_id','mg_CH2O/m2_leaf',[x['leaf_id']for x in p['leaves']]),
        ('internodes','compartment_id','mg_CH2O/m_internode',[x['compartment_id']for x in p['stem_root_compartments']if x['kind']=='internode'])]:
        rows=v[name];_need(type(rows)is list and len(rows)==len(ids),'INVENTORY_HOLD: complete geometry costs required');values=[]
        for row,identifier in zip(rows,ids,strict=True):
            part._closed(row,{key,'construction_cost'});_need(row[key]==identifier,'IDENTITY_HOLD: ordered actual geometry cost required')
            value=part._number(row['construction_cost'],unit);_need(value>0,'PARAMETER_HOLD: positive construction cost required');values.append(value)
        costs[name]=values;normalized[name]=[{key:identifier,'construction_cost':part._q(value,unit)}for identifier,value in zip(ids,values,strict=True)]
    return costs,normalized


def _fence(context,data):
    _need(type(context)is Context and context._token is _TOKEN and _canonical(data['descriptor'])==context._raw
        and _hash(data['descriptor'])==context.root_sha256,'CONTEXT_HOLD: genuine immutable new context required')
    header=data['descriptor']
    for key,raw in [('parent_checkpoint_sha256',context._parent),('parameter_input_sha256',context._inputs),('initial_bound_sha256',context._initial)]:
        _need(type(raw)is bytes and sha256(raw).hexdigest()==header[key],'SOURCE_HOLD: immutable context proofs required')
    _need(_canonical(data['initial'])==context._initial and _canonical(data['parent'],MAX_CP)==context._parent,
        'SOURCE_HOLD: unchanged parsed initial evidence required')
    expected={k:[x['construction_cost']['value']for x in data['initial']['parameters'][k]]for k in ['leaves','internodes']}
    _need(data['costs']==expected and header['parent_context_sha256']==context._source.root_sha256
        and header['source_code_sha256']==_pins(),'SOURCE_HOLD: actual source context, parameters and current code required')
    source._fence(context._source,data['source_data'])
    profiles=source.stock.parent._profiles(context._source._source._root)
    _need(set(data['profiles'])==set(profiles)and all(type(data['profiles'][k])is type(v)and vars(data['profiles'][k])==vars(v)for k,v in profiles.items()),
        'PROFILE_HOLD: actual complete current profile objects required')
    timeline=data['source_data']['point']['before_candidate']['source_root_certificate']['source_timeline']
    indices={row['compartment_id']:i for i,row in enumerate(data['program']['stem_root_compartments'])}
    _need(data['shoot_base_temperature']==timeline['base_temperature']['value']and data['stem_stock_indices']==[indices[row['compartment_id']]for row in data['initial']['organs']['internodes']],
        'SOURCE_HOLD: actual shoot base and stock identity indices required')


def _context(context):
    _need(type(context)is Context and context._token is _TOKEN,'CONTEXT_HOLD: genuine supply context required')
    _need(all(type(x)is bytes for x in [context._raw,context._parent,context._inputs,context._initial])
        and sum(map(len,[context._raw,context._parent,context._inputs,context._initial]))<=MAX_BYTES,'CAPACITY_HOLD: bounded complete context proof set required')
    h=_parse(context._raw,context.root_sha256);source.stock.arithmetic._closed(h,{'version','model_version','source_code_sha256',
        'parent_context_sha256','parent_checkpoint_sha256','parameter_input_sha256','initial_bound_sha256','scope','G0_G4'})
    _need(h['version']==CONTEXT_VERSION and h['model_version']==VERSION and h['scope']=='software_research_only'and h['G0_G4']=='not_assessed','SCOPE_HOLD: original supply context version required')
    parent=_parse(context._parent,h['parent_checkpoint_sha256'],MAX_CP);initial=_parse(context._initial,h['initial_bound_sha256'])
    inputs=_parse(context._inputs,h['parameter_input_sha256'],bound.MAX_INPUT_BYTES)
    sd=source._context(context._source);source._shape(context._source,sd,parent);p=sd['captured']['program']
    costs,normalized=_costs(context._source,parent,context._inputs,p)
    _need(initial['model_version']==bound.VERSION and initial['context_sha256']==context._source.root_sha256
        and initial['checkpoint_sha256']==h['parent_checkpoint_sha256']and initial['parameter_input_sha256']==h['parameter_input_sha256']
        and initial['parameters']==normalized and initial['source_code_sha256']==bound._pins()
        and initial['calculation_sha256']==_hash({k:v for k,v in initial.items()if k!='calculation_sha256'}),'SOURCE_HOLD: original bound stage and hashes required')
    organs=bound._organs(context._source,sd,parent);old=parent['last_confirmed']['state']
    state=[*old,*[x['represented_age']['value']for x in organs['internodes']],*[x['legacy_length']['value']for x in organs['internodes']]]
    _need(initial['organs']==organs and initial['state']==state and initial['at']==parent['at']
        and initial['stage_input_sha256']==_hash({'program':p,'state':state,'organs':organs,'costs':costs}),
        'SOURCE_HOLD: actual original state/geometry/birth clocks required')
    profiles=source.stock.parent._profiles(context._source._source._root)
    _need(initial['profile_sha256']=={k:v.sha256 for k,v in profiles.items()},'PROFILE_HOLD: original complete profiles required')
    timeline=sd['point']['before_candidate']['source_root_certificate']['source_timeline']
    indices={x['compartment_id']:i for i,x in enumerate(p['stem_root_compartments'])}
    data={'descriptor':h,'source_data':sd,'parent':parent,'initial':initial,'program':p,'costs':costs,'profiles':profiles,
        'shoot_base_temperature':timeline['base_temperature']['value'],'stem_stock_indices':[indices[x['compartment_id']]for x in organs['internodes']]}
    count=sd['captured']['original_numerical']['step_count']-parent['grid_index']
    _need(1<=count and X(parent['at']['elapsed_seconds_exact'])<_time(data,count),'HORIZON_HOLD: original time remaining required')
    _need((count+1)*(len(state)+len(books.flux_units(p,organs))+2*(len(p['leaves'])+len(organs['internodes']))+8)<=32768,
        'CAPACITY_HOLD: original horizon exceeds sample scalar budget')
    _fence(context,data);return data


@_public
def prepare_context(source_context,raw_checkpoint,*,expected_sha256,inputs):
    initial=bound.evaluate_bound_rhs(source_context,raw_checkpoint,expected_sha256=expected_sha256,inputs=inputs)
    initial_raw=_canonical(initial);raw_inputs=_canonical(inputs,bound.MAX_INPUT_BYTES)
    header={'version':CONTEXT_VERSION,'model_version':VERSION,'source_code_sha256':_pins(),'parent_context_sha256':source_context.root_sha256,
        'parent_checkpoint_sha256':expected_sha256,'parameter_input_sha256':sha256(raw_inputs).hexdigest(),
        'initial_bound_sha256':sha256(initial_raw).hexdigest(),'scope':'software_research_only','G0_G4':'not_assessed'}
    raw=_canonical(header);context=Context(source_context,raw_checkpoint,raw_inputs,initial_raw,raw,sha256(raw).hexdigest(),_TOKEN)
    _context(context);return context


@_public
def restore_context(source_context,raw_bytes,*,expected_sha256,proof_bytes):
    _need(type(proof_bytes)is dict and set(proof_bytes)=={'parent_checkpoint','inputs','initial_bound'},'INPUT_HOLD: complete immutable context proofs required')
    context=Context(source_context,proof_bytes['parent_checkpoint'],proof_bytes['inputs'],proof_bytes['initial_bound'],raw_bytes,expected_sha256,_TOKEN)
    _context(context);return context


@_public
def context_bytes(context):_context(context);return context._raw


@_public
def proof_bytes(context):
    _context(context);return {'parent_checkpoint':context._parent,'inputs':context._inputs,'initial_bound':context._initial}


def _time(data,steps):
    count=data['source_data']['captured']['original_numerical']['step_count'];index=data['parent']['grid_index']
    _need(type(steps)is int and 0<=steps<=count-index,'TIME_HOLD: original remaining endpoint count required')
    return X(data['parent']['at']['elapsed_seconds_exact'])if steps==0 else F(data['source_data']['captured']['original_numerical']['step_seconds'])*(index+steps)


def _clock(data,totals,at):
    units=books.flux_units(data['program'],data['initial']['organs']);air=F(totals[list(units).index('indoor_air_temperature_time')])
    elapsed=at-X(data['parent']['at']['elapsed_seconds_exact']);schedule=deepcopy(data['parent']['schedule'])
    age=X(schedule['age_exact'])+(air-F(data['shoot_base_temperature'])*elapsed)/86400
    _need(age>=X(schedule['age_exact']),'CLOCK_HOLD: monotone supported shoot clock required')
    schedule['age_exact']=Q(age,'degC_day');return schedule


def _sample(data,at,y,rhs):
    return {'at':{'time_origin_utc':data['initial']['at']['time_origin_utc'],'elapsed_seconds_exact':Q(at,'s')},
        'state':list(y),'derived':deepcopy(rhs['derived'])}


def _prefix(context,sample,steps,previous):
    return _hash({'context_sha256':context.root_sha256,'previous':previous,'sample_sha256':_hash(sample),
        'steps':steps,'phase':'branch_start'if steps==0 else'original_grid_endpoint'})


def _build(context,data,sample,totals,steps,link):
    at=_time(data,steps);_need(sample['at']=={'time_origin_utc':data['initial']['at']['time_origin_utc'],'elapsed_seconds_exact':Q(at,'s')},'TIME_HOLD: actual original grid point required')
    p=data['program'];units=books.flux_units(p,data['initial']['organs']);schedule=_clock(data,totals,at)
    _need(X(schedule['age_exact'])<X(schedule['next_threshold_exact']),'EVENT_HOLD: first due threshold requires new-law candidate')
    local,global_books,diagnostics,lifetime=books.calculate(context,data,sample['state'],{'derived':sample['derived']},totals,steps,at)
    if steps==0:
        _need(link is None,'PREFIX_HOLD: original branch prefix required');previous=data['parent']['output_prefix_sha256']
    else:
        source.stock.arithmetic._closed(link,{'previous_output_prefix_sha256','sample_sha256'})
        _need(source.stock.parent._digest(link['previous_output_prefix_sha256'])and link['sample_sha256']==_hash(sample),'PREFIX_HOLD: actual confirmed sample link required')
        previous=link['previous_output_prefix_sha256']
    return {'version':CHECKPOINT_VERSION,'model_version':VERSION,'source_code_sha256':_pins(),'context_sha256':context.root_sha256,
        'parent_context_sha256':context._source.root_sha256,'parent_checkpoint_sha256':data['descriptor']['parent_checkpoint_sha256'],
        'at':deepcopy(sample['at']),'branch_steps':steps,'grid_index':data['parent']['grid_index']+steps,
        'phase':'supply_morphology_branch_start'if steps==0 else'original_grid_endpoint',
        'event_sequence':data['parent']['event_sequence'],'schedule':schedule,'last_confirmed':deepcopy(sample),
        'branch_integrated_transfers':{name:numeric._q(v,unit)for(name,unit),v in zip(units.items(),totals,strict=True)},
        'lifetime_transfers_exact':{k:Q(v,units[k])for k,v in lifetime.items()},'point_totals_exact':deepcopy(data['parent']['point_totals_exact']),
        'branch_ledgers':local,'global_ledgers':global_books,'geometry_diagnostics':diagnostics,
        'output_cursor':data['parent']['output_cursor']+1+steps,'output_prefix_sha256':_prefix(context,sample,steps,previous),'output_prefix_link':deepcopy(link),
        'scope':'software_research_only','G0_G4':'not_assessed','redistribution_authorized':data['initial']['redistribution_authorized']}


def _seal(context,data,payload):
    raw=_canonical(payload,MAX_CP);_fence(context,data);return Checkpoint(raw,sha256(raw).hexdigest(),context.root_sha256,_TOKEN)


@_public
def start(context):
    data=_context(context);initial=data['initial'];totals=(0.,)*len(books.flux_units(data['program'],initial['organs']))
    sample=_sample(data,_time(data,0),initial['state'],initial['stage'])
    return _seal(context,data,_build(context,data,sample,totals,0,None))


def _raw_checkpoint(context,checkpoint):
    _need(type(checkpoint)is Checkpoint and checkpoint._token is _TOKEN and checkpoint.context_sha256==context.root_sha256
        and type(checkpoint._raw)is bytes and 0<len(checkpoint._raw)<=MAX_CP and sha256(checkpoint._raw).hexdigest()==checkpoint.sha256,
        'CHECKPOINT_HOLD: actual immutable matching new checkpoint required')
    return checkpoint._raw


def _shape(context,data,payload):
    y=payload['last_confirmed']['state'];initial=data['initial'];steps=payload['branch_steps'];_time(data,steps)
    _need(type(y)is list and len(y)==len(initial['state'])and all(type(v)is float and isfinite(v)for v in y),'STATE_HOLD: complete finite extended state required')
    source.stock.arithmetic._closed(payload['last_confirmed'],{'at','state','derived'})
    units=books.flux_units(data['program'],initial['organs']);source.stock.arithmetic._closed(payload['branch_integrated_transfers'],set(units))
    totals=[]
    for name,unit in units.items():
        row=payload['branch_integrated_transfers'][name];source.stock.legacy._captured_quantity(row,unit);totals.append(row['value'])
    expected=_build(context,data,payload['last_confirmed'],tuple(totals),steps,payload['output_prefix_link'])
    _need(_canonical(payload,MAX_CP)==_canonical(expected,MAX_CP),'CHECKPOINT_HOLD: actual state/time/flow/clock/books/prefix required')
    if steps==0:
        sample=_sample(data,_time(data,0),initial['state'],initial['stage'])
        _need(payload==_build(context,data,sample,(0.,)*len(units),0,None),'CHECKPOINT_HOLD: original branch seed required')
    return tuple(y),tuple(totals)


def _rhs(context,data,state,progress,label):
    _fence(context,data);progress['stage']=label
    _need(state[104]>=data['shoot_base_temperature'],'TEMPERATURE_DOMAIN_HOLD: air below shoot base')
    key='current_validation_RHS_evaluations'if label=='current_validation'else'new_RHS_evaluations';progress[key]+=1
    before=_canonical({'state':state,'organs':data['initial']['organs'],'costs':data['costs']})
    rhs=bound.stage.evaluate(data['program'],state,data['initial']['organs'],data['costs'],data['profiles'])
    _need(_canonical({'state':state,'organs':data['initial']['organs'],'costs':data['costs']})==before,'SOURCE_HOLD: unchanged new stage input required')
    _fence(context,data);return rhs


def _validate(context,data,payload,progress):
    y,totals=_shape(context,data,payload);rhs=_rhs(context,data,y,progress,'current_validation')
    _need(payload['last_confirmed']==_sample(data,_time(data,payload['branch_steps']),y,rhs),'CHECKPOINT_HOLD: actual new current RHS required')
    return y,totals,rhs


@_public
def checkpoint_bytes(context,checkpoint):
    data=_context(context);raw=_raw_checkpoint(context,checkpoint);_shape(context,data,_parse(raw,checkpoint.sha256,MAX_CP));_fence(context,data);return raw


@_public
def restore_checkpoint(context,raw_bytes,*,expected_sha256):
    data=_context(context);payload=_parse(raw_bytes,expected_sha256,MAX_CP);_validate(context,data,payload,{'current_validation_RHS_evaluations':0,'new_RHS_evaluations':0})
    return _seal(context,data,payload)


def _step(context,data,state,totals,rhs,at,h,progress):
    combine=source.candidate.old._combine;rows=[];p=data['program'];organs=data['initial']['organs']
    rates=tuple(rhs['rates']);flow=books.flux(p,state,rhs,organs)
    rows.append({'stage':'k1','at_elapsed_seconds_exact':Q(at,'s'),'state':list(state),'rates':list(rates),'flux':list(flow)})
    last_rates=rates
    for name,offset in [('k2',h/2),('k3',h/2),('k4',h)]:
        progress['stage']=name;trial=combine(state,(last_rates,),(Fraction(1),),offset)
        r=_rhs(context,data,trial,progress,name);last_rates=tuple(r['rates'])
        rows.append({'stage':name,'at_elapsed_seconds_exact':Q(at+offset,'s'),'state':list(trial),'rates':list(last_rates),'flux':list(books.flux(p,trial,r,organs))})
    weights=(Fraction(1,6),Fraction(1,3),Fraction(1,3),Fraction(1,6))
    progress['stage']='endpoint';candidate=combine(state,tuple(tuple(r['rates'])for r in rows),weights,h)
    cumulative=combine(totals,tuple(tuple(r['flux'])for r in rows),weights,h)
    end=_rhs(context,data,candidate,progress,'endpoint')
    return candidate,cumulative,end,{'left_elapsed_seconds_exact':Q(at,'s'),'right_elapsed_seconds_exact':Q(at+h,'s'),
        'step_seconds_exact':Q(h,'s'),'stages':rows,'endpoint':{'state':list(candidate),'rates':deepcopy(end['rates']),
            'flux':list(books.flux(p,candidate,end,organs))},'flux_order':[{'name':k,'unit':v}for k,v in books.flux_units(p,organs).items()]}


def _interval_clock(data,confirmed,trace,right_clock):
    h=X(trace['step_seconds_exact']);temperatures=[F(row['state'][104])for row in trace['stages']]
    a,b,c,d=temperatures;base=F(data['shoot_base_temperature'])
    coefficients=(X(confirmed['schedule']['age_exact']),h*(a-base)/86400,
        h*(-3*a/2+b+c-d/2)/86400,h*(2*a/3-2*b/3-2*c/3+2*d/3)/86400)
    _,c1,c2,c3=coefficients;derivatives=[c1,c1+2*c2+3*c3]
    if c3>0:
        vertex=-c2/(3*c3)
        if 0<vertex<1:derivatives.append(c1+2*c2*vertex+3*c3*vertex*vertex)
    minimum=min(derivatives)
    _need(minimum>=0,'SCHEDULE_HOLD: unresolved monotonicity of new shared-stage shoot polynomial')
    threshold=X(confirmed['schedule']['next_threshold_exact']);dense_right=sum(coefficients,Fraction(0))
    _need((dense_right>=threshold)==(X(right_clock['age_exact'])>=threshold),
        'SCHEDULE_ROUNDING_HOLD: dense and accumulated right threshold classifications differ')
    return {'shoot_age_coefficients_exact':[Q(v,'degC_day')for v in coefficients],
        'minimum_derivative_per_unit_theta_exact':Q(minimum,'degC_day'),
        'dense_right_age_exact':Q(dense_right,'degC_day'),'accumulated_right_age_exact':deepcopy(right_clock['age_exact']),
        'scope':'certified_dense_polynomial_monotonicity_not_physical_emergence_or_root_time_error'}


def _coordinates(data):
    layout=data['initial']['state_layout'];old=layout['original'];units=old['units'];rows=[]
    for name in old['plant']:rows.append({'block':'plant','name':name,'unit':units['plant'][name]})
    for name in old['cohort_arrays']:
        rows.extend({'block':name,'index':i,'unit':units['cohort_arrays'][name]}for i in range(50))
    for name in old['climate']:rows.append({'block':'climate','name':name,'unit':units['climate'][name]})
    for name in old['leaf_blocks']:
        rows.extend({'block':'leaf','name':name,'leaf_id':identifier,'unit':units['leaf_blocks'][name]}for identifier in old['leaf_ids'])
    for item in old['stem_root_compartments']:rows.append({'block':'stem_root','name':'carbon',**item,'unit':units['stem_root_blocks']['carbon']})
    for name in layout['appended_blocks']:
        rows.extend({'block':'internode','name':name,'compartment_id':identifier,'unit':layout['appended_units'][name]}for identifier in layout['internode_ids'])
    _need(len(rows)==len(data['initial']['state']),'STATE_HOLD: complete actual coordinate inventory required');return rows


@_public
def compare_interval_refinements(context,raw_checkpoint,*,expected_sha256):
    data=_context(context);payload=_parse(raw_checkpoint,expected_sha256,MAX_CP)
    progress={'current_validation_RHS_evaluations':0,'new_RHS_evaluations':0}
    state,totals,rhs=_validate(context,data,payload,progress);steps=payload['branch_steps'];left=_time(data,steps);right=_time(data,steps+1)
    rows=[]
    for count in (1,2,4):
        y,t,r=state,totals,rhs;h=(right-left)/count;traces=[]
        for i in range(count):
            y,t,r,trace=_step(context,data,y,t,r,left+i*h,h,progress);traces.append(trace)
        local,global_books,diagnostics,_=books.calculate(context,data,y,r,t,steps+count,right)
        rows.append({'subdivisions':count,'at':{'time_origin_utc':data['initial']['at']['time_origin_utc'],'elapsed_seconds_exact':Q(right,'s')},
            'state':list(y),'derived':deepcopy(r['derived']),'transfers':{name:numeric._q(v,unit)for(name,unit),v in zip(books.flux_units(data['program'],data['initial']['organs']).items(),t,strict=True)},
            'branch_ledgers':local,'global_ledgers':global_books,'geometry_diagnostics':diagnostics,'intervals':traces,
            'shoot_age_exact':_clock(data,t,right)['age_exact']})
    coordinates=_coordinates(data)
    differences=[{'coordinate':coordinate,'one_to_two_exact':Q(abs(F(rows[0]['state'][i])-F(rows[1]['state'][i])),coordinate['unit']),
        'two_to_four_exact':Q(abs(F(rows[1]['state'][i])-F(rows[2]['state'][i])),coordinate['unit'])}for i,coordinate in enumerate(coordinates)]
    out={'version':VERSION,'context_sha256':context.root_sha256,'checkpoint_sha256':expected_sha256,'rows':rows,'state_differences':differences,
        **progress,'scope':'readonly_same_time_numerical_diagnostic_not_adopted_trajectory_or_error_guarantee','checkpoint_issued':False,
        'threshold_scope':'unadopted_right_candidates_no_material_point','G0_G4':'not_assessed'}
    _fence(context,data);_canonical(out);return out


@_public
def advance_chunk(context,checkpoint,step_budget):
    _need(type(step_budget)is int and 1<=step_budget<=128,'BUDGET_HOLD: 1..128 original endpoints required')
    data=_context(context);raw=_raw_checkpoint(context,checkpoint);payload=_parse(raw,checkpoint.sha256,MAX_CP)
    progress={'stage':'current_validation','current_validation_RHS_evaluations':0,'new_RHS_evaluations':0}
    state,totals,rhs=_validate(context,data,payload,progress);steps=payload['branch_steps'];confirmed=payload
    samples=[];intervals=[];pending=None;reason=None;status='yielded';remaining=data['source_data']['captured']['original_numerical']['step_count']-payload['grid_index']
    _need(remaining>0,'COMPLETED_HOLD: original horizon already completed')
    try:
        for _ in range(min(step_budget,remaining)):
            at=_time(data,steps);right=_time(data,steps+1)
            candidate,cumulative,end,trace=_step(context,data,state,totals,rhs,at,right-at,progress)
            clock=_clock(data,cumulative,right)
            progress['stage']='interval_clock';trace['shoot_clock_certificate']=_interval_clock(data,confirmed,trace,clock)
            if X(clock['age_exact'])>=X(clock['next_threshold_exact']):
                pending={'scope':'unrefined_new_shared_stage_endpoint_bracket_only','left_at':deepcopy(confirmed['at']),
                    'right_at':{'time_origin_utc':data['initial']['at']['time_origin_utc'],'elapsed_seconds_exact':Q(right,'s')},
                    'left_age_exact':deepcopy(confirmed['schedule']['age_exact']),'right_age_exact':clock['age_exact'],
                    'source_next_sequence':clock['next_sequence'],'threshold_exact':clock['next_threshold_exact'],'interval':trace,
                    'candidate_or_checkpoint_issued':False,'schedule_consumed':False}
                reason='EVENT_HOLD: new-law first pending threshold requires a refined candidate';status='hold';break
            progress['stage']='endpoint_books';sample=_sample(data,right,candidate,end)
            link={'previous_output_prefix_sha256':confirmed['output_prefix_sha256'],'sample_sha256':_hash(sample)}
            proposed=_build(context,data,sample,cumulative,steps+1,link);sealed=_seal(context,data,proposed)
            _canonical({'samples':[*samples,sample],'intervals':[*intervals,trace],'last_confirmed':proposed})
            state,totals,rhs=candidate,cumulative,end;steps+=1;confirmed=sealed.value;samples.append(sample);intervals.append(trace)
        if status!='hold'and confirmed['grid_index']==data['source_data']['captured']['original_numerical']['step_count']:status='completed'
        _fence(context,data);_need(_raw_checkpoint(context,checkpoint)==raw,'SOURCE_HOLD: caller checkpoint changed during advance')
    except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:
        reason=str(error);status='hold'
        try:_fence(context,data);_need(_raw_checkpoint(context,checkpoint)==raw,'SOURCE_HOLD: caller checkpoint changed')
        except(ValueError,TypeError,KeyError,AttributeError,OSError):
            samples=[];intervals=[];confirmed=None;pending=None
    result={'status':status,'hold':reason,'failed_stage':progress['stage']if status=='hold'else None,
        'samples':samples,'intervals':intervals,'pending_event':pending,'last_confirmed':deepcopy(confirmed),
        'checkpoint':None if status=='hold'else _seal(context,data,confirmed),**progress,'scope':'software_research_only','G0_G4':'not_assessed'}
    public={k:v for k,v in result.items()if k!='checkpoint'};_canonical(public);return result
