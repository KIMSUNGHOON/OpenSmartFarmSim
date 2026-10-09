"""Immutable bounded resume state; crop-climate-joint-continuation-v1.md."""
from copy import deepcopy
from dataclasses import dataclass,field
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import platform
import sys

from . import crop_climate_joint_boundary as driver

VERSION='joint-crop-climate-continuation-research-v1'
CHECKPOINT_VERSION='joint-crop-climate-checkpoint-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_CONTEXT_BYTES=2*1024**2
MAX_CHECKPOINT_BYTES=65536
MAX_CHUNK_BOUNDARIES=128
PROFILE_NAMES=('growth','cohort','transport','exchange')
_TOKEN=object()


class ContinuationRejected(ValueError):
    """Invalid context/checkpoint/budget; no numerical step began."""


def _need(condition,reason):
    if not condition:raise ContinuationRejected(reason)


def _canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _hash(v):return sha256(_canonical(v)).hexdigest()
def _digest(v):return type(v) is str and len(v)==64 and all(c in '0123456789abcdef' for c in v)
def _prefix(previous,record):return _hash({'previous':previous,'record':record})


def _identity(profiles):
    return {'engine_version':VERSION,'engine_code_sha256':CODE_SHA256,
        'driver_code_sha256':driver.CODE_SHA256,'short_code_sha256':driver.short.CODE_SHA256,
        'management_code_sha256':driver.management.CODE_SHA256,'rhs_code_sha256':driver.joint.CODE_SHA256,
        'component_code_sha256':dict(driver.joint.COMPONENT_CODE_SHA256),
        'policy_sha256':driver.joint.crop.startup.POLICY_SHA256,
        'profile_sha256':{k:p.sha256 for k,p in zip(PROFILE_NAMES,profiles,strict=True)},
        'state_schema':driver.joint.STATE_SCHEMA,'physical_clock_contract':driver.joint.CLOCK_CONTRACT,
        'python_version':platform.python_version(),'platform_machine':platform.machine(),'platform_system':platform.system(),
        'byteorder':sys.byteorder,'float_mant_dig':sys.float_info.mant_dig,'float_radix':sys.float_info.radix}


@dataclass(frozen=True)
class Context:
    _program:bytes
    _manifest:bytes
    _first:bytes
    root_sha256:str
    _profiles:tuple=field(repr=False)
    _token:object=field(repr=False)

    @property
    def manifest(self):return json.loads(self._manifest)
    @property
    def program(self):return json.loads(self._program)


@dataclass(frozen=True)
class Checkpoint:
    _raw:bytes=field(repr=False)
    sha256:str
    context_sha256:str
    _token:object=field(repr=False)

    @property
    def value(self):return json.loads(self._raw)


def _profiles(context):return {k+'_profile':p for k,p in zip(PROFILE_NAMES,context._profiles,strict=True)}


def _context(context):
    _need(type(context) is Context and context._token is _TOKEN,'CONTEXT_HOLD: prepared context required')
    try:
        _need(all(type(v) is bytes for v in (context._program,context._manifest,context._first))
            and len(context._program)+len(context._manifest)+len(context._first)<=MAX_CONTEXT_BYTES,
            'CONTEXT_HOLD: bounded immutable bytes required')
        manifest=context.manifest
        _need(_hash(manifest)==context.root_sha256 and manifest['identity']==_identity(context._profiles)
            and manifest['program_sha256']==sha256(context._program).hexdigest()
            and manifest['initial_rhs_sha256']==sha256(context._first).hexdigest(),
            'CONTEXT_HOLD: changed code/profile/environment/program/seed')
        return context.program,json.loads(context._first)
    except (ValueError,TypeError,KeyError,AttributeError) as exc:
        raise ContinuationRejected('CONTEXT_HOLD: invalid immutable context: '+str(exc)) from exc


def prepare_context(*,scenario,events,output_steps,step_seconds,step_count,
        growth_profile,cohort_profile,transport_profile,exchange_profile):
    profiles=(growth_profile,cohort_profile,transport_profile,exchange_profile)
    try:
        dt,schedule,outputs=driver._prepare(events,output_steps,step_seconds,step_count)
        first=driver.joint.evaluate_rhs(scenario=scenario,**{k+'_profile':p for k,p in zip(PROFILE_NAMES,profiles,strict=True)})
        program={'scenario':first['scenario'],'events':schedule,'output_steps':outputs,'step_seconds':dt,'step_count':step_count}
        raw=_canonical(program);initial=_canonical(first)
        manifest={'identity':_identity(profiles),'program_sha256':sha256(raw).hexdigest(),
            'initial_rhs_sha256':sha256(initial).hexdigest(),'initial_calculation_sha256':first['calculation_sha256'],
            'policy_sha256':first['policy_sha256'],'numerical':{'step_seconds':dt,'step_count':step_count,
                'duration_seconds':dt*step_count,'method':'single-step-shared-rk4-kernel-events-v1',
                'quantity_rule':'cohort-decimal-rational-removal-v1','roundoff_rule':'64-ulp-per-step-and-event-global-ledger-v1'},
            'scope':'software_research_only','clock_contract':'elapsed-grid-shared-rk4-events-v1'}
        bound=_canonical(manifest)
        _need(len(raw)+len(initial)+len(bound)<=MAX_CONTEXT_BYTES,'RESOURCE_HOLD: context byte limit')
    except (driver.BoundaryHold,driver.joint.JointClimateHold,OverflowError,ValueError,ZeroDivisionError) as exc:
        raise ContinuationRejected(str(exc)) from exc
    return Context(raw,bound,initial,sha256(bound).hexdigest(),profiles,_TOKEN)


def _initial(context,program,first):
    t,e=driver._zero(driver.short.FLUX_UNITS),driver._zero(driver.EVENT_UNITS)
    residuals,budgets=driver._balances(program['scenario'],program['scenario'],t,e,first,first,0,_profiles(context))
    return {'version':CHECKPOINT_VERSION,'context_sha256':context.root_sha256,'next_index':0,
        'output_cursor':0,'event_cursor':0,'output_prefix_sha256':_hash([]),'event_prefix_sha256':_hash([]),
        'last_confirmed':driver._snapshot(0,program['step_seconds'],program['scenario'],first,t,e,0,residuals,budgets,'initial')}


def _seal(context,payload):
    raw=_canonical(payload);_need(len(raw)<=MAX_CHECKPOINT_BYTES,'RESOURCE_HOLD: checkpoint byte limit')
    return Checkpoint(raw,sha256(raw).hexdigest(),context.root_sha256,_TOKEN)


def start(context):
    program,first=_context(context);return _seal(context,_initial(context,program,first))


def checkpoint_bytes(context,checkpoint):
    _context(context)
    _need(type(checkpoint) is Checkpoint and checkpoint._token is _TOKEN
        and checkpoint.context_sha256==context.root_sha256 and type(checkpoint._raw) is bytes
        and len(checkpoint._raw)<=MAX_CHECKPOINT_BYTES and sha256(checkpoint._raw).hexdigest()==checkpoint.sha256,
        'CHECKPOINT_HOLD: immutable matching checkpoint required')
    return checkpoint._raw


def _validate(context,payload,program,first):
    initial=_initial(context,program,first)
    _need(type(payload) is dict and set(payload)==set(initial) and payload['version']==CHECKPOINT_VERSION
        and payload['context_sha256']==context.root_sha256,'CHECKPOINT_HOLD: closed matching checkpoint')
    n=payload['next_index'];_need(type(n) is int and 0<=n<=program['step_count']+1,'CHECKPOINT_HOLD: next index')
    for k in ('output_cursor','event_cursor'):_need(type(payload[k]) is int,'CHECKPOINT_HOLD: integer cursor')
    _need(payload['output_cursor']==sum(i<n for i in program['output_steps'])
        and payload['event_cursor']==sum(row['step_index']<n for row in program['events']),
        'CHECKPOINT_HOLD: cursor/position mismatch')
    for kind in ('output','event'):
        digest=payload[kind+'_prefix_sha256'];_need(_digest(digest),'CHECKPOINT_HOLD: prefix SHA')
        if payload[kind+'_cursor']==0:_need(digest==_hash([]),'CHECKPOINT_HOLD: empty prefix')
    if n==0:_need(payload==initial,'CHECKPOINT_HOLD: original initial state required')
    last=payload['last_confirmed'];_need(type(last) is dict and set(last)==set(initial['last_confirmed']),
        'CHECKPOINT_HOLD: closed confirmed snapshot')
    current={**program['scenario'],**{k:last[k] for k in ('plant_state','cohort_state','climate_state')}}
    for key,units in (('integrated_transfers',driver.short.FLUX_UNITS),('event_totals',driver.EVENT_UNITS)):
        ledger=last[key];_need(type(ledger) is dict and set(ledger)==set(units),'CHECKPOINT_HOLD: closed ledger')
        for k,u in units.items():
            q=ledger[k];_need(type(q) is dict and set(q)=={'value','unit'} and q['unit']==u
                and type(q['value']) is float and isfinite(q['value']),'CHECKPOINT_HOLD: finite float64 ledger')
    try:
        rhs=driver.joint.evaluate_rhs(scenario=current,**_profiles(context));index=max(0,n-1)
        residuals,budgets=driver._balances(program['scenario'],current,last['integrated_transfers'],last['event_totals'],
            first,rhs,index+payload['event_cursor'],_profiles(context))
    except (driver.BoundaryHold,driver.joint.JointClimateHold,OverflowError,ValueError,ZeroDivisionError) as exc:
        raise ContinuationRejected('CHECKPOINT_HOLD: invalid current state or global balances: '+str(exc)) from exc
    phase='boundary-after-event' if n and any(row['step_index']==index for row in program['events']) else 'step-end' if index else 'initial'
    expected=driver._snapshot(index,program['step_seconds'],rhs['scenario'],rhs,last['integrated_transfers'],last['event_totals'],
        payload['event_cursor'],residuals,budgets,phase)
    _need(_canonical(last)==_canonical(expected),'CHECKPOINT_HOLD: stale state/derived/phase/elapsed/balance')
    return rhs


def restore_checkpoint(context,raw_bytes,*,expected_sha256):
    program,first=_context(context)
    _need(type(raw_bytes) is bytes and 0<len(raw_bytes)<=MAX_CHECKPOINT_BYTES and _digest(expected_sha256)
        and sha256(raw_bytes).hexdigest()==expected_sha256,'CHECKPOINT_HOLD: trusted expected raw digest required')
    def pairs(rows):
        out={}
        for k,v in rows:_need(k not in out,'CHECKPOINT_HOLD: duplicate JSON key');out[k]=v
        return out
    def constant(v):raise ContinuationRejected('CHECKPOINT_HOLD: nonfinite JSON constant')
    try:
        payload=json.loads(raw_bytes.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
        _need(_canonical(payload)==raw_bytes,'CHECKPOINT_HOLD: canonical bytes required')
        _validate(context,payload,program,first)
    except (UnicodeError,ValueError,TypeError,KeyError,RecursionError,OverflowError) as exc:
        raise ContinuationRejected('CHECKPOINT_HOLD: invalid external checkpoint: '+str(exc)) from exc
    return _seal(context,payload)


def advance_chunk(context,checkpoint,boundary_budget):
    _need(type(boundary_budget) is int and 1<=boundary_budget<=MAX_CHUNK_BOUNDARIES,'BUDGET_HOLD: 1..128 boundaries')
    program,first=_context(context);payload=json.loads(checkpoint_bytes(context,checkpoint))
    rhs=_validate(context,payload,program,first);begin=payload['next_index']
    _need(begin<=program['step_count'],'COMPLETED_HOLD: no boundary remains')
    confirmed=payload['last_confirmed'];current={**program['scenario'],**{k:confirmed[k] for k in ('plant_state','cohort_state','climate_state')}}
    t,e=confirmed['integrated_transfers'],confirmed['event_totals'];event_count=payload['event_cursor']
    samples=[];journal=[];index=begin;phase='initial';calls=0;held=None
    schedule={row['step_index']:row['event'] for row in program['events']};outputs=set(program['output_steps']);dt=program['step_seconds']
    try:
        for index in range(begin,min(begin+boundary_budget,program['step_count']+1)):
            if index:
                phase='interval';part=driver.short.integrate(scenario=current,step_seconds=dt,step_count=1,**_profiles(context))
                end=part['samples'][-1];candidate={**current,**{k:end[k] for k in ('plant_state','cohort_state','climate_state')}}
                phase='global-step-balance';totals=driver._add(t,part['integrated_transfers'],driver.short.FLUX_UNITS)
                next_rhs={'derived':end['derived']}
                residuals,budgets=driver._balances(program['scenario'],candidate,totals,e,first,next_rhs,index+event_count,_profiles(context))
                current,t,rhs=candidate,totals,next_rhs;calls+=part['numerical']['rhs_evaluations']
                confirmed=driver._snapshot(index,dt,current,rhs,t,e,event_count,residuals,budgets,'step-end')
            if index in schedule:
                phase='event';applied=driver.management.apply_management(scenario=current,event=schedule[index],**_profiles(context))
                phase='global-event-balance';increment={}
                for k,u in driver.EVENT_UNITS.items():
                    q=applied['removed'][k];increment[k]=driver._q(driver._sum(v['value'] for v in q),u) if isinstance(q,list) else q
                totals=driver._add(e,increment,driver.EVENT_UNITS);candidate=applied['after']['scenario'];next_rhs=applied['after']
                residuals,budgets=driver._balances(program['scenario'],candidate,t,totals,first,next_rhs,index+event_count+1,_profiles(context))
                current,e,rhs=candidate,totals,next_rhs;event_count+=1;calls+=2
                confirmed=driver._snapshot(index,dt,current,rhs,t,e,event_count,residuals,budgets,'boundary-after-event')
                row={'step_index':index,'elapsed_seconds':index*dt,'management':applied};journal.append(row)
                payload['event_prefix_sha256']=_prefix(payload['event_prefix_sha256'],row)
            if index in outputs:
                samples.append(confirmed);payload['output_prefix_sha256']=_prefix(payload['output_prefix_sha256'],confirmed)
            payload.update(next_index=index+1,event_cursor=event_count,output_cursor=payload['output_cursor']+int(index in outputs),last_confirmed=confirmed)
        next_checkpoint=_seal(context,payload)
    except (driver.BoundaryHold,driver.short.JointIntegrationHold,driver.management.JointManagementHold,
            driver.joint.JointClimateHold,OverflowError,ValueError,ZeroDivisionError) as exc:
        held={'step_index':index,'elapsed_seconds':index*dt,'phase':phase,'reason':str(exc)};next_checkpoint=None
    return {'status':'hold' if held else 'completed' if payload['next_index']==program['step_count']+1 else 'yielded',
        'scope':'software_research_only','claim_scope':'synthetic_joint_crop_climate_continuation_only','G0_G4':'not_assessed',
        'manifest':context.manifest,'context_sha256':context.root_sha256,'steps':confirmed['step_index'],'planned_steps':program['step_count'],
        'output_start':checkpoint.value['output_cursor'],'event_start':checkpoint.value['event_cursor'],
        'samples':deepcopy(samples),'events':deepcopy(journal),'last_confirmed':deepcopy(confirmed),
        'checkpoint':next_checkpoint,'hold':held,'confirmed_numerical_rhs_evaluations':calls,'checkpoint_validation_rhs_evaluations':1}
