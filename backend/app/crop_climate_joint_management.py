"""Atomic shared crop/capacity removal; crop-climate-joint-management-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum,isfinite,ulp
from pathlib import Path

from . import crop_climate_joint_rhs as joint

VERSION='joint-crop-climate-management-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MASS='mg_CH2O/m2_floor';NUMBER='fruits_equivalent/m2_floor';ENERGY='J/m2_floor';CAPACITY='J/m2_floor/K'


class JointManagementHold(ValueError):
    """An atomic event failed; the caller retains the confirmed pre-event state."""


def _need(condition,reason):
    if not condition:raise JointManagementHold(reason)


def _q(value,unit):return {'value':value,'unit':unit}
def _hash(value):return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _sum(values):
    total=fsum(values);_need(isfinite(total),'NUMERIC_HOLD: nonfinite event sum');return total


def _remove(old,amount):
    _need(0<=amount<=old,'EVENT_HOLD: removal exceeds storage')
    after=old-amount
    _need(isfinite(after) and (amount==0 or after<old),'NUMERIC_HOLD: removal lost to rounding')
    return after


def _event(event):
    _need(type(event) is dict and set(event)=={'input_id','origin','values'},'INPUT_HOLD: closed event required')
    _need(type(event['input_id']) is str and 1<=len(event['input_id'])<=200 and bool(event['input_id'].strip())
        and type(event['origin']) is str and event['origin'] in ('synthetic','reference_calculation'),
        'INPUT_HOLD: event provenance required')
    block=event['values']
    _need(type(block) is dict and set(block)=={'leaf','stem_root','fruit_fraction'},'INPUT_HOLD: closed removals required')
    organs,normalized=joint._quantities({k:block[k] for k in ('leaf','stem_root')},{'leaf':MASS,'stem_root':MASS})
    fractions,arrays=joint._quantities({'fruit_fraction':block['fruit_fraction']},{'fruit_fraction':'1'},arrays=True)
    _need(all(v>=0 for v in organs.values()) and all(0<=v<=1 for v in fractions['fruit_fraction']),
        'EVENT_HOLD: nonnegative removal and fractions 0..1 required')
    return organs,fractions['fruit_fraction'],{**event,'values':{**normalized,**arrays}}


def _snapshot(rhs):
    return {'scenario':rhs['scenario'],'derived':rhs['derived'],'input_sha256':rhs['input_sha256'],
        'calculation_sha256':rhs['calculation_sha256']}


def _ledger(before,after,terms,unit):
    residual=_sum((before,-after,*(-v for v in terms)))
    budget=64*ulp(max(abs(before),abs(after),_sum(map(abs,terms))))
    _need(isfinite(budget) and abs(residual)<=budget,'BALANCE_HOLD: event inventory mismatch')
    return _q(residual,unit),_q(budget,unit)


def apply_management(*,scenario,event,growth_profile,cohort_profile,transport_profile,exchange_profile):
    """Validate all pre/post quantities before returning a new joint scenario."""
    profiles=dict(growth_profile=growth_profile,cohort_profile=cohort_profile,
        transport_profile=transport_profile,exchange_profile=exchange_profile)
    before=None;phase='initial'
    try:
        first=joint.evaluate_rhs(scenario=scenario,**profiles);before=_snapshot(first);base=first['scenario']
        phase='event_schema';organs,fractions,normalized=_event(event)
        candidate=deepcopy(base);removed={k:_q(v,MASS) for k,v in organs.items()}
        phase='event_removal'
        for key,amount in organs.items():candidate['plant_state'][key]['value']=_remove(base['plant_state'][key]['value'],amount)
        for key,unit in (('fruit_carbohydrate',MASS),('fruit_number',NUMBER)):
            amounts=[]
            for old,fraction,row in zip(base['cohort_state'][key],fractions,candidate['cohort_state'][key],strict=True):
                value=old['value'];exact=Fraction(str(value))*Fraction(str(fraction));amount=float(exact)
                _need(isfinite(amount) and (value==0 or fraction==0 or amount!=0),'NUMERIC_HOLD: fractional removal underflow')
                after=float(Fraction(str(value))-exact)
                _need(isfinite(after) and (exact==0 or after<value),'NUMERIC_HOLD: removal lost to rounding')
                row['value']=after;amounts.append(_q(amount,unit))
            removed[key]=amounts
        capacity=joint.inventory.calculate_leaf_removal(event={'input_id':normalized['input_id'],
            'origin':normalized['origin'],'values':{
                'leaf_carbohydrate':base['plant_state']['leaf'],'leaf_removed':removed['leaf'],
                'leaf_heat_capacity':base['parameters']['leaf_heat_capacity'],
                'canopy_sensible_energy':base['climate_state']['canopy_sensible_energy'],
                'reference_temperature':base['parameters']['reference_temperature']}},profile=growth_profile)
        _need(candidate['plant_state']['leaf']==capacity['after']['leaf_carbohydrate'],
            'BALANCE_HOLD: conflicting event leaf')
        candidate['climate_state']['canopy_sensible_energy']=capacity['after']['canopy_sensible_energy']
        removed['canopy_sensible_energy']=capacity['outgoing_sensible_energy']
        removed['canopy_capacity']=_q(growth_profile.values['sla']*organs['leaf']*
            base['parameters']['leaf_heat_capacity']['value'],CAPACITY)
        phase='candidate';last=joint.evaluate_rhs(scenario=candidate,**profiles)
        total_c=lambda s:_sum([s['plant_state'][k]['value'] for k in ('buffer','leaf','stem_root')]+
            [q['value'] for q in s['cohort_state']['fruit_carbohydrate']])
        total_n=lambda s:_sum(q['value'] for q in s['cohort_state']['fruit_number'])
        removed_c=_sum([organs['leaf'],organs['stem_root'],*[q['value'] for q in removed['fruit_carbohydrate']]])
        removed_n=_sum(q['value'] for q in removed['fruit_number'])
        phase='event_balance';residuals,budgets={},{}
        for key,start,end,terms,unit in (
            ('carbohydrate',total_c(base),total_c(candidate),(removed_c,),MASS),
            ('number',total_n(base),total_n(candidate),(removed_n,),NUMBER),
            ('canopy_sensible',base['climate_state']['canopy_sensible_energy']['value'],
                candidate['climate_state']['canopy_sensible_energy']['value'],(removed['canopy_sensible_energy']['value'],),ENERGY),
            ('crop_capacity',first['derived']['canopy_capacity']['value'],last['derived']['canopy_capacity']['value'],
                (removed['canopy_capacity']['value'],),CAPACITY)):
            residuals[key],budgets[key]=_ledger(start,end,terms,unit)
        temperature=last['derived']['canopy_temperature']['value']-first['derived']['canopy_temperature']['value']
        _need(abs(temperature)<=2e-13,'NUMERIC_HOLD: event changed canopy temperature')
        residuals['temperature']=_q(temperature,'K');budgets['temperature']=_q(2e-13,'K')
    except (joint.JointClimateHold,joint.inventory.CanopyEnergyHold,JointManagementHold,OverflowError,ValueError,ZeroDivisionError) as exc:
        reason=str(exc) if isinstance(exc,(joint.JointClimateHold,joint.inventory.CanopyEnergyHold,JointManagementHold)) else 'NUMERIC_HOLD: event arithmetic failed'
        held=JointManagementHold(f'{reason}: phase={phase}');held.failed_phase=phase;held.last_confirmed=before
        raise held from exc
    bound={'model_version':VERSION,'code_sha256':CODE_SHA256,'rhs_code_sha256':joint.CODE_SHA256,
        'component_code_sha256':dict(joint.COMPONENT_CODE_SHA256),'event_sha256':_hash(normalized),
        'before_calculation_sha256':first['calculation_sha256'],'after_calculation_sha256':last['calculation_sha256'],
        'quantity_rule':'cohort-decimal-rational-removal-v1',
        'roundoff_rule':'64-ulp-event-inventory-v1','time_coordinate':'instantaneous_no_clock'}
    return {**bound,'calculation_sha256':_hash(bound),'event':normalized,'before':before,'after':_snapshot(last),
        'profile_sha256':first['profile_sha256'],'policy_sha256':first['policy_sha256'],'removed':removed,
        'removed_totals':{'carbohydrate':_q(removed_c,MASS),'number':_q(removed_n,NUMBER)},
        'balance_residuals':residuals,'balance_budgets':budgets,'scope':'software_research_only',
        'claim_scope':'synthetic_joint_crop_climate_management_only','G0_G4':'not_assessed'}
