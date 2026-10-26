"""Funded topology and shared-stage resume; crop-leaf-funded-birth-continuation-v1.md."""
from copy import deepcopy
from dataclasses import dataclass, field
from fractions import Fraction
from functools import wraps
from hashlib import sha256
import json
from math import isfinite, ulp
from pathlib import Path

from . import crop_leaf_funded_birth_point as point

parent = point.resume
short = parent.short
numeric = short.numeric
VERSION = 'leaf-funded-birth-continuation-research-v1'
CHECKPOINT_VERSION = 'funded-individual-leaf-continuation-checkpoint-v1'
CONTEXT_VERSION = 'funded-individual-leaf-context-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
MAX_CHECKPOINT_BYTES = 1024**2
_TOKEN = object()


class FundedContinuationHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise FundedContinuationHold(reason)


def _public(fn):
    @wraps(fn)
    def checked(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except FundedContinuationHold:
            raise
        except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, ZeroDivisionError, RecursionError) as error:
            raise FundedContinuationHold(str(error) if isinstance(error, ValueError)
                                         else 'INPUT_HOLD: invalid funded continuation input') from None
    return checked


def _canonical(v):
    raw = parent._canonical(v)
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: 2MiB funded context/response required')
    return raw


def _hash(v):
    return sha256(_canonical(v)).hexdigest()


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256, 'CODE_HOLD: original funded engine required')
    point._fence()


def _exact(index, dt):
    value = Fraction.from_float(dt)*index
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'unit': 's'}


def _identity(root):
    _fence()
    return {'version': VERSION, 'code_sha256': CODE_SHA256, 'point_code_sha256': point.CODE_SHA256,
            'clock_code_sha256': point.CLOCK_CODE_SHA256, 'root_identity': parent._identity(root._profiles)}


@dataclass(frozen=True)
class Context:
    _root: parent.Context = field(repr=False)
    _program: bytes = field(repr=False)
    _seed: bytes = field(repr=False)
    _history: bytes = field(repr=False)
    _manifest: bytes = field(repr=False)
    root_sha256: str
    _token: object = field(repr=False)

    @property
    def manifest(self): return json.loads(self._manifest)

    @property
    def program(self): return json.loads(self._program)

    @property
    def point_history(self): return json.loads(self._history)


def _root_bases(p, seed):
    n = len(p['leaves']); y = seed['state']
    return [{'leaf_id': leaf['leaf_id'], 'step_index': 0, 'thermal_age': y[107+i],
             'carbon': y[107+2*n+i], 'air_temperature_integral': 0.}
            for i, leaf in enumerate(p['leaves'])]


def _captured_quantity(row, unit):
    point._closed(row, {'value', 'unit'})
    _need(row['unit'] == unit and type(row['value']) is float and isfinite(row['value']),
          'CONTEXT_HOLD: finite captured float64 quantity/unit required')


def _history_units(record):
    units = {'structural_carbon': point.MASS, 'growth_respiration': point.MASS,
             'buffer_debit': point.MASS, 'capacity_in': numeric.CAPACITY, 'sensible_in': numeric.ENERGY}
    point._closed(record['point_flows'], units)
    for name, unit in units.items():
        _captured_quantity(record['point_flows'][name], unit)
        _need(name == 'sensible_in' or record['point_flows'][name]['value'] > 0,
              'CONTEXT_HOLD: positive captured structural transfer required')
    balance_units = {'buffer': point.MASS, 'new_stock': point.MASS, 'whole_carbon': point.MASS,
                     'sensible': numeric.ENERGY, 'capacity': numeric.CAPACITY}
    point._closed(record['balances'], balance_units)
    for name, unit in balance_units.items():
        balance = record['balances'][name]; point._closed(balance, {'residual', 'budget'})
        for row in balance.values(): _captured_quantity(row, unit)
        _need(balance['budget']['value'] >= 0 and abs(balance['residual']['value']) <= balance['budget']['value'],
              'CONTEXT_HOLD: original point balance required')
    _need(type(record['air_temperature_integral']) is float and isfinite(record['air_temperature_integral']),
          'CONTEXT_HOLD: captured air clock integral required')


def _leaf_declaration(leaf, declared):
    units = {**short.old.LEAF_UNITS, **short.STOCK_FIELDS}
    for row in (leaf, declared): point._closed(row, {'leaf_id', 'curve', *units})
    short.old.leaf_area._identifier(leaf['leaf_id'])
    for name, unit in units.items():
        _captured_quantity(leaf[name], unit)
        _need(leaf[name]['value'] == point._quantity(declared[name], unit), 'CONTEXT_HOLD: original new leaf declaration required')
    _need(leaf['thermal_age']['value'] == 0 and leaf['initial_carbon']['value'] > 0
          and leaf['initial_area']['value'] > 0 and leaf['sink_weight']['value'] >= 0
          and leaf['carbon_removal']['value'] >= 0, 'CONTEXT_HOLD: supported captured birth leaf required')
    curve_units = {'maximum_area': 'm2', 'steepness': '1/degC_day', 'inflection_age': 'degC_day'}
    for curve in (leaf['curve'], declared['curve']):
        point._closed(curve, {'profile_id', 'origin', 'values'}); point._closed(curve['values'], curve_units)
    _need(leaf['curve']['profile_id'] == declared['curve']['profile_id']
          and leaf['curve']['origin'] == declared['curve']['origin'] == 'synthetic', 'CONTEXT_HOLD: original curve identity required')
    short.old.leaf_area._identifier(leaf['curve']['profile_id'])
    for name, unit in curve_units.items():
        _captured_quantity(leaf['curve']['values'][name], unit)
        value = point._quantity(declared['curve']['values'][name], unit)
        _need(value == leaf['curve']['values'][name]['value'] and (value >= 0 if name == 'inflection_age' else value > 0),
              'CONTEXT_HOLD: supported captured curve required')


def _capture(root, result, anchors, bases, history):
    p = result['after_program']; before = result['before_checkpoint']; count = len(result['inputs']['events'])
    history = [*deepcopy(history), {'inputs': result['inputs'], 'calculation_sha256': result['calculation_sha256'],
               'after_sample_sha256': _hash(result['after_sample']), 'new_leaves': deepcopy(p['leaves'][-count:]),
               'point_flows': result['point_flows'], 'balances': result['balances'],
               'air_temperature_integral': before['integrated_transfers']['indoor_air_temperature_time']['value']}]
    totals = {name: deepcopy(before['integrated_transfers'].get(name, numeric._q(0., unit)))
              for name, unit in short._flux_units(p).items()}
    new_bases = [{'leaf_id': leaf['leaf_id'], 'step_index': before['step_index'], 'thermal_age': 0.,
                  'carbon': leaf['initial_carbon']['value'],
                  'air_temperature_integral': history[-1]['air_temperature_integral']}
                 for leaf in p['leaves'][-count:]]
    seed = {'last_confirmed': result['after_sample'], 'before_checkpoint': before,
            'anchors': [*deepcopy(anchors), *(numeric._q(0., 'm2') for _ in new_bases)],
            'birth_bases': [*deepcopy(bases), *new_bases], 'base_transfers': totals}
    parts = {'program': _canonical(p), 'seed': _canonical(seed), 'history': _canonical(history)}
    root_manifest = root.manifest
    manifest = {'version': CONTEXT_VERSION, 'identity': _identity(root), 'root_context_sha256': root.root_sha256,
                'parent_context_sha256': result['context_sha256'], 'parent_checkpoint_sha256': result['checkpoint_sha256'],
                **{name+'_sha256': sha256(raw).hexdigest() for name, raw in parts.items()},
                'numerical': {**root_manifest['numerical'], 'event_global_step_index': before['step_index']},
                'state_layout': short._layout(p)}
    raw = _canonical(manifest)
    context = Context(root, parts['program'], parts['seed'], parts['history'], raw, sha256(raw).hexdigest(), _TOKEN)
    _context(context); context_bytes(context)
    return context


def _context(context):
    _need(type(context) is Context and context._token is _TOKEN, 'CONTEXT_HOLD: prepared funded context required')
    _fence()
    original, original_seed, root_manifest = parent._context(context._root)
    parts = (context._program, context._seed, context._history, context._manifest)
    _need(all(type(x) is bytes for x in parts) and sum(map(len, parts)) <= MAX_BYTES,
          'CAPACITY_HOLD: bounded immutable funded context required')
    p, seed, history, m = map(json.loads, parts)
    point._closed(m, {'version', 'identity', 'root_context_sha256', 'parent_context_sha256',
                     'parent_checkpoint_sha256', 'program_sha256', 'seed_sha256', 'history_sha256', 'numerical', 'state_layout'})
    point._closed(seed, {'last_confirmed', 'before_checkpoint', 'anchors', 'birth_bases', 'base_transfers'})
    _need(_canonical(m) == context._manifest and _hash(m) == context.root_sha256
          and m['identity'] == _identity(context._root) and m['version'] == CONTEXT_VERSION
          and m['root_context_sha256'] == context._root.root_sha256, 'CONTEXT_HOLD: changed identity/root')
    for name, raw in zip(('program', 'seed', 'history'), parts[:3], strict=True):
        _need(sha256(raw).hexdigest() == m[name+'_sha256'] and _canonical(json.loads(raw)) == raw,
              'CONTEXT_HOLD: changed captured '+name)
    _need(type(history) is list and 1 <= len(history) <= 511, 'CONTEXT_HOLD: bounded nonempty birth history required')
    event_ids = set(); leaves = deepcopy(original['leaves']); bases = _root_bases(original, original_seed)
    previous = 0
    for record in history:
        point._closed(record, {'inputs', 'calculation_sha256', 'after_sample_sha256', 'new_leaves',
                              'point_flows', 'balances', 'air_temperature_integral'})
        _history_units(record)
        v = record['inputs']; point._closed(v, point.FIELDS)
        _need(v['schema_version'] == 'leaf-funded-birth-point-input-v1' and v['origin'] == 'synthetic'
              and v['policy'] == point.POLICY and parent._digest(record['calculation_sha256'])
              and parent._digest(record['after_sample_sha256']), 'CONTEXT_HOLD: original point scope/hashes required')
        _need(point._quantity(v['model_floor_area'], 'm2_floor') == original['model_floor_area']['value'],
              'CONTEXT_HOLD: original point floor required')
        step = point.clock._seconds(v['at_elapsed_seconds_exact'])/Fraction.from_float(root_manifest['numerical']['step_seconds'])
        _need(step.denominator == 1 and previous <= step <= root_manifest['numerical']['step_count'],
              'CONTEXT_HOLD: ordered original-grid events required')
        previous = int(step)
        _need(len(record['new_leaves']) == len(v['events']) and record['new_leaves'], 'CONTEXT_HOLD: nonempty point leaves required')
        for event, leaf in zip(v['events'], record['new_leaves'], strict=True):
            point._closed(event, {'event_id', 'attachment_internode_id', 'incoming_temperature', 'leaf'})
            _leaf_declaration(leaf, event['leaf'])
            numeric._temperature(point._quantity(event['incoming_temperature'], 'degC'))
            for key in ('event_id', 'attachment_internode_id'):
                short.old.leaf_area._identifier(event[key])
            _need(event['event_id'] not in event_ids and event['leaf']['leaf_id'] == leaf['leaf_id'], 'EVENT_HOLD: repeated event or changed leaf')
            event_ids.add(event['event_id'])
            bases.append({'leaf_id': leaf['leaf_id'], 'step_index': int(step), 'thermal_age': 0.,
                          'carbon': leaf['initial_carbon']['value'], 'air_temperature_integral': record['air_temperature_integral']})
        leaves.extend(record['new_leaves'])
    expected = {**original, 'leaves': leaves}
    _need(_canonical(p) == _canonical(expected) and 1 <= len(leaves) <= 512 and len({x['leaf_id'] for x in leaves}) == len(leaves),
          'CONTEXT_HOLD: original ordered program and unique appended leaves required')
    _need(seed['birth_bases'] == bases and seed['anchors'] == [*original_seed['evaluation']['curve_residuals'],
          *(numeric._q(0., 'm2') for _ in range(len(leaves)-len(original['leaves'])))], 'CONTEXT_HOLD: original anchors/birth bases required')
    before = seed['before_checkpoint']; after = seed['last_confirmed']
    _need(type(after['step_index']) is int and type(after['elapsed_seconds']) is float
          and type(after['state']) is list and len(after['state']) == 107+3*len(leaves)
          and all(type(v) is float and isfinite(v) for v in after['state']), 'CONTEXT_HOLD: finite captured state required')
    _need(_hash(before) == m['parent_checkpoint_sha256'] and before['context_sha256'] == m['parent_context_sha256']
          and _hash(after) == history[-1]['after_sample_sha256'] and after['step_index'] == before['step_index'] == previous
          and after['elapsed_seconds'] == before['last_confirmed']['elapsed_seconds'], 'CONTEXT_HOLD: original point coordinate required')
    _need(_canonical(m['numerical']) == _canonical({**root_manifest['numerical'], 'event_global_step_index': previous})
          and m['state_layout'] == short._layout(p), 'CONTEXT_HOLD: original grid/layout required')
    expected_totals = {name: before['integrated_transfers'].get(name, numeric._q(0., unit)) for name, unit in short._flux_units(p).items()}
    _need(_canonical(seed['base_transfers']) == _canonical(expected_totals), 'CONTEXT_HOLD: original continuous prefix required')
    for name, unit in short._flux_units(p).items(): _captured_quantity(seed['base_transfers'][name], unit)
    remaining = root_manifest['numerical']['step_count']-previous
    _need((remaining+1)*(len(after['state'])+2*len(leaves)+8) <= 32768, 'CAPACITY_HOLD: remaining sample scalar budget exceeded')
    return p, seed, m


@_public
def prepare_context(*, parent_context, raw_parent_checkpoint, expected_parent_sha256, inputs):
    original, seed, _ = parent._context(parent_context)
    result = point.apply_births(context=parent_context, raw_checkpoint=raw_parent_checkpoint,
                               expected_sha256=expected_parent_sha256, inputs=inputs)
    return _capture(parent_context, result, seed['evaluation']['curve_residuals'], _root_bases(original, seed), [])


@_public
def context_bytes(context):
    p, seed, manifest = _context(context)
    return _canonical({'program': p, 'seed': seed, 'history': context.point_history, 'manifest': manifest})


def _parse(raw, expected_sha256, limit):
    _need(type(raw) is bytes and 0 < len(raw) <= limit and parent._digest(expected_sha256)
          and sha256(raw).hexdigest() == expected_sha256, 'CHECKPOINT_HOLD: trusted bounded raw digest required')
    def pairs(items):
        value = {}
        for k, v in items:
            _need(k not in value, 'CHECKPOINT_HOLD: duplicate JSON key')
            value[k] = v
        return value
    def constant(v): raise FundedContinuationHold('CHECKPOINT_HOLD: nonfinite JSON constant')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    _need(_canonical(value) == raw, 'CHECKPOINT_HOLD: canonical bytes required')
    return value


@_public
def restore_context(*, root_context, raw_bytes, expected_sha256):
    v = _parse(raw_bytes, expected_sha256, MAX_BYTES)
    _need(type(v) is dict and set(v) == {'program', 'seed', 'history', 'manifest'}, 'CONTEXT_HOLD: closed snapshot required')
    context = Context(root_context, _canonical(v['program']), _canonical(v['seed']), _canonical(v['history']),
                      _canonical(v['manifest']), _hash(v['manifest']), _TOKEN)
    _context(context)
    return context


def _point_totals(context):
    history = context.point_history
    return {name: numeric._q(point._rounded(sum((Fraction.from_float(row['point_flows'][name]['value'])
            for row in history), Fraction(0))), quantity['unit'])
            for name, quantity in history[0]['point_flows'].items()}


def _lifetime(p, seed, totals):
    return {name: numeric._q(numeric._sum(seed['base_transfers'][name]['value'], value), unit)
            for (name, unit), value in zip(short._flux_units(p).items(), totals, strict=True)}


def _segment_balances(context, p, seed, state, totals, sample, local):
    first = seed['last_confirmed']; initial = first['state']; dt = context.manifest['numerical']['step_seconds']
    latent = context._root._profiles[-1].values['latent_heat']
    views = [{'joint': {'derived': item['derived']}} for item in (first, sample)]
    residuals, budgets = short.old._balances(p, short._project(p, initial), short._project(p, state),
            totals[:21], *views, local, local*dt, latent)
    n = len(p['leaves'])
    for i in range(n):
        a, b = initial[107+2*n+i], state[107+2*n+i]; g, maintenance, removal = totals[21+3*i:24+3*i]
        terms = (numeric._sum(b, -a), -g, maintenance, removal)
        residual = numeric._sum(*terms)
        budget = numeric._multiply(64*(local+1), ulp(max(abs(a), abs(b), numeric._sum(*map(abs, terms)))))
        _need(abs(residual) <= budget, 'BALANCE_HOLD: individual segment carbon')
        name = 'leaf_carbon_'+str(i)
        residuals[name], budgets[name] = numeric._q(residual, point.MASS), numeric._q(budget, point.MASS)
    return residuals, budgets


def _global_balances(context, p, seed, state, lifetime, sample, segment_budgets, index):
    original, root_seed, _ = parent._context(context._root)
    initial = root_seed['state']; n0 = len(original['leaves']); n = len(p['leaves'])
    first = short._view(root_seed['evaluation'])['joint']['derived']; last = sample['derived']
    ca = first['air_capacity']['value']; latent = context._root._profiles[-1].values['latent_heat']
    _need(ca == last['air_capacity']['value'], 'BALANCE_HOLD: original air capacity required')
    t = {k: v['value'] for k, v in lifetime.items()}; points = _point_totals(context)
    point_value = lambda name: points[name]['value']
    carbon_terms = (state[0], state[1], *state[4:54], *state[107+2*n:], -initial[0], -initial[1],
                   *(-v for v in initial[4:54]), *(-v for v in initial[107+2*n0:]), -t['photosynthesis'],
                   *(t[k] for k in ('growth_respiration', 'maintenance_leaf', 'maintenance_stem', 'maintenance_fruit',
                                    'removal_leaf', 'removal_stem', 'terminal_carbon')), point_value('growth_respiration'))
    number = (*state[54:104], *(-v for v in initial[54:104]), -t['entry_number'], t['terminal_number'])
    du = (state[104], -initial[104]); da = numeric._multiply(ca, numeric._sum(state[105], -initial[105]))
    dw = numeric._sum(state[106], -initial[106])
    sensible = (*du, -t['canopy_external'], t['sensible'], t['latent'], -t['incoming_heat'],
                t['outgoing_heat'], -point_value('sensible_in'))
    air = (da, -t['air_external'], -t['sensible'])
    vapor = (state[106], -initial[106], -t['vapor'], -t['external_vapor'])
    capacity = (last['canopy_capacity']['value'], -first['canopy_capacity']['value'],
                -t['capacity_in'], t['capacity_out'], -point_value('capacity_in'))
    reduced = (*du, da, numeric._multiply(latent, dw), -t['canopy_external'], -t['air_external'],
               -numeric._multiply(latent, t['external_vapor']), -t['incoming_heat'], t['outgoing_heat'],
               -point_value('sensible_in'))
    rows = {'carbohydrate': (carbon_terms, point.MASS, 'whole_carbon'),
            'number': (number, 'fruits_equivalent/m2_floor', None),
            'canopy_sensible': (sensible, numeric.ENERGY, 'sensible'),
            'air_sensible': (air, numeric.ENERGY, None), 'vapor': (vapor, 'kg_water/m2_floor', None),
            'area_capacity': (capacity, numeric.CAPACITY, 'capacity'),
            'reduced_energy': (reduced, numeric.ENERGY, 'sensible')}
    dt = context.manifest['numerical']['step_seconds']
    for i, base in enumerate(seed['birth_bases']):
        duration = numeric._multiply(index-base['step_index'], dt)
        rows['leaf_age_'+str(i)] = ((state[107+i], -base['thermal_age'],
            -numeric._divide(t['indoor_air_temperature_time'], 86400),
            numeric._divide(base['air_temperature_integral'], 86400),
            numeric._divide(numeric._multiply(p['leaves'][i]['base_temperature']['value'], duration), 86400)), 'degC_day', None)
        rows['leaf_carbon_'+str(i)] = ((state[107+2*n+i], -base['carbon'], -t[f'leaf_{i}_inflow'],
                                      t[f'leaf_{i}_maintenance'], t[f'leaf_{i}_removal']), point.MASS, None)
    before = seed['before_checkpoint']
    prior = before.get('global_balance_budgets', before['balance_budgets'])
    point_budgets = context.point_history[-1]['balances']
    residuals, budgets = {}, {}
    for name, (terms, unit, event_key) in rows.items():
        aggregation = numeric._multiply(64, ulp(numeric._sum(*map(abs, terms))))
        budget = numeric._sum(prior.get(name, numeric._q(0., unit))['value'], segment_budgets[name]['value'], aggregation,
                              0. if event_key is None else point_budgets[event_key]['budget']['value'])
        residual = numeric._sum(*terms)
        _need(abs(residual) <= budget, 'GLOBAL_BALANCE_HOLD: '+name)
        residuals[name], budgets[name] = numeric._q(residual, unit), numeric._q(budget, unit)
    return residuals, budgets


@dataclass(frozen=True)
class Checkpoint:
    _raw: bytes = field(repr=False)
    sha256: str
    context_sha256: str
    _token: object = field(repr=False)

    @property
    def value(self): return json.loads(self._raw)


def _seal(context, payload):
    _fence()
    raw = _canonical(payload)
    _need(len(raw) <= MAX_CHECKPOINT_BYTES, 'CAPACITY_HOLD: 1MiB funded checkpoint required')
    return Checkpoint(raw, sha256(raw).hexdigest(), context.root_sha256, _TOKEN)


def _build(context, p, seed, m, sample, totals, prefix):
    index = sample['step_index']; local = index-m['numerical']['event_global_step_index']
    lifetime = _lifetime(p, seed, totals)
    residuals, budgets = _segment_balances(context, p, seed, sample['state'], totals, sample, local)
    gr, gb = _global_balances(context, p, seed, sample['state'], lifetime, sample, budgets, index)
    return {'version': CHECKPOINT_VERSION, 'context_sha256': context.root_sha256,
            'step_index': index, 'segment_step_index': local, 'event_sequence': len(context.point_history),
            'phase': 'after_birth' if local == 0 else 'funded_birth_interval',
            'at_elapsed_seconds_exact': _exact(index, m['numerical']['step_seconds']),
            'last_confirmed': deepcopy(sample), 'output_cursor': seed['before_checkpoint']['output_cursor']+1+local,
            'output_prefix_sha256': prefix, 'integrated_transfers': lifetime,
            'segment_integrated_transfers': {name: numeric._q(v, unit) for (name, unit), v in
                zip(short._flux_units(p).items(), totals, strict=True)},
            'point_history_sha256': m['history_sha256'], 'point_totals': _point_totals(context),
            'balance_residuals': residuals, 'balance_budgets': budgets,
            'global_balance_residuals': gr, 'global_balance_budgets': gb,
            'scope': 'software_research_only', 'G0_G4': 'not_assessed'}


def _prefix(previous, sample, sequence, phase):
    return _hash({'previous': previous, 'sample': sample, 'event_sequence': sequence, 'phase': phase})


def _initial(context, p, seed, m):
    sample = seed['last_confirmed']
    prefix = _prefix(seed['before_checkpoint']['output_prefix_sha256'], sample, len(context.point_history), 'after_birth')
    return _build(context, p, seed, m, sample, (0.,)*len(short._flux_units(p)), prefix)


@_public
def start(context):
    p, seed, m = _context(context)
    return _seal(context, _initial(context, p, seed, m))


@_public
def checkpoint_bytes(context, checkpoint):
    _context(context)
    _need(type(checkpoint) is Checkpoint and checkpoint._token is _TOKEN and checkpoint.context_sha256 == context.root_sha256
          and type(checkpoint._raw) is bytes and 0 < len(checkpoint._raw) <= MAX_CHECKPOINT_BYTES
          and sha256(checkpoint._raw).hexdigest() == checkpoint.sha256, 'CHECKPOINT_HOLD: immutable matching funded checkpoint required')
    return checkpoint._raw


def _validate(context, payload, p, seed, m):
    initial = _initial(context, p, seed, m)
    _need(type(payload) is dict and set(payload) == set(initial), 'CHECKPOINT_HOLD: closed funded checkpoint required')
    static = {'version', 'context_sha256', 'event_sequence', 'point_history_sha256', 'point_totals', 'scope', 'G0_G4'}
    _need(_canonical({k: payload[k] for k in static}) == _canonical({k: initial[k] for k in static}),
          'CHECKPOINT_HOLD: changed funded source/point identity')
    index = payload['step_index']; local = payload['segment_step_index']; event = m['numerical']['event_global_step_index']
    _need(type(index) is int and type(local) is int and 0 <= local <= m['numerical']['step_count']-event
          and index == event+local and type(payload['output_cursor']) is int
          and payload['output_cursor'] == initial['output_cursor']+local and parent._digest(payload['output_prefix_sha256']),
          'CHECKPOINT_HOLD: original global index/cursor/prefix required')
    _need(payload['at_elapsed_seconds_exact'] == _exact(index, m['numerical']['step_seconds'])
          and payload['phase'] == ('after_birth' if local == 0 else 'funded_birth_interval'), 'TIME_HOLD: current exact coordinate/phase required')
    sample = payload['last_confirmed']
    _need(type(sample) is dict and set(sample) == set(seed['last_confirmed']), 'CHECKPOINT_HOLD: closed current sample required')
    state = sample['state']
    _need(type(state) is list and len(state) == len(seed['last_confirmed']['state'])
          and all(type(v) is float and isfinite(v) for v in state), 'CHECKPOINT_HOLD: finite float64 state required')
    rows = payload['segment_integrated_transfers']; units = short._flux_units(p)
    _need(type(rows) is dict and set(rows) == set(units), 'CHECKPOINT_HOLD: closed segment transfers required')
    for name, unit in units.items():
        row = rows[name]
        _need(type(row) is dict and set(row) == {'value', 'unit'} and row['unit'] == unit
              and type(row['value']) is float and isfinite(row['value']), 'CHECKPOINT_HOLD: finite float64 transfer/unit required')
    totals = tuple(rows[name]['value'] for name in units)
    rates, current = short._evaluate(p, tuple(state), parent._profiles(context._root))
    expected = short._sample(index, m['numerical']['step_seconds'], state, current, seed['anchors'])
    built = _build(context, p, seed, m, expected, totals, payload['output_prefix_sha256'])
    _need(_canonical(payload) == _canonical(built), 'CHECKPOINT_HOLD: stale current sample/derived/ledgers')
    if local == 0:
        _need(_canonical(payload) == _canonical(initial), 'CHECKPOINT_HOLD: original birth snapshot required')
    return tuple(state), totals, rates, current


@_public
def restore_checkpoint(context, raw_bytes, *, expected_sha256):
    p, seed, m = _context(context)
    payload = _parse(raw_bytes, expected_sha256, MAX_CHECKPOINT_BYTES)
    _validate(context, payload, p, seed, m)
    return _seal(context, payload)


@_public
def adopt_births(*, context, raw_checkpoint, expected_sha256, inputs):
    p, seed, m = _context(context)
    cp = restore_checkpoint(context, raw_checkpoint, expected_sha256=expected_sha256)
    point._closed(inputs, point.FIELDS)
    seen = {event['event_id'] for record in context.point_history for event in record['inputs']['events']}
    _need(type(inputs['events']) is list and all(type(event) is dict and event.get('event_id') not in seen for event in inputs['events']),
          'EVENT_HOLD: previously funded event cannot be debited again')
    result = point._apply_current(program=p, anchors=seed['anchors'], manifest=m, saved=cp.value,
            context_sha256=context.root_sha256, checkpoint_sha256=cp.sha256, profiles=parent._profiles(context._root), inputs=inputs)
    return _capture(context._root, result, seed['anchors'], seed['birth_bases'], context.point_history)


@_public
def advance_chunk(context, checkpoint, step_budget):
    _need(type(step_budget) is int and 1 <= step_budget <= 128, 'BUDGET_HOLD: 1..128 integer steps required')
    p, seed, m = _context(context)
    payload = json.loads(checkpoint_bytes(context, checkpoint))
    state, totals, rates, current = _validate(context, payload, p, seed, m)
    begin = payload['step_index']; count = m['numerical']['step_count']; dt = m['numerical']['step_seconds']
    _need(begin < count, 'COMPLETED_HOLD: no funded interval step remains')
    flux = short._flux(p, state, current); samples = []; attempts = 0; held = None; sealed = checkpoint
    index = begin; phase = 'ready'
    try:
        for index in range(begin+1, min(count, begin+step_budget)+1):
            phase = 'k2'; y2 = short._advance(state, rates, dt/2); attempts += 1
            k2, r2 = short._evaluate(p, y2, parent._profiles(context._root))
            phase = 'k3'; y3 = short._advance(state, k2, dt/2); attempts += 1
            k3, r3 = short._evaluate(p, y3, parent._profiles(context._root))
            phase = 'k4'; y4 = short._advance(state, k3, dt); attempts += 1
            k4, r4 = short._evaluate(p, y4, parent._profiles(context._root))
            phase = 'endpoint'; candidate = short._advance(state, short._weighted(rates, k2, k3, k4), dt)
            cumulative = short._advance(totals, short._weighted(flux, short._flux(p, y2, r2), short._flux(p, y3, r3), short._flux(p, y4, r4)), dt)
            attempts += 1
            new_rates, evaluated = short._evaluate(p, candidate, parent._profiles(context._root))
            sample = short._sample(index, dt, candidate, evaluated, seed['anchors'])
            phase = 'endpoint_balance'
            new_payload = _build(context, p, seed, m, sample, cumulative,
                _prefix(payload['output_prefix_sha256'], sample, len(context.point_history), 'funded_birth_interval'))
            phase = 'checkpoint'; candidate_cp = _seal(context, new_payload)
            state, totals, rates, current = candidate, cumulative, new_rates, evaluated
            flux = short._flux(p, state, current); payload = new_payload; sealed = candidate_cp; samples.append(sample)
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, ZeroDivisionError, RecursionError) as error:
        held = {'step_index': index, 'at_elapsed_seconds_exact': _exact(index, dt), 'stage': phase,
                'reason': str(error) if isinstance(error, ValueError) else 'INPUT_HOLD: funded interval arithmetic'}
        sealed = None
    result = {'status': 'hold' if held else 'completed' if payload['step_index'] == count else 'yielded',
              'manifest': m, 'context_sha256': context.root_sha256, 'samples': samples, 'hold': held, 'checkpoint': sealed,
              **{name: deepcopy(payload[name]) for name in ('step_index', 'phase', 'last_confirmed', 'integrated_transfers',
                  'segment_integrated_transfers', 'point_totals', 'balance_residuals', 'balance_budgets',
                  'global_balance_residuals', 'global_balance_budgets', 'output_cursor', 'output_prefix_sha256')},
              'checkpoint_validation_stage_evaluations': 1, 'attempted_new_stage_evaluations': attempts,
              'confirmed_new_steps': payload['step_index']-begin, 'scope': 'software_research_only',
              'claim_scope': 'synthetic_funded_leaf_continuation_only', 'G0_G4': 'not_assessed'}
    _canonical({k: v for k, v in result.items() if k != 'checkpoint'})
    return result
