"""Read-only current clocks; crop-organ-current-shoot-clock-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path

from . import crop_organ_funded_continuation as stock
from . import crop_funded_shoot_clock as prior

VERSION = 'individual-organ-current-shoot-clock-research-v1'
POLICY = prior.POLICY
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
stem = stock.leaf.binding.stem


class CurrentShootClockHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise CurrentShootClockHold(reason)


def _pins():
    expected = {**stock._pins(), 'backend/app/crop_funded_shoot_clock.py': prior.CODE_SHA256,
                'backend/app/crop_organ_current_shoot_clock.py': CODE_SHA256}
    root = Path(__file__).resolve().parents[2]
    actual = {name: sha256((root/name).read_bytes()).hexdigest() for name in expected}
    _need(actual == expected, 'CODE_HOLD: original current clock dependencies required')
    return actual


def _exact(value, unit):
    result = {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'unit': unit}
    (stem._elapsed if unit == 's' else stem._age)(result)
    return result


def _age(initial, integral, seconds, base):
    value = initial+(Fraction(integral)-Fraction.from_float(float(base))*seconds)/86400
    _need(value >= 0, 'AGE_HOLD: signed thermal age is negative; no clipping permitted')
    return _exact(value, 'degC_day')


def _integral(row):
    _need(type(row) is dict and set(row) == {'value', 'unit'} and row['unit'] == 'degC_s'
          and type(row['value']) is float and isfinite(row['value']), 'UNIT_HOLD: finite original float64 degC_s air integral required')
    return row['value']


def _snapshot(context):
    return (context.root_sha256, context._program, context._seed, context._history, context._selection, context._manifest,
            context._directories, context._root.root_sha256, context._root._request, context._root._program,
            context._root._seed, context._root._manifest, context._token, context._root._token)


def derive_current_shoot_clock(context, raw_checkpoint, *, expected_sha256):
    try:
        pins = _pins()
        program, _, manifest = stock._context(context)
        before = _snapshot(context)
        binding = stock._source(context)
        cp = stock.restore_checkpoint(context, raw_checkpoint, expected_sha256=expected_sha256)
        current = cp.value
        elapsed_record = current['at_elapsed_seconds_exact']; stem._elapsed(elapsed_record)
        seconds = stem._fraction(elapsed_record)
        air = current['integrated_transfers']['indoor_air_temperature_time']; integral = _integral(air)
        selected = binding['stem_selection']; state = selected['source_state']; stem._state(state)
        timeline = state['timeline_state']; base = timeline['base_temperature']['value']
        origin, start = stem._utc(timeline['started_at']), stem._utc(timeline['at'])
        _need(timeline['at'] == binding['crop_selection']['time_origin_utc'] and origin <= start,
              'TIME_HOLD: actual selected development and simulation origins required')
        delta = start-origin
        offset = Fraction(delta.days*86400+delta.seconds)+Fraction(delta.microseconds, 1000000)
        initial_nodes = []
        for node in state['internodes']:
            clock = node['length_state']['clock_state']
            _need(clock['base_temperature'] == timeline['base_temperature'] and clock['time_origin_utc'] == timeline['started_at']
                  and stem._fraction(clock['at_elapsed_seconds_exact']) == offset,
                  'BASIS_HOLD: original common stem base and development origin required')
            initial_nodes.append({'internode_id': clock['internode_id'], 'sequence': node['sequence'],
                'age_basis': 'since_internode_emergence', 'source_clock': deepcopy(clock),
                'age_exact': _age(stem._fraction(clock['age_exact']), integral, seconds, base)})
        declared = []
        for sequence, record in enumerate(context.point_history, 1):
            if record['kind'] != 'internode':
                continue
            at = record['inputs']['at_elapsed_seconds_exact']; stem._elapsed(at); point_seconds = stem._fraction(at)
            _need(point_seconds <= seconds, 'TIME_HOLD: current CP cannot precede an adopted material point')
            point_air = _integral({'value': record['air_temperature_integral'], 'unit': 'degC_s'})
            for event, item in zip(record['inputs']['events'], record['new_items'], strict=True):
                declared.append({'internode_id': item['compartment_id'], 'event_id': event['event_id'],
                    'parent_internode_id': event['parent_internode_id'], 'event_sequence': sequence,
                    'age_basis': 'since_declared_material_point', 'physiological_emergence': 'not_established',
                    'base_temperature': deepcopy(timeline['base_temperature']),
                    'base_policy': 'selected_shoot_base_for_material_clock_only',
                    'point_at_elapsed_seconds_exact': deepcopy(at), 'point_air_temperature_integral': {'value': point_air, 'unit': 'degC_s'},
                    'age_exact': _age(Fraction(0), Fraction.from_float(integral)-Fraction.from_float(point_air), seconds-point_seconds, base)})
        ids = [r['internode_id'] for r in initial_nodes+declared]
        _need(ids == [r['compartment_id'] for r in program['stem_root_compartments'] if r['kind'] == 'internode']
              and len(ids) == len(set(ids)), 'IDENTITY_HOLD: complete ordered initial and declared internodes required')
        result = {'model_version': VERSION, 'policy': POLICY, 'code_sha256': CODE_SHA256, 'source_code_sha256': pins,
            'scope': 'software_research_only', 'G0_G4': 'not_assessed', 'time_kind': 'synthetic_model_clock_not_observation',
            'claim_scope': 'current_numerical_air_shoot_and_declared_material_clocks_only',
            'context_sha256': context.root_sha256, 'root_context_sha256': context._root.root_sha256,
            'checkpoint_sha256': cp.sha256, **{k: current[k] for k in ('step_index','event_sequence','phase','output_cursor','output_prefix_sha256')},
            'initial_binding_sha256': manifest['initial_binding_sha256'], 'crop_selection': deepcopy(binding['crop_selection']),
            'stem_selection': {k: deepcopy(v) for k, v in selected.items() if k != 'source_state'},
            'source_rights': deepcopy(binding['source_rights']), 'point_rights': [deepcopy(r['inputs']['rights']) for r in context.point_history],
            'redistribution_authorized': manifest['redistribution_authorized'],
            'development_origin_utc': timeline['started_at'], 'simulation_origin_utc': timeline['at'],
            'simulation_start_development_elapsed_seconds_exact': _exact(offset, 's'),
            'at_elapsed_seconds_exact': deepcopy(elapsed_record), 'development_elapsed_seconds_exact': _exact(offset+seconds, 's'),
            'air_temperature_integral': deepcopy(air), 'selected_source_timeline': deepcopy(timeline),
            'shoot': {**{k: deepcopy(timeline[k]) for k in ('shoot_id','development_origin_id','schedule_id','age_basis','base_temperature')},
                'initial_age_exact': deepcopy(timeline['age_exact']), 'age_exact': _age(stem._fraction(timeline['age_exact']), integral, seconds, base)},
            'initial_internodes': initial_nodes, 'declared_internodes': declared,
            'unclocked_root_system_ids': [r['compartment_id'] for r in program['stem_root_compartments'] if r['kind'] == 'root_system'],
            'historical_forcing_scope': 'selected_source_state_not_reintegrated',
            'air_scope': 'original_lifetime_RK4_integral_not_analytic_or_observed',
            'automatic_threshold_detection': 'not_performed', 'geometry_update': 'not_performed',
            'checkpoint_validation_stage_evaluations': 1, 'new_growth_steps': 0}
        result['calculation_sha256'] = sha256(stock._canonical(result)).hexdigest()
        _need(len(stock._canonical(result)) <= MAX_BYTES, 'CAPACITY_HOLD: bounded 2MiB current clock result required')
        _need(stock._source(context) == binding and _snapshot(context) == before,
              'SOURCE_HOLD: current source/rights/context changed before return')
        _need(_pins() == pins, 'CODE_HOLD: current clock dependencies changed before return')
        return deepcopy(result)
    except CurrentShootClockHold:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise CurrentShootClockHold(str(error)) from None
