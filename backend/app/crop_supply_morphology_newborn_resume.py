"""Original-grid continuation from a genuine post-material seed, without events."""
from copy import deepcopy
from dataclasses import dataclass,field
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path

from . import crop_supply_morphology_context as owner
from . import crop_supply_morphology_newborn_books as books

resume=owner.resume
source=owner.source
F,Q,X=owner.F,owner.Q,owner.X
VERSION='supply-morphology-newborn-continuation-research-v1'
CHECKPOINT_VERSION='supply-morphology-newborn-checkpoint-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES,MAX_CP=owner.MAX_BYTES,owner.MAX_CP
_TOKEN=object()
SupplyNewbornHold=owner.SupplyContextHold
_need=owner._need
_public=owner._public
_canonical,_hash,_parse=owner._canonical,owner._hash,resume._parse


def _pins():
    pins={**owner._pins(),'backend/app/crop_supply_morphology_newborn_resume.py':CODE_SHA256,'backend/app/crop_supply_morphology_newborn_books.py':books.CODE_SHA256}
    root=Path(__file__).resolve().parents[2]
    _need(all(sha256((root/k).read_bytes()).hexdigest()==v for k,v in pins.items()),'CODE_HOLD: original newborn continuation sources required');return pins


def _context(context):
    data=owner._context(context);p=data['program'];indices={v['compartment_id']:i for i,v in enumerate(p['stem_root_compartments'])}
    data['stem_stock_indices']=[indices[v['compartment_id']]for v in data['organs']['internodes']]
    data['shoot_base_temperature']=data['origin_data']['shoot_base_temperature']
    data['seed_checkpoint_sha256']=_hash(owner._seed_checkpoint(context,data));_fence(context,data);return data


def _fence(context,data):
    owner._fence(context,data);_pins()
    indices={v['compartment_id']:i for i,v in enumerate(data['program']['stem_root_compartments'])}
    _need(data['stem_stock_indices']==[indices[v['compartment_id']]for v in data['organs']['internodes']]
        and data['shoot_base_temperature']==data['origin_data']['shoot_base_temperature']
        and data['seed_checkpoint_sha256']==_hash(owner._seed_checkpoint(context,data)),'SOURCE_HOLD: unchanged actual newborn projections required')


@dataclass(frozen=True)
class Checkpoint:
    _raw:bytes=field(repr=False)
    sha256:str
    context_sha256:str
    _token:object=field(repr=False)
    @property
    def value(self):return resume.json.loads(self._raw)


def _time(data,steps):
    seed=data['seed'];numerical=seed['original_numerical'];index=seed['original_grid_position']['completed_grid_index']
    _need(type(steps)is int and 0<=steps<=numerical['step_count']-index,'TIME_HOLD: original remaining endpoint count required')
    return X(seed['initial_sample']['at']['elapsed_seconds_exact'])if steps==0 else F(numerical['step_seconds'])*(index+steps)


def _clock(data,totals,at):
    seed=data['seed'];units=books.flux_units(data['program'],data['organs']);air=F(totals[list(units).index('indoor_air_temperature_time')])
    schedule=deepcopy(seed['schedule']);duration=at-_time(data,0);age=X(schedule['age_exact'])+(air-F(data['shoot_base_temperature'])*duration)/86400
    _need(age>=X(schedule['age_exact']),'CLOCK_HOLD: monotone supported newborn shoot clock required');schedule['age_exact']=Q(age,'degC_day');return schedule


def _sample(data,at,state,rhs):
    return {'at':{'time_origin_utc':data['seed']['initial_sample']['at']['time_origin_utc'],'elapsed_seconds_exact':Q(at,'s')},'state':list(state),'derived':deepcopy(rhs['derived'])}


def _prefix(context,data,sample,steps,previous):
    return _hash({'context_sha256':context.root_sha256,'seed_checkpoint_sha256':data['seed_checkpoint_sha256'],'previous':previous,'sample_sha256':_hash(sample),
        'steps':steps,'phase':'original_grid_endpoint','model_version':VERSION})


def _build(context,data,sample,totals,steps,link):
    seed=data['seed'];at=_time(data,steps);_need(sample['at']==_sample(data,at,[],{'derived':{}})['at'],'TIME_HOLD: actual original grid endpoint required')
    schedule=_clock(data,totals,at);_need(X(schedule['age_exact'])<X(schedule['next_threshold_exact']),'EVENT_HOLD: next pending threshold requires new-owner candidate')
    local,global_books,diagnostics,lifetime=books.calculate(context,data,sample['state'],{'derived':sample['derived']},totals,steps,at)
    if steps==0:
        _need(link is None,'PREFIX_HOLD: original actual material seed prefix required');prefix=seed['output_prefix_sha256']
    else:
        source.stock.arithmetic._closed(link,{'previous_output_prefix_sha256','sample_sha256'})
        _need(source.stock.parent._digest(link['previous_output_prefix_sha256'])and link['sample_sha256']==_hash(sample),'PREFIX_HOLD: actual confirmed endpoint link required')
        prefix=_prefix(context,data,sample,steps,link['previous_output_prefix_sha256'])
    return {'version':CHECKPOINT_VERSION,'model_version':VERSION,'source_code_sha256':_pins(),'context_sha256':context.root_sha256,
        'seed_checkpoint_sha256':data['seed_checkpoint_sha256'],'origin_context_sha256':context._origin.root_sha256,'point_sha256':data['descriptor']['point_sha256'],
        'at':deepcopy(sample['at']),'branch_steps':steps,'grid_index':seed['original_grid_position']['completed_grid_index']+steps,
        'phase':'fractional_after_compatible_material_point'if steps==0 else'original_grid_endpoint','event_sequence':seed['event_sequence'],'schedule':schedule,'last_confirmed':deepcopy(sample),
        'branch_integrated_transfers':{k:resume.numeric._q(v,unit)for(k,unit),v in zip(books.flux_units(data['program'],data['organs']).items(),totals,strict=True)},
        'lifetime_transfers_exact':{k:Q(v,books.flux_units(data['program'],data['organs'])[k])for k,v in lifetime.items()},'point_totals_exact':deepcopy(seed['point_totals_exact']),
        'branch_ledgers':local,'global_ledgers':global_books,'geometry_diagnostics':diagnostics,'transfer_origins':deepcopy(seed['transfer_origins']),
        'output_cursor':seed['output_cursor']+steps,'output_prefix_sha256':prefix,'output_prefix_link':deepcopy(link),
        'scope':'software_research_only','G0_G4':'not_assessed','redistribution_authorized':seed['redistribution_authorized']}


def _seal(context,data,payload):
    raw=_canonical(payload,MAX_CP);_fence(context,data);return Checkpoint(raw,sha256(raw).hexdigest(),context.root_sha256,_TOKEN)


@_public
def start(context):
    data=_context(context);return _seal(context,data,_build(context,data,data['seed']['initial_sample'],(0.,)*len(books.flux_units(data['program'],data['organs'])),0,None))


def _raw(context,checkpoint):
    _need(type(checkpoint)is Checkpoint and checkpoint._token is _TOKEN and checkpoint.context_sha256==context.root_sha256
        and type(checkpoint._raw)is bytes and 0<len(checkpoint._raw)<=MAX_CP and sha256(checkpoint._raw).hexdigest()==checkpoint.sha256,'CHECKPOINT_HOLD: genuine newborn continuation CP required');return checkpoint._raw


def _shape(context,data,payload):
    sample=payload['last_confirmed'];y=sample['state'];steps=payload['branch_steps'];_time(data,steps)
    _need(type(y)is list and len(y)==len(data['seed']['initial_sample']['state'])and all(type(v)is float and isfinite(v)for v in y),'STATE_HOLD: complete finite actual newborn state required')
    source.stock.arithmetic._closed(sample,{'at','state','derived'});units=books.flux_units(data['program'],data['organs']);source.stock.arithmetic._closed(payload['branch_integrated_transfers'],set(units));totals=[]
    for name,unit in units.items():
        quantity=payload['branch_integrated_transfers'][name];source.stock.legacy._captured_quantity(quantity,unit);totals.append(quantity['value'])
    _need(payload==_build(context,data,sample,tuple(totals),steps,payload['output_prefix_link']),'CHECKPOINT_HOLD: exact newborn state/time/clock/accounts/prefix required')
    if steps==0:_need(sample==data['seed']['initial_sample']and all(v==0. for v in totals),'CHECKPOINT_HOLD: actual material seed required')
    return tuple(y),tuple(totals)


def _rhs(context,data,state,progress,label):
    _fence(context,data);progress['stage']=label;_need(state[104]>=data['shoot_base_temperature'],'TEMPERATURE_DOMAIN_HOLD: air below shoot base')
    key='current_validation_RHS_evaluations'if label=='current_validation'else'new_RHS_evaluations';progress[key]+=1
    snapshot=_canonical({'program':data['program'],'state':state,'organs':data['organs'],'costs':data['costs']})
    rhs=owner.point.core.stage.evaluate(data['program'],state,data['organs'],data['costs'],data['profiles'])
    _need(snapshot==_canonical({'program':data['program'],'state':state,'organs':data['organs'],'costs':data['costs']}),'SOURCE_HOLD: unchanged actual newborn stage input required');_fence(context,data);return rhs


def _validate(context,data,payload,progress):
    y,t=_shape(context,data,payload);rhs=_rhs(context,data,y,progress,'current_validation')
    _need(payload['last_confirmed']==_sample(data,_time(data,payload['branch_steps']),y,rhs),'CHECKPOINT_HOLD: actual current newborn RHS required');return y,t,rhs


@_public
def checkpoint_bytes(context,checkpoint):
    data=_context(context);raw=_raw(context,checkpoint);_shape(context,data,_parse(raw,checkpoint.sha256,MAX_CP));_fence(context,data);return raw


@_public
def restore_checkpoint(context,raw_bytes,*,expected_sha256):
    data=_context(context);payload=_parse(raw_bytes,expected_sha256,MAX_CP);_validate(context,data,payload,{'current_validation_RHS_evaluations':0,'new_RHS_evaluations':0});return _seal(context,data,payload)


def _step(context,data,state,totals,rhs,at,h,progress):
    combine=source.candidate.old._combine;rows=[];p=data['program'];organs=data['organs']
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


_interval_clock=resume._interval_clock

@_public
def advance_chunk(context,checkpoint,step_budget):
    _need(type(step_budget)is int and 1<=step_budget<=128,'BUDGET_HOLD: 1..128 original endpoints required')
    data=_context(context);raw=_raw(context,checkpoint);payload=_parse(raw,checkpoint.sha256,MAX_CP)
    progress={'stage':'current_validation','current_validation_RHS_evaluations':0,'new_RHS_evaluations':0}
    state,totals,rhs=_validate(context,data,payload,progress);steps=payload['branch_steps'];confirmed=payload
    samples=[];intervals=[];pending=None;reason=None;status='yielded';remaining=data['seed']['original_numerical']['step_count']-payload['grid_index']
    _need(remaining>0,'COMPLETED_HOLD: original horizon already completed')
    try:
        for _ in range(min(step_budget,remaining)):
            at=_time(data,steps);right=_time(data,steps+1)
            candidate,cumulative,end,trace=_step(context,data,state,totals,rhs,at,right-at,progress)
            clock=_clock(data,cumulative,right)
            progress['stage']='interval_clock';trace['shoot_clock_certificate']=_interval_clock(data,confirmed,trace,clock)
            if X(clock['age_exact'])>=X(clock['next_threshold_exact']):
                pending={'scope':'unrefined_new_shared_stage_endpoint_bracket_only','left_at':deepcopy(confirmed['at']),
                    'right_at':{'time_origin_utc':data['seed']['initial_sample']['at']['time_origin_utc'],'elapsed_seconds_exact':Q(right,'s')},
                    'left_age_exact':deepcopy(confirmed['schedule']['age_exact']),'right_age_exact':clock['age_exact'],
                    'source_next_sequence':clock['next_sequence'],'threshold_exact':clock['next_threshold_exact'],'interval':trace,
                    'candidate_or_checkpoint_issued':False,'schedule_consumed':False}
                reason='EVENT_HOLD: new-law first pending threshold requires a refined candidate';status='hold';break
            progress['stage']='endpoint_books';sample=_sample(data,right,candidate,end)
            link={'previous_output_prefix_sha256':confirmed['output_prefix_sha256'],'sample_sha256':_hash(sample)}
            proposed=_build(context,data,sample,cumulative,steps+1,link);sealed=_seal(context,data,proposed)
            _canonical({'samples':[*samples,sample],'intervals':[*intervals,trace],'last_confirmed':proposed})
            state,totals,rhs=candidate,cumulative,end;steps+=1;confirmed=sealed.value;samples.append(sample);intervals.append(trace)
        if status!='hold'and confirmed['grid_index']==data['seed']['original_numerical']['step_count']:status='completed'
        _fence(context,data);_need(_raw(context,checkpoint)==raw,'SOURCE_HOLD: caller checkpoint changed during advance')
    except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:
        reason=str(error);status='hold'
        try:_fence(context,data);_need(_raw(context,checkpoint)==raw,'SOURCE_HOLD: caller checkpoint changed')
        except(ValueError,TypeError,KeyError,AttributeError,OSError):
            samples=[];intervals=[];confirmed=None;pending=None
    result={'status':status,'hold':reason,'failed_stage':progress['stage']if status=='hold'else None,
        'samples':samples,'intervals':intervals,'pending_event':pending,'last_confirmed':deepcopy(confirmed),
        'checkpoint':None if status=='hold'else _seal(context,data,confirmed),**progress,'past_intervals_reintegrated':0,'scope':'software_research_only','G0_G4':'not_assessed'}
    public={k:v for k,v in result.items()if k!='checkpoint'};_canonical(public);return result
