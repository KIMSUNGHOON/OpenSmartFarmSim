"""Genuine repeated-family authority rooted in an accepted successor trajectory."""
from copy import deepcopy
from dataclasses import dataclass, field
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
import json

from . import crop_supply_morphology_successor_resume as initial
from . import crop_supply_morphology_repeat_encoding as encoding

resume = initial
source = initial.source
F, Q, X = initial.F, initial.Q, initial.X
MAX_BYTES, MAX_CP = initial.MAX_BYTES, initial.MAX_CP
VERSION = 'supply-morphology-repeat-authority-research-v2'
CONTEXT_VERSION = 'supply-morphology-repeat-context-v2'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_TOKEN = object()
SupplyContextHold = initial.SupplySuccessorHold
_need, _public = initial._need, initial._public
_canonical, _hash = initial._canonical, initial._hash
_UPSTREAM_PINS = MappingProxyType(initial._pins())
_MODULE_PINS = {
    'crop_supply_morphology_repeat_context.py': CODE_SHA256,
    **{name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
       for name in ('crop_supply_morphology_repeat_resume.py', 'crop_supply_morphology_repeat_books.py',
                    'crop_supply_morphology_repeat_candidate.py', 'crop_supply_morphology_repeat_candidate_books.py',
                    'crop_supply_morphology_repeat_point.py', 'crop_supply_morphology_repeat_point_core.py',
                    'crop_supply_morphology_repeat_point_books.py', 'crop_supply_morphology_repeat_proofs.py',
                    'crop_supply_morphology_repeat_encoding.py')},
}


def _pins():
    pins = {**_UPSTREAM_PINS, **{'backend/app/' + k: v for k, v in _MODULE_PINS.items()}}
    root = Path(__file__).resolve().parents[2]
    _need(all(sha256((root / name).read_bytes()).hexdigest() == value for name, value in pins.items()),
          'CODE_HOLD: unchanged repeated-family sources required')
    return pins


@dataclass(frozen=True, eq=False)
class Context:
    _origin: initial.owner.Context = field(repr=False)
    _root: object = field(repr=False)
    _raw: bytes = field(repr=False)
    root_sha256: str
    _token: object = field(repr=False)

    @property
    def value(self):
        return json.loads(self._raw)['descriptor']


def _grid(seed, at):
    numerical = seed['original_numerical']
    dt = F(numerical['step_seconds'])
    count = numerical['step_count']
    completed = int(at // dt)
    _need(0 <= completed <= count and at <= dt * count,
          'HORIZON_HOLD: unchanged original grid and horizon required')
    next_at = dt * (completed + 1) if completed < count else None
    return {'completed_grid_index': completed, 'at_original_grid': at == dt * completed,
            'next_grid_index': completed + 1 if next_at is not None else None,
            'next_grid_elapsed_seconds_exact': Q(next_at, 's') if next_at is not None else None,
            'remaining_to_next_grid_seconds_exact': Q(next_at - at if next_at is not None else Fraction(0), 's')}


def _root_seed(origin, data, checkpoint):
    initial._shape(origin, data, checkpoint)
    seed = deepcopy(data['seed'])
    for target, key in [('initial_sample', 'last_confirmed'), ('lifetime_transfers_exact', 'lifetime_transfers_exact'),
                        ('point_totals_exact', 'point_totals_exact'), ('global_ledgers', 'global_ledgers'),
                        ('schedule', 'schedule'), ('event_sequence', 'event_sequence'),
                        ('output_cursor', 'output_cursor'), ('output_prefix_sha256', 'output_prefix_sha256')]:
        seed[target] = deepcopy(checkpoint[key])
    seed['original_grid_position'] = _grid(seed, X(checkpoint['at']['elapsed_seconds_exact']))
    return seed


def _descriptor(origin, checkpoint_sha, seed, receipt_hashes):
    return {'version': CONTEXT_VERSION, 'model_version': VERSION, 'source_code_sha256': _pins(),
            'origin_context_sha256': origin.root_sha256, 'root_checkpoint_sha256': checkpoint_sha,
            'point_sha256': receipt_hashes[-1] if receipt_hashes else checkpoint_sha,
            'receipt_sha256': list(receipt_hashes), 'seed': deepcopy(seed),
            'scope': 'software_research_only', 'G0_G4': 'not_assessed'}


def _data(origin, original, descriptor):
    root = origin._origin._origin._source._source._root
    root_program, root_seed, _ = source.stock.parent._context(root)
    actual_source = original['origin_data']['origin_data']['source_data']
    binding = source.stock._source(origin._origin._origin._source._source)
    seed = descriptor['seed']
    return {'descriptor': descriptor, 'seed': seed, '_original_data': original,
            'root_program': root_program, 'root_seed': root_seed,
            'source_data': actual_source, 'emergence_profile': binding['stem_selection']['source_state']['emergence_profile'],
            'initial_binding_sha256': actual_source['source_snapshot']['manifest']['initial_binding_sha256'],
            'origin_data': {'shoot_base_temperature': original['shoot_base_temperature']},
            'profiles': original['profiles'],
            **{key: seed[key] for key in ['program', 'organs', 'costs', 'state_layout', 'birth_bases', 'geometry_baselines']}}


def _fence(context, data):
    _need(type(context) is Context and context._token is _TOKEN and type(context._raw) is bytes
          and 0 < len(context._raw) <= MAX_BYTES and sha256(context._raw).hexdigest() == context.root_sha256,
          'CONTEXT_HOLD: genuine bounded repeated-family authority required')
    descriptor = data['descriptor']
    initial.source.stock.arithmetic._closed(json.loads(context._raw), {'version', 'descriptor', 'root_checkpoint', 'receipts'})
    _need(descriptor == json.loads(context._raw)['descriptor'] and descriptor['source_code_sha256'] == _pins()
          and descriptor['origin_context_sha256'] == context._origin.root_sha256,
          'SOURCE_HOLD: unchanged actual repeated-family descriptor required')
    initial._fence(context._origin, data['_original_data'])
    _need(context._root is context._origin._origin._origin._source._source._root,
          'SOURCE_HOLD: actual original physical authority required')
    _need(data['seed'] == descriptor['seed'] and all(data[k] == descriptor['seed'][k]
          for k in ['program', 'organs', 'costs', 'state_layout', 'birth_bases', 'geometry_baselines']),
          'SOURCE_HOLD: unchanged repeated-family seed projection required')


def _context(context):
    _need(type(context) is Context and context._token is _TOKEN,
          'CONTEXT_HOLD: genuine repeated-family context required')
    bundle = initial._parse(context._raw, context.root_sha256, MAX_BYTES)
    source.stock.arithmetic._closed(bundle, {'version', 'descriptor', 'root_checkpoint', 'receipts'})
    _need(bundle['version'] == CONTEXT_VERSION and type(bundle['receipts']) is list,
          'CONTEXT_HOLD: versioned flat repeated-family bundle required')
    original = initial._context(context._origin)
    checkpoint = bundle['root_checkpoint']
    seed = _root_seed(context._origin, original, checkpoint)
    digest = _hash(checkpoint)
    receipts, receipt_hashes, event_ids = [], [], []
    for packed in bundle['receipts']:
        from . import crop_supply_morphology_repeat_proofs as proofs
        parent_descriptor = _descriptor(context._origin, digest, seed, receipt_hashes)
        parent_raw = _canonical({'version': CONTEXT_VERSION, 'descriptor': parent_descriptor,
                                 'root_checkpoint': checkpoint, 'receipts': receipts})
        parent = Context(context._origin, context._root, parent_raw, sha256(parent_raw).hexdigest(), _TOKEN)
        parent_data = _data(context._origin, original, parent_descriptor)
        parent_data['stem_stock_indices'] = [{v['compartment_id']: i for i, v in enumerate(seed['program']['stem_root_compartments'])}[row['compartment_id']]
                                            for row in seed['organs']['internodes']]
        parent_data['shoot_base_temperature'] = original['shoot_base_temperature']
        parent_data['seed_checkpoint_sha256'] = _hash(_seed_checkpoint(parent, parent_data))
        receipt = encoding.unpack(seed, packed, _pins())
        proofs.validate(parent, receipt, data=parent_data)
        seed = _after_seed(parent_data, receipt)
        receipts.append(packed)
        receipt_hashes.append(_hash(receipt))
        event_ids.extend(receipt['source_event'][key] for key in ['source_event_id', 'internode_event_id', 'leaf_event_id'])
    expected = _descriptor(context._origin, digest, seed, receipt_hashes)
    _need(_canonical(expected) == _canonical(bundle['descriptor']),
          'CONTEXT_HOLD: actual source-derived repeated seed required')
    data = _data(context._origin, original, expected)
    event_ids.extend(original['point']['source_event'][key] for key in ['source_event_id', 'internode_event_id', 'leaf_event_id'])
    data['verified_material_event_ids'] = tuple(event_ids)
    _fence(context, data)
    return data


@_public
def prepare_context(origin, raw_checkpoint, *, expected_sha256):
    original = initial._context(origin)
    checkpoint = initial._parse(raw_checkpoint, expected_sha256, MAX_CP)
    initial._validate(origin, original, checkpoint, {'current_validation_RHS_evaluations': 0, 'new_RHS_evaluations': 0})
    seed = _root_seed(origin, original, checkpoint)
    descriptor = _descriptor(origin, expected_sha256, seed, [])
    raw = _canonical({'version': CONTEXT_VERSION, 'descriptor': descriptor, 'root_checkpoint': checkpoint, 'receipts': []})
    initial._need(_canonical(checkpoint, MAX_CP) == raw_checkpoint,
                  'SOURCE_HOLD: unchanged original successor checkpoint bytes required')
    context = Context(origin, origin._origin._origin._source._source._root, raw, sha256(raw).hexdigest(), _TOKEN)
    _context(context)
    return context


@_public
def restore_context(origin, raw_bytes, *, expected_sha256):
    context = Context(origin, origin._origin._origin._source._source._root, raw_bytes, expected_sha256, _TOKEN)
    _context(context)
    return context


@_public
def context_bytes(context):
    _context(context)
    return context._raw


def _seed_checkpoint(context, data):
    return {'version': VERSION, 'context_sha256': context.root_sha256, 'seed': deepcopy(data['seed'])}


def _prefix(previous, sample, sequence, phase, point_sha):
    return _hash({'previous_output_prefix_sha256': previous, 'sample_sha256': _hash(sample),
                  'event_sequence': sequence, 'phase': phase, 'material_point_sha256': point_sha, 'version': VERSION})


def _after_seed(data, result):
    before = result['before_candidate']
    cp = before['source_prefix']
    event = result['source_event']
    timeline = data['source_data']['point']['before_candidate']['source_root_certificate']['source_timeline']
    threshold, spacing = X(event['threshold_exact']), X(timeline['phyllochron_exact'])
    age = X(before['dense_candidate']['shoot_age_exact'])
    _need(spacing > 0 and threshold <= age < threshold + spacing,
          'SCHEDULE_HOLD: exactly the first unconsumed event required')
    schedule = {'consumed_event_id': event['source_event_id'], 'consumed_sequence': event['sequence'],
                'consumed_threshold_exact': deepcopy(event['threshold_exact']), 'next_sequence': event['sequence'] + 1,
                'next_threshold_exact': Q(threshold + spacing, 'degC_day'),
                'age_exact': deepcopy(before['dense_candidate']['shoot_age_exact']),
                'source_schedule_id': timeline['schedule_id'], 'policy': 'repeated_material_event_once_no_threshold_snap',
                'age_basis': 'numerical_air_integral_not_physical_emergence'}
    seed = deepcopy(data['seed'])
    mapping = {'program': 'after_program', 'organs': 'after_organs', 'costs': 'after_costs',
               'state_layout': 'after_state_layout', 'birth_bases': 'after_birth_baselines',
               'geometry_baselines': 'after_geometry_baselines', 'global_ledgers': 'post_point_global_ledgers_preview',
               'lifetime_transfers_exact': 'post_point_lifetime_transfers_exact_preview',
               'point_totals_exact': 'post_point_point_totals_exact_preview'}
    seed.update({key: deepcopy(result[value]) for key, value in mapping.items()})
    sample = {'at': deepcopy(result['at']), 'state': deepcopy(result['after_state']),
              'derived': deepcopy(result['after_derived'])}
    dense = {key: deepcopy(before['dense_candidate'][key]) for key in ['at', 'state', 'derived']}
    sequence = cp['event_sequence'] + 1
    point_sha = _hash(result)
    prefix_before = _prefix(cp['output_prefix_sha256'], dense, cp['event_sequence'],
                            'fractional_before_compatible_material_point', point_sha)
    seed.update(initial_sample=sample, schedule=schedule, event_sequence=sequence,
                output_cursor=cp['output_cursor'] + 2, source_output_prefix_sha256=cp['output_prefix_sha256'],
                before_material_prefix_sha256=prefix_before,
                output_prefix_sha256=_prefix(prefix_before, sample, sequence,
                                             'fractional_after_compatible_material_point', point_sha),
                original_grid_position=_grid(seed, X(result['at']['elapsed_seconds_exact'])),
                redistribution_authorized=result['redistribution_authorized'])
    n, m = len(seed['program']['leaves']), len(seed['program']['stem_root_compartments'])
    h = len(seed['organs']['internodes'])
    units = initial.books.flux_units(seed['program'], seed['organs'])
    remaining = seed['original_numerical']['step_count'] - seed['original_grid_position']['completed_grid_index']
    _need(n <= 512 and m <= 512 and h <= 512
          and (remaining + 1) * (len(sample['state']) + len(units) + 2 * (n + h) + 8) <= 32768,
          'CAPACITY_HOLD: unchanged inventory/scalar limits required')
    return seed


@_public
def prepare_next_context(context, raw_checkpoint, *, expected_sha256, time_tolerance_seconds_exact, inputs, prepared_candidate=None):
    from . import crop_supply_morphology_repeat_point as point
    from . import crop_supply_morphology_repeat_proofs as proofs
    data = _context(context)
    original_inputs = _canonical(inputs, point.MAX_INPUT_BYTES)
    tolerance = deepcopy(time_tolerance_seconds_exact)
    result = point.apply_fractional_material_point(context, raw_checkpoint, expected_sha256=expected_sha256,
                time_tolerance_seconds_exact=time_tolerance_seconds_exact, inputs=inputs, prepared_candidate=prepared_candidate)
    receipt = proofs.compact(result)
    # Validation derives the next seed from actual current authority and saved
    # arithmetic, without executing a historical material operation.
    from . import crop_supply_morphology_repeat_resume as continuation
    actual_data = continuation._context(context)
    proofs.validate(context, receipt, data=actual_data)
    seed = _after_seed(actual_data, receipt)
    bundle = json.loads(context._raw)
    receipts = [*bundle['receipts'], encoding.pack(actual_data['seed'], receipt, _pins())]
    hashes = [*bundle['descriptor']['receipt_sha256'], _hash(receipt)]
    descriptor = _descriptor(context._origin, bundle['descriptor']['root_checkpoint_sha256'], seed, hashes)
    raw = _canonical({'version': CONTEXT_VERSION, 'descriptor': descriptor,
                      'root_checkpoint': bundle['root_checkpoint'], 'receipts': receipts})
    _fence(context, data)
    _need(_canonical(inputs, point.MAX_INPUT_BYTES) == original_inputs and time_tolerance_seconds_exact == tolerance,
          'INPUT_HOLD: unchanged caller seed declaration/tolerance required')
    output = Context(context._origin, context._root, raw, sha256(raw).hexdigest(), _TOKEN)
    _context(output)
    return output
