"""Compute-free replay of explicitly trusted rational-time morphology artifacts."""
from fractions import Fraction
from hashlib import sha256
from math import gcd
import re

from .crop_morphology_artifact_io import MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import (
    PROGRAM_MAX, RESULT_MAX, ROOT_MAX, FLAGS, EQUATION_REFERENCE, _canonical, _closed,
    _hash, _id, _utc, _quantity, _age, _curve, _parse,
)


MODEL_VERSIONS = {
    'whole_second_air': 'piecewise-constant-air-exact-v1',
    'clock': 'internode-rational-air-thermal-clock-research-v1',
    'point': 'internode-logistic-length-point-research-v1',
    'length': 'internode-rational-length-state-research-v1',
    'emergence': 'phytomer-thermal-events-research-v1',
    'timeline': 'shoot-air-phytomer-timeline-research-v1',
    'air_adapter': 'whole-second-utc-to-rational-air-segments-research-v1',
    'new_internodes': 'shoot-rational-new-internodes-research-v1',
    'inventory': 'shoot-rational-internode-inventory-research-v1',
}
SOURCE_PATHS = tuple('backend/app/' + name + '.py' for name in (
    'crop_internode_elongation', 'crop_morphology_thermal_clock', 'crop_internode_length_change',
    'crop_internode_length', 'crop_phytomer_emergence', 'crop_shoot_timeline',
    'crop_rational_morphology_clock', 'crop_rational_internode_length', 'crop_rational_new_internodes',
    'crop_rational_shoot_inventory', 'crop_morphology_artifact_io', 'crop_morphology_artifact_reader',
    'crop_rational_morphology_artifact_reader', 'crop_rational_morphology_artifact_producer',
    'job_store', 'content_access', 'thermal_run_store'))
ROOT_CONSTANTS = {
    'schema_version': 'morphology-research-artifact-v2', **FLAGS,
    'status': 'completed_software_fixture', 'time_kind': 'synthetic_model_clock_not_observation',
    'parameter_scope': 'synthetic_software_fixture_only',
    'model_versions': MODEL_VERSIONS, 'equation_reference': EQUATION_REFERENCE,
}
ROOT_FIELDS = set(ROOT_CONSTANTS) | {'program_sha256', 'program_bytes', 'initial_state_sha256',
    'program_rights', 'code_sha256', 'samples', 'terminal_state_sha256'}


def _fraction(record):
    return Fraction(int(record['numerator']), int(record['denominator']))


def _elapsed(value):
    _closed(value, {'numerator', 'denominator', 'unit'})
    _need(value['unit'] == 's', 'UNIT_HOLD: elapsed seconds required')
    for key in ('numerator', 'denominator'):
        _need(type(value[key]) is str and re.fullmatch(r'0|[1-9][0-9]{0,1023}', value[key]),
              'FORMAT_HOLD: bounded canonical seconds required')
    n, d = int(value['numerator']), int(value['denominator'])
    _need(d > 0 and gcd(n, d) == 1, 'FORMAT_HOLD: reduced elapsed seconds required')


def _clock(c):
    _closed(c, {'origin', 'age_basis', 'temperature_basis', 'internode_id', 'time_origin_utc',
        'emerged_elapsed_seconds_exact', 'at_elapsed_seconds_exact', 'base_temperature', 'age_exact'})
    _need(c['origin'] == 'synthetic' and c['age_basis'] == 'since_internode_emergence'
          and c['temperature_basis'] == 'indoor_air_piecewise_constant', 'SCOPE_HOLD: synthetic rational clock required')
    _id(c['internode_id']); _utc(c['time_origin_utc']); _quantity(c['base_temperature'], 'degC'); _age(c['age_exact'])
    _elapsed(c['emerged_elapsed_seconds_exact']); _elapsed(c['at_elapsed_seconds_exact'])
    birth, at = (_fraction(c[k]) for k in ('emerged_elapsed_seconds_exact', 'at_elapsed_seconds_exact'))
    _need(birth <= at and (birth != at or c['age_exact']['numerator'] == '0'), 'TIME_HOLD: inconsistent birth/current clock')


def _length(s):
    _closed(s, {'model_version', 'clock_state', 'curve', 'curve_sha256', 'length', 'anchor'})
    _need(s['model_version'] == MODEL_VERSIONS['length'], 'MODEL_HOLD: unsupported rational length state')
    _clock(s['clock_state']); _curve(s['curve']); _hash(s['curve_sha256']); _quantity(s['length'], 'm', positive=True)
    a = s['anchor']; _closed(a, {'clock_state', 'curve_sha256', 'requested_length', 'canonical_length'})
    _clock(a['clock_state']); _hash(a['curve_sha256'])
    _quantity(a['requested_length'], 'm', positive=True); _quantity(a['canonical_length'], 'm', positive=True)
    _need(a['curve_sha256'] == s['curve_sha256'], 'HASH_HOLD: curve receipt mismatch')
    initial, current = a['clock_state'], s['clock_state']
    constants = set(current) - {'at_elapsed_seconds_exact', 'age_exact'}
    before, after = (_fraction(c['at_elapsed_seconds_exact']) for c in (initial, current))
    _need(all(initial[k] == current[k] for k in constants) and before <= after
          and _fraction(initial['age_exact']) <= _fraction(current['age_exact'])
          and (before != after or initial['age_exact'] == current['age_exact']), 'STATE_HOLD: initial clock identity mismatch')


def _state(s):
    _closed(s, {'timeline_state', 'inventory_start_sequence', 'internodes', 'emergence_profile'})
    t = s['timeline_state']
    _closed(t, {'origin', 'age_basis', 'shoot_id', 'development_origin_id', 'schedule_id', 'started_at',
        'at', 'base_temperature', 'age_exact', 'next_threshold_exact', 'phyllochron_exact', 'next_sequence'})
    _need(t['origin'] == 'synthetic' and t['age_basis'] == 'since_shoot_development_origin', 'SCOPE_HOLD: synthetic shoot required')
    for key in ('shoot_id', 'development_origin_id', 'schedule_id'):
        _id(t[key])
    origin, at = _utc(t['started_at']), _utc(t['at']); _need(origin <= at, 'TIME_HOLD: shoot origin after checkpoint')
    delta = at - origin; expected_seconds = delta.days * 86400 + delta.seconds
    _quantity(t['base_temperature'], 'degC'); _age(t['age_exact'])
    _age(t['next_threshold_exact'], positive=True); _age(t['phyllochron_exact'], positive=True)
    first, nodes = s['inventory_start_sequence'], s['internodes']
    _need(type(first) is int and type(t['next_sequence']) is int and 0 <= first <= t['next_sequence'] <= 2**31 - 1,
          'FORMAT_HOLD: bounded sequence required')
    _need(type(nodes) is list and len(nodes) <= 512 and first + len(nodes) == t['next_sequence'],
          'FORMAT_HOLD: contiguous bounded inventory required')
    ids = set(); previous_seconds = previous_age = Fraction(0)
    for index, n in enumerate(nodes):
        _closed(n, {'sequence', 'birth_age_exact', 'length_state'})
        _need(type(n['sequence']) is int and n['sequence'] == first + index, 'FORMAT_HOLD: ordered inventory required')
        _age(n['birth_age_exact']); _length(n['length_state']); c = n['length_state']['clock_state']
        birth_seconds, birth_age = _fraction(c['emerged_elapsed_seconds_exact']), _fraction(n['birth_age_exact'])
        _need(c['time_origin_utc'] == t['started_at'] and _fraction(c['at_elapsed_seconds_exact']) == expected_seconds
              and c['base_temperature'] == t['base_temperature'] and previous_seconds <= birth_seconds
              and previous_age <= birth_age and c['internode_id'] not in ids, 'STATE_HOLD: inventory identity/time mismatch')
        _need(_fraction(c['age_exact']) + birth_age == _fraction(t['age_exact']), 'STATE_HOLD: inventory thermal age linkage mismatch')
        ids.add(c['internode_id']); previous_seconds, previous_age = birth_seconds, birth_age
    _closed(s['emergence_profile'], {'curve', 'initial_length'})
    _curve(s['emergence_profile']['curve']); _quantity(s['emergence_profile']['initial_length'], 'm', positive=True)


def _program(p):
    _closed(p, {'schema_version', 'origin', 'program_id', 'rights', 'initial_state', 'segments', 'output_times'})
    _need(p['schema_version'] == 'morphology-software-program-v2' and p['origin'] == 'synthetic',
          'SCOPE_HOLD: synthetic software program required')
    _id(p['program_id']); r = p['rights']
    required = {'ownership_asserted', 'access', 'store', 'use', 'transform', 'display'}
    _closed(r, required | {'declaration_id', 'revision', 'declared_at_utc', 'redistribute'})
    _id(r['declaration_id']); _id(r['revision']); _utc(r['declared_at_utc'])
    _need(all(r[k] is True for k in required) and type(r['redistribute']) is bool, 'RIGHTS_HOLD: explicit synthetic rights required')
    _state(p['initial_state'])
    at = p['initial_state']['timeline_state']['at']; segments = p['segments']
    _need(type(segments) is list and 1 <= len(segments) <= 512, 'CAPACITY_HOLD: bounded forcing required')
    for segment in segments:
        _closed(segment, {'start_utc', 'end_utc', 'air_temperature'})
        _need(segment['start_utc'] == at and _utc(at) < _utc(segment['end_utc']), 'TIME_HOLD: contiguous forward forcing required')
        _quantity(segment['air_temperature'], 'degC')
        _need(segment['air_temperature']['value'] >= p['initial_state']['timeline_state']['base_temperature']['value'],
              'TEMPERATURE_HOLD: air below unsupported base')
        at = segment['end_utc']
    times = p['output_times']
    _need(type(times) is list and 1 <= len(times) <= 64, 'CAPACITY_HOLD: bounded output times required')
    previous = p['initial_state']['timeline_state']['at']
    for value in times:
        _need(_utc(previous) < _utc(value) and value <= at, 'TIME_HOLD: ordered output times inside program required')
        previous = value
    _need(times[-1] == at, 'TIME_HOLD: final output must consume whole program')


def _load_manifest(store, root_sha256):
    m = _parse(store.get(root_sha256, maximum=ROOT_MAX), ROOT_MAX)
    _closed(m, ROOT_FIELDS)
    _need(all(m[k] == v for k, v in ROOT_CONSTANTS.items()), 'MODEL_HOLD: unsupported research artifact')
    _closed(m['code_sha256'], SOURCE_PATHS)
    for value in m['code_sha256'].values():
        _hash(value)
    raw = store.get(m['program_sha256'], maximum=PROGRAM_MAX)
    _need(type(m['program_bytes']) is int and m['program_bytes'] == len(raw), 'HASH_HOLD: program byte count mismatch')
    p = _parse(raw, PROGRAM_MAX); _program(p)
    _need(m['program_rights'] == p['rights'] and m['initial_state_sha256'] == sha256(_canonical(p['initial_state'])).hexdigest(),
          'HASH_HOLD: program rights/state mismatch')
    samples = m['samples']
    _need(type(samples) is list and len(samples) == len(p['output_times']), 'FORMAT_HOLD: complete samples required')
    previous = m['initial_state_sha256']
    for i, d in enumerate(samples):
        _closed(d, {'index', 'at', 'result_sha256', 'result_bytes', 'input_state_sha256', 'state_sha256', 'input_sha256'})
        _need(type(d['index']) is int and d['index'] == i and d['at'] == p['output_times'][i]
              and d['input_state_sha256'] == previous, 'HASH_HOLD: sample chain mismatch')
        _need(type(d['result_bytes']) is int and 1 <= d['result_bytes'] <= RESULT_MAX, 'CAPACITY_HOLD: bounded result required')
        for key in ('result_sha256', 'input_state_sha256', 'state_sha256', 'input_sha256'):
            _hash(d[key])
        previous = d['state_sha256']
    _need(m['terminal_state_sha256'] == previous, 'HASH_HOLD: terminal state mismatch')
    return m


def read_rational_morphology_manifest(directory, access, root_sha256):
    with MorphologyBlobStore(directory, access) as store:
        return _load_manifest(store, root_sha256)


def read_rational_morphology_frame(directory, access, root_sha256, *, index):
    with MorphologyBlobStore(directory, access) as store:
        manifest = _load_manifest(store, root_sha256)
        _need(type(index) is int and 0 <= index < len(manifest['samples']), 'INDEX_HOLD: explicit bounded frame index required')
        d = manifest['samples'][index]; raw = store.get(d['result_sha256'], maximum=RESULT_MAX)
        _need(len(raw) == d['result_bytes'], 'HASH_HOLD: result byte count mismatch')
        r = _parse(raw, RESULT_MAX)
        _closed(r, {'model_version', *FLAGS, 'input_sha256', 'state', 'step_receipts', 'tracked_axis_length'})
        _need(r['model_version'] == MODEL_VERSIONS['inventory'] and all(r[k] == v for k, v in FLAGS.items())
              and r['input_sha256'] == d['input_sha256'] and sha256(_canonical(r['state'])).hexdigest() == d['state_sha256'],
              'HASH_HOLD: model result identity mismatch')
        _state(r['state']); t = r['state']['timeline_state']
        _need(t['at'] == d['at'], 'TIME_HOLD: selected result UTC mismatch')
        _quantity(r['tracked_axis_length'], 'm')
        _need(r['tracked_axis_length']['value'] >= 0, 'NUMERIC_HOLD: nonnegative stored axis required')
        nodes = r['state']['internodes']; receipts = r['step_receipts']
        _need(type(receipts) is list and len(receipts) == len(nodes), 'FORMAT_HOLD: step receipts required')
        for n, receipt in zip(nodes, receipts, strict=True):
            _need(type(receipt) is dict and receipt.get('kind') in ('advanced', 'new'), 'FORMAT_HOLD: known step receipt required')
            keys = {'input_sha256'} if receipt['kind'] == 'advanced' else {'initialization_input_sha256', 'advancement_input_sha256'}
            _closed(receipt, keys | {'sequence', 'kind'})
            _need(type(receipt['sequence']) is int and receipt['sequence'] == n['sequence'], 'FORMAT_HOLD: receipt sequence mismatch')
            for key in keys:
                if key != 'advancement_input_sha256' or receipt[key] is not None:
                    _hash(receipt[key])
        return {'schema_version': 'morphology-replay-frame-v2', **FLAGS, 'artifact_sha256': root_sha256,
            'result_sha256': d['result_sha256'], 'input_sha256': r['input_sha256'], 'index': index,
            'at': t['at'], 'shoot_id': t['shoot_id'], 'time_origin_utc': t['started_at'], 'tracked_axis_length': r['tracked_axis_length'],
            'internodes': [{'sequence': n['sequence'], 'birth_age_exact': n['birth_age_exact'],
                **{key: n['length_state']['clock_state'][key] for key in ('internode_id', 'emerged_elapsed_seconds_exact', 'age_exact')},
                'length': n['length_state']['length']} for n in nodes]}
