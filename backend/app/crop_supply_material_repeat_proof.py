"""Saved-stage algebra for a flat material lineage; no live RHS or adoption."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys

from . import crop_supply_material_repeat_point as point

VERSION = 'supply-material-repeat-proof-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
base, old, q, x = point.base, point.old, point.q, point.x
need, raw, digest = point.need, point.raw, point.digest

CANDIDATE_FIELDS = {'schema_version', *point.FLAGS, 'model_version','code_sha256','status','hold','source',
    'effective_rights','pending_page_sha256','source_schedule','source_interval','root_certificate','state_layout',
    'state_coordinates','at','selection_policy','dense_candidate','refinements','state_differences','transfer_differences',
    'account_rule','diagnostic_scope','work','checkpoint_issued','history_committed','material_consumed','calculation_sha256'}
POINT_FIELDS = {'schema_version', *point.FLAGS, 'model_version','code_sha256','status','hold','policy','source',
    'pending_page_sha256','initial_binding_sha256','input_sha256','inputs','candidate_sha256','candidate','effective_rights',
    'point_data','work','elapsed_seconds_advanced','schedule_adoption','checkpoint_issued','history_committed',
    'material_consumed','calculation_sha256'}
WITNESS_FIELDS = {'schema_version', *point.FLAGS, 'model_version','code_sha256','producer_model_version',
    'producer_code_sha256','source','pending_page_sha256','time_tolerance_seconds_exact','inputs','dense_derived',
    'refinements','after_stage','work','public_candidate_calculation_sha256','public_calculation_sha256','public_point_sha256'}


def _head(value, schema, fields, source):
    base.reader._closed(value, fields)
    need(value['schema_version'] == schema and value['model_version'] == point.VERSION
         and value['code_sha256'] == point.CODE_SHA256 and value['source'] == source
         and all(value[k] == v for k,v in point.FLAGS.items())
         and value['hold'] is None and value['checkpoint_issued'] is False
         and value['history_committed'] is False and value['material_consumed'] is False
         and value['calculation_sha256'] == digest({k:v for k,v in value.items() if k != 'calculation_sha256'}),
         'PROOF_HOLD: exact source-bound original successor receipt required')


def _candidate_reuse(s, current, source, pending, tolerance, dense_derived, refinements, meter, inputs, after_stage):
    seal = meter.algebra
    if seal is None:
        return None
    need(type(seal) is point._Algebra and seal.token is point._TOKEN,
         'PROOF_HOLD: original operation-local algebra seal required')
    if inputs is None or after_stage is None or seal.inputs is None or seal.after_stage is None:
        return None
    if raw(inputs, point.INPUT_MAX) != seal.inputs or raw(after_stage) != seal.after_stage:
        return None
    keys = (raw(source), raw(current, base.CURRENT_MAX), raw(s.basis), pending, raw(q(x(tolerance, 's'), 's')))
    if keys != (seal.source, seal.current, seal.basis, seal.pending, seal.tolerance):
        return None
    need(type(refinements) is list and len(refinements) == 3, 'PROOF_HOLD: three original refinement observations required')
    for value in refinements:
        base.reader._closed(value, {'substeps','step_seconds_exact','intervals','derived'})
    observations = raw({'dense_derived': dense_derived, 'refinements': refinements})
    if observations != seal.observations:
        return None
    parts = json.loads(seal.derived)
    dense = {**parts['dense_candidate'], 'derived': deepcopy(dense_derived)}
    packets = [{**packet, 'intervals': deepcopy(observed['intervals']), 'derived': deepcopy(observed['derived'])}
               for packet, observed in zip(parts['refinements'], refinements, strict=True)]
    meter.fence('history_validation')
    need(keys == (raw(source), raw(current, base.CURRENT_MAX), raw(s.basis), pending, raw(q(x(tolerance, 's'), 's'))),
         'SOURCE_HOLD: sealed algebra scope changed')
    meter.algebra_hits += 1
    return parts['root_certificate'], dense, packets, parts['work']


def _candidate_saved(s, current, source, pending, tolerance, dense_derived, refinements, meter, *, inputs=None, after_stage=None):
    page, math = point._pending(s, current, source, pending)
    trace = page['interval']
    reused = _candidate_reuse(s, current, source, pending, tolerance, dense_derived, refinements, meter, inputs, after_stage)
    n = current['numeric']; state = tuple(n['last_confirmed']['state'])
    if reused is None:
        root, theta, bisections = point._root(s, current, trace, tolerance, meter)
        n = current['numeric']; state = tuple(n['last_confirmed']['state']); zero = (0.,)*len(math.units)
        dt = x(trace['step_seconds_exact'], 's'); left = x(n['at']['elapsed_seconds_exact'], 's')
        at = x(root['root']['upper_elapsed_seconds_exact'], 's'); duration = at-left
        weights = point.state_math.old._weights(theta)
        dense_state = base.combine(state, tuple(tuple(v['rates']) for v in trace['stages']), weights, dt)
        partial = base.combine(zero, tuple(tuple(v['flux']) for v in trace['stages']), weights, dt)
        dense = point.books.packet(math, n, dense_state, partial, dense_derived, at, 1)
        need(dense['represented_threshold_status'] == 'crossed',
             'STATE_HOLD: actual saved dense state and accounts required')
        expected_refinements = []
        need(type(refinements) is list and len(refinements) == 3, 'PROOF_HOLD: original three refinements required')
        for count, saved in zip((1,2,4), refinements, strict=True):
            base.reader._closed(saved, {'substeps','step_seconds_exact','intervals','derived'})
            need(type(saved['substeps']) is int and saved['substeps'] == count
                 and saved['step_seconds_exact'] == q(duration/count, 's'), 'TRACE_HOLD: exact refinement count/step required')
            need(type(saved['intervals']) is list and len(saved['intervals']) == count, 'PROOF_HOLD: bounded refinement intervals required')
            y, totals = state, zero
            rates, flow = tuple(trace['stages'][0]['rates']), tuple(trace['stages'][0]['flux'])
            intervals = []
            for i, interval in enumerate(saved['intervals']):
                base.reader._closed(interval, {'left_elapsed_seconds_exact','right_elapsed_seconds_exact','step_seconds_exact','stages','endpoint'})
                need(type(interval['stages']) is list and len(interval['stages']) == 4,
                     'TRACE_HOLD: four saved refinement stages required')
                calls = iter([*interval['stages'][1:], interval['endpoint']])
                def evaluate(trial, label):
                    meter.fence('history_validation')
                    row = next(calls)
                    need(raw(list(trial)) == raw(row['state']), 'TRACE_HOLD: exact saved refinement stage state required')
                    return tuple(row['rates']), tuple(row['flux']), saved['derived'] if label == 'endpoint' else None
                need(raw(list(y)) == raw(interval['stages'][0]['state'])
                     and raw(list(rates)) == raw(interval['stages'][0]['rates'])
                     and raw(list(flow)) == raw(interval['stages'][0]['flux']), 'TRACE_HOLD: exact first refinement stage required')
                y, totals, rates, flow, derived, rebuilt = point.state_math._rk4(y, totals, rates, flow,
                    duration/count, left+i*duration/count, evaluate)
                need(raw(rebuilt) == raw(interval), 'TRACE_HOLD: exact algebraic refinement trace required')
                intervals.append(rebuilt)
            packet = point.books.packet(math, n, y, totals, saved['derived'], at, count)
            rebuilt = {'substeps': count, 'step_seconds_exact': q(duration/count, 's'), 'intervals': intervals, **packet}
            expected_refinements.append(rebuilt)
        work = {'interval_replay_RHS_evaluations': 5, 'dense_state_RHS_evaluations': 29,
            'point_stage_RHS_evaluations': 0, 'root_bisections': bisections}
    else:
        root, dense, expected_refinements, work = reused
    coordinates = deepcopy(math.data['seed']['state_layout'])
    coordinate_rows = base.arithmetic.resume._coordinates({'initial': {'state_layout': coordinates, 'state': state}, 'program': math.data['program']})
    packets = [dense, *expected_refinements]
    _, _, differences = point.state_math._differences(packets)
    states = differences([v['state'] for v in packets], [r['unit'] for r in coordinate_rows])
    for row, coordinate in zip(states, coordinate_rows, strict=True): row['coordinate'] = coordinate
    transfers = differences([[packet['partial_interval_transfers'][name]['value'] for name in math.units] for packet in packets], list(math.units.values()))
    for row, name in zip(transfers, math.units, strict=True): row['name'] = name
    result = {**point.FLAGS, 'schema_version': 'supply-material-successor-candidate-v1', 'model_version': point.VERSION,
        'code_sha256': point.CODE_SHA256, 'status': 'candidate_ready', 'hold': None, 'source': deepcopy(source),
        'effective_rights': deepcopy(current['effective_rights']), 'pending_page_sha256': pending,
        'source_schedule': deepcopy(n['schedule']), 'source_interval': deepcopy(trace), 'root_certificate': root,
        'state_layout': coordinates, 'state_coordinates': coordinate_rows, 'state_differences': states,
        'transfer_differences': transfers, 'at': deepcopy(dense['at']), 'dense_candidate': dense, 'refinements': expected_refinements,
        'selection_policy': 'certified_dense_root_upper_bound_no_threshold_snap',
        'account_rule': 'exact_source_plus_partial_residual_and_unchanged_budget_sum',
        'diagnostic_scope': 'same_time_local_differences_not_certified_ODE_or_agronomic_error',
        'work': work,
        'checkpoint_issued': False, 'history_committed': False, 'material_consumed': False}
    result['calculation_sha256'] = digest(result)
    raw(result)
    meter.fence('history_validation')
    return result


def _observations(refinements):
    return [{k: deepcopy(value[k]) for k in ('substeps','step_seconds_exact','intervals','derived')} for value in refinements]


def verify_candidate(s, current, source, pending, value, meter):
    _head(value, 'supply-material-successor-candidate-v1', CANDIDATE_FIELDS, source)
    rebuilt = _candidate_saved(s, current, source, pending, value['root_certificate']['time_tolerance_seconds_exact'],
        value['dense_candidate']['derived'], _observations(value['refinements']), meter)
    need(raw(rebuilt) == raw(value), 'PROOF_HOLD: complete public candidate differs from saved-stage algebra')


def _point_saved(s, current, source, pending, inputs, candidate, after_stage, meter):
    event = point._event_data(s, current)
    point._head(s, current, source, event, inputs, pending)
    snapshot = raw(inputs, point.INPUT_MAX)
    need(inputs['candidate_sha256'] == candidate['calculation_sha256']
         and inputs['at_elapsed_seconds_exact'] == candidate['at']['elapsed_seconds_exact'], 'POINT_HOLD: exact saved candidate/input time required')
    age = x(candidate['dense_candidate']['shoot_age_exact'], 'degC_day')
    threshold = x(event['event']['threshold_exact'], 'degC_day')
    need(threshold <= age < threshold+x(event['timeline']['phyllochron_exact'], 'degC_day'), 'EVENT_HOLD: first threshold only')
    data = point._point_data(s, current, event, inputs, candidate, lambda *args: deepcopy(after_stage))
    base._vector(data['after_rates'], len(data['after_state']))
    work = deepcopy(candidate['work']); work['point_stage_RHS_evaluations'] = 2 if inputs['leaf'] is not None else 1
    result = {**point.FLAGS, 'schema_version': 'supply-material-successor-point-result-v1', 'model_version': point.VERSION,
        'code_sha256': point.CODE_SHA256, 'status': 'point_ready', 'hold': None, 'policy': point.POLICY,
        'source': deepcopy(source), 'pending_page_sha256': pending, 'initial_binding_sha256': event['initial_binding_sha256'],
        'input_sha256': sha256(snapshot).hexdigest(), 'inputs': deepcopy(inputs), 'candidate_sha256': candidate['calculation_sha256'],
        'candidate': candidate, 'effective_rights': {k: current['effective_rights'][k] and inputs['rights'][k] for k in current['effective_rights']},
        'point_data': data, 'work': work, 'elapsed_seconds_advanced': q(0, 's'), 'schedule_adoption': 'not_performed',
        'checkpoint_issued': False, 'history_committed': False, 'material_consumed': False}
    result['calculation_sha256'] = digest(result)
    raw(result)
    need(raw(inputs, point.INPUT_MAX) == snapshot, 'SOURCE_HOLD: saved-stage proof changed inputs')
    meter.fence('history_validation')
    return result


def verify_point(s, current, source, pending, value, meter):
    _head(value, 'supply-material-successor-point-result-v1', POINT_FIELDS, source)
    verify_candidate(s, current, source, pending, value['candidate'], meter)
    rebuilt = _point_saved(s, current, source, pending, value['inputs'], value['candidate'], value['point_data']['after_stage'], meter)
    need(raw(rebuilt) == raw(value), 'PROOF_HOLD: complete public point differs from saved-stage algebra')


def pack_point_witness(value):
    _head(value, 'supply-material-successor-point-result-v1', POINT_FIELDS, value['source'])
    need(value['status'] == 'point_ready', 'POINT_HOLD: completed public point required for storage')
    witness = {**point.FLAGS, 'schema_version': 'supply-material-successor-point-witness-v1',
        'model_version': VERSION, 'code_sha256': CODE_SHA256, 'producer_model_version': point.VERSION,
        'producer_code_sha256': point.CODE_SHA256, 'source': deepcopy(value['source']),
        'pending_page_sha256': value['pending_page_sha256'],
        'time_tolerance_seconds_exact': deepcopy(value['candidate']['root_certificate']['time_tolerance_seconds_exact']),
        'inputs': deepcopy(value['inputs']), 'dense_derived': deepcopy(value['candidate']['dense_candidate']['derived']),
        'refinements': _observations(value['candidate']['refinements']), 'after_stage': deepcopy(value['point_data']['after_stage']),
        'work': deepcopy(value['work']), 'public_candidate_calculation_sha256': value['candidate']['calculation_sha256'],
        'public_calculation_sha256': value['calculation_sha256'], 'public_point_sha256': digest(value)}
    raw(witness)
    return witness


def expand_point_witness(s, current, source, pending, witness, meter):
    """Resolve a real CAS witness to the entire original public receipt, with zero RHS."""
    meter.fence('history_validation')
    base.reader._closed(witness, WITNESS_FIELDS)
    need(witness['schema_version'] == 'supply-material-successor-point-witness-v1'
         and witness['model_version'] == VERSION and witness['code_sha256'] == CODE_SHA256
         and witness['producer_model_version'] == point.VERSION and witness['producer_code_sha256'] == point.CODE_SHA256
         and all(witness[k] == v for k,v in point.FLAGS.items()) and raw(witness['source']) == raw(source)
         and witness['pending_page_sha256'] == pending, 'PROOF_HOLD: exact source-bound saved-stage witness required')
    for name in ('public_candidate_calculation_sha256','public_calculation_sha256','public_point_sha256'):
        base.reader._hash(witness[name])
    raw(witness)
    candidate = _candidate_saved(s, current, source, pending, witness['time_tolerance_seconds_exact'],
        witness['dense_derived'], witness['refinements'], meter, inputs=witness['inputs'], after_stage=witness['after_stage'])
    need(candidate['calculation_sha256'] == witness['public_candidate_calculation_sha256'],
         'PROOF_HOLD: full public candidate hash differs from actual saved observations')
    result = _point_saved(s, current, source, pending, witness['inputs'], candidate, witness['after_stage'], meter)
    need(result['calculation_sha256'] == witness['public_calculation_sha256']
         and digest(result) == witness['public_point_sha256'] and raw(result['work']) == raw(witness['work']),
         'PROOF_HOLD: full public point, inner calculation or work identity differs')
    meter.fence('history_validation')
    return result


_SIGNATURE = point._signature(sys.modules[__name__])
