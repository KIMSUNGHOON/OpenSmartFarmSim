"""Same-stage inflow coupling; crop-stem-root-partition-climate-rhs-v1.md."""
from copy import deepcopy
from hashlib import sha256
import json
from math import fsum, isfinite, ulp
from pathlib import Path
from sys import modules

from . import crop_leaf_carbon_stock_rhs as source
from . import crop_stem_root_carbon_partition as partition

MODEL_VERSION = 'stem-root-partition-individual-leaf-climate-rhs-research-v1'
MAX_BYTES = 512 * 1024
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENT_CODE_SHA256 = {**source.COMPONENT_CODE_SHA256,
                        **{m.__name__: sha256(Path(m.__file__).read_bytes()).hexdigest() for m in (source, partition)}}


class StemRootClimateHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise StemRootClimateHold(reason)


def _canonical(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: 512KiB stem/root joint input/output required')
    return raw


def _fence():
    expected = {**COMPONENT_CODE_SHA256, __name__: CODE_SHA256}
    _need(all(sha256(Path(modules[name].__file__).read_bytes()).hexdigest() == digest for name, digest in expected.items()),
          'CODE_HOLD: original stem/root joint sources required')


def _rate(quantity):
    partition._closed(quantity, {'value', 'unit'})
    _need(quantity['unit'] == partition.source.RATE_UNIT and type(quantity['value']) in (int, float) and
          isfinite(quantity['value']), 'UNIT_HOLD: finite original carbon rate required')
    return float(quantity['value'])


def _stage(value, scenario, leaf_stocks):
    partition._closed(value, {'input_id', 'origin', 'policy', 'model_floor_area', 'compartments'})
    _need(type(scenario) is dict and type(leaf_stocks) is dict and value['input_id'] == scenario.get('input_id') == leaf_stocks.get('input_id') and
          value['origin'] == 'synthetic' and value['policy'] == partition.POLICY_ID, 'SCOPE_HOLD: one declared stem/root stage required')
    partition._id(value['input_id'])
    floor = partition._number(value['model_floor_area'], 'm2_floor')
    _need(floor > 0 and partition._q(floor, 'm2_floor') == scenario['geometry']['model_floor_area'] == leaf_stocks['model_floor_area'],
          'BASIS_HOLD: same positive source/leaf/stem footprint required')
    rows = value['compartments']
    _need(type(rows) is list and 1 <= len(rows) <= 512, 'CAPACITY_HOLD: declared 1..512 compartments required')
    normalized = []
    for row in rows:
        partition._closed(row, {'compartment_id', 'kind', 'sink_weight'})
        partition._id(row['compartment_id'])
        _need(row['kind'] in ('internode', 'root_system'), 'INVENTORY_HOLD: explicit compartment kind required')
        normalized.append({**row, 'sink_weight': partition._q(partition._number(row['sink_weight'], '1'), '1')})
    _need(len({r['compartment_id'] for r in normalized}) == len(rows) and sum(r['kind'] == 'root_system' for r in normalized) == 1,
          'INVENTORY_HOLD: unique compartment IDs and exactly one root system required')
    return {**value, 'model_floor_area': partition._q(floor, 'm2_floor'), 'compartments': normalized}


def evaluate_rhs(*, scenario, leaf_stocks, stem_root_stage, growth_profile, cohort_profile, transport_profile, exchange_profile):
    try:
        _fence()
        raw = _canonical({'scenario': scenario, 'leaf_stocks': leaf_stocks, 'stem_root_stage': stem_root_stage})
        captured = json.loads(raw); s, l = captured['scenario'], captured['leaf_stocks']
        stem = _stage(captured['stem_root_stage'], s, l)
        source_raw = source._canonical({'scenario': s, 'leaf_stocks': l})
        original = source.evaluate_rhs(scenario=s, leaf_stocks=l, growth_profile=growth_profile, cohort_profile=cohort_profile,
                                       transport_profile=transport_profile, exchange_profile=exchange_profile)
        profiles = {'growth': growth_profile, 'cohort': cohort_profile, 'transport': transport_profile, 'exchange': exchange_profile}
        _need(original['model_version'] == source.MODEL_VERSION and original['code_sha256'] == COMPONENT_CODE_SHA256[source.__name__] and
              original['scope'] == 'software_research_only' and original['claim_scope'] == 'synthetic_individual_leaf_carbon_rhs_only' and original['G0_G4'] == 'not_assessed' and
              original['profile_sha256'] == {k: sha256(v.raw_bytes).hexdigest() for k, v in profiles.items()} and
              original['raw_input_sha256'] == sha256(source_raw).hexdigest() and source._canonical({'scenario': s, 'leaf_stocks': l}) == source_raw and
              original['calculation_sha256'] == sha256(source._canonical({k: v for k, v in original.items() if k != 'calculation_sha256'})).hexdigest(),
              'SOURCE_HOLD: original same-stage leaf/climate result required')
        prior = original['source_stage']; crop = prior['source_joint']['crop']
        request = crop['allocation']['stem_root']
        _need(request == prior['adjusted_carbon']['allocation']['stem_root'], 'SOURCE_HOLD: original structural stem/root inflow required')
        part_inputs = {'input_id': stem['input_id'], 'origin': 'synthetic', 'policy': stem['policy'],
                       'model_floor_area': deepcopy(stem['model_floor_area']), 'requested_stem_root_growth': deepcopy(request),
                       'compartments': deepcopy(stem['compartments'])}
        part_raw = partition._canonical(part_inputs)
        allocated = partition.calculate_partition(inputs=part_inputs, growth_profile=growth_profile)
        _need(allocated['model_version'] == partition.MODEL_VERSION and allocated['code_sha256'] == COMPONENT_CODE_SHA256[partition.__name__] and allocated['source_code_sha256'] == partition.SOURCE_SHA256 and
              allocated['scope'] == 'software_research_only' and allocated['claim_scope'] == 'synthetic_stem_root_partition_math_only' and allocated['G0_G4'] == 'not_assessed' and
              allocated['policy_id'] == partition.POLICY_ID and
              allocated['profile_sha256'] == original['profile_sha256']['growth'] and allocated['policy_sha256'] == partition.POLICY_SHA256 and
              allocated['inputs'] == part_inputs and partition._canonical(part_inputs) == part_raw and allocated['raw_input_sha256'] == sha256(part_raw).hexdigest() and
              allocated['calculation_sha256'] == sha256(partition._canonical({k: v for k, v in allocated.items() if k != 'calculation_sha256'})).hexdigest(),
              'SOURCE_HOLD: same original stem/root allocation required')
        _need([(r['compartment_id'], r['kind']) for r in allocated['allocation']] == [(r['compartment_id'], r['kind']) for r in stem['compartments']],
              'INVENTORY_HOLD: original allocation identities/order required')
        adjustments = allocated['derivative_adjustments']; plant = deepcopy(original['derivatives']['plant']); q = partition._q
        for name in ('buffer', 'stem_root'):
            change = _rate(adjustments[name])
            if change != 0:
                plant[name] = q(fsum((_rate(plant[name]), change)))
        growth = _rate(prior['adjusted_carbon']['growth_respiration'])
        if _rate(adjustments['growth_respiration']) != 0:
            growth = fsum((growth, _rate(adjustments['growth_respiration'])))
        _need(isfinite(growth) and growth >= 0 and all(isfinite(v['value']) for v in plant.values()),
              'NUMERIC_HOLD: finite derivatives and nonnegative growth respiration required')
        states = original['inputs']['scenario']['plant_state']
        _need(all(states[k]['value'] != 0 or plant[k]['value'] >= 0 for k in ('buffer', 'stem_root')),
              'DEPLETED_STATE_HOLD: outward adjusted derivative at zero buffer or stem/root stock')
        leaf = original['leaf_totals']; cohorts = original['derivatives']['cohorts']
        terms = [*(_rate(plant[k]) for k in ('buffer', 'leaf', 'stem_root')), *(_rate(v) for v in cohorts['fruit_carbohydrate']), growth,
                 _rate(leaf['maintenance']), _rate(crop['vegetative_maintenance']['stem_root']), _rate(crop['fruit_maintenance']),
                 _rate(leaf['removal']), _rate(crop['removals']['stem_root']), _rate(crop['cohorts']['terminal_outflow']['fruit_carbohydrate']), -_rate(crop['photosynthesis'])]
        stem_terms = [_rate(plant['stem_root']), _rate(crop['vegetative_maintenance']['stem_root']), _rate(crop['removals']['stem_root']),
                      *(-_rate(v['carbohydrate_inflow']) for v in allocated['allocation'])]
        residuals = {'carbohydrate': fsum(terms), 'stem_root_compartment': fsum(stem_terms)}
        budgets = {'carbohydrate': fsum((_rate(original['balance_budgets']['carbohydrate']),
                                       _rate(allocated['balance_budgets']['whole_stem_root_budget']), 64 * ulp(max(1., *map(abs, terms))))),
                   'stem_root_compartment': fsum((_rate(allocated['balance_budgets']['allocation']), 64 * ulp(max(1., *map(abs, stem_terms)))))}
        _need(all(isfinite(v) for v in (*residuals.values(), *budgets.values())) and all(abs(v) <= budgets[k] for k, v in residuals.items()),
              'BALANCE_HOLD: unresolved same-stage whole carbon or stem/root ledger')
        identity = {'model_version': MODEL_VERSION, 'code_sha256': CODE_SHA256, 'component_code_sha256': dict(COMPONENT_CODE_SHA256),
                    'profile_sha256': dict(original['profile_sha256']), 'policy_id': partition.POLICY_ID, 'policy_sha256': partition.POLICY_SHA256,
                    'inputs': {**deepcopy(original['inputs']), 'stem_root_stage': deepcopy(stem)},
                    'source_stage_calculation_sha256': original['calculation_sha256'], 'partition_calculation_sha256': allocated['calculation_sha256']}
        result = {**identity, 'raw_input_sha256': sha256(raw).hexdigest(), 'input_sha256': sha256(_canonical(identity)).hexdigest(),
                  'scope': 'software_research_only', 'claim_scope': 'synthetic_stem_root_partition_joint_rhs_only', 'G0_G4': 'not_assessed',
                  'time_coordinate': 'derivatives_per_second_no_time_advance', 'source_stage': deepcopy(original), 'stem_root_partition': deepcopy(allocated),
                  'organ_carbon_stocks': 'not_allocated_in_this_instantaneous_inflow_stage', 'geometry_binding': 'declared_synthetic_sinks_only',
                  'adjusted_carbon': {'requested_allocation': deepcopy(prior['adjusted_carbon']['requested_allocation']),
                                      'allocation': {**deepcopy(prior['adjusted_carbon']['allocation']), 'stem_root': deepcopy(allocated['effective_stem_root_growth'])},
                                      'growth_respiration': q(growth), 'derivatives': deepcopy(plant)},
                  'derivatives': {'plant': plant, 'cohorts': deepcopy(cohorts), 'climate': deepcopy(original['derivatives']['climate'])},
                  'balance_residuals': {**deepcopy(original['balance_residuals']), **{k: q(v) for k, v in residuals.items()}},
                  'balance_budgets': {**deepcopy(original['balance_budgets']), **{k: q(v) for k, v in budgets.items()}}}
        result['calculation_sha256'] = sha256(_canonical(result)).hexdigest()
        _canonical(result); _fence()
        return result
    except StemRootClimateHold:
        raise
    except (source.LeafCarbonStockHold, partition.StemRootPartitionHold) as error:
        raise StemRootClimateHold(str(error)) from None
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, RecursionError, ZeroDivisionError):
        raise StemRootClimateHold('INPUT_HOLD: invalid or unrepresentable stem/root joint stage') from None
