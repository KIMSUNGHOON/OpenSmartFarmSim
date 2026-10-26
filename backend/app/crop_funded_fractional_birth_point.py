"""Declared material jump at a validated fractional threshold candidate."""
from copy import deepcopy
from dataclasses import dataclass, field
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from . import crop_funded_event_state as candidate
from . import crop_leaf_funded_birth_point as point
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical, _parse

VERSION = 'funded-fractional-structural-birth-point-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
FIELDS = {'schema_version', 'input_id', 'origin', 'policy', 'context_sha256',
          'candidate_sha256', 'at_elapsed_seconds_exact', 'model_floor_area', 'events'}
_TOKEN = object()
leaf = candidate.event.leaf
stem = candidate.event.epochs.stem
short = candidate.dynamics


class FractionalBirthHold(MorphologyArtifactHold):
    pass


def _pins():
    return {**candidate._pins(), 'backend/app/crop_funded_fractional_birth_point.py': sha256(Path(__file__).read_bytes()).hexdigest()}


def _digest(v):
    return sha256(_canonical(v)).hexdigest()


@dataclass(frozen=True)
class FractionalBirthContext:
    _raw: bytes = field(repr=False)
    _leaf_directory: Path = field(repr=False)
    _stem_directory: Path = field(repr=False)
    _access: object = field(repr=False)
    _profiles: tuple = field(repr=False)
    sha256: str
    _token: object = field(repr=False)

    @property
    def value(self):
        return json.loads(self._raw)


def _sources(context, data):
    selection = data['candidate']['selection']
    lm = leaf.read_funded_leaf_manifest(context._leaf_directory, context._access, selection['leaf_root_sha256'])
    sm = stem.read_rational_morphology_manifest(context._stem_directory, context._access, selection['stem_root_sha256'])
    _need(all(lm['source_rights'][k] is True for k in ('use', 'transform', 'display'))
          and all(sm['program_rights'][k] is True for k in ('use', 'display')), 'RIGHTS_HOLD: original source grants required')
    with MorphologyBlobStore(context._leaf_directory, context._access) as store:
        _, _, _, seed, frames, _, _ = leaf._graph(store, lm)
    index = data['candidate']['source_root_certificate']['source_bracket']['left_frame_index']
    original = frames[index]
    anchors = seed['evaluation']['curve_residuals'] if original['context'] is None else original['context']['seed']['anchors']
    history = [] if original['context'] is None else original['context']['history']
    _need(data['program'] == original['program'] and data['anchors'] == anchors
          and data['past_event_ids'] == [event['event_id'] for row in history for event in row['inputs']['events']],
          'CONTEXT_HOLD: original program anchors and past events required')
    return lm, sm


def _context(context):
    _need(type(context) is FractionalBirthContext and context._token is _TOKEN, 'CONTEXT_HOLD: prepared fractional context required')
    _need(type(context._raw) is bytes and 0 < len(context._raw) <= MAX_BYTES
          and sha256(context._raw).hexdigest() == context.sha256, 'CONTEXT_HOLD: original captured bytes required')
    data = _parse(context._raw, MAX_BYTES)
    point._closed(data, {'version', 'candidate', 'program', 'anchors', 'past_event_ids', 'code_sha256', 'profile_sha256'})
    _need(data['version'] == VERSION, 'CONTEXT_HOLD: fractional material context version required')
    _need(_canonical(data) == context._raw and data['code_sha256'] == _pins()
          and data['code_sha256']['backend/app/crop_funded_fractional_birth_point.py'] == CODE_SHA256,
          'CODE_HOLD: original captured components required')
    profiles = {name: value for name, value in zip(('growth_profile', 'cohort_profile', 'transport_profile', 'exchange_profile'), context._profiles, strict=True)}
    _need({k: v.sha256 for k, v in profiles.items()} == data['profile_sha256'], 'PROFILE_HOLD: original profiles required')
    return data, profiles


def _snapshot(at, state, evaluated, anchors):
    gaps = evaluated['curve_residuals']
    return {'schema_version': 'fractional-individual-leaf-point-snapshot-v1', 'at': deepcopy(at), 'state': list(state),
            'derived': deepcopy(short._view(evaluated)['joint']['derived']), 'curve_residuals': deepcopy(gaps),
            'curve_invariant_changes': [point.numeric._q(point.numeric._sum(row['value'], -old['value']), 'm2')
                                        for row, old in zip(gaps, anchors, strict=True)]}


def prepare_fractional_birth_context(leaf_directory, stem_directory, access, **selection):
    try:
        pins = _pins()
        result = candidate.calculate_funded_threshold_state(leaf_directory, stem_directory, access, **selection)
        with MorphologyBlobStore(leaf_directory, access) as store:
            raw = store.get(result['selection']['leaf_root_sha256'], maximum=leaf.MAX)
            m = _parse(raw, leaf.MAX)
            _, _, _, seed, frames, _, raws = leaf._graph(store, m)
            index = result['source_root_certificate']['source_bracket']['left_frame_index']
            frame = frames[index]
            p = frame['program']
            anchors = seed['evaluation']['curve_residuals'] if frame['context'] is None else frame['context']['seed']['anchors']
            profiles = tuple(kind(raws[name]) for name, kind in (
                ('growth_profile', candidate.event.Growth), ('cohort_profile', candidate.event.Cohort),
                ('transport_profile', candidate.event.Transport), ('exchange_profile', candidate.event.Exchange)))
            history = [] if frame['context'] is None else frame['context']['history']
            event_ids = [event['event_id'] for row in history for event in row['inputs']['events']]
            data = {'version': VERSION, 'candidate': result, 'program': p, 'anchors': anchors,
                    'past_event_ids': event_ids, 'code_sha256': pins,
                    'profile_sha256': {name: value.sha256 for name, value in zip(
                        ('growth_profile', 'cohort_profile', 'transport_profile', 'exchange_profile'), profiles, strict=True)}}
            captured = _canonical(data)
            _need(len(captured) <= MAX_BYTES, 'CAPACITY_HOLD: bounded captured candidate required')
            leaf._fence(store, m, {**raws, 'root': raw})
        context = FractionalBirthContext(captured, Path(leaf_directory), Path(stem_directory), access,
                                        profiles, sha256(captured).hexdigest(), _TOKEN)
        _context(context)
        _sources(context, data)
        return context
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise FractionalBirthHold(str(error)) from None


def _jump(p, state, before_rhs, anchors, profiles, events, past_ids):
    n = len(p['leaves'])
    _need(type(events) is list and 1 <= len(events) <= 512-n, 'CAPACITY_HOLD: nonempty batch and at most512 leaves required')
    ids = {row['leaf_id'] for row in p['leaves']}
    used = set(past_ids)
    leaves, receipts, capacities, energies = [], [], [], []
    k = p['scenario']['parameters']['leaf_heat_capacity']['value']
    ref = p['scenario']['parameters']['reference_temperature']['value']
    floor = p['model_floor_area']['value']
    for event in events:
        point._closed(event, {'event_id', 'attachment_internode_id', 'incoming_temperature', 'leaf'})
        for key in ('event_id', 'attachment_internode_id'):
            short.old.leaf_area._identifier(event[key])
        normalized, receipt = point._new_leaf(event['leaf'])
        _need(normalized['leaf_id'] not in ids and event['event_id'] not in used, 'EVENT_HOLD: unique new leaf and event IDs required')
        ids.add(normalized['leaf_id']); used.add(event['event_id'])
        incoming = point._quantity(event['incoming_temperature'], 'degC')
        point.numeric._temperature(incoming)
        cap = point._rounded(Fraction.from_float(k)*Fraction.from_float(receipt['state']['area']['value'])/Fraction.from_float(floor))
        energy = point._rounded(Fraction.from_float(cap)*(Fraction.from_float(incoming)-Fraction.from_float(ref)))
        _need(cap > 0, 'CAPACITY_HOLD: positive incoming capacity required')
        leaves.append(normalized); capacities.append(cap); energies.append(energy)
        receipts.append({'event_id': event['event_id'], 'attachment_internode_id': event['attachment_internode_id'],
                         'initialization': receipt, 'capacity_in': point.numeric._q(cap, point.numeric.CAPACITY),
                         'sensible_in': point.numeric._q(energy, point.numeric.ENERGY)})
    masses = [row['initial_carbon']['value'] for row in leaves]
    structural, respiration, debit, buffer = point._fund(state[0], masses, profiles['growth_profile'].values['cLeafG'])
    capacity = point._rounded(sum(map(Fraction.from_float, capacities), Fraction(0)))
    energy = point._rounded(sum(map(Fraction.from_float, energies), Fraction(0)))
    u = point._rounded(Fraction.from_float(state[104])+Fraction.from_float(energy))
    _need(energy == 0 or u != state[104], 'NUMERIC_HOLD: incoming heat lost')
    base = list(state[:107]); base[0], base[104] = buffer, u
    after = [*base, *state[107:107+n], *([0.]*len(leaves)), *state[107+n:107+2*n],
             *(row['initialization']['state']['area']['value'] for row in receipts), *state[107+2*n:], *masses]
    program = {**deepcopy(p), 'leaves': [*deepcopy(p['leaves']), *leaves]}
    rates, rhs = short._evaluate(program, tuple(after), profiles)
    after_anchors = [*deepcopy(anchors), *(point.numeric._q(0., 'm2') for _ in leaves)]
    carbon = lambda y, count: point.numeric._sum(y[0], y[1], *y[4:54], *y[107+2*count:])
    balances = {'buffer': point._balance((buffer, -state[0], debit), point.MASS),
                'new_stock': point._balance((*masses, -structural), point.MASS),
                'whole_carbon': point._balance((carbon(after, len(program['leaves'])), -carbon(state, n), respiration), point.MASS),
                'sensible': point._balance((u, -state[104], -energy), point.numeric.ENERGY),
                'capacity': point._balance((short._view(rhs)['joint']['derived']['canopy_capacity']['value'],
                    -short._view(before_rhs)['joint']['derived']['canopy_capacity']['value'], -capacity), point.numeric.CAPACITY)}
    flows = {name: point.numeric._q(value, unit) for name, value, unit in (
        ('structural_carbon', structural, point.MASS), ('growth_respiration', respiration, point.MASS),
        ('buffer_debit', debit, point.MASS), ('capacity_in', capacity, point.numeric.CAPACITY), ('sensible_in', energy, point.numeric.ENERGY))}
    return program, after, rates, rhs, after_anchors, receipts, flows, balances


def apply_fractional_births(*, context, inputs):
    try:
        raw = _canonical(inputs); _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: bounded fractional point input required')
        v = _parse(raw, MAX_BYTES); point._closed(v, FIELDS)
        data, profiles = _context(context)
        before_sources = _sources(context, data)
        source = data['candidate']
        _need(v['schema_version'] == 'funded-fractional-birth-point-input-v1' and v['origin'] == 'synthetic'
              and v['policy'] == point.POLICY, 'POLICY_HOLD: declared structural funding required')
        short.old.leaf_area._identifier(v['input_id'])
        _need(v['context_sha256'] == context.sha256 and v['candidate_sha256'] == _digest(source), 'HASH_HOLD: original fractional source required')
        stem._elapsed(v['at_elapsed_seconds_exact'])
        _need(v['at_elapsed_seconds_exact'] == source['at']['elapsed_seconds_exact'], 'TIME_HOLD: original exact fractional time required')
        p = data['program']
        _need(point._quantity(v['model_floor_area'], 'm2_floor') == p['model_floor_area']['value'], 'BASIS_HOLD: original common floor required')
        state = source['dense_candidate']['state']
        _, before_rhs = short._evaluate(p, tuple(state), profiles)
        values = _jump(p, state, before_rhs, data['anchors'], profiles, v['events'], data['past_event_ids'])
        program, after, rates, rhs, anchors, receipts, flows, balances = values
        result = {'model_version': VERSION, 'scope': 'software_research_only', 'G0_G4': 'not_assessed',
                  'claim_scope': 'synthetic_declared_fractional_material_point_only', 'policy': point.POLICY,
                  'code_sha256': CODE_SHA256, 'source_code_sha256': data['code_sha256'], 'context_sha256': context.sha256,
                  'input_sha256': sha256(raw).hexdigest(), 'inputs': v, 'source_candidate': source,
                  'before_sample': _snapshot(source['at'], state, before_rhs, data['anchors']),
                  'after_program': program, 'after_sample': _snapshot(source['at'], after, rhs, anchors),
                  'after_rates': list(rates), 'after_anchors': anchors, 'after_state_layout': short._layout(program),
                  'birth_receipts': receipts, 'point_flows': flows, 'balances': balances,
                  'rhs_evaluations': 2, 'elapsed_seconds_advanced': 0, 'checkpoint': None,
                  'attachment_status': 'declared_not_bound_to_stem', 'global_prefix_adoption': 'pending_fractional_continuation'}
        _need(len(_canonical(result)) <= MAX_BYTES, 'CAPACITY_HOLD: bounded fractional point result required')
        _need(_sources(context, data) == before_sources, 'HASH_HOLD: original source changed before return')
        _context(context)
        result['calculation_sha256'] = _digest(result)
        _need(len(_canonical(result)) <= MAX_BYTES, 'CAPACITY_HOLD: bounded sealed point result required')
        return deepcopy(result)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise FractionalBirthHold(str(error)) from None
