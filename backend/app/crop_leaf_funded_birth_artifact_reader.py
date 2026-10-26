"""Compute-free replay of trusted immutable funded-leaf graphs."""
from copy import deepcopy
from hashlib import sha256
from math import isfinite
from pathlib import Path

from . import crop_leaf_carbon_stock_artifact_reader as stock
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical, _closed, _hash, _id, _parse

MAX = stock.MAX
CHECKPOINT_MAX = 1024**2
POLICY = 'explicit-new-structural-carbon-from-buffer-v1'
POINT_FIELDS = {'schema_version', 'input_id', 'origin', 'policy', 'context_sha256', 'checkpoint_sha256',
                'at_elapsed_seconds_exact', 'model_floor_area', 'events'}
ROOT_CONSTANTS = {**stock.ROOT_CONSTANTS, 'schema_version': 'funded-leaf-research-artifact-v1',
    'claim_scope': 'synthetic_funded_leaf_replay_only', 'display_policy': {
        **stock.DISPLAY_POLICY, 'stem_pose_attachment': 'declared_ids_only_requires_bound_stem_source'}}
ROOT_FIELDS = {*ROOT_CONSTANTS, 'input_id', 'source_rights', 'time_origin_utc', 'sources', 'code_sha256',
               'context_sha256', 'initial_state_sha256', 'terminal_state_sha256', 'events', 'samples'}
SOURCE_PATHS = tuple(dict.fromkeys((*stock.SOURCE_PATHS,
    'backend/app/crop_rational_morphology_clock.py', 'backend/app/crop_leaf_funded_birth_point.py',
    'backend/app/crop_leaf_funded_birth_continuation.py', 'backend/app/crop_leaf_funded_birth_artifact_producer.py',
    'backend/app/crop_leaf_funded_birth_artifact_reader.py')))
DESCRIPTOR_FIELDS = {*stock.DESCRIPTOR_FIELDS, 'step_index', 'phase', 'event_sequence', 'context_sha256'}
EVENT_FIELDS = {'event_sequence', 'step_index', 'after_frame_index', 'point', 'context_snapshot', 'context_sha256'}


class FundedLeafArtifactHold(MorphologyArtifactHold):
    pass


def _digest(v): return sha256(_canonical(v)).hexdigest()


def _pins():
    root = Path(__file__).resolve().parents[2]
    return {name: sha256((root/name).read_bytes()).hexdigest() for name in SOURCE_PATHS}


def _base_inputs(inputs):
    return {**{k: v for k, v in inputs.items() if k != 'births'}, 'schema_version': 'leaf-carbon-stock-artifact-input-v1'}


def _inputs(raw):
    v = _parse(raw, MAX)
    _closed(v, {'schema_version', 'input_id', 'origin', 'rights', 'time_origin_utc', 'step_seconds', 'step_count', 'program', 'births'})
    _need(v['schema_version'] == 'funded-leaf-artifact-input-v1', 'SCOPE_HOLD: funded leaf input required')
    stock._inputs(_canonical(_base_inputs(v)))
    births = v['births']; _need(type(births) is list and 1 <= len(births) <= 511, 'CAPACITY_HOLD: nonempty bounded birth plan required')
    _need(v['step_count']+1+len(births) <= 512, 'CAPACITY_HOLD: at most512 total frames required')
    p = deepcopy(v['program']); seen = set(); previous = 0; grouped = {}
    for item in births:
        _closed(item, {'step_index', 'point_inputs'}); step = item['step_index']
        _need(type(step) is int and previous <= step <= v['step_count'], 'TIME_HOLD: ordered original-grid points required')
        previous = step; point = item['point_inputs']; _closed(point, POINT_FIELDS)
        _id(point['input_id']); _hash(point['context_sha256']); _hash(point['checkpoint_sha256'])
        _need(point['schema_version'] == 'leaf-funded-birth-point-input-v1' and point['origin'] == 'synthetic'
              and point['policy'] == POLICY, 'POLICY_HOLD: explicit structural growth required')
        _need(point['at_elapsed_seconds_exact'] == stock._offset(v['step_seconds'], step), 'TIME_HOLD: original exact point time required')
        stock._q(point['model_floor_area'], 'm2_floor')
        _need(point['model_floor_area']['value'] == p['model_floor_area']['value'], 'BASIS_HOLD: original common floor required')
        events = point['events']; _need(type(events) is list and 1 <= len(events) <= 512, 'CAPACITY_HOLD: nonempty event batch required')
        new_leaves = []
        for event in events:
            _closed(event, {'event_id', 'attachment_internode_id', 'incoming_temperature', 'leaf'})
            _id(event['event_id']); _id(event['attachment_internode_id']); stock._q(event['incoming_temperature'], 'degC')
            _need(event['event_id'] not in seen, 'EVENT_HOLD: unique funding event history required'); seen.add(event['event_id'])
            new_leaves.append(deepcopy(event['leaf']))
        p['leaves'].extend(new_leaves); stock._program(p)
        for leaf in new_leaves:
            _need(leaf['thermal_age']['value'] == 0 and leaf['initial_carbon']['value'] > 0,
                  'STATE_HOLD: zero age and positive new carbon required')
        grouped.setdefault(step, []).append(len(events))
    n = len(v['program']['leaves']); scalar = 0
    for step in range(v['step_count']+1):
        scalar += 115+5*n
        for count in grouped.get(step, []): n += count; scalar += 115+5*n
    _need(scalar <= 32768, 'CAPACITY_HOLD: total actual frame scalar budget exceeded')
    return v


POINT_UNITS = {'structural_carbon': 'mg_CH2O/m2_floor', 'growth_respiration': 'mg_CH2O/m2_floor',
               'buffer_debit': 'mg_CH2O/m2_floor', 'capacity_in': 'J/m2_floor/K', 'sensible_in': 'J/m2_floor'}
POINT_BALANCE_UNITS = {'buffer': 'mg_CH2O/m2_floor', 'new_stock': 'mg_CH2O/m2_floor',
                       'whole_carbon': 'mg_CH2O/m2_floor', 'sensible': 'J/m2_floor', 'capacity': 'J/m2_floor/K'}
POINT_RESULT_FIELDS = {'model_version', 'policy', 'code_sha256', 'clock_code_sha256', 'input_sha256',
    'context_sha256', 'checkpoint_sha256', 'parent_manifest', 'inputs', 'before_checkpoint', 'after_program',
    'after_sample', 'after_rates', 'after_state_layout', 'birth_receipts', 'point_flows', 'balances',
    'checkpoint_validation_stage_evaluations', 'after_stage_evaluations', 'elapsed_steps_advanced', 'checkpoint',
    'scope', 'claim_scope', 'G0_G4', 'calculation_sha256'}
FUNDED_CP_FIELDS = {'version', 'context_sha256', 'step_index', 'segment_step_index', 'event_sequence', 'phase',
    'at_elapsed_seconds_exact', 'last_confirmed', 'output_cursor', 'output_prefix_sha256', 'integrated_transfers',
    'segment_integrated_transfers', 'point_history_sha256', 'point_totals', 'balance_residuals', 'balance_budgets',
    'global_balance_residuals', 'global_balance_budgets', 'scope', 'G0_G4'}


def _sample(sample, p, step, dt):
    _closed(sample, {'step_index', 'elapsed_seconds', 'state', 'derived', 'curve_residuals', 'curve_invariant_changes'})
    _need(type(sample['step_index']) is int and sample['step_index'] == step and type(sample['elapsed_seconds']) is float
          and isfinite(sample['elapsed_seconds']) and sample['elapsed_seconds'] == step*float(dt), 'TIME_HOLD: original global sample required')
    stock._state(sample['state'], p); stock._block(sample['derived'], stock.DERIVED_UNITS, normalized=True)
    for key in ('curve_residuals', 'curve_invariant_changes'):
        rows = sample[key]; _need(type(rows) is list and len(rows) == len(p['leaves']), 'FORMAT_HOLD: original curve dimensions required')
        for row in rows: stock._q(row, 'm2', normalized=True)


def _layout(root_context, p):
    return {**deepcopy(root_context['state_layout']), 'leaf_ids': [leaf['leaf_id'] for leaf in p['leaves']]}


def _qc(cp, p, *, global_=False):
    units = {**stock.BALANCE_UNITS, **{f'leaf_age_{i}': 'degC_day' for i in range(len(p['leaves']))},
             **{f'leaf_carbon_{i}': 'mg_CH2O/m2_floor' for i in range(len(p['leaves']))}}
    rkey, bkey = ('global_balance_residuals', 'global_balance_budgets') if global_ else ('balance_residuals', 'balance_budgets')
    stock._block(cp[rkey], units, normalized=True); stock._block(cp[bkey], units, normalized=True)
    _need(all(cp[bkey][name]['value'] >= 0 and abs(cp[rkey][name]['value']) <= cp[bkey][name]['value'] for name in units),
          'QC_HOLD: recorded funded residual exceeds budget')


def _receipts(point, declared, p):
    rows = point['birth_receipts']; count = len(declared['events']); n = len(p['leaves']); y = point['after_sample']['state']
    _need(type(rows) is list and len(rows) == count, 'FORMAT_HOLD: original birth receipt count required')
    result = []
    for i, (event, row) in enumerate(zip(declared['events'], rows, strict=True)):
        _closed(row, {'event_id', 'attachment_internode_id', 'initialization', 'capacity_in', 'sensible_in'})
        _need(row['event_id'] == event['event_id'] and row['attachment_internode_id'] == event['attachment_internode_id'],
              'HASH_HOLD: original event/attachment receipt required')
        stock._q(row['capacity_in'], 'J/m2_floor/K', normalized=True); stock._q(row['sensible_in'], 'J/m2_floor', normalized=True)
        initial = row['initialization']; _closed(initial, {'model_version', 'scope', 'claim_scope', 'gates', 'input_sha256', 'state'})
        _need(initial['model_version'] == 'leaf-logistic-canonical-area-state-research-v1'
              and initial['scope'] == 'software_research_only' and initial['claim_scope'] == 'synthetic_crop_math_only'
              and initial['gates'] == 'not_assessed', 'MODEL_HOLD: supported original leaf initialization required')
        _hash(initial['input_sha256']); state = initial['state']
        _closed(state, {'model_version', 'origin', 'thermal_age_basis', 'normalization', 'leaf_id', 'curve', 'curve_sha256', 'age_exact', 'area', 'anchor'})
        leaf = p['leaves'][n-count+i]; anchor = state['anchor']
        _closed(anchor, {'leaf_id', 'age_exact', 'curve_sha256', 'requested_area', 'canonical_area'})
        _need(state['model_version'] == initial['model_version'] and state['origin'] == 'synthetic'
              and state['thermal_age_basis'] == 'since_leaf_emergence' and state['normalization'] == stock.POLICIES['normalization']
              and state['leaf_id'] == anchor['leaf_id'] == leaf['leaf_id'] and state['curve'] == leaf['curve']
              and state['curve_sha256'] == anchor['curve_sha256'], 'HASH_HOLD: original leaf curve anchor required')
        _hash(state['curve_sha256'])
        _need(state['age_exact'] == anchor['age_exact'] == {'numerator': '0', 'denominator': '1', 'unit': 'degC_day'},
              'TIME_HOLD: zero exact birth age required')
        for key in ('requested_area', 'canonical_area'): stock._q(anchor[key], 'm2', normalized=True)
        stock._q(state['area'], 'm2', normalized=True)
        _need(anchor['requested_area'] == stock._float_view(event['leaf']['initial_area'])
              and state['area'] == anchor['canonical_area'] and state['area']['value'] == y[107+n+(n-count+i)],
              'HASH_HOLD: original canonical initial area required')
        result.append({'kind': 'funded_birth', 'value': deepcopy(row)})
    return result


def _event(store, descriptor, item, sequence, before, previous_p, previous_context, previous_seed,
           previous_history, root_context, root_sha, pins, raws):
    _closed(descriptor, EVENT_FIELDS)
    _need(type(descriptor['event_sequence']) is int and descriptor['event_sequence'] == sequence
          and type(descriptor['step_index']) is int and descriptor['step_index'] == item['step_index']
          and type(descriptor['after_frame_index']) is int and descriptor['after_frame_index'] == item['step_index']+sequence,
          'HASH_HOLD: original event order/coordinate required')
    point_raw = stock._source(store, descriptor['point']); snapshot_raw = stock._source(store, descriptor['context_snapshot'])
    raws[f'point_{sequence}'] = point_raw; raws[f'context_{sequence}'] = snapshot_raw
    point = _parse(point_raw, MAX); archive = _parse(snapshot_raw, MAX)
    _closed(point, POINT_RESULT_FIELDS); _closed(archive, {'program', 'seed', 'history', 'manifest'})
    _need(point['model_version'] == 'leaf-funded-structural-birth-point-research-v1' and point['policy'] == POLICY
          and point['code_sha256'] == pins['backend/app/crop_leaf_funded_birth_point.py']
          and point['clock_code_sha256'] == pins['backend/app/crop_rational_morphology_clock.py']
          and point['inputs'] == item['point_inputs'] and point['input_sha256'] == _digest(item['point_inputs'])
          and point['calculation_sha256'] == _digest({k: v for k, v in point.items() if k != 'calculation_sha256'}),
          'HASH_HOLD: original point source/calculation required')
    _need(point['scope'] == 'software_research_only' and point['G0_G4'] == 'not_assessed'
          and point['claim_scope'] == 'synthetic_declared_new_structural_allocation_point_only'
          and point['checkpoint'] is None and type(point['elapsed_steps_advanced']) is int and point['elapsed_steps_advanced'] == 0
          and type(point['checkpoint_validation_stage_evaluations']) is int and point['checkpoint_validation_stage_evaluations'] == 1
          and type(point['after_stage_evaluations']) is int and point['after_stage_evaluations'] == 1,
          'SCOPE_HOLD: original research point with no elapsed advance required')
    _need(_canonical(point['before_checkpoint']) == _canonical(before)
          and point['checkpoint_sha256'] == _digest(before) == item['point_inputs']['checkpoint_sha256']
          and point['context_sha256'] == before['context_sha256'] == item['point_inputs']['context_sha256']
          and point['parent_manifest'] == previous_context, 'HASH_HOLD: original previous CP/context required')
    m, seed, p, history = archive['manifest'], archive['seed'], archive['program'], archive['history']
    _closed(m, {'version', 'identity', 'root_context_sha256', 'parent_context_sha256', 'parent_checkpoint_sha256',
                'program_sha256', 'seed_sha256', 'history_sha256', 'numerical', 'state_layout'})
    _closed(seed, {'last_confirmed', 'before_checkpoint', 'anchors', 'birth_bases', 'base_transfers'})
    _need(m['version'] == 'funded-individual-leaf-context-v1' and _digest(m) == descriptor['context_sha256']
          and m['root_context_sha256'] == root_sha and m['parent_context_sha256'] == point['context_sha256']
          and m['parent_checkpoint_sha256'] == point['checkpoint_sha256'], 'HASH_HOLD: original frozen context ancestry required')
    expected_identity = {'version': 'leaf-funded-birth-continuation-research-v1',
        'code_sha256': pins['backend/app/crop_leaf_funded_birth_continuation.py'],
        'point_code_sha256': pins['backend/app/crop_leaf_funded_birth_point.py'],
        'clock_code_sha256': pins['backend/app/crop_rational_morphology_clock.py'], 'root_identity': root_context['identity']}
    _need(m['identity'] == expected_identity, 'CODE_HOLD: original funded identity required')
    for name in ('program', 'seed', 'history'):
        _need(m[name+'_sha256'] == _digest(archive[name]), 'HASH_HOLD: original frozen source part required')
    new_leaves = [stock._float_view(event['leaf']) for event in item['point_inputs']['events']]
    expected_p = {**previous_p, 'leaves': [*previous_p['leaves'], *new_leaves]}
    stock._program(p)
    _need(_canonical(p) == _canonical(expected_p) == _canonical(point['after_program'])
          and m['state_layout'] == point['after_state_layout'] == _layout(root_context, p), 'HASH_HOLD: original ordered appended program required')
    _need(_canonical(m['numerical']) == _canonical({**root_context['numerical'], 'event_global_step_index': item['step_index']}),
          'TIME_HOLD: original numerical scope required')
    _sample(point['after_sample'], p, item['step_index'], root_context['numerical']['step_seconds'])
    _need(seed['last_confirmed'] == point['after_sample'] and seed['before_checkpoint'] == before,
          'HASH_HOLD: original point sample required')
    count = len(new_leaves); n0 = len(previous_p['leaves']); n = len(p['leaves'])
    old, new = before['last_confirmed']['state'], point['after_sample']['state']
    _need(new[1:104] == old[1:104] and new[105:107] == old[105:107]
          and new[107:107+n0] == old[107:107+n0] and new[107+n0:107+n] == [0.]*count
          and new[107+n:107+n+n0] == old[107+n0:107+2*n0]
          and new[107+2*n:107+2*n+n0] == old[107+2*n0:]
          and new[107+2*n+n0:] == [leaf['initial_carbon']['value'] for leaf in new_leaves],
          'HASH_HOLD: original existing states/new initial C required')
    _need(type(point['after_rates']) is list and len(point['after_rates']) == len(new)
          and all(type(v) is float and isfinite(v) for v in point['after_rates']), 'FORMAT_HOLD: finite original RHS snapshot required')
    stock._block(point['point_flows'], POINT_UNITS, normalized=True)
    _closed(point['balances'], POINT_BALANCE_UNITS)
    for name, unit in POINT_BALANCE_UNITS.items():
        row = point['balances'][name]; _closed(row, {'residual', 'budget'})
        for quantity in row.values(): stock._q(quantity, unit, normalized=True)
        _need(row['budget']['value'] >= 0 and abs(row['residual']['value']) <= row['budget']['value'], 'QC_HOLD: original point balance required')
    _need(type(history) is list and len(history) == sequence and history[:-1] == previous_history,
          'HASH_HOLD: original point history prefix required')
    expected_record = {'inputs': item['point_inputs'], 'calculation_sha256': point['calculation_sha256'],
        'after_sample_sha256': _digest(point['after_sample']), 'new_leaves': new_leaves, 'point_flows': point['point_flows'],
        'balances': point['balances'], 'air_temperature_integral': before['integrated_transfers']['indoor_air_temperature_time']['value']}
    _need(_canonical(history[-1]) == _canonical(expected_record), 'HASH_HOLD: original point history receipt required')
    expected_anchors = [*previous_seed['anchors'], *({'value': 0., 'unit': 'm2'} for _ in new_leaves)]
    expected_bases = [*previous_seed['birth_bases'], *({'leaf_id': leaf['leaf_id'], 'step_index': item['step_index'],
        'thermal_age': 0., 'carbon': leaf['initial_carbon']['value'],
        'air_temperature_integral': expected_record['air_temperature_integral']} for leaf in new_leaves)]
    expected_transfers = {name: before['integrated_transfers'].get(name, {'value': 0., 'unit': unit})
                          for name, unit in stock._flux_units(p).items()}
    _need(_canonical(seed['anchors']) == _canonical(expected_anchors) and seed['birth_bases'] == expected_bases
          and seed['base_transfers'] == expected_transfers, 'HASH_HOLD: original anchors/clock/C bases/continuous prefix required')
    receipts = _receipts(point, item['point_inputs'], p)
    return archive, point, receipts


def _funded_checkpoint(raw, d, archive, previous_prefix, first_cp):
    cp = _parse(raw, CHECKPOINT_MAX); _closed(cp, FUNDED_CP_FIELDS)
    p, seed, m = archive['program'], archive['seed'], archive['manifest']; step = d['step_index']
    local = step-m['numerical']['event_global_step_index']
    _need(cp['version'] == 'funded-individual-leaf-continuation-checkpoint-v1'
          and cp['context_sha256'] == d['context_sha256'] == _digest(m)
          and type(cp['step_index']) is int and cp['step_index'] == step
          and type(cp['segment_step_index']) is int and cp['segment_step_index'] == local >= 0
          and type(cp['output_cursor']) is int and cp['output_cursor'] == d['index']+1
          and type(cp['event_sequence']) is int and cp['event_sequence'] == d['event_sequence'] == len(archive['history']),
          'HASH_HOLD: original funded index/context/cursor required')
    _need(cp['phase'] == d['phase'] == ('after_birth' if local == 0 else 'funded_birth_interval')
          and cp['at_elapsed_seconds_exact'] == d['elapsed_seconds_exact']
          and cp['point_history_sha256'] == m['history_sha256']
          and cp['scope'] == 'software_research_only' and cp['G0_G4'] == 'not_assessed', 'SCOPE_HOLD: original funded phase/clock required')
    sample = cp['last_confirmed']; _sample(sample, p, step, m['numerical']['step_seconds'])
    for key in ('integrated_transfers', 'segment_integrated_transfers'): stock._block(cp[key], stock._flux_units(p), normalized=True)
    stock._block(cp['point_totals'], POINT_UNITS, normalized=True); _qc(cp, p); _qc(cp, p, global_=True)
    if local == 0:
        _need(sample == seed['last_confirmed'] and cp['integrated_transfers'] == seed['base_transfers']
              and all(row['value'] == 0 for row in cp['segment_integrated_transfers'].values()),
              'HASH_HOLD: original after-birth snapshot required')
    else:
        _need(first_cp is not None and cp['point_totals'] == first_cp['point_totals'], 'HASH_HOLD: frozen point totals required')
    prefix = _digest({'previous': previous_prefix, 'sample': sample, 'event_sequence': cp['event_sequence'], 'phase': cp['phase']})
    _need(cp['output_prefix_sha256'] == prefix and _digest(sample) == d['sample_sha256']
          and _digest(sample['state']) == d['state_sha256'], 'HASH_HOLD: original funded sample/prefix required')
    return cp, prefix


def _graph(store, m):
    _closed(m, ROOT_FIELDS)
    _need(all(_canonical(m[k]) == _canonical(v) for k, v in ROOT_CONSTANTS.items()), 'SCOPE_HOLD: supported funded artifact required')
    pins = _pins(); _need(m['code_sha256'] == pins, 'CODE_HOLD: stored funded source version differs')
    _closed(m['sources'], stock.SOURCE_NAMES)
    raws = {name: stock._source(store, d) for name, d in m['sources'].items()}
    for name, expected in {**stock.PROFILE_SHA, 'license_notice': stock.NOTICE_SHA}.items():
        _need(m['sources'][name]['sha256'] == expected, 'PROFILE_HOLD: original reference/notice required')
    inputs = _inputs(raws['inputs'])
    _need(m['input_id'] == inputs['input_id'] and m['source_rights'] == inputs['rights']
          and m['time_origin_utc'] == inputs['time_origin_utc'], 'HASH_HOLD: original source/rights/epoch required')
    root_p, root_context, root_seed = stock._context(m, raws, _base_inputs(inputs), pins)
    descriptors, events = m['samples'], m['events']
    _need(type(descriptors) is list and len(descriptors) == inputs['step_count']+1+len(inputs['births'])
          and type(events) is list and len(events) == len(inputs['births']), 'FORMAT_HOLD: complete original frame/event lists required')
    event_by_index = {}
    for j, (d, item) in enumerate(zip(events, inputs['births'], strict=True)):
        _closed(d, EVENT_FIELDS)
        _need(type(d['after_frame_index']) is int and d['after_frame_index'] == item['step_index']+j+1,
              'FORMAT_HOLD: original event frame required')
        event_by_index[d['after_frame_index']] = (j, d, item)
    n0 = len(root_p['leaves']); root_y = root_seed['state']
    p, context, history = root_p, root_context, []
    seed = {'anchors': root_seed['evaluation']['curve_residuals'], 'birth_bases': [
        {'leaf_id': leaf['leaf_id'], 'step_index': 0, 'thermal_age': root_y[107+i], 'carbon': root_y[107+2*n0+i],
         'air_temperature_integral': 0.} for i, leaf in enumerate(root_p['leaves'])]}
    receipts = [{'kind': 'initial', 'value': row} for row in root_seed['initial_area_receipts']]
    frames = []; parsed_events = []; archive = None; first_cp = None
    previous = None; prefix = _digest([]); sequence = 0; previous_step = -1
    for i, d in enumerate(descriptors):
        _closed(d, DESCRIPTOR_FIELDS)
        _need(type(d['index']) is int and d['index'] == i and type(d['step_index']) is int
              and 0 <= d['step_index'] <= inputs['step_count'] and type(d['event_sequence']) is int
              and d['elapsed_seconds_exact'] == stock._offset(inputs['step_seconds'], d['step_index'])
              and d['previous_checkpoint_sha256'] == previous, 'HASH_HOLD: original frame order/time/CP chain required')
        for name in ('checkpoint_sha256', 'sample_sha256', 'state_sha256', 'context_sha256'): _hash(d[name])
        if i in event_by_index:
            j, event_d, item = event_by_index[i]
            _need(frames and d['step_index'] == previous_step == item['step_index'] and j+1 == sequence+1,
                  'TIME_HOLD: point must follow its original before-frame')
            archive, point, new_receipts = _event(store, event_d, item, j+1, frames[-1]['checkpoint'], p,
                context, seed, history, root_context, m['context_sha256'], pins, raws)
            p, seed, context, history = archive['program'], archive['seed'], archive['manifest'], archive['history']
            receipts = [*receipts, *new_receipts]; sequence += 1; first_cp = None
            parsed_events.append({'point': point, 'context': archive})
        else:
            _need(d['step_index'] == previous_step+1, 'TIME_HOLD: original consecutive step required')
        _need(d['event_sequence'] == sequence and d['context_sha256'] == (m['context_sha256'] if sequence == 0 else _digest(context)),
              'HASH_HOLD: original frame context/sequence required')
        raw = stock._source(store, {'sha256': d['checkpoint_sha256'], 'bytes': d['checkpoint_bytes']}, maximum=CHECKPOINT_MAX)
        raws[f'checkpoint_{i}'] = raw
        if sequence == 0:
            _need(d['phase'] == 'root_interval' and i == d['step_index'], 'SCOPE_HOLD: original root interval required')
            cp, prefix = stock._checkpoint(raw, d, m, root_p, root_seed, prefix)
        else:
            cp, prefix = _funded_checkpoint(raw, d, archive, prefix, first_cp)
            if first_cp is None: first_cp = cp
        frames.append({'checkpoint': cp, 'program': p, 'layout': _layout(root_context, p),
                       'creation_receipts': receipts, 'creation_bases': deepcopy(seed['birth_bases']),
                       'context': archive})
        previous = d['checkpoint_sha256']; previous_step = d['step_index']
    _need(previous_step == inputs['step_count'] and sequence == len(events)
          and descriptors[-1]['state_sha256'] == m['terminal_state_sha256'], 'HASH_HOLD: original completed terminal required')
    return inputs, root_p, root_context, root_seed, frames, parsed_events, raws


def _fence(store, m, raws):
    _need(_pins() == m['code_sha256'], 'CODE_HOLD: source changed before funded return')
    _inputs(raws['inputs'])
    for raw in raws.values():
        _need(store.get(sha256(raw).hexdigest(), maximum=MAX) == raw, 'HASH_HOLD: original source changed before funded return')
    _need(_pins() == m['code_sha256'], 'CODE_HOLD: source changed during final funded read')


def _read(directory, access, root_sha256, index):
    try:
        _hash(root_sha256)
        with MorphologyBlobStore(directory, access) as store:
            raw = store.get(root_sha256, maximum=MAX); m = _parse(raw, MAX)
            inputs, _, _, _, frames, _, raws = _graph(store, m)
            if index is None:
                result = deepcopy(m)
            else:
                _need(type(index) is int and 0 <= index < len(frames), 'INDEX_HOLD: stored funded frame required')
                frame = frames[index]; cp = frame['checkpoint']; sample = cp['last_confirmed']; p = frame['program']
                n = len(p['leaves']); y = sample['state']; d = m['samples'][index]
                leaves = []
                for j, leaf in enumerate(p['leaves']):
                    receipt = frame['creation_receipts'][j]
                    attachment = {'status': 'separate_authored_asset_required', 'internode_id': None} if receipt['kind'] == 'initial' else {
                        'status': 'declared_not_bound', 'internode_id': receipt['value']['attachment_internode_id']}
                    leaves.append({'leaf_id': leaf['leaf_id'], 'thermal_age': {'value': y[107+j], 'unit': 'degC_day'},
                        'area': {'value': y[107+n+j], 'unit': 'm2'}, 'carbon': {'value': y[107+2*n+j], 'unit': 'mg_CH2O/m2_floor'},
                        'curve_sha256': _digest(leaf['curve']), 'creation_receipt': receipt,
                        'creation_basis': frame['creation_bases'][j], 'attachment': attachment})
                result = {**ROOT_CONSTANTS, 'schema_version': 'funded-leaf-replay-frame-v1', 'artifact_sha256': root_sha256,
                    'input_id': m['input_id'], 'input_sha256': m['sources']['inputs']['sha256'], 'source_rights': inputs['rights'],
                    **{k: d[k] for k in ('index', 'step_index', 'phase', 'event_sequence', 'context_sha256', 'checkpoint_sha256', 'sample_sha256', 'state_sha256')},
                    'at': {'time_origin_utc': m['time_origin_utc'], 'elapsed_seconds_exact': d['elapsed_seconds_exact']},
                    'leaf_ids': frame['layout']['leaf_ids'], 'state_layout': frame['layout'], 'leaves': leaves, 'sample': sample,
                    'plant': {k: {'value': y[j], 'unit': unit} for j, (k, unit) in enumerate(stock.PLANT_UNITS.items())},
                    'cohorts': {k: [{'value': v, 'unit': unit} for v in y[4+j*50:54+j*50]] for j, (k, unit) in enumerate(stock.COHORT_UNITS.items())},
                    'climate': {k: {'value': y[104+j], 'unit': unit} for j, (k, unit) in enumerate(stock.CLIMATE_UNITS.items())},
                    **{k: cp[k] for k in ('integrated_transfers', 'balance_residuals', 'balance_budgets')},
                    **{k: cp.get(k) for k in ('segment_integrated_transfers', 'point_totals', 'global_balance_residuals', 'global_balance_budgets')}}
                result = deepcopy(result)
            raws['root'] = raw; _fence(store, m, raws)
            return result
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as error:
        if isinstance(error, MorphologyArtifactHold): raise FundedLeafArtifactHold(str(error)) from None
        raise FundedLeafArtifactHold('FORMAT_HOLD: invalid stored funded leaf graph') from None


def read_funded_leaf_manifest(directory, access, root_sha256): return _read(directory, access, root_sha256, None)


def read_funded_leaf_frame(directory, access, root_sha256, *, index):
    _need(type(index) is int, 'INDEX_HOLD: integer funded frame index required')
    return _read(directory, access, root_sha256, index)
