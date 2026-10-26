"""Conditional inflow arithmetic; crop-stem-root-carbon-partition-v1.md."""
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum, isfinite, ulp
from pathlib import Path
import re
from sys import float_info

from . import crop_growth_rates as source

MODEL_VERSION = 'stem-root-carbon-budget-partition-research-v1'
POLICY_ID = 'explicit-stem-root-sinks-and-empty-deferral-v1'
POLICY = {'id': POLICY_ID, 'weights': 'declared_relative_priorities_not_mass_demand_caps',
          'root': 'one_explicit_root_system_compartment', 'empty': 'defer_growth_and_its_growth_respiration',
          'debit_basis': 'structural_inflow_before_maintenance_plus_profile_cStemG_cost',
          'initial_stock_allocation': False, 'length_feedback': False}
MAX_BYTES = 128 * 1024
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
SOURCE_SHA256 = sha256(Path(source.__file__).read_bytes()).hexdigest()
POLICY_SHA256 = sha256(json.dumps(POLICY, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class StemRootPartitionHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise StemRootPartitionHold(reason)


def _closed(value, keys):
    _need(type(value) is dict and set(value) == set(keys), 'INPUT_HOLD: closed stem/root fields required')


def _canonical(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: 128KiB stem/root input/output required')
    return raw


def _normal(value):
    _need(isfinite(value) and (value == 0 or abs(value) >= float_info.min), 'NUMERIC_HOLD: finite normal value or zero required')
    return value


def _number(value, unit):
    _closed(value, {'value', 'unit'})
    _need(value['unit'] == unit and type(value['value']) in (int, float), 'UNIT_HOLD: explicit numeric quantity and original unit required')
    result = _normal(float(value['value']))
    _need(result >= 0, 'INPUT_HOLD: nonnegative quantity required')
    return result


def _id(value):
    _need(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', value), 'INPUT_HOLD: bounded ASCII identity required')


def _q(value, unit=source.RATE_UNIT):
    return {'value': value, 'unit': unit}


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256 and
          sha256(Path(source.__file__).read_bytes()).hexdigest() == SOURCE_SHA256, 'CODE_HOLD: original stem/root partition sources required')


def calculate_partition(*, inputs, growth_profile):
    try:
        _fence()
        _need(type(growth_profile) is source.ReferenceParameters and growth_profile.sha256 == source.PROFILE_SHA256 ==
              sha256(growth_profile.raw_bytes).hexdigest(), 'PROFILE_HOLD: original pinned growth profile required')
        cost = growth_profile.values['cStemG']
        _need(cost == float(json.loads(growth_profile.raw_bytes)['parameters']['cStemG']['value']) and cost > 0,
              'PROFILE_HOLD: original stem/root growth cost required')
        _closed(inputs, {'input_id', 'origin', 'policy', 'model_floor_area', 'requested_stem_root_growth', 'compartments'})
        _need(type(inputs['compartments']) is list, 'INPUT_HOLD: explicit compartment list required')
        raw = _canonical(inputs)
        value = json.loads(raw)
        _id(value['input_id'])
        _need(value['origin'] == 'synthetic' and value['policy'] == POLICY_ID, 'SCOPE_HOLD: explicit synthetic stem/root policy required')
        floor = _number(value['model_floor_area'], 'm2_floor')
        _need(floor > 0, 'BASIS_HOLD: positive common model footprint required')
        growth = _number(value['requested_stem_root_growth'], source.RATE_UNIT)
        rows = value['compartments']
        _need(1 <= len(rows) <= 512, 'CAPACITY_HOLD: 1..512 declared compartments required')
        ids, kinds, weights = [], [], []
        for row in rows:
            _closed(row, {'compartment_id', 'kind', 'sink_weight'})
            _id(row['compartment_id'])
            _need(row['kind'] in ('internode', 'root_system'), 'INPUT_HOLD: explicit internode or root system required')
            ids.append(row['compartment_id']); kinds.append(row['kind']); weights.append(_number(row['sink_weight'], '1'))
        _need(len(set(ids)) == len(ids) and kinds.count('root_system') == 1, 'INVENTORY_HOLD: unique IDs and exactly one root system required')
        total = _normal(fsum(weights))
        denominator = sum(map(Fraction.from_float, weights), Fraction(0))
        flows = []
        for weight in weights:
            flow = _normal(float(Fraction.from_float(growth) * Fraction.from_float(weight) / denominator) if denominator else 0.)
            _need(not (growth > 0 and weight > 0) or flow > 0, 'NUMERIC_HOLD: positive compartment inflow lost')
            flows.append(flow)
        effective = growth if denominator else 0.
        deferred = growth - effective
        requested, realized, avoided = [_normal(cost * amount) for amount in (growth, effective, deferred)]
        _need(growth == 0 or requested > 0, 'NUMERIC_HOLD: positive growth cost lost')
        refund = _normal(fsum((deferred, avoided)))
        adjustments = {'buffer': refund, 'stem_root': -deferred if deferred else 0., 'growth_respiration': -avoided if avoided else 0.}
        residuals = {'allocation': fsum((*flows, -effective)), 'request': fsum((effective, deferred, -growth)),
                     'respiration': fsum((realized, avoided, -requested)), 'refund': fsum((refund, -deferred, -avoided)),
                     'adjustments': fsum(adjustments.values()), 'whole_stem_root_budget': fsum((-growth, -requested, refund, *flows, realized))}
        scale = max(growth, requested, refund, realized, *flows)
        budget = 64 * (len(rows) + 8) * ulp(scale) if scale else 0.
        _need(isfinite(budget) and all(isfinite(v) and abs(v) <= budget for v in residuals.values()), 'BALANCE_HOLD: unresolved stem/root allocation budget')
        normalized = {'input_id': value['input_id'], 'origin': value['origin'], 'policy': POLICY_ID,
                      'model_floor_area': _q(floor, 'm2_floor'), 'requested_stem_root_growth': _q(growth),
                      'compartments': [{'compartment_id': i, 'kind': k, 'sink_weight': _q(w, '1')}
                                       for i, k, w in zip(ids, kinds, weights, strict=True)]}
        result = {'model_version': MODEL_VERSION, 'code_sha256': CODE_SHA256, 'source_code_sha256': SOURCE_SHA256,
                  'profile_sha256': growth_profile.sha256, 'policy_id': POLICY_ID, 'policy_sha256': POLICY_SHA256,
                  'scope': 'software_research_only', 'claim_scope': 'synthetic_stem_root_partition_math_only', 'G0_G4': 'not_assessed',
                  'inputs': normalized, 'raw_input_sha256': sha256(raw).hexdigest(), 'input_sha256': sha256(_canonical(normalized)).hexdigest(),
                  'requested_stem_root_growth': _q(growth), 'effective_stem_root_growth': _q(effective), 'deferred_stem_root_growth': _q(deferred),
                  'sink_weight_sum': _q(total, '1'), 'growth_respiration_coefficient': _q(cost, '1'),
                  'allocation': [{'compartment_id': i, 'kind': k, 'carbohydrate_inflow': _q(f)} for i, k, f in zip(ids, kinds, flows, strict=True)],
                  'growth_respiration': {k: _q(v) for k, v in (('requested', requested), ('realized', realized), ('avoided', avoided))},
                  'derivative_adjustments': {k: _q(v) for k, v in adjustments.items()},
                  'balance_residuals': {k: _q(v) for k, v in residuals.items()}, 'balance_budgets': {k: _q(budget) for k in residuals}}
        result['calculation_sha256'] = sha256(_canonical(result)).hexdigest()
        _canonical(result)
        _fence()
        return result
    except StemRootPartitionHold:
        raise
    except (OverflowError, ValueError, TypeError, KeyError, AttributeError, OSError, RecursionError, ZeroDivisionError):
        raise StemRootPartitionHold('INPUT_HOLD: invalid or unrepresentable stem/root partition') from None
