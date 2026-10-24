"""Explicit instantaneous C/area bookkeeping; crop-leaf-carbon-removal-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum, isfinite, ulp
from pathlib import Path
import re
from sys import float_info

from . import crop_leaf_lifecycle as lifecycle
from . import crop_climate_joint_management as management

VERSION = 'declared-leaf-carbon-removal-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
DEPENDENCY_SHA256 = {m.__name__: sha256(Path(m.__file__).read_bytes()).hexdigest()
                     for m in (lifecycle, management)}
FIELDS = {'schema_version', 'input_id', 'origin', 'case_id', 'shoot_id', 'lifecycle_state',
          'joint_state', 'mass_basis', 'event_ids'}
BASIS_FIELDS = {'schema_version', 'case_id', 'shoot_id', 'origin', 'evidence_level', 'evidence_id',
                'lifecycle_state_sha256', 'joint_state_sha256', 'floor_area', 'leaf_carbohydrate'}


class LeafCarbonRemovalHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise LeafCarbonRemovalHold(reason)


def _canonical(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    _need(len(raw) <= 2*1024**2, 'CAPACITY_HOLD: bounded leaf carbon composition required')
    return raw


def _hash(value):
    return sha256(_canonical(value)).hexdigest()


def _closed(value, keys):
    _need(type(value) is dict and set(value) == set(keys), 'INPUT_HOLD: closed leaf carbon input required')


def _identifier(value):
    _need(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', value),
          'INPUT_HOLD: bounded ASCII identity required')


def _quantity(value, unit):
    _closed(value, {'value', 'unit'})
    _need(value['unit'] == unit, 'UNIT_HOLD: ' + unit + ' required')
    _need(type(value['value']) in (int, float), 'INPUT_HOLD: explicit numeric quantity required')
    number = float(value['value'])
    _need(isfinite(number) and number >= float_info.min, 'NUMERIC_HOLD: positive normal quantity required')
    return number


def _per_floor(values, floor):
    exact = sum((Fraction(v) for v in values), Fraction(0)) / Fraction(floor)
    value = float(exact)
    _need(isfinite(value) and (exact == 0 or value >= float_info.min), 'NUMERIC_HOLD: normal floor quantity required')
    return value


def _area_balance(area, carbon, sla):
    expected = sla * carbon
    _need(isfinite(expected) and (carbon == 0 or expected >= float_info.min), 'NUMERIC_HOLD: canopy area domain')
    residual = area - expected; budget = 64*ulp(max(abs(area), abs(expected)))
    _need(isfinite(budget) and abs(residual) <= budget, 'CANOPY_HOLD: declared geometry and SLA carbon differ')
    return {'value': residual, 'unit': 'm2_leaf/m2_floor'}, {'value': budget, 'unit': 'm2_leaf/m2_floor'}


def apply_leaf_carbon_removals(*, inputs, growth_profile, cohort_profile, transport_profile, exchange_profile):
    try:
        _closed(inputs, FIELDS); raw = _canonical(inputs); value = json.loads(raw)
        _need(value['schema_version'] == 'leaf-carbon-removal-input-v1' and value['origin'] == 'synthetic',
              'SCOPE_HOLD: explicit synthetic composition required')
        for name in ('input_id', 'case_id', 'shoot_id'): _identifier(value[name])
        _need(type(growth_profile) is management.joint.growth.ReferenceParameters, 'PROFILE_HOLD: pinned growth required')
        basis = value['mass_basis']; _closed(basis, BASIS_FIELDS)
        _need(basis['schema_version'] == 'explicit-leaf-carbon-basis-v1' and basis['origin'] == 'synthetic'
              and basis['evidence_level'] == 'assumed', 'SCOPE_HOLD: explicit assumed leaf masses required')
        _identifier(basis['evidence_id'])
        _need(all(basis[k] == value[k] for k in ('case_id', 'shoot_id')), 'BINDING_HOLD: same declared case and shoot required')
        for name in ('lifecycle_state', 'joint_state'):
            _need(basis[name + '_sha256'] == _hash(value[name]), 'HASH_HOLD: original mass basis states required')
        state = lifecycle.normalize_leaf_lifecycle_state(state=value['lifecycle_state'])
        joint = value['joint_state']; _closed(joint, {'time_origin_utc', 'at_elapsed_seconds_exact', 'scenario'})
        existing = state['existing_inventory_state']; origin = existing['source_population']['time_origin_utc']
        at = existing['at_elapsed_seconds_exact']; lifecycle.single._seconds(joint['at_elapsed_seconds_exact'])
        _need(joint['time_origin_utc'] == origin and joint['at_elapsed_seconds_exact'] == at,
              'TIME_HOLD: same exact instantaneous coordinate required')
        scenario = joint['scenario']
        _need(type(scenario) is dict and scenario.get('origin') == 'synthetic', 'SCOPE_HOLD: same synthetic joint origin required')
        batch = [d for d in state['removal_declarations'] if d['at_elapsed_seconds_exact'] == at]
        events = value['event_ids']
        _need(type(events) is list and 1 <= len(events) <= 512
              and events == [d['event_id'] for d in batch], 'EVENT_HOLD: complete original current removal batch required')
        checkpoints = [*existing['leaf_checkpoints'], *state['new_leaf_checkpoints']]
        before = [r for r in checkpoints if r['state'] is not None and (r['removal_receipt'] is None
                  or r['removal_receipt']['at_elapsed_seconds_exact'] == at)]
        active = [r for r in before if r['removal_receipt'] is None]
        identifiers = [r['state']['clock_state']['leaf_id'] for r in before]
        records = basis['leaf_carbohydrate']
        _need(type(records) is list and len(records) == len(before), 'MASS_BALANCE_HOLD: all pre-event leaf masses required')
        floor = _quantity(basis['floor_area'], 'm2_floor'); masses = {}
        for identifier, record in zip(identifiers, records, strict=True):
            _closed(record, {'leaf_id', 'carbohydrate'})
            _need(record['leaf_id'] == identifier, 'MASS_BALANCE_HOLD: original pre-event leaf order required')
            masses[identifier] = _quantity(record['carbohydrate'], 'mg_CH2O')
        carbon = _per_floor(masses.values(), floor)
        plant, _ = management.joint._quantities(scenario.get('plant_state'), management.joint.SCALAR_BLOCKS['plant_state'])
        _need(plant['leaf'] == carbon, 'MASS_BALANCE_HOLD: explicit leaf mass sum differs from joint stock')
        removals, _ = management.joint._quantities(scenario.get('removals'), management.joint.SCALAR_BLOCKS['removals'])
        _need(removals['leaf'] == 0, 'DUPLICATE_REMOVAL_HOLD: continuous leaf removal needs separate event attribution')
        removed = _per_floor((masses[d['leaf_id']] for d in batch), floor)
        area0 = _per_floor((r['state']['area_state']['area']['value'] for r in before), floor)
        area1 = _per_floor((r['state']['area_state']['area']['value'] for r in active), floor)
        residual0, budget0 = _area_balance(area0, carbon, growth_profile.values['sla'])
        event = {'input_id': value['input_id'], 'origin': 'synthetic', 'values': {
            'leaf': {'value': removed, 'unit': management.MASS}, 'stem_root': {'value': 0.0, 'unit': management.MASS},
            'fruit_fraction': [{'value': 0.0, 'unit': '1'} for _ in range(50)]}}
        transition = management.apply_management(scenario=scenario, event=event, growth_profile=growth_profile,
            cohort_profile=cohort_profile, transport_profile=transport_profile, exchange_profile=exchange_profile)
        residual1, budget1 = _area_balance(area1, transition['after']['scenario']['plant_state']['leaf']['value'],
                                         growth_profile.values['sla'])
        result = {'model_version': VERSION, 'code_sha256': CODE_SHA256, 'dependency_sha256': dict(DEPENDENCY_SHA256),
            'input_sha256': sha256(raw).hexdigest(), 'mass_basis_sha256': _hash(basis),
            'source': {name + '_sha256': basis[name + '_sha256'] for name in ('lifecycle_state', 'joint_state')},
            'case_id': value['case_id'], 'shoot_id': value['shoot_id'], 'time_origin_utc': origin,
            'at_elapsed_seconds_exact': deepcopy(at), 'time_coordinate': 'same_instant_only_no_advance',
            'population_scope': 'complete_declared_synthetic_inventory_not_physical_canopy',
            'lifecycle_state': state, 'removal_declarations': deepcopy(batch), 'mass_basis': deepcopy(basis),
            'removed_carbohydrate': {'value': removed, 'unit': management.MASS},
            'tracked_lai': {'before': {'value': area0, 'unit': 'm2_leaf/m2_floor'},
                            'after': {'value': area1, 'unit': 'm2_leaf/m2_floor'}},
            'area_residuals': {'before': residual0, 'after': residual1}, 'area_budgets': {'before': budget0, 'after': budget1},
            'transition': transition, 'scope': 'software_research_only',
            'claim_scope': 'synthetic_leaf_carbon_removal_math_only', 'G0_G4': 'not_assessed'}
        result['calculation_sha256'] = _hash(result); _canonical(result)
        return result
    except LeafCarbonRemovalHold:
        raise
    except (ValueError, OverflowError, TypeError, KeyError, RecursionError) as exc:
        raise LeafCarbonRemovalHold(str(exc) if isinstance(exc, (lifecycle.LeafLifecycleHold,
                                   management.JointManagementHold, management.joint.JointClimateHold))
                                   else 'INPUT_HOLD: invalid leaf carbon composition') from None
