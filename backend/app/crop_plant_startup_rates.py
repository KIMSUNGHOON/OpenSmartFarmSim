"""Post-onset whole-plant rates with explicit-entry empty-sink carbon deferral."""
from hashlib import sha256
import json
from math import fsum, isfinite, ulp

from . import crop_growth_rates as plant
from . import crop_fruit_cohorts as fruit
from . import crop_fruit_startup as startup
from . import crop_plant_cohort_rates as original
from .crop_fruit_transport import ReferenceFruitTransportParameters

MODEL_VERSION = 'explicit-entry-empty-sink-plant-rates-research-v1'


class PlantStartupHold(ValueError):
    """No plant/cohort rates are supplied outside the declared research domain."""


def _need(condition, reason):
    if not condition:
        raise PlantStartupHold(reason)


def calculate_plant_startup_rates(*, state, cohort_state, forcing, removals, fruit_entry,
                                 growth_profile, cohort_profile, transport_profile):
    """Apply retained carbon and realized growth respiration together; no time advance."""
    _need(type(growth_profile) is plant.ReferenceParameters
          and type(cohort_profile) is fruit.ReferenceFruitCohortParameters
          and type(transport_profile) is ReferenceFruitTransportParameters,
          'PROFILE_HOLD: pinned profiles required')
    for pkey, ckey in (('cFruitG', 'fruit_growth_respiration'), ('cFruitM', 'fruit_maintenance'),
                      ('cRgr', 'cRgr'), ('q10m', 'Q10'),
                      ('maintenance_temperature_reference_c', 'maintenance_temperature_reference_c'),
                      ('q10_temperature_interval_c', 'q10_temperature_interval_c'),
                      ('seconds_per_day', 'seconds_per_day')):
        _need(growth_profile.values[pkey]==cohort_profile.values[ckey],
              'PROFILE_HOLD: incompatible plant/cohort coefficients')
    try:
        for block, fields in ((state, original.PLANT_UNITS),
            (cohort_state, {**fruit.ARRAY_UNITS, **fruit.SCALAR_UNITS}), (forcing, plant.FORCING_UNITS),
            (removals, original.REMOVAL_UNITS), (fruit_entry, original.ENTRY_UNITS)):
            original._closed_block(block, fields)
        demand = fruit.calculate_demand_rates(state=cohort_state, profile=cohort_profile)
        total_fruit = fsum(float(q['value']) for q in cohort_state['values']['fruit_carbohydrate'])
        _need(isfinite(total_fruit), 'NUMERIC_HOLD: nonfinite derived fruit total')
        base_state = {**state, 'values': {**state['values'], 'fruit': original._q(total_fruit, plant.MASS_UNIT)}}
        base_removals = {**removals, 'values': {**removals['values'], 'fruit': original._q(0.0)}}
        base = plant.calculate_rates(state=base_state, forcing=forcing, removals=base_removals, profile=growth_profile)
        _need(all(float(state['values'][k]['value'])==float(cohort_state['values'][k]['value'])
                  for k in fruit.SCALAR_UNITS), 'STATE_MISMATCH_HOLD: conflicting shared temperatures')
        requested = {**fruit_entry, 'values': {**fruit_entry['values'],
            'fruit_carbohydrate_inflow': base['allocation']['fruit'],
            'fruit_potential_demand': demand['weighted_demand']}}
        retained = startup.calculate_startup_rates(state=requested, profile=cohort_profile)
        inflow = {**fruit_entry, 'values': {**fruit_entry['values'],
            'fruit_carbohydrate_inflow': retained['effective_carbohydrate_inflow']}}
        cohorts = fruit.calculate_cohort_rates(state=cohort_state, inflow=inflow,
            profile=cohort_profile, transport_profile=transport_profile)
        _need(cohorts['allocation']==retained['carbohydrate_inflow'] and
              cohorts['fruit_growth_respiration']==retained['realized_growth_respiration'],
              'BALANCE_HOLD: inconsistent realized cohort allocation or respiration')
        derivatives = {k: v for k, v in base['derivatives'].items() if k!='fruit'}
        derivatives['buffer'] = original._q(fsum((base['derivatives']['buffer']['value'],
            retained['buffer_derivative_adjustment']['value'])))
        vegetative_growth = [startup._product(growth_profile.values[coefficient], base['allocation'][organ]['value'])
                             for coefficient, organ in (('cLeafG', 'leaf'), ('cStemG', 'stem_root'))]
        growth = fsum((*vegetative_growth, retained['realized_growth_respiration']['value']))
        maintenance = fsum(q['value'] for q in cohorts['maintenance'])
        carbon_terms = [*(derivatives[k]['value'] for k in ('buffer', 'leaf', 'stem_root')),
            *(q['value'] for q in cohorts['derivatives']['fruit_carbohydrate']), growth,
            *(base['maintenance_respiration'][k]['value'] for k in ('leaf', 'stem_root')),
            maintenance, *(base['removals'][k]['value'] for k in original.REMOVAL_UNITS),
            cohorts['terminal_outflow']['fruit_carbohydrate']['value'], -base['photosynthesis']['value']]
        carbon_residual = fsum(carbon_terms)
        scale = max(map(abs, carbon_terms))
        carbon_budget = fsum((base['carbon_residual_budget']['value'],
            cohorts['balance_budget']['carbohydrate']['value'],
            retained['balance_budget']['whole_plant']['value'], 32*ulp(scale)))
        _need(all(isfinite(v) for v in (*carbon_terms, carbon_residual, carbon_budget)),
              'NUMERIC_HOLD: nonfinite whole-plant aggregate')
        _need(abs(carbon_residual)<=carbon_budget, 'BALANCE_HOLD: unresolved whole-plant carbon residual')
    except (plant.CropRateHold, fruit.FruitCohortHold, startup.FruitStartupHold, original.PlantCohortHold) as exc:
        raise PlantStartupHold(str(exc)) from exc
    except OverflowError as exc:
        raise PlantStartupHold('NUMERIC_HOLD: derived mass or balance overflow') from exc
    profiles = {k: p.sha256 for k, p in (
        ('growth_profile', growth_profile), ('cohort_profile', cohort_profile), ('transport_profile', transport_profile))}
    component_inputs = {'plant': base['input_sha256'], 'cohorts': cohorts['input_sha256'],
                        'startup': retained['input_sha256']}
    bound = {'model_version': MODEL_VERSION, 'policy_sha256': startup.POLICY_SHA256,
             'component_input_sha256': component_inputs, 'profile_sha256': profiles}
    return {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
        'input_sha256': sha256(json.dumps(bound, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
        'policy_id': startup.POLICY_ID, 'policy_sha256': startup.POLICY_SHA256, 'profile_sha256': profiles,
        'component_model_versions': {'plant': base['model_version'], 'cohorts': cohorts['model_version'],
                                     'startup': retained['model_version']},
        'component_input_sha256': component_inputs, 'research_assumptions': list(original.ASSUMPTIONS),
        'derivatives': derivatives, 'cohorts': cohorts, 'fruit_startup': retained,
        'fruit_carbohydrate_total': original._q(total_fruit, plant.MASS_UNIT),
        'fruit_maintenance': original._q(maintenance), 'photosynthesis': base['photosynthesis'],
        'growth_respiration': original._q(growth), 'lai': base['lai'],
        'requested_allocation': base['allocation'],
        'allocation': {**base['allocation'], 'fruit': retained['effective_carbohydrate_inflow']},
        'vegetative_maintenance': {k: base['maintenance_respiration'][k] for k in ('leaf', 'stem_root')},
        'removals': {k: base['removals'][k] for k in original.REMOVAL_UNITS},
        'balance_residual': {'carbohydrate': original._q(carbon_residual), 'number': cohorts['balance_residual']['number']},
        'balance_budget': {'carbohydrate': original._q(carbon_budget), 'number': cohorts['balance_budget']['number']}}
