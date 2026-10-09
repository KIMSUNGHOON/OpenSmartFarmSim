"""Bounded automatic shared steps/events; crop-climate-joint-boundary-driver-v1.md."""
from copy import deepcopy
from hashlib import sha256
import json
from math import fsum,isfinite,ulp
from pathlib import Path

from . import crop_climate_joint_integration as short
from . import crop_climate_joint_management as management

joint=short.joint
VERSION='joint-crop-climate-boundary-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
EVENT_UNITS={'leaf':short.MASS,'stem_root':short.MASS,'fruit_carbohydrate':short.MASS,
    'fruit_number':short.NUMBER,'canopy_sensible_energy':short.ENERGY,'canopy_capacity':'J/m2_floor/K'}


class BoundaryHold(ValueError):
    """Failure with confirmed state/output prefixes, never a successful partial Run."""


def _need(condition,reason):
    if not condition:raise BoundaryHold(reason)


def _hash(value):return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def _q(v,u):return {'value':v,'unit':u}
def _zero(units):return {k:_q(0.0,u) for k,u in units.items()}
def _sum(values):
    total=fsum(values);_need(isfinite(total),'NUMERIC_HOLD: nonfinite global sum');return total


def _prepare(events,outputs,step_seconds,step_count):
    _need(type(step_seconds) in (int,float),'BUDGET_HOLD: numeric step required')
    try:dt=float(step_seconds)
    except OverflowError as exc:raise BoundaryHold('BUDGET_HOLD: unrepresentable step') from exc
    _need(isfinite(dt) and dt>0 and type(step_count) is int and 1<=step_count<=4096,
        'BUDGET_HOLD: positive step and 1..4096 integer steps')
    _need(isfinite(dt*step_count) and 0<dt*step_count<=600,'BUDGET_HOLD: 600s horizon')
    _need(type(events) is list and len(events)<=128,'BUDGET_HOLD: bounded event list required')
    _need(type(outputs) is list and 2<=len(outputs)<=512 and all(type(i) is int and 0<=i<=step_count for i in outputs)
        and outputs[0]==0 and outputs[-1]==step_count and all(a<b for a,b in zip(outputs,outputs[1:])),
        'TIME_HOLD: ordered bounded output indices must cover period')
    normalized=[];previous=-1;ids=set()
    for row in events:
        _need(type(row) is dict and set(row)=={'step_index','event'},'INPUT_HOLD: closed scheduled event')
        i=row['step_index']
        _need(type(i) is int and previous<i<=step_count,'TIME_HOLD: unique ordered in-grid event index')
        _,_,event=management._event(row['event'])
        _need(event['input_id'] not in ids,'INPUT_HOLD: duplicate event identity')
        normalized.append({'step_index':i,'event':event});ids.add(event['input_id']);previous=i
    return dt,normalized,list(outputs)


def _add(existing,increment,units):
    _need(set(existing)==set(increment)==set(units),'BALANCE_HOLD: incomplete global ledger')
    result={}
    for k,u in units.items():
        a,b=existing[k],increment[k]
        _need(a['unit']==b['unit']==u,'UNIT_HOLD: global ledger unit')
        v=_sum((a['value'],b['value']))
        _need(b['value']==0 or v!=a['value'],'NUMERIC_HOLD: cumulative increment lost to rounding')
        result[k]=_q(v,u)
    return result


def _balances(seed,current,t,e,first,last,operations,profiles):
    a,b=short._state(seed),short._state(current);t={k:q['value'] for k,q in t.items()};e={k:q['value'] for k,q in e.items()}
    ca=first['derived']['air_capacity']['value'];latent=profiles['exchange_profile'].values['latent_heat']
    reference=seed['parameters']['reference_temperature']['value']
    carbon=lambda y:_sum((*y[:3],*y[5:55]));number=lambda y:_sum(y[55:105])
    du=b[105]-a[105];da=ca*(b[106]-a[106]);dw=b[107]-a[107]
    air0,air1=(ca*(y[106]-reference) for y in (a,b));cap0,cap1=(r['derived']['canopy_capacity']['value'] for r in (first,last))
    material=(-t['incoming_capacity_heat'],t['maintenance_capacity_heat'],t['removal_capacity_heat'],e['canopy_sensible_energy'])
    ledgers={
        'carbohydrate':((carbon(b)-carbon(a),-t['photosynthesis'],*[t[k] for k in tuple(short.FLUX_UNITS)[1:8]],e['leaf'],e['stem_root'],e['fruit_carbohydrate']),carbon(a),carbon(b),short.MASS),
        'number':((number(b)-number(a),-t['fruit_number_inflow'],t['terminal_fruit_number'],e['fruit_number']),number(a),number(b),short.NUMBER),
        'canopy_sensible':((du,-t['canopy_external_heat'],t['canopy_to_air_sensible'],t['canopy_to_vapor_latent'],*material),a[105],b[105],short.ENERGY),
        'air_sensible':((da,-t['air_external_sensible_heat'],-t['canopy_to_air_sensible']),air0,air1,short.ENERGY),
        'vapor_and_water_boundaries':((dw,-t['canopy_to_air_vapor'],-t['air_external_vapor']),a[107],b[107],short.WATER),
        'crop_capacity':((cap1-cap0,-t['capacity_allocation'],t['capacity_maintenance'],t['capacity_removal'],e['canopy_capacity']),cap0,cap1,'J/m2_floor/K'),
        'reduced_energy':((du,da,latent*dw,-t['canopy_external_heat'],-t['air_external_sensible_heat'],-latent*t['air_external_vapor'],*material),
            _sum((a[105],air0,latent*a[107])),_sum((b[105],air1,latent*b[107])),short.ENERGY)}
    residuals,budgets={},{}
    for k,(terms,start,end,u) in ledgers.items():
        v=_sum(terms);budget=64*(operations+1)*ulp(max(abs(start),abs(end),_sum(map(abs,terms))))
        _need(isfinite(budget) and abs(v)<=budget,'BALANCE_HOLD: unresolved global '+k)
        residuals[k]=_q(v,u);budgets[k]=_q(budget,u)
    return residuals,budgets


def _snapshot(index,dt,current,r,t,e,event_count,residuals,budgets,phase):
    return {'step_index':index,'elapsed_seconds':index*dt,
        **{k:current[k] for k in ('plant_state','cohort_state','climate_state')},'derived':r['derived'],
        'integrated_transfers':t,'event_totals':e,'event_count':event_count,
        'balance_residuals':residuals,'balance_budgets':budgets,'phase':phase}


def integrate_events(*,scenario,events,output_steps,step_seconds,step_count,
        growth_profile,cohort_profile,transport_profile,exchange_profile):
    """Confirm shared steps and atomic events against one immutable global seed."""
    profiles=dict(growth_profile=growth_profile,cohort_profile=cohort_profile,
        transport_profile=transport_profile,exchange_profile=exchange_profile)
    confirmed=None;samples=[];journal=[];index=0;phase='input'
    try:
        dt,schedule,outputs=_prepare(events,output_steps,step_seconds,step_count)
        phase='initial';first=joint.evaluate_rhs(scenario=scenario,**profiles);seed=first['scenario'];current=seed;rhs=first
        t=_zero(short.FLUX_UNITS);e=_zero(EVENT_UNITS);event_count=0;calls=1
        residuals,budgets=_balances(seed,current,t,e,first,rhs,0,profiles)
        confirmed=_snapshot(0,dt,current,rhs,t,e,0,residuals,budgets,'initial')
        pending={row['step_index']:row['event'] for row in schedule};requested=set(outputs)
        for index in range(step_count+1):
            if index:
                phase='interval';part=short.integrate(scenario=current,step_seconds=dt,step_count=1,**profiles)
                end=part['samples'][-1]
                candidate={**current,**{k:end[k] for k in ('plant_state','cohort_state','climate_state')}}
                phase='global-step-balance';totals=_add(t,part['integrated_transfers'],short.FLUX_UNITS)
                next_rhs={'derived':end['derived']}
                residuals,budgets=_balances(seed,candidate,totals,e,first,next_rhs,index+event_count,profiles)
                current,t,rhs=candidate,totals,next_rhs;calls+=part['numerical']['rhs_evaluations']
                confirmed=_snapshot(index,dt,current,rhs,t,e,event_count,residuals,budgets,'step-end')
            if index in pending:
                phase='event';applied=management.apply_management(scenario=current,event=pending[index],**profiles)
                phase='global-event-balance';increment={}
                for k,u in EVENT_UNITS.items():
                    q=applied['removed'][k]
                    increment[k]=_q(_sum(v['value'] for v in q),u) if isinstance(q,list) else q
                totals=_add(e,increment,EVENT_UNITS);candidate=applied['after']['scenario'];next_rhs=applied['after']
                residuals,budgets=_balances(seed,candidate,t,totals,first,next_rhs,index+event_count+1,profiles)
                current,e,rhs=candidate,totals,next_rhs;event_count+=1;calls+=2
                confirmed=_snapshot(index,dt,current,rhs,t,e,event_count,residuals,budgets,'boundary-after-event')
                journal.append({'step_index':index,'elapsed_seconds':index*dt,'management':applied})
            if index in requested:samples.append(confirmed)
    except (BoundaryHold,short.JointIntegrationHold,management.JointManagementHold,joint.JointClimateHold,OverflowError,ValueError,ZeroDivisionError) as exc:
        reason=str(exc) if isinstance(exc,(BoundaryHold,short.JointIntegrationHold,management.JointManagementHold,joint.JointClimateHold)) else 'NUMERIC_HOLD: boundary arithmetic failed'
        held=BoundaryHold(f'{reason}: global_step={index}; phase={phase}')
        held.step_index=index;held.failed_phase=phase;held.last_confirmed=deepcopy(confirmed)
        held.last_confirmed_elapsed_seconds=None if confirmed is None else confirmed['elapsed_seconds']
        held.samples=deepcopy(samples);held.events=deepcopy(journal)
        raise held from exc
    numerical={'method':'single-step-shared-rk4-kernel-events-v1','step_seconds':dt,'step_count':step_count,
        'duration_seconds':step_count*dt,'rhs_evaluations':calls,'forcing_sampling':'explicit_constant_for_entire_program',
        'roundoff_rule':'64-ulp-per-step-and-event-global-ledger-v1','time_coordinate':'elapsed_step_grid_no_UTC_checkpoint',
        'quantity_rule':'cohort-decimal-rational-removal-v1'}
    input_sha=_hash({'scenario':seed,'events':schedule,'output_steps':outputs,'numerical':numerical})
    bound={'model_version':VERSION,'code_sha256':CODE_SHA256,'short_code_sha256':short.CODE_SHA256,
        'management_code_sha256':management.CODE_SHA256,'rhs_code_sha256':joint.CODE_SHA256,
        'component_code_sha256':dict(joint.COMPONENT_CODE_SHA256),'input_sha256':input_sha,
        'initial_rhs_calculation_sha256':first['calculation_sha256'],'numerical':numerical}
    payload={'samples':samples,'events':journal,'last_confirmed':confirmed,'integrated_transfers':t,'event_totals':e}
    return {**bound,**payload,'calculation_sha256':_hash(bound),'result_sha256':_hash(payload),'status':'completed',
        'scenario':seed,'scheduled_events':schedule,'output_steps':outputs,'profile_sha256':first['profile_sha256'],
        'policy_sha256':first['policy_sha256'],'state_schema_version':joint.STATE_SCHEMA,
        'clock_contract':'elapsed-grid-shared-rk4-events-v1','physical_clock_contract':joint.CLOCK_CONTRACT,
        'scope':'software_research_only','claim_scope':'synthetic_joint_crop_climate_boundary_driver_only','G0_G4':'not_assessed'}
