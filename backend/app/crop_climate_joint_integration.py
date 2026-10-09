"""Bounded event-free shared integration; crop-climate-joint-short-integration-v1.md."""
from hashlib import sha256
import json
from math import fsum,isfinite,ulp
from pathlib import Path

from . import crop_climate_joint_rhs as joint

VERSION='joint-crop-climate-short-rk4-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
PLANT=tuple(joint.SCALAR_BLOCKS['plant_state'])
COHORT=tuple(joint.ARRAY_BLOCKS['cohort_state'])
CLIMATE=tuple(joint.CLIMATE_UNITS)
MASS='mg_CH2O/m2_floor';NUMBER='fruits_equivalent/m2_floor';ENERGY='J/m2_floor';WATER='kg_water/m2_floor'
FLUX_UNITS={**dict.fromkeys(('photosynthesis','growth_respiration','maintenance_leaf','maintenance_stem_root',
    'maintenance_fruit','removal_leaf','removal_stem_root','terminal_fruit_carbohydrate'),MASS),
    **dict.fromkeys(('fruit_number_inflow','terminal_fruit_number'),NUMBER),
    **dict.fromkeys(('canopy_to_air_sensible','canopy_to_vapor_latent','incoming_capacity_heat',
        'maintenance_capacity_heat','removal_capacity_heat','canopy_external_heat','air_external_sensible_heat'),ENERGY),
    **dict.fromkeys(('canopy_to_air_vapor','air_external_vapor'),WATER),
    **dict.fromkeys(('capacity_allocation','capacity_maintenance','capacity_removal'),'J/m2_floor/K')}


class JointIntegrationHold(ValueError):
    """A joint trial or ledger failed; no partial successful calculation is returned."""


def _need(condition,reason):
    if not condition:raise JointIntegrationHold(reason)


def _q(value,unit):return {'value':value,'unit':unit}
def _hash(value):return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _sum(values):
    value=fsum(values)
    _need(isfinite(value),'NUMERIC_HOLD: nonfinite sum')
    return value


def _state(s):
    return tuple([s['plant_state'][k]['value'] for k in PLANT]+
        [q['value'] for k in COHORT for q in s['cohort_state'][k]]+
        [s['climate_state'][k]['value'] for k in CLIMATE])


def _scenario(base,y):
    return {**base,'plant_state':{k:_q(y[i],joint.SCALAR_BLOCKS['plant_state'][k]) for i,k in enumerate(PLANT)},
        'cohort_state':{k:[_q(v,joint.ARRAY_BLOCKS['cohort_state'][k]) for v in y[5+i*50:55+i*50]]
            for i,k in enumerate(COHORT)},'climate_state':{k:_q(y[105+i],joint.CLIMATE_UNITS[k]) for i,k in enumerate(CLIMATE)}}


def _evaluate(base,y,profiles):
    r=joint.evaluate_rhs(scenario=_scenario(base,y),**profiles)
    return _from_result(r,base)


def _from_result(r,base):
    rates=tuple([r['derivatives']['plant'][k]['value'] for k in PLANT]+
        [q['value'] for k in COHORT for q in r['derivatives']['cohorts'][k]]+
        [r['derivatives']['climate'][k]['value'] for k in CLIMATE])
    c=r['crop'];f=base['forcing'];x=r['exchange']['exchange'];m=r['capacity_transport'];terminal=c['cohorts']['terminal_outflow']
    flow={
        'photosynthesis':c['photosynthesis']['value'],'growth_respiration':c['growth_respiration']['value'],
        'maintenance_leaf':c['vegetative_maintenance']['leaf']['value'],
        'maintenance_stem_root':c['vegetative_maintenance']['stem_root']['value'],'maintenance_fruit':c['fruit_maintenance']['value'],
        'removal_leaf':c['removals']['leaf']['value'],'removal_stem_root':c['removals']['stem_root']['value'],
        'terminal_fruit_carbohydrate':terminal['fruit_carbohydrate']['value'],
        'fruit_number_inflow':base['fruit_entry']['fruit_number_inflow']['value'],'terminal_fruit_number':terminal['fruit_number']['value'],
        'canopy_to_air_sensible':x['sensible_heat']['value'],'canopy_to_vapor_latent':x['latent_heat']['value'],
        'incoming_capacity_heat':m['energy_flows']['incoming']['value'],
        'maintenance_capacity_heat':m['energy_flows']['maintenance_outgoing']['value'],
        'removal_capacity_heat':m['energy_flows']['removal_outgoing']['value'],
        'canopy_external_heat':f['canopy_external_heat']['value'],'air_external_sensible_heat':f['air_external_sensible_heat']['value'],
        'canopy_to_air_vapor':x['water_vapor']['value'],'air_external_vapor':f['air_external_vapor']['value'],
        **{'capacity_'+k:m['capacity_rates'][k]['value'] for k in ('allocation','maintenance','removal')}}
    return rates,tuple(flow[k] for k in FLUX_UNITS),r


def _advance(values,rates,dt):
    result=[]
    for old,rate in zip(values,rates,strict=True):
        change=dt*rate;value=old+change
        _need(isfinite(change) and isfinite(value),'NUMERIC_HOLD: increment overflow')
        _need(rate==0 or change!=0,'NUMERIC_HOLD: increment underflow')
        _need(change==0 or value!=old,'NUMERIC_HOLD: increment lost to rounding')
        result.append(value)
    return tuple(result)


def _weighted(a,b,c,d):return tuple(_sum((v,2*w,2*x,z))/6 for v,w,x,z in zip(a,b,c,d,strict=True))


def _balances(initial,final,cumulative,first,last,index,latent,reference):
    t=dict(zip(FLUX_UNITS,cumulative));ca=first['derived']['air_capacity']['value']
    carbon=lambda y:_sum((*y[:3],*y[5:55]));number=lambda y:_sum(y[55:105])
    u0,u1=initial[105],final[105];air0,air1=ca*(initial[106]-reference),ca*(final[106]-reference)
    w0,w1=initial[107],final[107];cap0,cap1=(r['derived']['canopy_capacity']['value'] for r in (first,last))
    dc=carbon(final)-carbon(initial);dn=number(final)-number(initial);du=u1-u0;da=ca*(final[106]-initial[106]);dw=w1-w0
    heat=(t['canopy_external_heat'],t['air_external_sensible_heat'],latent*t['air_external_vapor'],
        t['incoming_capacity_heat'],-t['maintenance_capacity_heat'],-t['removal_capacity_heat'])
    ledgers={
        'carbohydrate':((dc,-t['photosynthesis'],t['growth_respiration'],t['maintenance_leaf'],t['maintenance_stem_root'],
            t['maintenance_fruit'],t['removal_leaf'],t['removal_stem_root'],t['terminal_fruit_carbohydrate']),carbon(initial),carbon(final),MASS),
        'number':((dn,-t['fruit_number_inflow'],t['terminal_fruit_number']),number(initial),number(final),NUMBER),
        'canopy_sensible':((du,-t['canopy_external_heat'],t['canopy_to_air_sensible'],t['canopy_to_vapor_latent'],
            -t['incoming_capacity_heat'],t['maintenance_capacity_heat'],t['removal_capacity_heat']),u0,u1,ENERGY),
        'air_sensible':((da,-t['air_external_sensible_heat'],-t['canopy_to_air_sensible']),air0,air1,ENERGY),
        'vapor_and_water_boundaries':((dw,-t['canopy_to_air_vapor'],-t['air_external_vapor']),w0,w1,WATER),
        'crop_capacity':((cap1-cap0,-t['capacity_allocation'],t['capacity_maintenance'],t['capacity_removal']),cap0,cap1,'J/m2_floor/K'),
        'reduced_energy':((du,da,latent*dw,*(-v for v in heat)),_sum((u0,air0,latent*w0)),_sum((u1,air1,latent*w1)),ENERGY)}
    residuals,budgets={},{}
    for name,(terms,start,end,unit) in ledgers.items():
        value=_sum(terms);scale=max(abs(start),abs(end),_sum(map(abs,terms)))
        budget=64*(index+1)*ulp(scale)
        _need(isfinite(budget) and abs(value)<=budget,'BALANCE_HOLD: unresolved '+name)
        residuals[name]=_q(value,unit);budgets[name]=_q(budget,unit)
    return residuals,budgets


def _sample(index,dt,base,y,r):
    s=_scenario(base,y)
    return {'step_index':index,'elapsed_seconds':index*dt,
        **{k:s[k] for k in ('plant_state','cohort_state','climate_state')},'derived':r['derived']}


def _hold(exc,index,phase,last):
    reason=str(exc) if isinstance(exc,(joint.JointClimateHold,JointIntegrationHold)) else 'NUMERIC_HOLD: arithmetic failed'
    held=JointIntegrationHold(f'{reason}: step={index}; stage={phase}')
    held.step_index=index;held.failed_stage=phase;held.last_confirmed_sample=last
    held.last_confirmed_elapsed_seconds=None if last is None else last['elapsed_seconds']
    return held


def integrate(*,scenario,step_seconds,step_count,growth_profile,cohort_profile,transport_profile,exchange_profile):
    """Integrate one explicit constant-forcing interval and its paired ledgers."""
    _need(type(step_seconds) in (int,float),'BUDGET_HOLD: numeric step required')
    try:dt=float(step_seconds)
    except OverflowError as exc:raise JointIntegrationHold('BUDGET_HOLD: unrepresentable step') from exc
    _need(isfinite(dt) and dt>0 and type(step_count) is int and 1<=step_count<=4096,
        'BUDGET_HOLD: positive step and 1..4096 integer steps required')
    duration=dt*step_count
    _need(isfinite(duration) and 0<duration<=600,'BUDGET_HOLD: 600s research horizon')
    profiles=dict(growth_profile=growth_profile,cohort_profile=cohort_profile,
        transport_profile=transport_profile,exchange_profile=exchange_profile)
    try:
        first=joint.evaluate_rhs(scenario=scenario,**profiles);base=first['scenario'];initial=_state(base)
        first_values=_from_result(first,base)
        state=initial;current=first_values;cumulative=(0.0,)*len(FLUX_UNITS)
        samples=[_sample(0,dt,base,state,first)]
        latent=exchange_profile.values['latent_heat'];reference=base['parameters']['reference_temperature']['value']
        residuals,budgets=_balances(initial,state,cumulative,first,first,0,latent,reference)
    except (joint.JointClimateHold,JointIntegrationHold,OverflowError,ValueError,ZeroDivisionError) as exc:
        raise _hold(exc,0,'initial',None) from exc
    for index in range(1,step_count+1):
        phase='k2'
        try:
            k1,j1,_=current
            k2,j2,_=_evaluate(base,_advance(state,k1,dt/2),profiles)
            phase='k3';k3,j3,_=_evaluate(base,_advance(state,k2,dt/2),profiles)
            phase='k4';k4,j4,_=_evaluate(base,_advance(state,k3,dt),profiles)
            phase='endpoint';candidate=_advance(state,_weighted(k1,k2,k3,k4),dt)
            totals=_advance(cumulative,_weighted(j1,j2,j3,j4),dt)
            next_rhs=_evaluate(base,candidate,profiles)
            phase='endpoint_balance';residuals,budgets=_balances(initial,candidate,totals,first,next_rhs[2],index,latent,reference)
        except (joint.JointClimateHold,JointIntegrationHold,OverflowError,ValueError,ZeroDivisionError) as exc:
            raise _hold(exc,index,phase,samples[-1]) from exc
        state,cumulative,current=candidate,totals,next_rhs
        samples.append(_sample(index,dt,base,state,current[2]))
    numerical={'method':'shared-stage-fixed-rk4-v1','step_seconds':dt,'step_count':step_count,'duration_seconds':duration,
        'rhs_evaluations':4*step_count+1,'forcing_sampling':'explicit_constant_for_entire_interval',
        'roundoff_rule':'64-ulp-per-step-ledger-v1','time_coordinate':'elapsed_seconds_no_UTC_checkpoint'}
    bound={'model_version':VERSION,'code_sha256':CODE_SHA256,'initial_rhs_calculation_sha256':first['calculation_sha256'],'numerical':numerical}
    transfers={k:_q(v,FLUX_UNITS[k]) for k,v in zip(FLUX_UNITS,cumulative,strict=True)}
    return {**bound,'calculation_sha256':_hash(bound),'input_sha256':first['input_sha256'],
        'rhs_code_sha256':joint.CODE_SHA256,'component_code_sha256':dict(joint.COMPONENT_CODE_SHA256),
        'profile_sha256':first['profile_sha256'],'policy_sha256':first['policy_sha256'],
        'state_schema_version':joint.STATE_SCHEMA,'clock_contract':joint.CLOCK_CONTRACT,'scenario':base,
        'samples':samples,'integrated_transfers':transfers,'canopy_water_boundary':_q(-transfers['canopy_to_air_vapor']['value'],WATER),
        'balance_residuals':residuals,'balance_budgets':budgets,'scope':'software_research_only',
        'claim_scope':'synthetic_joint_crop_climate_short_integration_only','G0_G4':'not_assessed'}
