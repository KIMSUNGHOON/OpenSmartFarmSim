"""Compose pinned plant and explicit-entry cohort rates without time advance."""
from hashlib import sha256
import json
from math import fsum, isfinite, ulp

from . import crop_growth_rates as plant
from . import crop_fruit_cohorts as fruit
from .crop_fruit_transport import ReferenceFruitTransportParameters


MODEL_VERSION = 'vanthoor-greenlight-explicit-entry-plant-rates-research-v1'
PLANT_UNITS = {k:v for k,v in plant.STATE_UNITS.items() if k != 'fruit'}
REMOVAL_UNITS = {k:v for k,v in plant.REMOVAL_UNITS.items() if k != 'fruit'}
ENTRY_UNITS = {k:v for k,v in fruit.INFLOW_UNITS.items() if k != 'fruit_carbohydrate_inflow'}
ASSUMPTIONS = ('leaf_stem_fixed_RGR_from_reference_profile_not_measured',)


class PlantCohortHold(ValueError):
    """No coupled result is supplied outside the declared research domain."""


def _need(condition, reason):
    if not condition:
        raise PlantCohortHold(reason)


def _closed_block(block, fields):
    _need(type(block) is dict and set(block) == {'input_id','origin','values'},
          'INPUT_HOLD: closed block required')
    _need(type(block['input_id']) is str and 0 < len(block['input_id']) <= 256
          and bool(block['input_id'].strip()) and type(block['origin']) is str
          and block['origin'] in ('synthetic','reference_calculation','reference_observation'),
          'INPUT_HOLD: bounded research provenance required')
    _need(type(block['values']) is dict and set(block['values']) == set(fields),
          'INPUT_HOLD: missing or unexpected quantity')


def _q(value, unit=plant.RATE_UNIT):
    return {'value':value,'unit':unit}


def calculate_plant_cohort_rates(*, state, cohort_state, forcing, removals, fruit_entry,
                                growth_profile, cohort_profile, transport_profile):
    """Derive total fruit once and replace its maintenance/derivative by cohorts."""
    _need(type(growth_profile) is plant.ReferenceParameters
          and type(cohort_profile) is fruit.ReferenceFruitCohortParameters
          and type(transport_profile) is ReferenceFruitTransportParameters,
          'PROFILE_HOLD: pinned profiles required')
    for pkey, ckey in (('cFruitG','fruit_growth_respiration'),('cFruitM','fruit_maintenance'),
                      ('cRgr','cRgr'),('q10m','Q10'),
                      ('maintenance_temperature_reference_c','maintenance_temperature_reference_c'),
                      ('q10_temperature_interval_c','q10_temperature_interval_c'),
                      ('seconds_per_day','seconds_per_day')):
        _need(growth_profile.values[pkey] == cohort_profile.values[ckey],
              'PROFILE_HOLD: incompatible plant/cohort coefficients')
    for block, fields in ((state,PLANT_UNITS),(cohort_state,{**fruit.ARRAY_UNITS,**fruit.SCALAR_UNITS}),
                          (forcing,plant.FORCING_UNITS),(removals,REMOVAL_UNITS),(fruit_entry,ENTRY_UNITS)):
        _closed_block(block, fields)
    try:
        # Public cohort validation precedes deriving mass from its input quantities.
        fruit.calculate_demand_rates(state=cohort_state, profile=cohort_profile)
        total_fruit = fsum(float(q['value']) for q in cohort_state['values']['fruit_carbohydrate'])
        _need(isfinite(total_fruit), 'NUMERIC_HOLD: nonfinite derived fruit total')
        base_state = {**state,'values':{**state['values'],'fruit':_q(total_fruit,plant.MASS_UNIT)}}
        base_removals = {**removals,'values':{**removals['values'],'fruit':_q(0.0)}}
        base = plant.calculate_rates(state=base_state, forcing=forcing, removals=base_removals,
                                     profile=growth_profile)
        _need(all(float(state['values'][k]['value']) == float(cohort_state['values'][k]['value'])
                  for k in fruit.SCALAR_UNITS), 'STATE_MISMATCH_HOLD: conflicting shared temperatures')
        inflow = {**fruit_entry,'values':{**fruit_entry['values'],
                   'fruit_carbohydrate_inflow':base['allocation']['fruit']}}
        cohorts = fruit.calculate_cohort_rates(state=cohort_state, inflow=inflow,
                    profile=cohort_profile, transport_profile=transport_profile)
        derivatives = {k:v for k,v in base['derivatives'].items() if k != 'fruit'}
        maintenance = fsum(q['value'] for q in cohorts['maintenance'])
        carbon_terms = [*(derivatives[k]['value'] for k in ('buffer','leaf','stem_root')),
            *(q['value'] for q in cohorts['derivatives']['fruit_carbohydrate']),
            base['growth_respiration']['value'],
            *(base['maintenance_respiration'][k]['value'] for k in ('leaf','stem_root')),
            maintenance, *(base['removals'][k]['value'] for k in REMOVAL_UNITS),
            cohorts['terminal_outflow']['fruit_carbohydrate']['value'], -base['photosynthesis']['value']]
        carbon_residual = fsum(carbon_terms)
        scale = max(1.0, *map(abs,carbon_terms))
        carbon_budget = fsum((base['carbon_residual_budget']['value'],
            cohorts['balance_budget']['carbohydrate']['value'], 32*ulp(scale)))
        _need(isfinite(carbon_residual) and isfinite(maintenance) and isfinite(carbon_budget),
              'NUMERIC_HOLD: nonfinite coupled aggregate')
        _need(abs(carbon_residual) <= carbon_budget, 'BALANCE_HOLD: unresolved whole plant residual')
    except (plant.CropRateHold,fruit.FruitCohortHold) as exc:
        raise PlantCohortHold(str(exc)) from exc
    except OverflowError as exc:
        raise PlantCohortHold('NUMERIC_HOLD: derived mass or balance overflow') from exc
    profile_hashes = {k:p.sha256 for k,p in (
        ('growth_profile',growth_profile),('cohort_profile',cohort_profile),('transport_profile',transport_profile))}
    bound = {'model_version':MODEL_VERSION,'plant_input_sha256':base['input_sha256'],
             'cohort_input_sha256':cohorts['input_sha256'],'profile_sha256':profile_hashes}
    return {'model_version':MODEL_VERSION,'scope':'software_research_only',
        'input_sha256':sha256(json.dumps(bound,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),
        'profile_sha256':profile_hashes, 'component_model_versions':{
            'plant':base['model_version'],'cohorts':cohorts['model_version']},
        'component_input_sha256':{'plant':base['input_sha256'],'cohorts':cohorts['input_sha256']},
        'research_assumptions':list(ASSUMPTIONS), 'derivatives':derivatives, 'cohorts':cohorts,
        'fruit_carbohydrate_total':_q(total_fruit,plant.MASS_UNIT),
        'fruit_maintenance':_q(maintenance), 'photosynthesis':base['photosynthesis'],
        'growth_respiration':base['growth_respiration'], 'lai':base['lai'], 'allocation':base['allocation'],
        'vegetative_maintenance':{k:base['maintenance_respiration'][k] for k in ('leaf','stem_root')},
        'removals':{k:base['removals'][k] for k in REMOVAL_UNITS},
        'balance_residual':{'carbohydrate':_q(carbon_residual),'number':cohorts['balance_residual']['number']},
        'balance_budget':{'carbohydrate':_q(carbon_budget),'number':cohorts['balance_budget']['number']}}
