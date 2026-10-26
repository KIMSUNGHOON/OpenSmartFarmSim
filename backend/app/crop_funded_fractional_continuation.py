"""Fractional material-point checkpoints and original-grid RK4 continuation."""
from copy import deepcopy
from dataclasses import dataclass, field
from fractions import Fraction
from functools import wraps
from hashlib import sha256
import json
from math import isfinite, ulp
from pathlib import Path

from . import crop_funded_fractional_birth_point as birth
from . import crop_leaf_funded_birth_continuation as old
from .crop_morphology_artifact_io import MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical, _parse, _hash

VERSION = 'funded-fractional-original-grid-continuation-research-v1'
CHECKPOINT_VERSION = 'fractional-individual-leaf-checkpoint-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_CONTEXT_BYTES = 2*1024**2
MAX_CHECKPOINT_BYTES = 1024**2
POINT_FIELDS = {'schema_version', 'input_id', 'origin', 'policy', 'context_sha256',
                'checkpoint_sha256', 'at_elapsed_seconds_exact', 'model_floor_area', 'events'}
POINT_UNITS = {'structural_carbon': birth.point.MASS, 'growth_respiration': birth.point.MASS,
               'buffer_debit': birth.point.MASS, 'capacity_in': birth.point.numeric.CAPACITY,
               'sensible_in': birth.point.numeric.ENERGY}
F = Fraction.from_float
short = birth.short
_TOKEN = object()


class FractionalContinuationHold(ValueError):
    pass


def _public(fn):
    @wraps(fn)
    def checked(*a, **k):
        try:
            return fn(*a, **k)
        except FractionalContinuationHold:
            raise
        except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, ZeroDivisionError, RecursionError) as error:
            raise FractionalContinuationHold(str(error)) from None
    return checked


def _digest(v): return sha256(_canonical(v)).hexdigest()
def _q(v, unit): return {'value': v, 'unit': unit}
def _exact(v): return birth.candidate.event._rational(v, 's')
def _seconds(v): birth.stem._elapsed(v); return birth.stem._fraction(v)
def _round(v): return birth.candidate._rounded(v)


def _pins():
    return {**birth._pins(), 'backend/app/crop_funded_fractional_continuation.py': sha256(Path(__file__).read_bytes()).hexdigest()}


@dataclass(frozen=True)
class Context:
    _raw: bytes = field(repr=False)
    _leaf_directory: Path = field(repr=False)
    _stem_directory: Path = field(repr=False)
    _access: object = field(repr=False)
    _profiles: tuple = field(repr=False)
    sha256: str
    _token: object = field(repr=False)

    @property
    def value(self): return json.loads(self._raw)


@dataclass(frozen=True)
class Checkpoint:
    _raw: bytes = field(repr=False)
    sha256: str
    context_sha256: str
    _token: object = field(repr=False)

    @property
    def value(self): return json.loads(self._raw)


def _original(leaf_directory, stem_directory, access, source):
    selection = source['candidate']['selection']
    with MorphologyBlobStore(leaf_directory, access) as store:
        raw = store.get(selection['leaf_root_sha256'], maximum=birth.leaf.MAX)
        m = _parse(raw, birth.leaf.MAX)
        inputs, root_p, _, root_seed, frames, _, raws = birth.leaf._graph(store, m)
        index = source['candidate']['source_root_certificate']['source_bracket']['left_frame_index']
        _need(type(index) is int and 0 <= index < len(frames), 'SOURCE_HOLD: bounded original source index required')
        _need(m['samples'][index]['checkpoint_sha256'] == source['candidate']['source_left_checkpoint_sha256'],
              'SOURCE_HOLD: original selected source checkpoint required')
        frame = frames[index]
        anchors = root_seed['evaluation']['curve_residuals'] if frame['context'] is None else frame['context']['seed']['anchors']
        history = [] if frame['context'] is None else frame['context']['history']
        _need(source['program'] == frame['program'] and source['anchors'] == anchors
              and source['past_event_ids'] == [e['event_id'] for row in history for e in row['inputs']['events']],
              'SOURCE_HOLD: original captured program/anchors/history required')
        _need(source['code_sha256'] == birth._pins() and all(m['source_rights'][k] is True for k in ('use', 'transform', 'display')),
              'SOURCE_HOLD: original point code/grants required')
        profiles = tuple(kind(raws[name]) for name, kind in (
            ('growth_profile', birth.candidate.event.Growth), ('cohort_profile', birth.candidate.event.Cohort),
            ('transport_profile', birth.candidate.event.Transport), ('exchange_profile', birth.candidate.event.Exchange)))
        _need(source['profile_sha256'] == dict(zip(('growth_profile','cohort_profile','transport_profile','exchange_profile'),
            (v.sha256 for v in profiles), strict=True)), 'PROFILE_HOLD: original captured profile identities required')
        root_sample = {'state': root_seed['state'], 'derived': short._view(root_seed['evaluation'])['joint']['derived']}
        book = {'root_sample': root_sample, 'root_leaf_ids': [v['leaf_id'] for v in root_p['leaves']],
                'left_checkpoint': frame['checkpoint'], 'source_birth_bases': frame['creation_bases'],
                'grid_step_seconds': float(inputs['step_seconds']), 'grid_step_count': inputs['step_count']}
        birth.leaf._fence(store, m, {**raws, 'root': raw})
    sm = birth.stem.read_rational_morphology_manifest(stem_directory, access, selection['stem_root_sha256'])
    _need(all(sm['program_rights'][k] is True for k in ('use', 'display')), 'RIGHTS_HOLD: original stem grants required')
    return book, profiles


def _sample(at, state, rhs, anchors):
    return {**birth._snapshot(at, state, rhs, anchors), 'schema_version': 'fractional-individual-leaf-state-v1'}


def _prefix(previous, sample, sequence, phase):
    return _digest({'previous': previous, 'model_version': VERSION, 'sample': sample,
                    'event_sequence': sequence, 'phase': phase})


def _sum_rows(units, *blocks):
    return {name: _q(_round(sum((F(b.get(name, _q(0., unit))['value']) for b in blocks), Fraction(0))), unit)
            for name, unit in units.items()}


def _zero(p): return {k: _q(0., unit) for k, unit in short._flux_units(p).items()}


def _record(inputs, leaves, receipts, flows, balances, at, branch_air, lifetime_air, before_hash, sample, p):
    return {'inputs': deepcopy(inputs), 'input_sha256': _digest(inputs), 'at': deepcopy(at),
            'new_leaves': deepcopy(leaves), 'receipts': deepcopy(receipts), 'point_flows': deepcopy(flows),
            'balances': deepcopy(balances), 'branch_air_integral_at_birth': branch_air,
            'lifetime_air_integral_at_birth': lifetime_air, 'before_checkpoint_sha256': before_hash,
            'after_sample_sha256': _digest(sample), 'after_program_sha256': _digest(p)}


def _context(context, *, sources=True):
    _need(type(context) is Context and context._token is _TOKEN, 'CONTEXT_HOLD: prepared fractional continuation required')
    _need(type(context._raw) is bytes and 0 < len(context._raw) <= MAX_CONTEXT_BYTES
          and sha256(context._raw).hexdigest() == context.sha256, 'CONTEXT_HOLD: immutable context bytes required')
    data = _parse(context._raw, MAX_CONTEXT_BYTES)
    birth.point._closed(data, {'version', 'code_sha256', 'source', 'original', 'program', 'anchors', 'branch_initial',
                              'base_lifetime_transfers', 'base_prior_budgets', 'records', 'seed'})
    _need(_canonical(data) == context._raw and data['version'] == VERSION and data['code_sha256'] == _pins()
          and data['code_sha256']['backend/app/crop_funded_fractional_continuation.py'] == CODE_SHA256,
          'CODE_HOLD: original continuation identity required')
    source = data['source']; p = deepcopy(source['program']); ids = {v['leaf_id'] for v in p['leaves']}; events = set(source['past_event_ids'])
    birth.point._closed(source, {'version','candidate','program','anchors','past_event_ids','code_sha256','profile_sha256'})
    _need(source['version'] == birth.VERSION, 'CONTEXT_HOLD: original material-point source version required')
    records = data['records']; _need(type(records) is list and 1 <= len(records) <= 511, 'CAPACITY_HOLD: bounded nonempty point history required')
    previous = _seconds(source['candidate']['at']['elapsed_seconds_exact'])
    for i, row in enumerate(records):
        birth.point._closed(row, {'inputs', 'input_sha256', 'at', 'new_leaves', 'receipts', 'point_flows', 'balances',
            'branch_air_integral_at_birth', 'lifetime_air_integral_at_birth', 'before_checkpoint_sha256', 'after_sample_sha256', 'after_program_sha256'})
        v = row['inputs']; birth.point._closed(v, birth.FIELDS if i == 0 else POINT_FIELDS)
        _need(v['schema_version'] == ('funded-fractional-birth-point-input-v1' if i == 0 else 'fractional-continuation-birth-input-v1')
              and v['origin'] == 'synthetic' and v['policy'] == birth.point.POLICY and row['input_sha256'] == _digest(v), 'POINT_HOLD: original point input required')
        if i == 0:
            _need(v['context_sha256'] == _digest(source) and v['candidate_sha256'] == _digest(source['candidate']), 'POINT_HOLD: original prepared candidate required')
        for name in ('context_sha256',): _hash(v[name])
        if i > 0:
            _hash(v['checkpoint_sha256'])
            _need(v['checkpoint_sha256'] == row['before_checkpoint_sha256'], 'POINT_HOLD: original prior checkpoint required')
        _hash(row['before_checkpoint_sha256']); _hash(row['after_sample_sha256']); _hash(row['after_program_sha256'])
        at = _seconds(row['at']); _need(previous <= at and row['at'] == v['at_elapsed_seconds_exact'], 'TIME_HOLD: ordered original exact point times required'); previous = at
        _need(birth.point._quantity(v['model_floor_area'], 'm2_floor') == p['model_floor_area']['value'], 'BASIS_HOLD: original common floor required')
        _need(len(row['new_leaves']) == len(v['events']) == len(row['receipts']) and row['new_leaves'], 'POINT_HOLD: complete nonempty point leaves required')
        for event, new_leaf in zip(v['events'], row['new_leaves'], strict=True):
            old._leaf_declaration(new_leaf, event['leaf'])
            _need(new_leaf['leaf_id'] not in ids and event['event_id'] not in events, 'EVENT_HOLD: repeated leaf/event history')
            ids.add(new_leaf['leaf_id']); events.add(event['event_id'])
        old._history_units({'point_flows': row['point_flows'], 'balances': row['balances'], 'air_temperature_integral': row['lifetime_air_integral_at_birth']})
        _need(type(row['branch_air_integral_at_birth']) is float and isfinite(row['branch_air_integral_at_birth']), 'POINT_HOLD: finite captured branch clock required')
        p['leaves'].extend(deepcopy(row['new_leaves']))
    _need(p == data['program'] and len(p['leaves']) <= 512 and data['anchors'] == [*source['anchors'], *[_q(0., 'm2') for _ in range(len(p['leaves'])-len(source['program']['leaves']))]],
          'CONTEXT_HOLD: original appended program and anchors required')
    seed = data['seed']; birth.point._closed(seed, {'sample', 'branch_base_transfers', 'branch_step_count', 'output_cursor', 'output_prefix_sha256'})
    birth.point._closed(seed['sample'], {'schema_version','at','state','derived','curve_residuals','curve_invariant_changes'})
    _need(seed['sample']['schema_version'] == 'fractional-individual-leaf-state-v1'
          and seed['sample']['at']['time_origin_utc'] == source['candidate']['at']['time_origin_utc'], 'TIME_HOLD: original snapshot origin/schema required')
    birth.point._closed(seed['sample']['at'], {'time_origin_utc','elapsed_seconds_exact'})
    birth.leaf.stock._state(seed['sample']['state'], p)
    birth.leaf.stock._block(seed['sample']['derived'], birth.leaf.stock.DERIVED_UNITS, normalized=True)
    _need(_digest(seed['sample']) == records[-1]['after_sample_sha256'] and _digest(p) == records[-1]['after_program_sha256']
          and seed['sample']['at']['elapsed_seconds_exact'] == records[-1]['at'], 'CONTEXT_HOLD: original after-point seed required')
    _need(data['branch_initial']['state'] == source['candidate']['dense_candidate']['state']
          and data['branch_initial']['at'] == source['candidate']['at'], 'CONTEXT_HOLD: original branch initial state/time required')
    units = short._flux_units(p)
    birth.point._closed(seed['branch_base_transfers'], units)
    for name, unit in units.items(): old._captured_quantity(seed['branch_base_transfers'][name], unit)
    if len(records) == 1:
        _need(seed['branch_base_transfers'] == _zero(p) and seed['branch_step_count'] == 0,
              'CONTEXT_HOLD: original zero branch prefix required')
    dt = F(data['original']['grid_step_seconds']); duration = dt*data['original']['grid_step_count']; at = _seconds(seed['sample']['at']['elapsed_seconds_exact'])
    _need(0 <= at <= duration and type(seed['branch_step_count']) is int and seed['branch_step_count'] >= 0
          and type(seed['output_cursor']) is int and seed['output_cursor'] >= 0, 'TIME_HOLD: bounded source grid/cursor required')
    _hash(seed['output_prefix_sha256'])
    _need((data['original']['grid_step_count']-int(at//dt)+1)*(len(seed['sample']['state'])+2*len(p['leaves'])+8) <= 32768,
          'CAPACITY_HOLD: remaining source sample scalar budget exceeded')
    if sources:
        original, profiles = _original(context._leaf_directory, context._stem_directory, context._access, source)
        _need(original == data['original'] and [p.sha256 for p in profiles] == [p.sha256 for p in context._profiles], 'SOURCE_HOLD: original root/prefix/profiles required')
    return data


def _profiles(context):
    return dict(zip(('growth_profile', 'cohort_profile', 'transport_profile', 'exchange_profile'), context._profiles, strict=True))


def _seal_context(data, template, profiles):
    raw = _canonical(data); _need(len(raw) <= MAX_CONTEXT_BYTES, 'CAPACITY_HOLD: bounded fractional context required')
    context = Context(raw, template._leaf_directory, template._stem_directory, template._access, tuple(profiles), sha256(raw).hexdigest(), _TOKEN)
    _context(context)
    return context


def _point_totals(data, include_source=False):
    blocks = [row['point_flows'] for row in data['records']]
    if include_source: blocks.insert(0, data['original']['left_checkpoint'].get('point_totals', {}))
    return _sum_rows(POINT_UNITS, *blocks)


def _bases(data, lifetime):
    source = data['source']; dt = F(data['original']['grid_step_seconds']); rows = []
    if lifetime:
        for row in data['original']['source_birth_bases']:
            rows.append({'leaf_id': row['leaf_id'], 'age': row['thermal_age'], 'carbon': row['carbon'],
                         'at': dt*row['step_index'], 'air': row['air_temperature_integral']})
    else:
        p = source['program']; y = data['branch_initial']['state']; n = len(p['leaves']); at = _seconds(data['branch_initial']['at']['elapsed_seconds_exact'])
        rows = [{'leaf_id': leaf['leaf_id'], 'age': y[107+i], 'carbon': y[107+2*n+i], 'at': at, 'air': 0.}
                for i, leaf in enumerate(p['leaves'])]
    for row in data['records']:
        rows.extend({'leaf_id': leaf['leaf_id'], 'age': 0., 'carbon': leaf['initial_carbon']['value'], 'at': _seconds(row['at']),
                     'air': row['lifetime_air_integral_at_birth' if lifetime else 'branch_air_integral_at_birth']} for leaf in row['new_leaves'])
    return rows


def _balances(data, sample, transfers, elapsed, steps, *, lifetime):
    p = data['program']; n = len(p['leaves']); first = data['original']['root_sample'] if lifetime else data['branch_initial']
    a, b = tuple(map(F, first['state'])), tuple(map(F, sample['state'])); n0 = (len(a)-107)//3
    t = {k: F(v['value']) for k, v in transfers.items()}; points = {k: F(v['value']) for k, v in _point_totals(data, lifetime).items()}
    ca = F(first['derived']['air_capacity']['value']); _need(ca == F(sample['derived']['air_capacity']['value']), 'BALANCE_HOLD: original air capacity required')
    lam = F(data['_latent']); ref = F(p['scenario']['parameters']['reference_temperature']['value'])
    carbon = lambda y, count: sum((y[0], y[1], *y[4:54], *y[107+2*count:]), Fraction(0))
    number = lambda y: sum(y[54:104], Fraction(0)); energy = lambda y: y[104]+ca*(y[105]-ref)+lam*y[106]
    du, da, dw = b[104]-a[104], ca*(b[105]-a[105]), b[106]-a[106]
    cap0, cap1 = F(first['derived']['canopy_capacity']['value']), F(sample['derived']['canopy_capacity']['value'])
    rows = {
        'carbohydrate': ((carbon(b,n)-carbon(a,n0), -t['photosynthesis'], *(t[k] for k in ('growth_respiration','maintenance_leaf','maintenance_stem','maintenance_fruit','removal_leaf','removal_stem','terminal_carbon')), points['growth_respiration']), carbon(a,n0), carbon(b,n), birth.point.MASS, 'whole_carbon'),
        'number': ((number(b)-number(a), -t['entry_number'], t['terminal_number']), number(a), number(b), 'fruits_equivalent/m2_floor', None),
        'canopy_sensible': ((du, -t['canopy_external'], t['sensible'], t['latent'], -t['incoming_heat'], t['outgoing_heat'], -points['sensible_in']), a[104], b[104], 'J/m2_floor', 'sensible'),
        'air_sensible': ((da, -t['air_external'], -t['sensible']), ca*(a[105]-ref), ca*(b[105]-ref), 'J/m2_floor', None),
        'vapor': ((dw, -t['vapor'], -t['external_vapor']), a[106], b[106], 'kg_water/m2_floor', None),
        'area_capacity': ((cap1-cap0, -t['capacity_in'], t['capacity_out'], -points['capacity_in']), cap0, cap1, 'J/m2_floor/K', 'capacity'),
        'reduced_energy': ((du, da, lam*dw, -t['canopy_external'], -t['air_external'], -lam*t['external_vapor'], -t['incoming_heat'], t['outgoing_heat'], -points['sensible_in']), energy(a), energy(b), 'J/m2_floor', 'sensible')}
    for i, base in enumerate(_bases(data, lifetime)):
        _need(base['leaf_id'] == p['leaves'][i]['leaf_id'], 'STATE_HOLD: original birth-basis order required')
        rows[f'leaf_age_{i}'] = ((b[107+i]-F(base['age']), -t['indoor_air_temperature_time']/86400, F(base['air'])/86400,
            F(p['leaves'][i]['base_temperature']['value'])*(elapsed-base['at'])/86400), F(base['age']), b[107+i], 'degC_day', None)
        rows[f'leaf_carbon_{i}'] = ((b[107+2*n+i]-F(base['carbon']), -t[f'leaf_{i}_inflow'], t[f'leaf_{i}_maintenance'], t[f'leaf_{i}_removal']), F(base['carbon']), b[107+2*n+i], birth.point.MASS, None)
    residuals, budgets = {}, {}
    for name, (terms, start, end, unit, point_key) in rows.items():
        scale = max(abs(start), abs(end), sum(map(abs, terms), Fraction(0)))
        budget = 64*(steps+1)*F(ulp(_round(scale)))
        if lifetime:
            budget += F(data['base_prior_budgets'].get(name, _q(0., unit))['value'])
        if point_key is not None:
            budget += sum((F(row['balances'][point_key]['budget']['value']) for row in data['records']), Fraction(0))
        budget += 64*F(ulp(_round(sum(map(abs, terms), Fraction(0)))))
        residual = sum(terms, Fraction(0)); _need(abs(residual) <= budget, 'BALANCE_HOLD: '+('lifetime ' if lifetime else 'branch ')+name)
        residuals[name], budgets[name] = _q(_round(residual), unit), _q(_round(budget), unit)
    return residuals, budgets


def _build(context, data, sample, segment, steps, prefix, cursor):
    p = data['program']; units = short._flux_units(p); branch = _sum_rows(units, data['seed']['branch_base_transfers'], segment)
    lifetime = _sum_rows(units, data['base_lifetime_transfers'], branch); elapsed = _seconds(sample['at']['elapsed_seconds_exact'])
    prepared = {**data, '_latent': context._profiles[-1].values['latent_heat']}; total_steps = data['seed']['branch_step_count']+steps
    br, bb = _balances(prepared, sample, branch, elapsed, total_steps, lifetime=False)
    gr, gb = _balances(prepared, sample, lifetime, elapsed, total_steps, lifetime=True)
    dt = F(data['original']['grid_step_seconds']); grid_index = int(elapsed//dt)
    return {'version': CHECKPOINT_VERSION, 'context_sha256': context.sha256, 'at': deepcopy(sample['at']),
        'grid_step_index': grid_index, 'segment_steps': steps, 'branch_steps': total_steps,
        'event_sequence': data['original']['left_checkpoint'].get('event_sequence', 0)+len(data['records']),
        'phase': 'after_birth' if steps == 0 else 'grid_endpoint', 'last_confirmed': deepcopy(sample),
        'output_cursor': cursor, 'output_prefix_sha256': prefix, 'segment_integrated_transfers': deepcopy(segment),
        'branch_integrated_transfers': branch, 'lifetime_integrated_transfers': lifetime,
        'branch_point_transfers': _point_totals(data), 'lifetime_point_transfers': _point_totals(data, True),
        'branch_balance_residuals': br, 'branch_balance_budgets': bb, 'global_balance_residuals': gr, 'global_balance_budgets': gb,
        'scope': 'software_research_only', 'G0_G4': 'not_assessed'}


def _seal(context, payload):
    raw = _canonical(payload); _need(len(raw) <= MAX_CHECKPOINT_BYTES, 'CAPACITY_HOLD: 1MiB fractional checkpoint required')
    return Checkpoint(raw, sha256(raw).hexdigest(), context.sha256, _TOKEN)


@_public
def prepare_context(*, point_context, inputs):
    source, _ = birth._context(point_context); result = birth.apply_fractional_births(context=point_context, inputs=inputs)
    original, profiles = _original(point_context._leaf_directory, point_context._stem_directory, point_context._access, source)
    before = {**result['before_sample'], 'schema_version': 'fractional-individual-leaf-state-v1'}
    after = {**result['after_sample'], 'schema_version': 'fractional-individual-leaf-state-v1'}
    p = result['after_program']; units = short._flux_units(p); partial = source['candidate']['dense_candidate']['partial_interval_transfers']
    baseline = _sum_rows(units, original['left_checkpoint']['integrated_transfers'], partial)
    prior = deepcopy(original['left_checkpoint'].get('global_balance_budgets', original['left_checkpoint']['balance_budgets']))
    for name, row in source['candidate']['dense_candidate']['local_ledgers'].items():
        quantity = prior.get(name, _q(0., row['budget_exact']['unit']))
        prior[name] = _q(_round(F(quantity['value'])+Fraction(int(row['budget_exact']['numerator']), int(row['budget_exact']['denominator']))), quantity['unit'])
    sequence = original['left_checkpoint'].get('event_sequence', 0)+1
    before_prefix = _prefix(original['left_checkpoint']['output_prefix_sha256'], before, sequence, 'before_birth')
    prefix = _prefix(before_prefix, after, sequence, 'after_birth')
    row = _record(result['inputs'], p['leaves'][len(source['program']['leaves']):], result['birth_receipts'],
        result['point_flows'], result['balances'], after['at']['elapsed_seconds_exact'], 0., baseline['indoor_air_temperature_time']['value'],
        source['candidate']['source_left_checkpoint_sha256'], after, p)
    data = {'version': VERSION, 'code_sha256': _pins(), 'source': source, 'original': original,
        'program': p, 'anchors': result['after_anchors'], 'branch_initial': before, 'base_lifetime_transfers': baseline,
        'base_prior_budgets': prior, 'records': [row], 'seed': {'sample': after, 'branch_base_transfers': _zero(p),
        'branch_step_count': 0, 'output_cursor': original['left_checkpoint']['output_cursor']+2, 'output_prefix_sha256': prefix}}
    context = _seal_context(data, point_context, profiles); start(context)
    return context


@_public
def context_bytes(context): _context(context); return context._raw


def _external(raw, expected, maximum):
    _hash(expected); _need(type(raw) is bytes and 0 < len(raw) <= maximum and sha256(raw).hexdigest() == expected, 'HASH_HOLD: trusted bounded raw bytes required')
    value = _parse(raw, maximum); _need(_canonical(value) == raw, 'FORMAT_HOLD: canonical bytes required'); return value


@_public
def restore_context(leaf_directory, stem_directory, access, *, raw_bytes, expected_sha256):
    data = _external(raw_bytes, expected_sha256, MAX_CONTEXT_BYTES)
    _, profiles = _original(leaf_directory, stem_directory, access, data['source'])
    template = Context(b'', Path(leaf_directory), Path(stem_directory), access, profiles, '', _TOKEN)
    return _seal_context(data, template, profiles)


@_public
def start(context):
    data = _context(context); seed = data['seed']
    return _seal(context, _build(context, data, seed['sample'], _zero(data['program']), 0, seed['output_prefix_sha256'], seed['output_cursor']))


@_public
def checkpoint_bytes(context, checkpoint):
    _context(context)
    _need(type(checkpoint) is Checkpoint and checkpoint._token is _TOKEN and checkpoint.context_sha256 == context.sha256
          and type(checkpoint._raw) is bytes and len(checkpoint._raw) <= MAX_CHECKPOINT_BYTES
          and sha256(checkpoint._raw).hexdigest() == checkpoint.sha256, 'CHECKPOINT_HOLD: original matching checkpoint required')
    return checkpoint._raw


def _validate(context, data, payload):
    p = data['program']; state = payload['last_confirmed']['state']; seed = data['seed']; steps = payload['segment_steps']
    birth.leaf.stock._state(state, p)
    birth.point._closed(payload['at'], {'time_origin_utc','elapsed_seconds_exact'})
    _need(payload['at']['time_origin_utc'] == seed['sample']['at']['time_origin_utc'], 'TIME_HOLD: original checkpoint origin required')
    birth.point._closed(payload['segment_integrated_transfers'], short._flux_units(p))
    for name, unit in short._flux_units(p).items(): old._captured_quantity(payload['segment_integrated_transfers'][name], unit)
    _need(type(steps) is int and steps >= 0, 'TIME_HOLD: bounded integer integration count required')
    dt = F(data['original']['grid_step_seconds']); seed_at = _seconds(seed['sample']['at']['elapsed_seconds_exact']); at = _seconds(payload['at']['elapsed_seconds_exact'])
    _need(at == (seed_at if steps == 0 else dt*(int(seed_at//dt)+steps)) and at <= dt*data['original']['grid_step_count'], 'TIME_HOLD: original grid remainder coordinate required')
    rates, rhs = short._evaluate(p, tuple(state), _profiles(context)); sample = _sample(payload['at'], state, rhs, data['anchors'])
    rebuilt = _build(context, data, sample, payload['segment_integrated_transfers'], steps, payload['output_prefix_sha256'], seed['output_cursor']+steps)
    _need(_canonical(rebuilt) == _canonical(payload), 'CHECKPOINT_HOLD: original current sample/clock/ledgers required')
    if steps == 0:
        _need(_canonical(sample) == _canonical(seed['sample']) and payload['segment_integrated_transfers'] == _zero(p)
              and payload['output_prefix_sha256'] == seed['output_prefix_sha256'], 'CHECKPOINT_HOLD: original point seed required')
    _hash(payload['output_prefix_sha256'])
    return tuple(state), rates, rhs


@_public
def restore_checkpoint(context, raw_bytes, *, expected_sha256):
    data = _context(context); value = _external(raw_bytes, expected_sha256, MAX_CHECKPOINT_BYTES)
    _validate(context, data, value)
    return _seal(context, value)


@_public
def advance_chunk(context, checkpoint, step_budget):
    _need(type(step_budget) is int and 1 <= step_budget <= 128, 'BUDGET_HOLD: 1..128 original-grid intervals required')
    data = _context(context); payload = json.loads(checkpoint_bytes(context, checkpoint)); state, rates, rhs = _validate(context, data, payload)
    p = data['program']; dt = F(data['original']['grid_step_seconds']); end = dt*data['original']['grid_step_count']; at = _seconds(payload['at']['elapsed_seconds_exact'])
    _need(at < end, 'TIME_HOLD: original source horizon exhausted')
    units = short._flux_units(p); totals = tuple(payload['segment_integrated_transfers'][k]['value'] for k in units)
    samples = []; failure = None; stage = 'initial'; profiles = _profiles(context); attempted = 0
    for _ in range(min(step_budget, data['original']['grid_step_count']-int(at//dt))):
        target = dt*(int(at//dt)+1); step = target-at
        try:
            stage = 'k2'; y2 = birth.candidate._combine(state, (rates,), (Fraction(1),), step/2); attempted += 1; k2, r2 = short._evaluate(p, y2, profiles)
            stage = 'k3'; y3 = birth.candidate._combine(state, (k2,), (Fraction(1),), step/2); attempted += 1; k3, r3 = short._evaluate(p, y3, profiles)
            stage = 'k4'; y4 = birth.candidate._combine(state, (k3,), (Fraction(1),), step); attempted += 1; k4, r4 = short._evaluate(p, y4, profiles)
            stage = 'endpoint'; candidate_state = birth.candidate._combine(state, (rates,k2,k3,k4), birth.candidate.RK4_WEIGHTS, step)
            cumulative = birth.candidate._combine(totals, (short._flux(p,state,rhs), short._flux(p,y2,r2), short._flux(p,y3,r3), short._flux(p,y4,r4)), birth.candidate.RK4_WEIGHTS, step)
            attempted += 1; new_rates, last = short._evaluate(p, candidate_state, profiles)
            at_record = {'time_origin_utc': payload['at']['time_origin_utc'], 'elapsed_seconds_exact': _exact(target)}
            sample = _sample(at_record, candidate_state, last, data['anchors']); prefix = _prefix(payload['output_prefix_sha256'], sample, payload['event_sequence'], 'grid_endpoint')
            stage = 'ledgers'; block = {k: _q(v, unit) for (k,unit),v in zip(units.items(),cumulative,strict=True)}
            new_payload = _build(context,data,sample,block,payload['segment_steps']+1,prefix,payload['output_cursor']+1)
            _seal(context,new_payload)
            state,rates,rhs,totals,at,payload = candidate_state,new_rates,last,cumulative,target,new_payload; samples.append(sample)
        except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, ZeroDivisionError, RecursionError) as error:
            failure = {'reason': str(error), 'stage': stage, 'target_elapsed_seconds_exact': _exact(target)}; break
    _context(context)
    return {'status': 'hold' if failure else 'completed' if at == end else 'yielded', 'hold': failure,
        'samples': samples, 'checkpoint': None if failure else _seal(context,payload), 'last_confirmed': deepcopy(payload),
        'checkpoint_validation_RHS_evaluations': 1, 'new_RHS_evaluations': attempted,
        'scope': 'software_research_only', 'G0_G4': 'not_assessed'}


@_public
def adopt_births(context, checkpoint, inputs):
    data = _context(context); payload = json.loads(checkpoint_bytes(context, checkpoint)); state, _, first = _validate(context,data,payload)
    raw = _canonical(inputs); v = _parse(raw,MAX_CONTEXT_BYTES); birth.point._closed(v,POINT_FIELDS)
    short.old.leaf_area._identifier(v['input_id'])
    _need(v['schema_version']=='fractional-continuation-birth-input-v1' and v['origin']=='synthetic' and v['policy']==birth.point.POLICY,
          'POLICY_HOLD: explicit fractional continuation point required')
    _need(v['context_sha256']==context.sha256 and v['checkpoint_sha256']==checkpoint.sha256
          and v['at_elapsed_seconds_exact']==payload['at']['elapsed_seconds_exact'], 'POINT_HOLD: original current checkpoint/time required')
    _need(birth.point._quantity(v['model_floor_area'],'m2_floor')==data['program']['model_floor_area']['value'], 'BASIS_HOLD: original common floor required')
    used = [*data['source']['past_event_ids'], *[event['event_id'] for row in data['records'] for event in row['inputs']['events']]]
    values = birth._jump(data['program'],list(state),first,data['anchors'],_profiles(context),v['events'],used)
    p,after,_,rhs,anchors,receipts,flows,balances = values; sample = _sample(payload['at'],after,rhs,anchors)
    row = _record(v,p['leaves'][len(data['program']['leaves']):],receipts,flows,balances,v['at_elapsed_seconds_exact'],
        payload['branch_integrated_transfers']['indoor_air_temperature_time']['value'],payload['lifetime_integrated_transfers']['indoor_air_temperature_time']['value'],checkpoint.sha256,sample,p)
    data['records'].append(row); data['program'],data['anchors'] = p,anchors
    data['seed'] = {'sample':sample,'branch_base_transfers':_sum_rows(short._flux_units(p),payload['branch_integrated_transfers']),
        'branch_step_count':payload['branch_steps'],'output_cursor':payload['output_cursor']+1,
        'output_prefix_sha256':_prefix(payload['output_prefix_sha256'],sample,payload['event_sequence']+1,'after_birth')}
    new_context = _seal_context(data,context,context._profiles); start(new_context)
    return new_context
