"""Read trusted stored companion states; never import or execute crop equations.

Contract: contracts/crop-growing-geometry-artifact-v1.md. Hash/QC checks do
not authenticate an arbitrarily replaced root or independently prove biology.
"""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path

from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical, _closed, _hash, _id, _parse, _utc

MAX = 2 * 1024**2
CHECKPOINT_MAX = 256 * 1024
MODEL_NAMES = (
    'crop_growing_geometry_continuation', 'crop_growing_geometry_climate',
    'crop_explicit_lai_climate_rhs', 'crop_explicit_lai_carbon_cohorts',
    'crop_explicit_lai_photosynthesis', 'crop_area_canopy_energy', 'crop_canopy_energy_transport',
    'crop_canopy_exchange', 'crop_growth_rates', 'crop_fruit_cohorts', 'crop_fruit_startup',
    'crop_plant_cohort_rates', 'crop_fruit_transport', 'crop_fruit_allocation',
    'crop_leaf_area', 'crop_leaf_area_change', 'crop_leaf_expansion', 'crop_morphology_thermal_clock')
SOURCE_PATHS = tuple(f'backend/app/{name}.py' for name in (*MODEL_NAMES,
    'crop_morphology_artifact_io', 'crop_morphology_artifact_reader', 'thermal_run_store',
    'job_store', 'content_access', 'crop_growing_geometry_artifact_producer', 'crop_growing_geometry_artifact_reader'))
PROFILE_SHA = {
    'growth_profile': 'd606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca',
    'cohort_profile': 'b453b4ffe618f26041e4ec6a1b1b7d2e5f38edb3d42adaaad4fa3cd4fbb99cbb',
    'transport_profile': '09ea5e176bc745361e8e3ec8945b0f8abb0b2b427b4e9c459d0663cf390e9070',
    'exchange_profile': '1e032ced2ffdaf8ba713184e89b628cce4173c9e7231f30710afeda8fbf20110'}
NOTICE_PATH = 'LICENSES/GreenLight-BSD-3-Clause-Clear.txt'
NOTICE_SHA = '96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a'
POLICIES = {'normalization': 'zero_lower_asymptote_sigmoid_v1',
    'thermal_age_policy': 'dynamic_indoor_air_no_clip_v1',
    'capacity_policy': 'declared_outflow_plus_area_capacity_derivative_v1'}
DISPLAY_POLICY = {'geometry_authority': 'stored_leaf_area',
    'stem_pose_attachment': 'separate_authored_asset_required',
    'fruit_height_yield_margin_ranking': 'not_derived'}
ROOT_CONSTANTS = {'schema_version': 'growing-geometry-research-artifact-v1',
    'scope': 'software_research_only', 'claim_scope': 'synthetic_growing_geometry_replay_only',
    'G0_G4': 'not_assessed', 'status': 'completed_software_fixture',
    'time_kind': 'synthetic_model_clock_not_observation',
    'parameter_scope': 'synthetic_inputs_with_pinned_research_reference_profiles', 'display_policy': DISPLAY_POLICY}
SOURCE_NAMES = {'inputs', 'request', 'program', 'seed', 'context', 'license_notice', *PROFILE_SHA}
ROOT_FIELDS = {*ROOT_CONSTANTS, 'input_id', 'source_rights', 'time_origin_utc', 'sources', 'code_sha256',
    'context_sha256', 'initial_state_sha256', 'terminal_state_sha256', 'samples'}
DESCRIPTOR_FIELDS = {'index', 'elapsed_seconds_exact', 'checkpoint_sha256', 'checkpoint_bytes',
    'sample_sha256', 'state_sha256', 'previous_checkpoint_sha256'}
PLANT_UNITS = dict.fromkeys(('buffer', 'leaf', 'stem_root'), 'mg_CH2O/m2_floor') | {
    'temperature_filtered_24h': 'degC', 'temperature_sum': 'degC_day'}
CLIMATE_UNITS = {'canopy_sensible_energy': 'J/m2_floor', 'air_temperature': 'degC', 'air_vapor_mass': 'kg_water/m2_floor'}
COHORT_UNITS = {'fruit_carbohydrate': 'mg_CH2O/m2_floor', 'fruit_number': 'fruits_equivalent/m2_floor'}
SCALAR_UNITS = {'plant_state': PLANT_UNITS, 'climate_state': CLIMATE_UNITS,
    'parameters': {'leaf_heat_capacity': 'J/m2_leaf/K', 'air_volume_per_floor_area': 'm3/m2_floor',
        'air_capacity_density': 'kg_air/m3', 'canopy_vapor_resistance': 's/m',
        'vapor_gas_constant': 'J/kg_water/K', 'reference_temperature': 'degC'},
    'forcing': {'canopy_external_heat': 'W/m2_floor', 'air_external_sensible_heat': 'W/m2_floor',
        'air_external_vapor': 'kg_water/m2_floor/s', 'incoming_capacity_temperature': 'degC',
        'outgoing_capacity_temperature': 'degC', 'par_above_canopy': 'umol_photons/m2_floor/s', 'co2': 'ppm'},
    'removals': dict.fromkeys(('leaf', 'stem_root'), 'mg_CH2O/m2_floor/s'),
    'fruit_entry': {'fruit_number_inflow': 'fruits_equivalent/m2_floor/s', 'fruit_entry_carbohydrate': 'mg_CH2O/fruit_equivalent'}}
ARRAY_UNITS = {'cohort_state': COHORT_UNITS, 'relative_growth_rate': {'fruit_relative_growth_rate': '1/s'}}
DERIVED_UNITS = {'canopy_temperature': 'degC', 'leaf_area_index': 'm2_leaf/m2_floor',
    'leaf_area_index_rate': 'm2_leaf/m2_floor/s', 'canopy_capacity': 'J/m2_floor/K',
    'air_capacity': 'J/m2_floor/K', 'air_vapor_pressure': 'Pa', 'canopy_temperature_rate': 'K/s'}
FLUX_UNITS = {**dict.fromkeys(('photosynthesis', 'growth_respiration', 'maintenance_leaf', 'maintenance_stem',
    'maintenance_fruit', 'removal_leaf', 'removal_stem', 'terminal_carbon'), 'mg_CH2O/m2_floor'),
    **dict.fromkeys(('entry_number', 'terminal_number'), 'fruits_equivalent/m2_floor'),
    **dict.fromkeys(('sensible', 'latent', 'incoming_heat', 'outgoing_heat', 'canopy_external', 'air_external'), 'J/m2_floor'),
    **dict.fromkeys(('vapor', 'external_vapor'), 'kg_water/m2_floor'),
    **dict.fromkeys(('capacity_in', 'capacity_out'), 'J/m2_floor/K'), 'indoor_air_temperature_time': 'degC_s'}
BALANCE_UNITS = {'carbohydrate': 'mg_CH2O/m2_floor', 'number': 'fruits_equivalent/m2_floor',
    'canopy_sensible': 'J/m2_floor', 'air_sensible': 'J/m2_floor', 'vapor': 'kg_water/m2_floor',
    'area_capacity': 'J/m2_floor/K', 'reduced_energy': 'J/m2_floor'}


class GrowingGeometryArtifactHold(MorphologyArtifactHold):
    pass


def _digest(value): return sha256(_canonical(value)).hexdigest()


def _pins():
    root = Path(__file__).resolve().parents[2]
    try: return {name: sha256((root/name).read_bytes()).hexdigest() for name in SOURCE_PATHS}
    except OSError: raise GrowingGeometryArtifactHold('CODE_HOLD: required source unavailable') from None


def _q(value, unit, *, normalized=False):
    _closed(value, {'value', 'unit'})
    _need(value['unit'] == unit, 'UNIT_HOLD: unsupported stored unit')
    _need(type(value['value']) in ((float,) if normalized else (int, float))
        and isfinite(value['value']), 'NUMERIC_HOLD: finite numeric quantity required')


def _block(value, units, *, arrays=False, normalized=False):
    _closed(value, units)
    for name, unit in units.items():
        rows = value[name] if arrays else [value[name]]
        _need(type(rows) is list and len(rows) == (50 if arrays else 1), 'FORMAT_HOLD: original quantity dimensions required')
        for row in rows: _q(row, unit, normalized=normalized)


def _inputs(raw):
    p = _parse(raw, MAX)
    _closed(p, {'schema_version', 'input_id', 'origin', 'rights', 'time_origin_utc', 'step_seconds', 'step_count', 'program'})
    _need(p['schema_version'] == 'growing-geometry-artifact-input-v1' and p['origin'] == 'synthetic', 'SCOPE_HOLD: explicit synthetic input required')
    _id(p['input_id']); _utc(p['time_origin_utc'])
    rights = p['rights']; _closed(rights, {'declaration_id', 'revision', 'declared_at_utc',
        'ownership_asserted', 'access', 'store', 'use', 'transform', 'display', 'redistribute'})
    _id(rights['declaration_id']); _id(rights['revision']); _utc(rights['declared_at_utc'])
    _need(all(rights[k] is True for k in ('ownership_asserted', 'access', 'store', 'use', 'transform', 'display'))
        and type(rights['redistribute']) is bool, 'RIGHTS_HOLD: explicit own input use and display permissions required')
    dt, count = p['step_seconds'], p['step_count']
    _need(type(dt) in (int, float) and isfinite(dt) and dt > 0 and type(count) is int and 1 <= count < 512
        and 0 < dt*count <= 600, 'CAPACITY_HOLD: bounded positive original time grid required')
    _program(p['program'])
    _need(p['program']['input_id'] == p['input_id'], 'SCOPE_HOLD: original program identity differs')
    n = len(p['program']['leaves'])
    _need((count+1)*(115+4*n) <= 32768, 'CAPACITY_HOLD: original sample scalar budget exceeded')
    return p


def _program(p):
    _closed(p, {'input_id', 'origin', *POLICIES, 'model_floor_area', 'capacity_outflow', 'scenario', 'leaves'})
    _id(p['input_id']); _need(p['origin'] == 'synthetic' and all(p[k] == v for k, v in POLICIES.items()), 'POLICY_HOLD: original research policy required')
    _q(p['model_floor_area'], 'm2_floor'); _q(p['capacity_outflow'], 'J/m2_floor/K/s')
    _need(p['model_floor_area']['value'] > 0 and p['capacity_outflow']['value'] >= 0, 'FORMAT_HOLD: invalid explicit basis or outflow')
    s = p['scenario']; _closed(s, {'input_id', 'origin', *SCALAR_UNITS, *ARRAY_UNITS})
    _need(s['input_id'] == p['input_id'] and s['origin'] == 'synthetic', 'SCOPE_HOLD: original scenario identity required')
    for name, units in SCALAR_UNITS.items(): _block(s[name], units)
    for name, units in ARRAY_UNITS.items(): _block(s[name], units, arrays=True)
    leaves = p['leaves']; _need(type(leaves) is list and 1 <= len(leaves) <= 512, 'CAPACITY_HOLD: bounded original leaf list required')
    ids = []
    for leaf in leaves:
        _closed(leaf, {'leaf_id', 'curve', 'thermal_age', 'base_temperature', 'initial_area'}); _id(leaf['leaf_id']); ids.append(leaf['leaf_id'])
        for key, unit in (('thermal_age', 'degC_day'), ('base_temperature', 'degC'), ('initial_area', 'm2')): _q(leaf[key], unit)
        c = leaf['curve']; _closed(c, {'profile_id', 'origin', 'values'}); _id(c['profile_id'])
        _need(c['origin'] == 'synthetic', 'SCOPE_HOLD: explicitly synthetic leaf curve required')
        _block(c['values'], {'maximum_area': 'm2', 'steepness': '1/degC_day', 'inflection_age': 'degC_day'})
        v = c['values']; _need(leaf['thermal_age']['value'] >= 0 and leaf['initial_area']['value'] > 0 and v['maximum_area']['value'] > 0
            and v['steepness']['value'] > 0 and v['inflection_age']['value'] >= 0, 'FORMAT_HOLD: invalid leaf metadata')
    _need(len(ids) == len(set(ids)), 'FORMAT_HOLD: unique leaf identities required')


def _float_view(value):
    if type(value) is dict:
        if set(value) == {'value', 'unit'}: return {'value': float(value['value']), 'unit': value['unit']}
        return {key: _float_view(item) for key, item in value.items()}
    if type(value) is list: return [_float_view(item) for item in value]
    return value


def _offset(dt, index):
    exact = Fraction.from_float(float(dt))*index
    return {'numerator': str(exact.numerator), 'denominator': str(exact.denominator), 'unit': 's'}


def _source(store, descriptor, *, maximum=MAX):
    _closed(descriptor, {'sha256', 'bytes'}); _hash(descriptor['sha256'])
    _need(type(descriptor['bytes']) is int and 0 < descriptor['bytes'] <= maximum, 'CAPACITY_HOLD: bounded blob descriptor required')
    raw = store.get(descriptor['sha256'], maximum=maximum)
    _need(len(raw) == descriptor['bytes'], 'HASH_HOLD: stored byte count differs')
    return raw


def _context(m, sources, inputs, pins):
    _need(sum(len(sources[k]) for k in ('request', 'program', 'seed', 'context')) <= MAX,
        'CAPACITY_HOLD: original combined context byte limit exceeded')
    p = _parse(sources['program'], MAX); request = _parse(sources['request'], MAX)
    _need(_canonical(request) == _canonical(inputs['program']) and _canonical(p) == _canonical(_float_view(request)), 'HASH_HOLD: original normalized program differs')
    c = _parse(sources['context'], MAX); _closed(c, {'identity', 'request_sha256', 'program_sha256', 'seed_sha256', 'numerical', 'state_layout'})
    for name in ('request', 'program', 'seed'): _need(c[name+'_sha256'] == m['sources'][name]['sha256'], 'HASH_HOLD: context source differs')
    _need(m['context_sha256'] == m['sources']['context']['sha256'], 'HASH_HOLD: original context differs')
    identity = c['identity']; _closed(identity, {'engine_version', 'engine_code_sha256', 'short_code_sha256', 'component_code_sha256',
        'profile_sha256', 'policies', 'state_schema', 'python_version', 'platform_system', 'platform_machine', 'byteorder', 'float_mant_dig', 'float_radix'})
    _need(identity['engine_version'] == 'growing-geometry-continuation-research-v1'
        and identity['engine_code_sha256'] == pins['backend/app/crop_growing_geometry_continuation.py']
        and identity['short_code_sha256'] == pins['backend/app/crop_growing_geometry_climate.py']
        and identity['policies'] == POLICIES and identity['state_schema'] == 'growing-geometry-companion-vector-v1'
        and identity['profile_sha256'] == {k.removesuffix('_profile'): v for k, v in PROFILE_SHA.items()}, 'MODEL_HOLD: unsupported original context identity')
    components = identity['component_code_sha256']; _need(type(components) is dict, 'CODE_HOLD: component pins required')
    expected = {n: pins[f'backend/app/{n}.py'] for n in MODEL_NAMES[2:] if n != 'crop_fruit_allocation'}
    _need(len(components) == len(expected) and {k.rsplit('.', 1)[-1]: v for k, v in components.items()} == expected, 'CODE_HOLD: original component source differs')
    _need(all(type(identity[k]) is str and 0 < len(identity[k]) <= 200 for k in ('python_version', 'platform_system', 'platform_machine'))
        and identity['byteorder'] in ('little', 'big') and type(identity['float_mant_dig']) is int and identity['float_mant_dig'] == 53
        and type(identity['float_radix']) is int and identity['float_radix'] == 2, 'MODEL_HOLD: original float environment required')
    dt = float(inputs['step_seconds']); count = inputs['step_count']
    _need(_canonical(c['numerical']) == _canonical({'step_seconds': dt, 'step_count': count, 'duration_seconds': dt*count,
        'method': 'shared-stage-fixed-rk4-growing-area-v1', 'sample_scalar_budget': 32768,
        'roundoff_rule': '64-ulp-per-step-ledger-v1', 'time_coordinate': 'elapsed_seconds_no_UTC_checkpoint'}), 'TIME_HOLD: original numerical grid differs')
    layout = {'plant': list(PLANT_UNITS), 'cohort_arrays': list(COHORT_UNITS), 'climate': list(CLIMATE_UNITS),
        'leaf_ids': [x['leaf_id'] for x in p['leaves']], 'leaf_blocks': ['thermal_age', 'area'],
        'units': {'plant': PLANT_UNITS, 'cohort_arrays': COHORT_UNITS, 'climate': CLIMATE_UNITS, 'leaf_blocks': {'thermal_age': 'degC_day', 'area': 'm2'}}}
    _need(c['state_layout'] == layout, 'FORMAT_HOLD: original state layout differs')
    seed = _parse(sources['seed'], MAX); _closed(seed, {'state', 'evaluation', 'initial_area_receipts'})
    receipts = seed['initial_area_receipts']; n = len(p['leaves'])
    _need(type(receipts) is list and len(receipts) == n, 'FORMAT_HOLD: original initial area receipts required')
    _state(seed['state'], p)
    s = p['scenario']; expected_initial = [s['plant_state'][k]['value'] for k in PLANT_UNITS]
    expected_initial += [q['value'] for k in COHORT_UNITS for q in s['cohort_state'][k]]
    expected_initial += [s['climate_state'][k]['value'] for k in CLIMATE_UNITS] + [x['thermal_age']['value'] for x in p['leaves']]
    for leaf, receipt in zip(p['leaves'], receipts, strict=True):
        _closed(receipt, {'leaf_id', 'requested_area', 'canonical_area', 'thermal_age'}); _q(receipt['canonical_area'], 'm2', normalized=True)
        _need(receipt['leaf_id'] == leaf['leaf_id'] and receipt['requested_area'] == leaf['initial_area']
            and receipt['thermal_age'] == leaf['thermal_age'], 'HASH_HOLD: original receipt metadata differs')
        expected_initial.append(receipt['canonical_area']['value'])
    _need(_canonical(seed['state']) == _canonical(expected_initial) and _digest(seed['state']) == m['initial_state_sha256'], 'HASH_HOLD: original initial vector differs')
    evaluation = seed['evaluation']; _closed(evaluation, {'joint', 'leaf_age_rates', 'leaf_area_rates', 'canonical_leaf_areas', 'curve_residuals'})
    for key, unit in (('leaf_age_rates', 'degC_day/s'), ('leaf_area_rates', 'm2/s'), ('canonical_leaf_areas', 'm2'), ('curve_residuals', 'm2')):
        _need(type(evaluation[key]) is list and len(evaluation[key]) == n, 'FORMAT_HOLD: original evaluation dimensions required')
        for q in evaluation[key]: _q(q, unit, normalized=True)
    _need(evaluation['canonical_leaf_areas'] == [r['canonical_area'] for r in receipts], 'HASH_HOLD: initial canonical areas differ')
    _block(evaluation['joint']['derived'], DERIVED_UNITS, normalized=True)
    return p, c, seed


def _state(y, p):
    n = len(p['leaves'])
    _need(type(y) is list and len(y) == 108+2*n and all(type(v) is float and isfinite(v) for v in y), 'FORMAT_HOLD: finite original float64 state required')
    _need(all(v >= 0 for v in (*y[:3], *y[4:105])) and y[107] >= 0, 'STATE_HOLD: negative stored inventory')
    for i, leaf in enumerate(p['leaves']):
        _need(y[108+i] >= leaf['thermal_age']['value'] and 0 < y[108+n+i] <= leaf['curve']['values']['maximum_area']['value'], 'STATE_HOLD: invalid stored leaf state')


def _checkpoint(raw, d, m, p, seed, previous_prefix):
    cp = _parse(raw, CHECKPOINT_MAX); _closed(cp, {'version', 'context_sha256', 'step_index', 'output_cursor',
        'output_prefix_sha256', 'last_confirmed', 'integrated_transfers', 'balance_residuals', 'balance_budgets'})
    i = d['index']; sample = cp['last_confirmed']; n = len(p['leaves'])
    _need(cp['version'] == 'growing-geometry-companion-checkpoint-v1' and cp['context_sha256'] == m['context_sha256']
        and type(cp['step_index']) is int and cp['step_index'] == i and type(cp['output_cursor']) is int and cp['output_cursor'] == i+1, 'HASH_HOLD: checkpoint identity/cursor differs')
    _closed(sample, {'step_index', 'elapsed_seconds', 'state', 'derived', 'curve_residuals', 'curve_invariant_changes'})
    _need(type(sample['step_index']) is int and sample['step_index'] == i and type(sample['elapsed_seconds']) is float
        and isfinite(sample['elapsed_seconds']), 'TIME_HOLD: original float sample time required')
    _state(sample['state'], p); _block(sample['derived'], DERIVED_UNITS, normalized=True)
    for key in ('curve_residuals', 'curve_invariant_changes'):
        _need(type(sample[key]) is list and len(sample[key]) == n, 'FORMAT_HOLD: original curve diagnostics required')
        for q in sample[key]: _q(q, 'm2', normalized=True)
    _block(cp['integrated_transfers'], FLUX_UNITS, normalized=True)
    units = {**BALANCE_UNITS, **{f'leaf_age_{j}': 'degC_day' for j in range(n)}}
    for key in ('balance_residuals', 'balance_budgets'): _block(cp[key], units, normalized=True)
    _need(all(cp['balance_budgets'][k]['value'] >= 0 and abs(cp['balance_residuals'][k]['value']) <= cp['balance_budgets'][k]['value'] for k in units), 'QC_HOLD: stored residual exceeds its recorded budget')
    if i == 0:
        _need(sample['state'] == seed['state'] and sample['derived'] == seed['evaluation']['joint']['derived']
            and sample['curve_residuals'] == seed['evaluation']['curve_residuals']
            and all(q['value'] == 0 for q in sample['curve_invariant_changes'])
            and all(q['value'] == 0 for q in cp['integrated_transfers'].values()), 'HASH_HOLD: original initial checkpoint differs')
    prefix = _digest({'previous': previous_prefix, 'sample': sample})
    _need(cp['output_prefix_sha256'] == prefix and _digest(sample) == d['sample_sha256']
        and _digest(sample['state']) == d['state_sha256'], 'HASH_HOLD: original sample/prefix differs')
    return cp, prefix


def _graph(store, m):
    _closed(m, ROOT_FIELDS)
    _need(all(_canonical(m[k]) == _canonical(v) for k, v in ROOT_CONSTANTS.items()), 'SCOPE_HOLD: supported stored research manifest required')
    pins = _pins(); _need(m['code_sha256'] == pins, 'CODE_HOLD: stored source version differs')
    _closed(m['sources'], SOURCE_NAMES)
    raws = {name: _source(store, d) for name, d in m['sources'].items()}
    for name, expected in {**PROFILE_SHA, 'license_notice': NOTICE_SHA}.items():
        _need(m['sources'][name]['sha256'] == expected, 'PROFILE_HOLD: original reference/notice bytes required')
    inputs = _inputs(raws['inputs'])
    _need(m['input_id'] == inputs['input_id'] and m['source_rights'] == inputs['rights']
        and m['time_origin_utc'] == inputs['time_origin_utc'], 'HASH_HOLD: original rights/identity/epoch differs')
    p, c, seed = _context(m, raws, inputs, pins)
    descriptors = m['samples']; count = inputs['step_count']; dt = float(inputs['step_seconds'])
    _need(type(descriptors) is list and len(descriptors) == count+1, 'FORMAT_HOLD: complete original sample list required')
    previous = None; prefix = _digest([]); checkpoints = []
    for i, d in enumerate(descriptors):
        _closed(d, DESCRIPTOR_FIELDS)
        _need(type(d['index']) is int and d['index'] == i and d['elapsed_seconds_exact'] == _offset(dt, i)
            and d['previous_checkpoint_sha256'] == previous, 'HASH_HOLD: original sample order/time/chain differs')
        for key in ('checkpoint_sha256', 'sample_sha256', 'state_sha256'): _hash(d[key])
        raw = _source(store, {'sha256': d['checkpoint_sha256'], 'bytes': d['checkpoint_bytes']}, maximum=CHECKPOINT_MAX)
        raws['checkpoint_'+str(i)] = raw
        cp, prefix = _checkpoint(raw, d, m, p, seed, prefix)
        exact = Fraction.from_float(dt)*i
        _need(cp['last_confirmed']['elapsed_seconds'] == i*dt == float(exact), 'TIME_HOLD: original sample float/exact grid differs')
        checkpoints.append(cp); previous = d['checkpoint_sha256']
    _need(m['terminal_state_sha256'] == descriptors[-1]['state_sha256'], 'HASH_HOLD: original terminal vector differs')
    return inputs, p, c, seed, checkpoints, raws


def _fence(store, m, raws):
    _need(_pins() == m['code_sha256'], 'CODE_HOLD: source changed before return')
    _inputs(raws['inputs'])
    for raw in raws.values():
        _need(store.get(sha256(raw).hexdigest(), maximum=MAX) == raw, 'HASH_HOLD: source changed before return')
    _need(_pins() == m['code_sha256'], 'CODE_HOLD: source changed during final evidence read')


def _read(directory, access, root_sha256, index):
    try:
        _hash(root_sha256)
        with MorphologyBlobStore(directory, access) as store:
            raw = store.get(root_sha256, maximum=MAX); m = _parse(raw, MAX)
            inputs, p, c, seed, checkpoints, raws = _graph(store, m)
            if index is None: result = deepcopy(m)
            else:
                _need(type(index) is int and 0 <= index < len(checkpoints), 'INDEX_HOLD: stored frame index required')
                cp = checkpoints[index]; sample = cp['last_confirmed']; y = sample['state']; n = len(p['leaves']); d = m['samples'][index]
                result = {**ROOT_CONSTANTS, 'schema_version': 'growing-geometry-replay-frame-v1', 'artifact_sha256': root_sha256,
                    'input_id': m['input_id'], 'input_sha256': m['sources']['inputs']['sha256'], 'context_sha256': m['context_sha256'],
                    **{k: d[k] for k in ('checkpoint_sha256', 'sample_sha256', 'state_sha256')}, 'index': index,
                    'at': {'time_origin_utc': m['time_origin_utc'], 'elapsed_seconds_exact': d['elapsed_seconds_exact']},
                    'elapsed_seconds': sample['elapsed_seconds'], 'leaf_ids': c['state_layout']['leaf_ids'], 'state_layout': c['state_layout'],
                    'leaves': [{'leaf_id': leaf['leaf_id'], 'thermal_age': {'value': y[108+j], 'unit': 'degC_day'},
                        'area': {'value': y[108+n+j], 'unit': 'm2'}, 'curve_sha256': _digest(leaf['curve']),
                        'initial_area_receipt': seed['initial_area_receipts'][j]} for j, leaf in enumerate(p['leaves'])],
                    'sample': sample, 'source_rights': inputs['rights'],
                    'plant': {k: {'value': y[j], 'unit': unit} for j, (k, unit) in enumerate(PLANT_UNITS.items())},
                    'cohorts': {k: [{'value': v, 'unit': unit} for v in y[5+j*50:55+j*50]] for j, (k, unit) in enumerate(COHORT_UNITS.items())},
                    'climate': {k: {'value': y[105+j], 'unit': unit} for j, (k, unit) in enumerate(CLIMATE_UNITS.items())},
                    **{k: cp[k] for k in ('integrated_transfers', 'balance_residuals', 'balance_budgets')}}
                result = deepcopy(result)
            raws['root'] = raw; _fence(store, m, raws)
            return result
    except (MorphologyArtifactHold, OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError) as exc:
        if isinstance(exc, MorphologyArtifactHold): raise GrowingGeometryArtifactHold(str(exc)) from None
        raise GrowingGeometryArtifactHold('FORMAT_HOLD: invalid stored growing geometry graph') from None


def read_growing_geometry_manifest(directory, access, root_sha256):
    return _read(directory, access, root_sha256, None)


def read_growing_geometry_frame(directory, access, root_sha256, *, index):
    _need(type(index) is int, 'INDEX_HOLD: integer frame index required')
    return _read(directory, access, root_sha256, index)
