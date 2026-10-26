"""Immutable individual organ resume; crop-stem-root-stock-continuation-v1.md."""
from copy import deepcopy
from dataclasses import dataclass,field
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import platform
import sys

from . import crop_stem_root_stock_dynamics as short

VERSION='stem-root-stock-dynamics-continuation-research-v1'
CHECKPOINT_VERSION='individual-stem-root-leaf-carbon-area-checkpoint-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
PROFILE_NAMES=('growth','cohort','transport','exchange')
MAX_CONTEXT_BYTES=2*1024**2
MAX_CHECKPOINT_BYTES=512*1024
_TOKEN=object()


class ContinuationRejected(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise ContinuationRejected(reason)


def _canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def _hash(value):return sha256(_canonical(value)).hexdigest()
def _digest(value):return type(value)is str and len(value)==64 and all(c in '0123456789abcdef'for c in value)
def _prefix(previous,sample):return _hash({'previous':previous,'sample':sample})


def _fence():
    try:
        _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256,
            'CODE_HOLD: original continuation source required')
        short._fence()
    except ContinuationRejected:raise
    except(short.StemRootDynamicsHold,OSError):
        raise ContinuationRejected('CODE_HOLD: continuation component unavailable or changed')from None


def _identity(profiles):
    _fence()
    return {'engine_version':VERSION,'engine_code_sha256':CODE_SHA256,'short_code_sha256':short.CODE_SHA256,
        'component_code_sha256':dict(short.COMPONENT_CODE_SHA256),
        'profile_sha256':{name:p.sha256 for name,p in zip(PROFILE_NAMES,profiles,strict=True)},
        'policies':dict(short.POLICIES),'state_schema':'individual-stem-root-leaf-carbon-area-vector-v1',
        'python_version':platform.python_version(),'platform_system':platform.system(),'platform_machine':platform.machine(),
        'byteorder':sys.byteorder,'float_mant_dig':sys.float_info.mant_dig,'float_radix':sys.float_info.radix}


@dataclass(frozen=True)
class Context:
    _request:bytes=field(repr=False)
    _program:bytes=field(repr=False)
    _seed:bytes=field(repr=False)
    _manifest:bytes=field(repr=False)
    root_sha256:str
    _profiles:tuple=field(repr=False)
    _token:object=field(repr=False)

    @property
    def program(self):return json.loads(self._request)

    @property
    def manifest(self):return json.loads(self._manifest)


@dataclass(frozen=True)
class Checkpoint:
    _raw:bytes=field(repr=False)
    sha256:str
    context_sha256:str
    _token:object=field(repr=False)

    @property
    def value(self):return json.loads(self._raw)


def _profiles(context):return {name+'_profile':p for name,p in zip(PROFILE_NAMES,context._profiles,strict=True)}


def _context(context):
    _need(type(context)is Context and context._token is _TOKEN,'CONTEXT_HOLD: prepared context required')
    try:
        parts=(context._request,context._program,context._seed,context._manifest)
        _need(all(type(v)is bytes for v in parts)and sum(map(len,parts))<=MAX_CONTEXT_BYTES,
              'CONTEXT_HOLD: bounded immutable bytes required')
        m=context.manifest
        _need(_hash(m)==context.root_sha256 and m['identity']==_identity(context._profiles),
              'CONTEXT_HOLD: changed code/profile/environment')
        for name,raw in zip(('request','program','seed'),parts[:3],strict=True):
            _need(m[name+'_sha256']==sha256(raw).hexdigest(),'CONTEXT_HOLD: changed request/program/seed')
        return json.loads(context._program),json.loads(context._seed),m
    except ContinuationRejected:
        raise
    except(UnicodeError,ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,RecursionError):
        raise ContinuationRejected('CONTEXT_HOLD: invalid immutable context')from None


def prepare_context(*,program,step_seconds,step_count,**profiles):
    try:
        _fence()
        _need(set(profiles)=={name+'_profile'for name in PROFILE_NAMES},'PROFILE_HOLD: exactly four profiles required')
        _need(type(step_seconds)in(int,float),'BUDGET_HOLD: explicit numeric step required');dt=float(step_seconds)
        _need(isfinite(dt)and dt>0 and type(step_count)is int and 1<=step_count<=4096,
              'BUDGET_HOLD: positive step and 1..4096 integer steps required')
        duration=short.numeric._multiply(dt,step_count);_need(0<duration<=600,'BUDGET_HOLD: 600s research horizon')
        request,p,y,receipts=short._prepare(program);n=len(p['leaves'])
        _need((step_count+1)*(len(y)+2*n+9)<=32768,'CAPACITY_HOLD: sample scalar budget exceeded')
        _,first=short._evaluate(p,y,profiles)
        raw=_canonical(p);seed=_canonical({'state':list(y),'evaluation':first,'initial_area_receipts':receipts})
        parts=tuple(profiles[name+'_profile']for name in PROFILE_NAMES)
        m={'identity':_identity(parts),'request_sha256':sha256(request).hexdigest(),
            'program_sha256':sha256(raw).hexdigest(),'seed_sha256':sha256(seed).hexdigest(),
            'numerical':{'step_seconds':dt,'step_count':step_count,'duration_seconds':duration,
                'method':'shared-stage-fixed-rk4-leaf-stem-root-carbon-area-v1','sample_scalar_budget':32768,
                'roundoff_rule':'64-ulp-per-step-ledger-v1','time_coordinate':'elapsed_seconds_no_UTC_checkpoint'},
            'state_layout':short._layout(p),'flux_units':short._flux_units(p)}
        manifest=_canonical(m)
        _need(sum(map(len,(request,raw,seed,manifest)))<=MAX_CONTEXT_BYTES,'CAPACITY_HOLD: context bytes exceeded')
        return Context(request,raw,seed,manifest,sha256(manifest).hexdigest(),parts,_TOKEN)
    except ContinuationRejected:
        raise
    except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:
        raise ContinuationRejected(str(short._translate(error)))from None


def _seal(context,payload):
    _fence()
    raw=_canonical(payload);_need(len(raw)<=MAX_CHECKPOINT_BYTES,'CAPACITY_HOLD: checkpoint bytes exceeded')
    return Checkpoint(raw,sha256(raw).hexdigest(),context.root_sha256,_TOKEN)


def _initial(context,p,seed,m):
    zero=(0.0,)*len(short._flux_units(p));first=seed['evaluation'];state=tuple(seed['state'])
    sample=short._sample(0,m['numerical']['step_seconds'],state,first,first['curve_residuals'])
    residuals,budgets=short._balances(p,state,state,zero,first,first,0,0,context._profiles[-1].values['latent_heat'])
    return {'version':CHECKPOINT_VERSION,'context_sha256':context.root_sha256,'step_index':0,
        'output_cursor':1,'output_prefix_sha256':_prefix(_hash([]),sample),'last_confirmed':sample,
        'integrated_transfers':{name:short.numeric._q(v,unit)for(name,unit),v in zip(short._flux_units(p).items(),zero,strict=True)},
        'balance_residuals':residuals,'balance_budgets':budgets}


def start(context):
    p,seed,m=_context(context);return _seal(context,_initial(context,p,seed,m))


def checkpoint_bytes(context,checkpoint):
    _context(context)
    _need(type(checkpoint)is Checkpoint and checkpoint._token is _TOKEN and checkpoint.context_sha256==context.root_sha256
        and type(checkpoint._raw)is bytes and len(checkpoint._raw)<=MAX_CHECKPOINT_BYTES
        and sha256(checkpoint._raw).hexdigest()==checkpoint.sha256,'CHECKPOINT_HOLD: immutable matching checkpoint required')
    return checkpoint._raw


def _validate(context,payload,p,seed,m):
    try:
        initial=_initial(context,p,seed,m)
        _need(type(payload)is dict and set(payload)==set(initial)and payload['version']==CHECKPOINT_VERSION
            and payload['context_sha256']==context.root_sha256,'CHECKPOINT_HOLD: closed matching checkpoint required')
        index=payload['step_index'];count=m['numerical']['step_count'];dt=m['numerical']['step_seconds']
        _need(type(index)is int and 0<=index<=count and type(payload['output_cursor'])is int
            and payload['output_cursor']==index+1 and _digest(payload['output_prefix_sha256']),
            'CHECKPOINT_HOLD: invalid step/cursor/prefix')
        sample=payload['last_confirmed'];_need(type(sample)is dict and set(sample)==set(initial['last_confirmed']),
            'CHECKPOINT_HOLD: closed current sample required')
        y=sample['state'];_need(type(y)is list and len(y)==len(seed['state'])
            and all(type(v)is float and isfinite(v)for v in y),'CHECKPOINT_HOLD: finite float64 state vector required')
        rows=payload['integrated_transfers'];_need(type(rows)is dict and set(rows)==set(short._flux_units(p)),
            'CHECKPOINT_HOLD: closed integrated transfers required')
        for name,unit in short._flux_units(p).items():
            row=rows[name];_need(type(row)is dict and set(row)=={'value','unit'}and row['unit']==unit
                and type(row['value'])is float and isfinite(row['value']),'CHECKPOINT_HOLD: finite float64 transfer/unit required')
        totals=tuple(rows[name]['value']for name in short._flux_units(p))
        rates,current=short._evaluate(p,tuple(y),_profiles(context))
        expected=short._sample(index,dt,y,current,seed['evaluation']['curve_residuals'])
        residuals,budgets=short._balances(p,tuple(seed['state']),tuple(y),totals,seed['evaluation'],current,
            index,index*dt,context._profiles[-1].values['latent_heat'])
        _need(_canonical(sample)==_canonical(expected)and _canonical(payload['balance_residuals'])==_canonical(residuals)
            and _canonical(payload['balance_budgets'])==_canonical(budgets),'CHECKPOINT_HOLD: stale current state/derived/balance')
        if index==0:_need(_canonical(payload)==_canonical(initial),'CHECKPOINT_HOLD: original initial checkpoint required')
        return tuple(y),totals,rates,current
    except ContinuationRejected:
        raise
    except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError):
        raise ContinuationRejected('CHECKPOINT_HOLD: invalid current state or global balances')from None


def restore_checkpoint(context,raw_bytes,*,expected_sha256):
    p,seed,m=_context(context)
    _need(type(raw_bytes)is bytes and 0<len(raw_bytes)<=MAX_CHECKPOINT_BYTES and _digest(expected_sha256)
        and sha256(raw_bytes).hexdigest()==expected_sha256,'CHECKPOINT_HOLD: trusted expected raw digest required')
    def pairs(items):
        result={}
        for name,value in items:_need(name not in result,'CHECKPOINT_HOLD: duplicate JSON key');result[name]=value
        return result
    def constant(value):raise ContinuationRejected('CHECKPOINT_HOLD: nonfinite JSON constant')
    try:
        payload=json.loads(raw_bytes.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
        _need(_canonical(payload)==raw_bytes,'CHECKPOINT_HOLD: canonical bytes required')
        _validate(context,payload,p,seed,m)
        return _seal(context,payload)
    except ContinuationRejected:
        raise
    except(UnicodeError,ValueError,TypeError,KeyError,OverflowError,RecursionError):
        raise ContinuationRejected('CHECKPOINT_HOLD: invalid external checkpoint JSON')from None


def advance_chunk(context,checkpoint,step_budget):
    _need(type(step_budget)is int and 1<=step_budget<=128,'BUDGET_HOLD: 1..128 integer steps required')
    p,seed,m=_context(context)
    try:payload=json.loads(checkpoint_bytes(context,checkpoint))
    except ContinuationRejected:
        raise
    except(ValueError,TypeError,UnicodeError,RecursionError):
        raise ContinuationRejected('CHECKPOINT_HOLD: invalid internal checkpoint bytes')from None
    count=m['numerical']['step_count'];dt=m['numerical']['step_seconds']
    _need(type(payload)is dict,'CHECKPOINT_HOLD: closed checkpoint required')
    _need(type(payload.get('step_index'))is not int or payload['step_index']!=count,
          'COMPLETED_HOLD: no step remains')
    state,totals,rates,current=_validate(context,payload,p,seed,m);begin=payload['step_index']
    flux=short._flux(p,state,current);samples=[];attempts=0;held=None;next_checkpoint=checkpoint
    initial=tuple(seed['state']);first=seed['evaluation'];latent=context._profiles[-1].values['latent_heat']
    index=begin;phase='ready'
    try:
        for index in range(begin+1,min(begin+step_budget,count)+1):
            phase='k2';y2=short._advance(state,rates,dt/2);attempts+=1;k2,r2=short._evaluate(p,y2,_profiles(context))
            phase='k3';y3=short._advance(state,k2,dt/2);attempts+=1;k3,r3=short._evaluate(p,y3,_profiles(context))
            phase='k4';y4=short._advance(state,k3,dt);attempts+=1;k4,r4=short._evaluate(p,y4,_profiles(context))
            phase='endpoint';candidate=short._advance(state,short._weighted(rates,k2,k3,k4),dt)
            cumulative=short._advance(totals,short._weighted(flux,short._flux(p,y2,r2),short._flux(p,y3,r3),short._flux(p,y4,r4)),dt)
            attempts+=1;new_rates,new_rhs=short._evaluate(p,candidate,_profiles(context))
            phase='endpoint_balance';residuals,budgets=short._balances(p,initial,candidate,cumulative,first,new_rhs,index,index*dt,latent)
            sample=short._sample(index,dt,candidate,new_rhs,first['curve_residuals'])
            candidate_payload={**payload,'step_index':index,'output_cursor':index+1,
                'output_prefix_sha256':_prefix(payload['output_prefix_sha256'],sample),'last_confirmed':sample,
                'integrated_transfers':{name:short.numeric._q(v,unit)for(name,unit),v in zip(short._flux_units(p).items(),cumulative,strict=True)},
                'balance_residuals':residuals,'balance_budgets':budgets}
            phase='checkpoint';sealed=_seal(context,candidate_payload)
            state,totals,rates,current=candidate,cumulative,new_rates,new_rhs;flux=short._flux(p,state,current)
            payload=candidate_payload;next_checkpoint=sealed;samples.append(sample)
    except(short.StemRootDynamicsHold,short.stock.StemRootCarbonStockHold,short.numeric.CanopyEnergyHold,
           short.old.leaf_area.LeafAreaHold,short.old.expansion.LeafExpansionHold,ContinuationRejected,
           ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError,RecursionError)as error:
        reason=str(error)if isinstance(error,ContinuationRejected)else str(short._translate(error))
        held={'step_index':index,'elapsed_seconds':index*dt,'stage':phase,'reason':reason}
        next_checkpoint=None
    return {'status':'hold'if held else'completed'if payload['step_index']==count else'yielded',
        'scope':'software_research_only','claim_scope':'synthetic_stem_root_stock_continuation_only','G0_G4':'not_assessed',
        'manifest':context.manifest,'context_sha256':context.root_sha256,
        'steps':payload['step_index'],'planned_steps':count,'output_start':begin+1,'samples':deepcopy(samples),
        'last_confirmed':deepcopy(payload['last_confirmed']),
        **{name:deepcopy(payload[name])for name in ('integrated_transfers','balance_residuals','balance_budgets')},
        'checkpoint':next_checkpoint,'hold':held,'checkpoint_validation_stage_evaluations':1,
        'attempted_new_stage_evaluations':attempts,'confirmed_new_steps':payload['step_index']-begin}
