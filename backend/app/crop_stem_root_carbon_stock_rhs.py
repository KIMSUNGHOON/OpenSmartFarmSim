"""Authoritative synthetic stem/root stocks; crop-stem-root-carbon-stock-rhs-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum, isfinite, ulp
from pathlib import Path
from sys import modules

from . import crop_stem_root_partition_climate_rhs as source
from . import crop_plant_cohort_rates as legacy

part = source.partition
MODEL_VERSION = 'individual-stem-root-carbon-stock-joint-rhs-research-v1'
POLICY_ID = 'stem-root-stocks-uniform-maintenance-explicit-removal-v1'
POLICY = {'id': POLICY_ID, 'stock': 'explicit_complete_same_floor_compartments_one_root',
          'aggregate': 'once_rounded_exact_sum_only', 'maintenance': 'original_total_proportional_to_current_stock',
          'zero_total': 'require_original_zero_maintenance_and_each_zero_maintenance',
          'removal': 'explicit_each_compartment', 'growth_partition_policy': part.POLICY_ID,
          'zero_stock': 'reject_outward_final_derivative_no_clipping', 'geometry_inference': False}
POLICY_SHA256 = sha256(json.dumps(POLICY, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
MAX_BYTES = 512 * 1024
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENT_CODE_SHA256 = {**source.COMPONENT_CODE_SHA256, source.__name__: sha256(Path(source.__file__).read_bytes()).hexdigest()}


class StemRootCarbonStockHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise StemRootCarbonStockHold(reason)


def _canonical(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: 512KiB stem/root stock input/output required')
    return raw


def _sum(values):
    return part._normal(float(sum(map(Fraction.from_float, values), Fraction(0))))


def _fence():
    expected = {**COMPONENT_CODE_SHA256, __name__: CODE_SHA256}
    _need(all(sha256(Path(modules[name].__file__).read_bytes()).hexdigest() == digest for name, digest in expected.items()),
          'CODE_HOLD: original individual stem/root stock sources required')


def evaluate_rhs(*, scenario, leaf_stocks, stem_root_stocks, growth_profile, cohort_profile, transport_profile, exchange_profile):
    try:
        _fence()
        _need(type(growth_profile) is part.source.ReferenceParameters and
              growth_profile.sha256 == part.source.PROFILE_SHA256 == sha256(growth_profile.raw_bytes).hexdigest() and
              dict(growth_profile.values) == {k: float(v['value']) for k, v in json.loads(growth_profile.raw_bytes)['parameters'].items()},
              'PROFILE_HOLD: growth values must match the original pinned bytes')
        part._closed(stem_root_stocks, {'input_id', 'origin', 'policy', 'model_floor_area', 'compartments'})
        _need(type(stem_root_stocks['compartments']) is list, 'INPUT_HOLD: explicit stock list required')
        _need(type(leaf_stocks) is dict and type(leaf_stocks.get('leaf_ids')) is list and type(leaf_stocks.get('leaves')) is list,
              'INPUT_HOLD: original explicit leaf stock lists required')
        raw = _canonical({'scenario': scenario, 'leaf_stocks': leaf_stocks, 'stem_root_stocks': stem_root_stocks})
        captured = json.loads(raw); s, l, stocks = (captured[k] for k in ('scenario', 'leaf_stocks', 'stem_root_stocks'))
        _need(type(s) is dict and type(l) is dict, 'INPUT_HOLD: declared source stage required')
        part._closed(s['plant_state'], set(legacy.PLANT_UNITS) - {'leaf', 'stem_root'})
        part._closed(s['removals'], set(legacy.REMOVAL_UNITS) - {'leaf', 'stem_root'})
        _need(stocks['input_id'] == s.get('input_id') == l.get('input_id') and stocks['origin'] == 'synthetic' and stocks['policy'] == POLICY_ID,
              'SCOPE_HOLD: one explicit synthetic stock stage and policy required')
        part._id(stocks['input_id']); floor = part._number(stocks['model_floor_area'], 'm2_floor')
        _need(floor > 0 and part._q(floor, 'm2_floor') == s['geometry']['model_floor_area'] == l['model_floor_area'],
              'BASIS_HOLD: same positive source/leaf/stem footprint required')
        _need(1 <= len(stocks['compartments']) <= 512, 'CAPACITY_HOLD: explicit 1..512 stock compartments required')
        rows = []
        for row in stocks['compartments']:
            part._closed(row, {'compartment_id', 'kind', 'carbon', 'sink_weight', 'removal'}); part._id(row['compartment_id'])
            _need(row['kind'] in ('internode', 'root_system'), 'INVENTORY_HOLD: explicit compartment kind required')
            rows.append({'compartment_id': row['compartment_id'], 'kind': row['kind'],
                         **{k: part._q(part._number(row[k], unit), unit) for k, unit in (
                             ('carbon', part.source.MASS_UNIT), ('sink_weight', '1'), ('removal', part.source.RATE_UNIT))}})
        _need(len({r['compartment_id'] for r in rows}) == len(rows) and sum(r['kind'] == 'root_system' for r in rows) == 1,
              'INVENTORY_HOLD: unique IDs and exactly one root system required')
        carbon = [r['carbon']['value'] for r in rows]; exact_C = sum(map(Fraction.from_float, carbon), Fraction(0))
        total_C = _sum(carbon); total_R = _sum(r['removal']['value'] for r in rows)
        assembled = deepcopy(s); assembled['plant_state']['stem_root'] = part._q(total_C, part.source.MASS_UNIT)
        assembled['removals']['stem_root'] = part._q(total_R)
        sink_stage = {'input_id': stocks['input_id'], 'origin': 'synthetic', 'policy': part.POLICY_ID,
                      'model_floor_area': part._q(floor, 'm2_floor'),
                      'compartments': [{k: deepcopy(r[k]) for k in ('compartment_id', 'kind', 'sink_weight')} for r in rows]}
        assembled_raw = source._canonical({'scenario': assembled, 'leaf_stocks': l, 'stem_root_stage': sink_stage})
        original = source.evaluate_rhs(scenario=assembled, leaf_stocks=l, stem_root_stage=sink_stage,
                                       growth_profile=growth_profile, cohort_profile=cohort_profile,
                                       transport_profile=transport_profile, exchange_profile=exchange_profile)
        profiles = dict(growth=growth_profile, cohort=cohort_profile, transport=transport_profile, exchange=exchange_profile)
        _need(original['model_version'] == source.MODEL_VERSION and original['code_sha256'] == COMPONENT_CODE_SHA256[source.__name__] and
              original['component_code_sha256'] == source.COMPONENT_CODE_SHA256 and original['scope'] == 'software_research_only' and
              original['claim_scope'] == 'synthetic_stem_root_partition_joint_rhs_only' and original['G0_G4'] == 'not_assessed' and
              original['profile_sha256'] == {k: sha256(p.raw_bytes).hexdigest() for k, p in profiles.items()} and
              original['raw_input_sha256'] == sha256(assembled_raw).hexdigest() and
              source._canonical({'scenario': assembled, 'leaf_stocks': l, 'stem_root_stage': sink_stage}) == assembled_raw and
              original['inputs']['scenario']['plant_state']['stem_root'] == assembled['plant_state']['stem_root'] and
              original['inputs']['scenario']['removals']['stem_root'] == assembled['removals']['stem_root'] and
              original['inputs']['stem_root_stage'] == sink_stage and
              original['calculation_sha256'] == sha256(source._canonical({k: v for k, v in original.items() if k != 'calculation_sha256'})).hexdigest(),
              'SOURCE_HOLD: original inventory-assembled stage and hashes required')
        leaf_stage = original['source_stage']; crop = leaf_stage['source_stage']['source_joint']['crop']
        M = part._normal(source._rate(crop['vegetative_maintenance']['stem_root']))
        _need((total_C == 0 and M == 0) or (total_C > 0 and M > 0), 'NUMERIC_HOLD: original aggregate maintenance inconsistent with stock')
        rates = []
        allocations = original['stem_root_partition']['allocation']
        _need(len(allocations) == len(rows), 'INVENTORY_HOLD: complete original allocation required')
        for row, c, allocation in zip(rows, carbon, allocations, strict=True):
            _need((row['compartment_id'], row['kind']) == (allocation['compartment_id'], allocation['kind']),
                  'INVENTORY_HOLD: original allocation identities/order required')
            maintenance = part._normal(float(Fraction.from_float(M) * Fraction.from_float(c) / exact_C)) if exact_C else 0.
            _need(c == 0 or maintenance > 0, 'NUMERIC_HOLD: positive individual maintenance lost')
            inflow = part._normal(source._rate(allocation['carbohydrate_inflow']))
            _need(inflow >= 0, 'NUMERIC_HOLD: nonnegative compartment inflow required')
            derivative = part._normal(fsum((inflow, -maintenance, -row['removal']['value'])))
            _need(c != 0 or derivative >= 0, 'DEPLETED_STATE_HOLD: outward derivative at zero individual stem/root stock')
            rates.append({'compartment_id': row['compartment_id'], 'kind': row['kind'], 'inflow': part._q(inflow),
                          'maintenance': part._q(maintenance), 'removal': deepcopy(row['removal']), 'derivative': part._q(derivative)})
        totals = {k: _sum(r[k]['value'] for r in rates) for k in ('inflow', 'maintenance', 'removal', 'derivative')}
        plant = deepcopy(original['derivatives']['plant']); plant['stem_root'] = part._q(totals['derivative'])
        targets = {'inflow': source._rate(original['adjusted_carbon']['allocation']['stem_root']), 'maintenance': M,
                   'removal': total_R, 'derivative': source._rate(original['derivatives']['plant']['stem_root'])}
        aggregation = {k: fsum((totals[k], -targets[k])) for k in totals}
        scale = max(1., *map(abs, targets.values()), *(abs(r[k]['value']) for r in rates for k in totals))
        roundoff = 64 * (len(rows) + 8) * ulp(scale)
        _need(isfinite(roundoff) and all(abs(v) <= roundoff for v in aggregation.values()), 'BALANCE_HOLD: unresolved individual stem/root aggregation')
        leaf = leaf_stage['leaf_totals']
        terms = [*(source._rate(plant[k]) for k in ('buffer', 'leaf', 'stem_root')),
                 *(source._rate(q) for q in original['derivatives']['cohorts']['fruit_carbohydrate']),
                 source._rate(original['adjusted_carbon']['growth_respiration']), source._rate(leaf['maintenance']), totals['maintenance'],
                 source._rate(crop['fruit_maintenance']), source._rate(leaf['removal']), totals['removal'],
                 source._rate(crop['cohorts']['terminal_outflow']['fruit_carbohydrate']), -source._rate(crop['photosynthesis'])]
        residuals = {'carbohydrate': fsum(terms), 'stem_root_compartment': fsum((totals['derivative'], totals['maintenance'], totals['removal'], -totals['inflow']))}
        budgets = {'carbohydrate': fsum((source._rate(original['balance_budgets']['carbohydrate']), roundoff, 64 * ulp(max(1., *map(abs, terms))))),
                   'stem_root_compartment': fsum((source._rate(original['balance_budgets']['stem_root_compartment']), roundoff))}
        _need(all(isfinite(v) for v in (*residuals.values(), *budgets.values())) and all(abs(v) <= budgets[k] for k, v in residuals.items()),
              'BALANCE_HOLD: unresolved individual/whole carbon ledger')
        normalized = deepcopy(original['inputs']['scenario']); normalized['plant_state'].pop('stem_root'); normalized['removals'].pop('stem_root')
        identity = {'model_version': MODEL_VERSION, 'code_sha256': CODE_SHA256, 'component_code_sha256': dict(COMPONENT_CODE_SHA256),
                    'profile_sha256': dict(original['profile_sha256']), 'policy_id': POLICY_ID, 'policy_sha256': POLICY_SHA256,
                    'inputs': {'scenario': normalized, 'leaf_stocks': deepcopy(original['inputs']['leaf_stocks']),
                               'stem_root_stocks': {**stocks, 'model_floor_area': part._q(floor, 'm2_floor'), 'compartments': deepcopy(rows)}},
                    'source_stage_calculation_sha256': original['calculation_sha256']}
        result = {**identity, 'raw_input_sha256': sha256(raw).hexdigest(), 'input_sha256': sha256(_canonical(identity)).hexdigest(),
                  'scope': 'software_research_only', 'claim_scope': 'synthetic_individual_stem_root_carbon_rhs_only', 'G0_G4': 'not_assessed',
                  'time_coordinate': 'derivatives_per_second_no_time_advance', 'geometry_binding': 'declared_synthetic_stocks_only',
                  'aggregate_stem_root_derivative_use': 'derived_diagnostic_not_independent_state',
                  'source_stage': deepcopy(original), 'stem_root_rates': rates,
                  'stem_root_totals': {'carbon': part._q(total_C, part.source.MASS_UNIT), **{k: part._q(v) for k, v in totals.items()}},
                  'adjusted_carbon': {**deepcopy(original['adjusted_carbon']), 'derivatives': deepcopy(plant)},
                  'derivatives': {'plant': plant, 'cohorts': deepcopy(original['derivatives']['cohorts']), 'climate': deepcopy(original['derivatives']['climate'])},
                  'aggregation_residuals': {k: part._q(v) for k, v in aggregation.items()},
                  'aggregation_budgets': {k: part._q(roundoff) for k in aggregation},
                  'balance_residuals': {**deepcopy(original['balance_residuals']), **{k: part._q(v) for k, v in residuals.items()}},
                  'balance_budgets': {**deepcopy(original['balance_budgets']), **{k: part._q(v) for k, v in budgets.items()}}}
        result['calculation_sha256'] = sha256(_canonical(result)).hexdigest(); _canonical(result); _fence()
        return result
    except StemRootCarbonStockHold:
        raise
    except (source.StemRootClimateHold, part.StemRootPartitionHold) as error:
        raise StemRootCarbonStockHold(str(error)) from None
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, RecursionError, ZeroDivisionError):
        raise StemRootCarbonStockHold('INPUT_HOLD: invalid or unrepresentable individual stem/root stock stage') from None
