"""Instantaneous explicit-entry cohorts with pinned Vanthoor equations."""

from dataclasses import dataclass, field
from hashlib import sha256
import json
from math import exp, expm1, fsum, isfinite, log, ulp
from types import MappingProxyType
from typing import Mapping

from app.crop_fruit_allocation import FruitAllocationHold, POLICY_SHA256, calculate_allocation_rates
from app.crop_fruit_transport import (
    FruitTransportHold, ReferenceFruitTransportParameters, calculate_transport_rates,
)


MODEL_VERSION = 'explicit-entry-fruit-cohort-rates-research-v1'
PROFILE_SHA256 = 'b453b4ffe618f26041e4ec6a1b1b7d2e5f38edb3d42adaaad4fa3cd4fbb99cbb'
ARRAY_UNITS = {'fruit_number':'fruits_equivalent/m2_floor',
               'fruit_carbohydrate':'mg_CH2O/m2_floor', 'fruit_relative_growth_rate':'1/s'}
SCALAR_UNITS = {'temperature_filtered_24h':'degC', 'temperature_sum':'degC_day'}
INFLOW_UNITS = {'fruit_carbohydrate_inflow':'mg_CH2O/m2_floor/s',
                'fruit_number_inflow':'fruits_equivalent/m2_floor/s',
                'fruit_entry_carbohydrate':'mg_CH2O/fruit_equivalent'}


class FruitCohortHold(ValueError):
    """An input or numeric domain for which no cohort result is supplied."""


def _need(condition, reason):
    if not condition:
        raise FruitCohortHold(reason)


@dataclass(frozen=True)
class ReferenceFruitCohortParameters:
    raw_bytes: bytes
    values: Mapping[str,float] = field(init=False,repr=False)
    sha256: str = field(init=False)
    profile_id: str = field(init=False)
    stages: int = field(init=False)

    def __post_init__(self):
        _need(type(self.raw_bytes) is bytes and len(self.raw_bytes)==5273,
              'PROFILE_HOLD: fixed reference bytes required')
        digest=sha256(self.raw_bytes).hexdigest()
        _need(digest==PROFILE_SHA256,'PROFILE_HOLD: unreviewed profile bytes')
        document=json.loads(self.raw_bytes)
        _need(document['allocation_policy']['source_register_sha256']==POLICY_SHA256,
              'PROFILE_HOLD: allocation policy mismatch')
        object.__setattr__(self,'values',MappingProxyType({k:float(v['value']) for k,v in document['parameters'].items()}))
        object.__setattr__(self,'sha256',digest)
        object.__setattr__(self,'profile_id',document['profile_id'])
        object.__setattr__(self,'stages',document['parameters']['nDev']['value'])


def _q(value,unit):
    return {'value':value,'unit':unit}


def _number(quantity,unit):
    _need(type(quantity) is dict and set(quantity)=={'value','unit'},'INPUT_HOLD: closed quantity required')
    _need(quantity['unit']==unit,'UNIT_HOLD: unexpected quantity unit')
    _need(type(quantity['value']) in (int,float),'INPUT_HOLD: numeric value required')
    try:
        value=float(quantity['value'])
    except OverflowError as exc:
        raise FruitCohortHold('NUMERIC_HOLD: unrepresentable input') from exc
    _need(isfinite(value) and value>=0,'INPUT_HOLD: finite nonnegative value required')
    return value


def _block(block,units,array_units=None):
    array_units=array_units or {}
    _need(type(block) is dict and set(block)=={'input_id','origin','values'},'INPUT_HOLD: closed block required')
    _need(type(block['input_id']) is str and 0<len(block['input_id'])<=256 and bool(block['input_id'].strip())
          and type(block['origin']) is str and block['origin'] in ('synthetic','reference_calculation','reference_observation'),
          'INPUT_HOLD: bounded provenance required')
    _need(type(block['values']) is dict and set(block['values'])==set(units)|set(array_units),
          'INPUT_HOLD: missing or unexpected quantity')
    values={name:_number(block['values'][name],unit) for name,unit in units.items()}
    normalized={name:_q(values[name],unit) for name,unit in units.items()}
    for name,unit in array_units.items():
        raw=block['values'][name]
        _need(type(raw) is list and len(raw)==50,'INPUT_HOLD: exact compartment array required')
        values[name]=[_number(q,unit) for q in raw]
        normalized[name]=[_q(v,unit) for v in values[name]]
    return values,{'input_id':block['input_id'],'origin':block['origin'],'values':normalized}


def _state(state,profile):
    _need(type(profile) is ReferenceFruitCohortParameters,'PROFILE_HOLD: pinned reference required')
    values,normalized=_block(state,SCALAR_UNITS,ARRAY_UNITS)
    _need(17<=values['temperature_filtered_24h']<=23 and values['temperature_sum']>0,
          'FRUIT_COHORT_DOMAIN_HOLD: outside post-onset shared research domain')
    _need(all(c==0 or n>0 for c,n in zip(values['fruit_carbohydrate'],values['fruit_number'],strict=True)),
          'FRUIT_COHORT_STATE_HOLD: carbohydrate without fruit number')
    return values,normalized


def _hash(operation,profile,state,**inputs):
    return sha256(json.dumps({'model_version':MODEL_VERSION,'operation':operation,
        'profile_sha256':profile.sha256,'state':state,**inputs},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _demand(values,profile,normalized):
    p=profile.values
    rate=fsum((p['cDev1'],p['cDev2']*values['temperature_filtered_24h']))
    period=1/(rate*p['seconds_per_day'])
    peak=p['Gompertz_M_intercept']+p['Gompertz_M_slope']*period
    steepness=1/(p['Gompertz_B_intercept']+p['Gompertz_B_M_slope']*peak)
    ages=[(j-p['stage_age_midpoint'])/profile.stages*period for j in range(1,profile.stages+1)]
    growth=[p['GMax']*steepness*exp(-steepness*(t-peak)-exp(-steepness*(t-peak))) for t in ages]
    demand=[n*g for n,g in zip(values['fruit_number'],growth,strict=True)]
    _need(all(isfinite(v) and v>0 for v in growth),'NUMERIC_HOLD: invalid potential growth')
    _need(all(isfinite(w) and (n==0 or w>0) for n,w in zip(values['fruit_number'],demand,strict=True)),
          'NUMERIC_HOLD: nonfinite or positive demand underflow')
    return {'model_version':MODEL_VERSION,'scope':'software_research_only','profile_id':profile.profile_id,
            'profile_sha256':profile.sha256,'input_sha256':_hash('potential_demand',profile,normalized),
            'development_rate':_q(rate,'1/s'),'fruit_growth_period':_q(period,'day'),
            'peak_age':_q(peak,'day'),'steepness':_q(steepness,'1/day'),
            'stage_age':[_q(v,'day') for v in ages],
            'potential_growth':[_q(v,'mg_CH2O/fruit_equivalent/day') for v in growth],
            'weighted_demand':[_q(v,'mg_CH2O/m2_floor/day') for v in demand]}


def calculate_demand_rates(*,state,profile):
    """Return potential rates and weighted demands, without advancing a state."""
    values,normalized=_state(state,profile)
    return _demand(values,profile,normalized)


def calculate_cohort_rates(*,state,inflow,profile,transport_profile):
    """Combine transport, allocation and maintenance; no time integration."""
    values,normalized=_state(state,profile)
    supplied,inflow_input=_block(inflow,INFLOW_UNITS)
    _need(type(transport_profile) is ReferenceFruitTransportParameters,
          'PROFILE_HOLD: pinned transport required')
    _need(all(profile.values[k]==transport_profile.values[k] for k in ('nDev','cDev1','cDev2')),
          'PROFILE_HOLD: inconsistent development parameters')
    demand=_demand(values,profile,normalized)
    transport_state={**normalized,'values':{k:v for k,v in normalized['values'].items() if k!='fruit_relative_growth_rate'}}
    allocation_state={**inflow_input,'values':{**inflow_input['values'],'fruit_potential_demand':demand['weighted_demand']}}
    try:
        transport=calculate_transport_rates(state=transport_state,profile=transport_profile)
        allocation=calculate_allocation_rates(state=allocation_state)
        p=profile.values
        temperature_factor=exp(log(p['Q10'])*(values['temperature_filtered_24h']-p['maintenance_temperature_reference_c'])/p['q10_temperature_interval_c'])
        maintenance=[]
        for carbon,rgr in zip(values['fruit_carbohydrate'],values['fruit_relative_growth_rate'],strict=True):
            exponent=p['cRgr']*rgr
            _need(isfinite(exponent),'NUMERIC_HOLD: maintenance exponent overflow')
            rate=p['fruit_maintenance']*carbon*(-expm1(-exponent))*temperature_factor
            _need(isfinite(rate) and (carbon==0 or rgr==0 or rate>0),
                  'NUMERIC_HOLD: nonfinite or positive maintenance underflow')
            maintenance.append(rate)
        carbon_derivatives=[fsum((t['value'],a['value'],-m)) for t,a,m in zip(
            transport['derivatives']['fruit_carbohydrate'],allocation['carbohydrate_inflow'],maintenance,strict=True)]
        number_derivatives=[fsum((t['value'],a['value'])) for t,a in zip(
            transport['derivatives']['fruit_number'],allocation['number_inflow'],strict=True)]
        F,S=supplied['fruit_carbohydrate_inflow'],supplied['fruit_number_inflow']
        growth=p['fruit_growth_respiration']*F
        _need(isfinite(growth) and (F==0 or growth>0),'NUMERIC_HOLD: invalid growth respiration')
        debit=fsum((F,growth))
        terminal=transport['terminal_outflow']
        carbon_terms=[*carbon_derivatives,terminal['fruit_carbohydrate']['value'],*maintenance]
        number_residual=fsum([*number_derivatives,terminal['fruit_number']['value'],-S])
        carbon_residual=fsum([*carbon_terms,-F])
        buffer_residual=fsum([*carbon_terms,growth,-debit])
        carbon_scale=max(F,debit,growth,*maintenance,*(q['value'] for q in allocation['carbohydrate_inflow']),
                         *(q['value'] for q in transport['outflows']['fruit_carbohydrate']),*map(abs,carbon_derivatives))
        number_scale=max(S,*(q['value'] for q in transport['outflows']['fruit_number']),*map(abs,number_derivatives))
        carbon_budget=2*(3*profile.stages+4)*ulp(carbon_scale)
        number_budget=2*(profile.stages+2)*ulp(number_scale)
        _need(all(isfinite(v) for v in (*carbon_derivatives,*number_derivatives,debit,carbon_residual,number_residual,buffer_residual)),
              'NUMERIC_HOLD: nonfinite aggregate')
        _need(abs(carbon_residual)<=carbon_budget and abs(buffer_residual)<=carbon_budget and abs(number_residual)<=number_budget,
              'BALANCE_HOLD: unresolved coupled residual')
    except (FruitTransportHold,FruitAllocationHold) as exc:
        raise FruitCohortHold(str(exc)) from exc
    except OverflowError as exc:
        raise FruitCohortHold('NUMERIC_HOLD: aggregate overflow') from exc
    carbon_unit,number_unit='mg_CH2O/m2_floor/s','fruits_equivalent/m2_floor/s'
    return {'model_version':MODEL_VERSION,'scope':'software_research_only','profile_id':profile.profile_id,
            'profile_sha256':profile.sha256,'transport_profile_sha256':transport_profile.sha256,
            'policy_sha256':allocation['policy_sha256'],
            'input_sha256':_hash('cohort_rates',profile,normalized,inflow=inflow_input,
                transport_profile_sha256=transport_profile.sha256,policy_sha256=allocation['policy_sha256']),
            'demand':demand,'allocation':allocation['carbohydrate_inflow'],
            'maintenance':[_q(v,carbon_unit) for v in maintenance],
            'derivatives':{'fruit_carbohydrate':[_q(v,carbon_unit) for v in carbon_derivatives],
                           'fruit_number':[_q(v,number_unit) for v in number_derivatives]},
            'terminal_outflow':terminal,'fruit_growth_respiration':_q(growth,carbon_unit),
            'fruit_buffer_debit':_q(debit,carbon_unit),
            'balance_residual':{'number':_q(number_residual,number_unit),'carbohydrate':_q(carbon_residual,carbon_unit),
                                'buffer_carbohydrate':_q(buffer_residual,carbon_unit)},
            'balance_budget':{'number':_q(number_budget,number_unit),'carbohydrate':_q(carbon_budget,carbon_unit),
                              'buffer_carbohydrate':_q(carbon_budget,carbon_unit)}}
