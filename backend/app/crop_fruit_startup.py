"""Explicit post-onset empty-sink deferral; caller must apply buffer/respiration together."""
from hashlib import sha256
import json
from math import fsum, isfinite, ulp

from . import crop_fruit_allocation as allocation
from .crop_fruit_cohorts import ReferenceFruitCohortParameters

MODEL_VERSION = 'explicit-entry-empty-sink-startup-rates-research-v1'
POLICY_ID = 'explicit-entry-empty-sink-deferral-research-v1'
POLICY_SHA256 = '882022c483ef935bfca5002059490244d0466e370b8f2d33b5551d8408f2ee1d'
RATE_UNIT = allocation.UNITS['fruit_carbohydrate_inflow']


class FruitStartupHold(ValueError):
    """No requested/realized allocation for invalid or unrepresentable inputs."""


def _need(condition, reason):
    if not condition:
        raise FruitStartupHold(reason)


def _product(a, b):
    result = a*b
    _need(isfinite(result) and (a==0 or b==0 or result>0),
          'NUMERIC_HOLD: nonfinite or positive product underflow')
    return result


def calculate_startup_rates(*, state, profile):
    """Return instant flows only; no phenology, seed, RGR or state advancement."""
    _need(type(profile) is ReferenceFruitCohortParameters,'PROFILE_HOLD: pinned cohort profile required')
    _need(type(state) is dict and set(state)=={'input_id','origin','values'},
          'INPUT_HOLD: closed provenance block required')
    _need(type(state['input_id']) is str and 0<len(state['input_id'])<=256 and bool(state['input_id'].strip())
          and type(state['origin']) is str and state['origin'] in
          ('synthetic','reference_calculation','reference_observation'),
          'INPUT_HOLD: bounded research provenance required')
    _need(type(state['values']) is dict and set(state['values'])==set(allocation.UNITS),
          'INPUT_HOLD: missing or unexpected quantity')
    try:
        normalized={}
        for name,unit in allocation.UNITS.items():
            raw=state['values'][name]
            if name=='fruit_potential_demand':
                _need(type(raw) is list and len(raw)==allocation.STAGES,'INPUT_HOLD: exact demand array required')
                normalized[name]=[allocation._quantity(allocation._number(q,unit),unit) for q in raw]
            else:
                normalized[name]=allocation._quantity(allocation._number(raw,unit),unit)
        requested=normalized['fruit_carbohydrate_inflow']['value']
        number=normalized['fruit_number_inflow']['value']
        mass=normalized['fruit_entry_carbohydrate']['value']
        _need(number==0 or mass>0,'FRUIT_ENTRY_STATE_HOLD: positive inflow requires entry mass')
        entry=_product(number,mass)
        _need(entry<=requested,'FRUIT_ENTRY_BUDGET_HOLD: entry exceeds requested carbon')
        demand=normalized['fruit_potential_demand']
        denominator=fsum(q['value'] for q in demand[1:])
        _need(isfinite(denominator),'NUMERIC_HOLD: nonfinite tail demand')
        effective=requested if denominator>0 else entry
        deferred=requested-effective
        cg=profile.values['fruit_growth_respiration']
        respiration=_product(effective,cg)
        avoided=_product(deferred,cg)
        requested_respiration=_product(requested,cg)
        adjustment=fsum((deferred,avoided))
        _need(isfinite(adjustment),'NUMERIC_HOLD: nonfinite buffer adjustment')
        adapted={'input_id':state['input_id'],'origin':state['origin'],
            'values':{**normalized,'fruit_carbohydrate_inflow':allocation._quantity(effective,RATE_UNIT)}}
        result=allocation.calculate_allocation_rates(state=adapted)
        residuals={'request':fsum((effective,deferred,-requested)),
            'whole_plant':fsum((-requested,-requested_respiration,adjustment,
                *(q['value'] for q in result['carbohydrate_inflow']),respiration))}
        scale=max(requested,requested_respiration,adjustment,respiration)
        budget=2*(allocation.STAGES+8)*ulp(scale)
        _need(isfinite(budget) and all(isfinite(r) and abs(r)<=budget for r in residuals.values()),
              'BALANCE_HOLD: unresolved requested/realized or whole-plant residual')
    except allocation.FruitAllocationHold as exc:
        raise FruitStartupHold(str(exc)) from exc
    except OverflowError as exc:
        raise FruitStartupHold('NUMERIC_HOLD: aggregate overflow') from exc
    bound={'model_version':MODEL_VERSION,'policy_sha256':POLICY_SHA256,
        'profile_sha256':profile.sha256,'allocation_input_sha256':result['input_sha256'],
        'state':{'input_id':state['input_id'],'origin':state['origin'],'values':normalized}}
    return {'model_version':MODEL_VERSION,'policy_id':POLICY_ID,'policy_sha256':POLICY_SHA256,
        'scope':'software_research_only','profile_sha256':profile.sha256,
        'input_sha256':sha256(json.dumps(bound,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),
        'allocation_model_version':result['model_version'],
        'allocation_input_sha256':result['input_sha256'],
        'requested_carbohydrate_inflow':allocation._quantity(requested,RATE_UNIT),
        'effective_carbohydrate_inflow':allocation._quantity(effective,RATE_UNIT),
        'deferred_carbohydrate_inflow':allocation._quantity(deferred,RATE_UNIT),
        'realized_growth_respiration':allocation._quantity(respiration,RATE_UNIT),
        'buffer_derivative_adjustment':allocation._quantity(adjustment,RATE_UNIT),
        'carbohydrate_inflow':result['carbohydrate_inflow'],'number_inflow':result['number_inflow'],
        'allocation_balance_residual':result['balance_residual'],
        'allocation_balance_budget':result['balance_budget'],
        'balance_residual':{k:allocation._quantity(v,RATE_UNIT) for k,v in residuals.items()},
        'balance_budget':{k:allocation._quantity(budget,RATE_UNIT) for k in residuals}}
