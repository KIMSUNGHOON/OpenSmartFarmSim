"""Post-event shared-stage RK4; growing-geometry-removal-next-interval-v1.md."""
from copy import deepcopy
from dataclasses import dataclass,field
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite,ulp
from pathlib import Path

from . import crop_growing_geometry_post_removal_context as post

parent=post.parent
short=parent.short
numeric=short.numeric
VERSION='growing-geometry-removal-next-interval-research-v1'
CHECKPOINT_VERSION='growing-geometry-post-removal-continuation-checkpoint-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_CHECKPOINT_BYTES=256*1024
MAX_RESPONSE_BYTES=2*1024**2
_TOKEN=object()


class RemovalIntervalHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise RemovalIntervalHold(reason)


def _canonical(value):return parent._canonical(value)
def _hash(value):return sha256(_canonical(value)).hexdigest()
def _prefix(previous,sample):return _hash({'previous':previous,'sample':sample})


def _identity():
    return {'model_version':VERSION,'code_sha256':CODE_SHA256,'post_context_code_sha256':post.CODE_SHA256}


def _translate(error):
    if isinstance(error,RemovalIntervalHold):return error
    if isinstance(error,(post.PostRemovalContextHold,parent.ContinuationRejected)):return RemovalIntervalHold(str(error))
    return RemovalIntervalHold(str(short._translate(error)))


def _scope(context):
    try:return post._context(context)
    except(ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError)as error:raise _translate(error)from None


def _first(seed):return {'joint':{'derived':seed['last_confirmed']['derived']}}


def _exact(index,dt):
    value=Fraction.from_float(dt)*index
    return {'numerator':str(value.numerator),'denominator':str(value.denominator),'unit':'s'}


def _segment_balances(context,p,seed,state,totals,current,index,dt):
    return short._balances(p,tuple(seed['last_confirmed']['state']),state,totals,_first(seed),current,index,index*dt,
        context._parent._profiles[-1].values['latent_heat'])


def _global_balances(context,p,seed,m,state,totals,current,segment_budgets,index):
    original=json.loads(context._parent._seed);before=original['state'];old=json.loads(context._parent_checkpoint)
    event=context.point_result;prior=seed['original_interval_transfers']
    new=dict(zip(short.FLUX_UNITS,totals,strict=True));out=seed['point_outflows']
    first=original['evaluation']['joint']['derived'];last=current['joint']['derived']
    ca=first['air_capacity']['value'];latent=context._parent._profiles[-1].values['latent_heat']
    _need(ca==last['air_capacity']['value'],'BALANCE_HOLD: changed air capacity')
    def pair(name,sign=1):return (sign*prior[name]['value'],sign*new[name])
    carbon_indices=(0,1,2,*range(5,55));number_indices=tuple(range(55,105))
    carbon_terms=tuple(state[i]for i in carbon_indices)+tuple(-before[i]for i in carbon_indices)+pair('photosynthesis',-1)
    for name in ('growth_respiration','maintenance_leaf','maintenance_stem','maintenance_fruit','removal_leaf','removal_stem','terminal_carbon'):
        carbon_terms+=pair(name)
    carbon_terms+=(out['carbohydrate']['value'],)
    number_terms=tuple(state[i]for i in number_indices)+tuple(-before[i]for i in number_indices)+pair('entry_number',-1)+pair('terminal_number')
    du=(state[105],-before[105]);da=numeric._multiply(ca,numeric._sum(state[106],-before[106]))
    dw=numeric._sum(state[107],-before[107])
    sensible=du+pair('canopy_external',-1)+pair('sensible')+pair('latent')+pair('incoming_heat',-1)+pair('outgoing_heat')+(out['sensible_energy']['value'],)
    air=(da,*pair('air_external',-1),*pair('sensible',-1))
    vapor=(state[107],-before[107],*pair('vapor',-1),*pair('external_vapor',-1))
    capacity=(last['canopy_capacity']['value'],-first['canopy_capacity']['value'],*pair('capacity_in',-1),*pair('capacity_out'),out['capacity']['value'])
    reduced=du+(da,numeric._multiply(latent,dw),*pair('canopy_external',-1),*pair('air_external',-1),
        *(-numeric._multiply(latent,v)for v in pair('external_vapor')),*pair('incoming_heat',-1),*pair('outgoing_heat'),out['sensible_energy']['value'])
    rows={'carbohydrate':(carbon_terms,numeric.MASS,'carbon'),'number':(number_terms,'fruits_equivalent/m2_floor',None),
        'canopy_sensible':(sensible,numeric.ENERGY,'sensible_energy'),'air_sensible':(air,numeric.ENERGY,None),
        'vapor':(vapor,'kg_water/m2_floor',None),'area_capacity':(capacity,numeric.CAPACITY,'capacity'),
        'reduced_energy':(reduced,numeric.ENERGY,'sensible_energy')}
    old_keys={name:name for name in rows}
    dt=m['numerical']['step_seconds'];duration=numeric._multiply(index,dt)
    for i,original_index in enumerate(m['original_leaf_indices']):
        base=p['leaves'][i]['base_temperature']['value']
        terms=(state[108+i],-before[108+original_index],-numeric._divide(prior['indoor_air_temperature_time']['value'],86400),
            -numeric._divide(new['indoor_air_temperature_time'],86400),numeric._divide(numeric._multiply(base,duration),86400))
        name='leaf_age_'+str(i);rows[name]=(terms,'degC_day',None);old_keys[name]='leaf_age_'+str(original_index)
    residuals={};budgets={}
    for name,(terms,unit,event_key)in rows.items():
        scale=numeric._sum(*map(abs,terms));aggregation=numeric._multiply(64,ulp(scale))
        event_budget=0.0 if event_key is None else event['balances'][event_key]['budget']['value']
        budget=numeric._sum(old['balance_budgets'][old_keys[name]]['value'],event_budget,
            segment_budgets[name]['value'],aggregation)
        residual=numeric._sum(*terms)
        _need(abs(residual)<=budget,'GLOBAL_BALANCE_HOLD: '+name)
        residuals[name]=numeric._q(residual,unit);budgets[name]=numeric._q(budget,unit)
    return residuals,budgets


@dataclass(frozen=True)
class Checkpoint:
    _raw:bytes=field(repr=False)
    sha256:str
    context_sha256:str
    _token:object=field(repr=False)

    @property
    def value(self):return json.loads(self._raw)


def _seal(context,payload):
    raw=_canonical(payload);_need(len(raw)<=MAX_CHECKPOINT_BYTES,'CAPACITY_HOLD: 256KiB interval checkpoint required')
    return Checkpoint(raw,sha256(raw).hexdigest(),context.root_sha256,_TOKEN)


def _initial(context,p,seed,m):
    event_snapshot=post._initial_bytes(context,seed,m);index=m['numerical']['event_global_step_index']
    payload={'context_sha256':context.root_sha256,'original_global_step_index':index,
        'phase':'after_removal_before_next_step','segment_step_index':0,'at_elapsed_seconds_exact':deepcopy(m['at_elapsed_seconds_exact']),
        'last_confirmed':deepcopy(seed['last_confirmed']),
        'active_original_curve_invariant':deepcopy(seed['active_original_curve_invariant']),
        'original_interval_transfers':deepcopy(seed['original_interval_transfers']),
        'point_outflows':deepcopy(seed['point_outflows']),'segment_integrated_transfers':post._zeros(),
        'event_snapshot_sha256':sha256(event_snapshot).hexdigest(),
        **{name+'_sha256':_hash(seed[name])for name in ('original_curve_invariant','original_initial_area_receipts','removed_last_states')},
        'scope':'software_research_only','G0_G4':'not_assessed'}
    zero=(0.0,)*len(short.FLUX_UNITS);y=tuple(seed['last_confirmed']['state']);current=_first(seed)
    residuals,budgets=_segment_balances(context,p,seed,y,zero,current,0,m['numerical']['step_seconds'])
    global_residuals,global_budgets=_global_balances(context,p,seed,m,y,zero,current,budgets,index)
    return {**payload,'version':CHECKPOINT_VERSION,'engine_identity':_identity(),'global_step_index':index,
        'output_cursor':1,'output_prefix_sha256':_prefix(_hash({'context_sha256':context.root_sha256,'engine_identity':_identity()}),payload['last_confirmed']),
        'balance_residuals':residuals,'balance_budgets':budgets,
        'global_balance_residuals':global_residuals,'global_balance_budgets':global_budgets,
        'claim_scope':'synthetic_post_removal_joint_continuation_only'}


def start(context):
    p,seed,m=_scope(context)
    try:return _seal(context,_initial(context,p,seed,m))
    except(ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError,RecursionError)as error:raise _translate(error)from None


def checkpoint_bytes(context,checkpoint):
    _scope(context)
    _need(type(checkpoint)is Checkpoint and checkpoint._token is _TOKEN
        and checkpoint.context_sha256==context.root_sha256 and type(checkpoint._raw)is bytes
        and 0<len(checkpoint._raw)<=MAX_CHECKPOINT_BYTES and sha256(checkpoint._raw).hexdigest()==checkpoint.sha256,
        'CHECKPOINT_HOLD: immutable matching interval checkpoint required')
    return checkpoint._raw


def _validate(context,payload,p,seed,m):
    try:
        initial=_initial(context,p,seed,m)
        _need(type(payload)is dict and set(payload)==set(initial),'CHECKPOINT_HOLD: closed interval checkpoint required')
        variable={'phase','segment_step_index','global_step_index','at_elapsed_seconds_exact','last_confirmed','segment_integrated_transfers',
            'output_cursor','output_prefix_sha256','balance_residuals','balance_budgets','global_balance_residuals','global_balance_budgets'}
        _need(_canonical({k:v for k,v in payload.items()if k not in variable})==_canonical({k:v for k,v in initial.items()if k not in variable}),
            'CHECKPOINT_HOLD: changed engine/source/point/original ledgers')
        local=payload['segment_step_index'];event=m['numerical']['event_global_step_index'];dt=m['numerical']['step_seconds']
        _need(type(local)is int and 0<=local<=m['numerical']['remaining_steps']
            and type(payload['global_step_index'])is int and payload['global_step_index']==event+local
            and type(payload['output_cursor'])is int and payload['output_cursor']==local+1
            and parent._digest(payload['output_prefix_sha256']),'CHECKPOINT_HOLD: invalid index/cursor/prefix')
        _need(payload['at_elapsed_seconds_exact']==_exact(event+local,dt)
            and payload['phase']==('after_removal_before_next_step'if local==0 else'post_removal_interval'),
            'CHECKPOINT_HOLD: changed exact time/phase')
        sample=payload['last_confirmed'];_need(type(sample)is dict and set(sample)==set(seed['last_confirmed']),
            'CHECKPOINT_HOLD: closed current sample required')
        y=sample['state'];_need(type(y)is list and len(y)==len(seed['last_confirmed']['state'])
            and all(type(v)is float and isfinite(v)for v in y),'CHECKPOINT_HOLD: finite float64 current state required')
        rows=payload['segment_integrated_transfers'];_need(type(rows)is dict and set(rows)==set(short.FLUX_UNITS),
            'CHECKPOINT_HOLD: closed segment transfers required')
        for name,unit in short.FLUX_UNITS.items():
            row=rows[name];_need(type(row)is dict and set(row)=={'value','unit'}and row['unit']==unit
                and type(row['value'])is float and isfinite(row['value']),'CHECKPOINT_HOLD: finite float64 transfer/unit required')
        totals=tuple(rows[name]['value']for name in short.FLUX_UNITS)
        rates,current=short._evaluate(p,tuple(y),parent._profiles(context._parent))
        expected=short._sample(event+local,dt,y,current,seed['active_original_curve_invariant'])
        residuals,budgets=_segment_balances(context,p,seed,tuple(y),totals,current,local,dt)
        gr,gb=_global_balances(context,p,seed,m,tuple(y),totals,current,budgets,event+local)
        _need(_canonical(sample)==_canonical(expected)and all(_canonical(payload[k])==_canonical(v)for k,v in (
            ('balance_residuals',residuals),('balance_budgets',budgets),('global_balance_residuals',gr),('global_balance_budgets',gb))),
            'CHECKPOINT_HOLD: stale current state/derived/balances')
        if local==0:_need(_canonical(payload)==_canonical(initial),'CHECKPOINT_HOLD: original event snapshot required')
        return tuple(y),totals,rates,current
    except(ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError,RecursionError)as error:raise _translate(error)from None


def restore_checkpoint(context,raw_bytes,*,expected_sha256):
    p,seed,m=_scope(context)
    _need(type(raw_bytes)is bytes and 0<len(raw_bytes)<=MAX_CHECKPOINT_BYTES and parent._digest(expected_sha256)
        and sha256(raw_bytes).hexdigest()==expected_sha256,'CHECKPOINT_HOLD: trusted expected raw digest required')
    def pairs(items):
        result={}
        for key,value in items:_need(key not in result,'CHECKPOINT_HOLD: duplicate JSON key');result[key]=value
        return result
    def constant(value):raise RemovalIntervalHold('CHECKPOINT_HOLD: nonfinite JSON constant')
    try:
        payload=json.loads(raw_bytes.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
        _need(_canonical(payload)==raw_bytes,'CHECKPOINT_HOLD: canonical interval bytes required')
        _validate(context,payload,p,seed,m);return _seal(context,payload)
    except(ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError,RecursionError)as error:raise _translate(error)from None


def advance_chunk(context,checkpoint,step_budget):
    _need(type(step_budget)is int and 1<=step_budget<=128,'BUDGET_HOLD: 1..128 integer steps required')
    p,seed,m=_scope(context);raw=checkpoint_bytes(context,checkpoint)
    try:payload=json.loads(raw)
    except(ValueError,TypeError,UnicodeError,RecursionError):raise RemovalIntervalHold('CHECKPOINT_HOLD: invalid internal interval bytes')from None
    state,totals,rates,current=_validate(context,payload,p,seed,m)
    begin=payload['segment_step_index'];count=m['numerical']['remaining_steps'];event=m['numerical']['event_global_step_index']
    _need(begin<count,'COMPLETED_HOLD: no post-event step remains')
    dt=m['numerical']['step_seconds'];flux=short._flux(p,state,current);samples=[];attempts=0;held=None;confirmed=checkpoint
    local=begin;phase='ready'
    try:
        for local in range(begin+1,min(begin+step_budget,count)+1):
            phase='k2';y2=short._advance(state,rates,dt/2);attempts+=1;k2,r2=short._evaluate(p,y2,parent._profiles(context._parent))
            phase='k3';y3=short._advance(state,k2,dt/2);attempts+=1;k3,r3=short._evaluate(p,y3,parent._profiles(context._parent))
            phase='k4';y4=short._advance(state,k3,dt);attempts+=1;k4,r4=short._evaluate(p,y4,parent._profiles(context._parent))
            phase='endpoint';candidate=short._advance(state,short._weighted(rates,k2,k3,k4),dt)
            cumulative=short._advance(totals,short._weighted(flux,short._flux(p,y2,r2),short._flux(p,y3,r3),short._flux(p,y4,r4)),dt)
            attempts+=1;new_rates,new_rhs=short._evaluate(p,candidate,parent._profiles(context._parent))
            phase='endpoint_balance';residuals,budgets=_segment_balances(context,p,seed,candidate,cumulative,new_rhs,local,dt)
            phase='endpoint_global_balance';gr,gb=_global_balances(context,p,seed,m,candidate,cumulative,new_rhs,budgets,event+local)
            sample=short._sample(event+local,dt,candidate,new_rhs,seed['active_original_curve_invariant'])
            candidate_payload={**payload,'phase':'post_removal_interval','segment_step_index':local,'global_step_index':event+local,
                'at_elapsed_seconds_exact':_exact(event+local,dt),'output_cursor':local+1,
                'output_prefix_sha256':_prefix(payload['output_prefix_sha256'],sample),'last_confirmed':sample,
                'segment_integrated_transfers':{name:numeric._q(v,unit)for(name,unit),v in zip(short.FLUX_UNITS.items(),cumulative,strict=True)},
                'balance_residuals':residuals,'balance_budgets':budgets,'global_balance_residuals':gr,'global_balance_budgets':gb}
            phase='checkpoint';sealed=_seal(context,candidate_payload);new_flux=short._flux(p,candidate,new_rhs)
            state,totals,rates,current,flux=candidate,cumulative,new_rates,new_rhs,new_flux
            payload=candidate_payload;confirmed=sealed;samples.append(sample)
    except(ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError,RecursionError)as error:
        held={'segment_step_index':local,'global_step_index':event+local,'at_elapsed_seconds_exact':_exact(event+local,dt),
            'stage':phase,'reason':str(_translate(error))}
    result={'status':'hold'if held else'completed'if payload['segment_step_index']==count else'yielded',
        'scope':'software_research_only','claim_scope':'synthetic_post_removal_joint_continuation_only','G0_G4':'not_assessed',
        'engine_identity':_identity(),'context_sha256':context.root_sha256,'manifest':context.manifest,
        'segment_steps':payload['segment_step_index'],'global_steps':payload['global_step_index'],'planned_segment_steps':count,
        'output_start':begin+1,'samples':deepcopy(samples),'last_confirmed':deepcopy(payload['last_confirmed']),
        **{name:deepcopy(payload[name])for name in ('original_interval_transfers','point_outflows','segment_integrated_transfers',
            'balance_residuals','balance_budgets','global_balance_residuals','global_balance_budgets')},
        'checkpoint':None if held else confirmed,'confirmed_checkpoint':confirmed,'hold':held,
        'checkpoint_validation_stage_evaluations':1,'attempted_new_stage_evaluations':attempts,
        'confirmed_new_steps':payload['segment_step_index']-begin}
    serializable={**result,'checkpoint':None if held else confirmed.sha256,'confirmed_checkpoint':confirmed.sha256}
    _need(len(_canonical(serializable))<=MAX_RESPONSE_BYTES,'CAPACITY_HOLD: 2MiB interval response required')
    return result
