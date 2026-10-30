"""Read repeated supply-limited crop states without importing growth equations."""
from copy import deepcopy
from fractions import Fraction
from math import isfinite
from hashlib import sha256
import os
from pathlib import Path
from types import MappingProxyType

from . import crop_supply_morphology_artifact_projection as projection
from . import crop_supply_morphology_repeat_encoding as encoding
from . import crop_leaf_carbon_stock_artifact_reader as carbon
from . import crop_rational_morphology_artifact_reader as stem
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _metadata, _need
from .crop_morphology_artifact_reader import _canonical, _closed, _hash, _id, _parse, _utc

MAX = 2 * 1024**2
CP_MAX = 512 * 1024
MODEL_SOURCE_PATHS = (
    'backend/app/content_access.py',
    'backend/app/crop_area_canopy_energy.py',
    'backend/app/crop_canopy_energy_transport.py',
    'backend/app/crop_canopy_exchange.py',
    'backend/app/crop_explicit_lai_carbon_cohorts.py',
    'backend/app/crop_explicit_lai_climate_rhs.py',
    'backend/app/crop_explicit_lai_photosynthesis.py',
    'backend/app/crop_fruit_allocation.py',
    'backend/app/crop_fruit_cohorts.py',
    'backend/app/crop_fruit_startup.py',
    'backend/app/crop_fruit_transport.py',
    'backend/app/crop_funded_event_state.py',
    'backend/app/crop_funded_event_time.py',
    'backend/app/crop_funded_shoot_clock.py',
    'backend/app/crop_growing_geometry_climate.py',
    'backend/app/crop_growth_rates.py',
    'backend/app/crop_internode_elongation.py',
    'backend/app/crop_internode_length.py',
    'backend/app/crop_internode_length_change.py',
    'backend/app/crop_leaf_area.py',
    'backend/app/crop_leaf_area_change.py',
    'backend/app/crop_leaf_carbon_partition.py',
    'backend/app/crop_leaf_carbon_stock_artifact_producer.py',
    'backend/app/crop_leaf_carbon_stock_artifact_reader.py',
    'backend/app/crop_leaf_carbon_stock_continuation.py',
    'backend/app/crop_leaf_carbon_stock_dynamics.py',
    'backend/app/crop_leaf_carbon_stock_rhs.py',
    'backend/app/crop_leaf_expansion.py',
    'backend/app/crop_leaf_funded_birth_continuation.py',
    'backend/app/crop_leaf_funded_birth_point.py',
    'backend/app/crop_leaf_partition_climate_rhs.py',
    'backend/app/crop_morphology_artifact_io.py',
    'backend/app/crop_morphology_artifact_reader.py',
    'backend/app/crop_morphology_thermal_clock.py',
    'backend/app/crop_organ_current_shoot_clock.py',
    'backend/app/crop_organ_fractional_candidate.py',
    'backend/app/crop_organ_fractional_clocks.py',
    'backend/app/crop_organ_fractional_context.py',
    'backend/app/crop_organ_fractional_continuation.py',
    'backend/app/crop_organ_fractional_point.py',
    'backend/app/crop_organ_funded_continuation.py',
    'backend/app/crop_organ_next_threshold.py',
    'backend/app/crop_organ_repeat.py',
    'backend/app/crop_organ_repeat_events.py',
    'backend/app/crop_organ_repeat_proofs.py',
    'backend/app/crop_organ_successor_candidate.py',
    'backend/app/crop_organ_successor_point.py',
    'backend/app/crop_phytomer_emergence.py',
    'backend/app/crop_plant_cohort_rates.py',
    'backend/app/crop_rational_internode_length.py',
    'backend/app/crop_rational_morphology_artifact_producer.py',
    'backend/app/crop_rational_morphology_artifact_reader.py',
    'backend/app/crop_rational_morphology_clock.py',
    'backend/app/crop_rational_new_internodes.py',
    'backend/app/crop_rational_shoot_inventory.py',
    'backend/app/crop_shoot_timeline.py',
    'backend/app/crop_stem_root_carbon_partition.py',
    'backend/app/crop_stem_root_carbon_stock_rhs.py',
    'backend/app/crop_stem_root_funded_internode_point.py',
    'backend/app/crop_stem_root_funded_leaf_point.py',
    'backend/app/crop_stem_root_initial_binding.py',
    'backend/app/crop_stem_root_partition_climate_rhs.py',
    'backend/app/crop_stem_root_stock_continuation.py',
    'backend/app/crop_stem_root_stock_dynamics.py',
    'backend/app/crop_supply_morphology_birth_stage.py',
    'backend/app/crop_supply_morphology_books.py',
    'backend/app/crop_supply_morphology_candidate.py',
    'backend/app/crop_supply_morphology_candidate_books.py',
    'backend/app/crop_supply_morphology_context.py',
    'backend/app/crop_supply_morphology_context_proofs.py',
    'backend/app/crop_supply_morphology_newborn_books.py',
    'backend/app/crop_supply_morphology_newborn_candidate.py',
    'backend/app/crop_supply_morphology_newborn_candidate_books.py',
    'backend/app/crop_supply_morphology_newborn_point.py',
    'backend/app/crop_supply_morphology_newborn_point_books.py',
    'backend/app/crop_supply_morphology_newborn_point_core.py',
    'backend/app/crop_supply_morphology_newborn_resume.py',
    'backend/app/crop_supply_morphology_point.py',
    'backend/app/crop_supply_morphology_point_books.py',
    'backend/app/crop_supply_morphology_point_core.py',
    'backend/app/crop_supply_morphology_repeat_books.py',
    'backend/app/crop_supply_morphology_repeat_candidate.py',
    'backend/app/crop_supply_morphology_repeat_candidate_books.py',
    'backend/app/crop_supply_morphology_repeat_context.py',
    'backend/app/crop_supply_morphology_repeat_encoding.py',
    'backend/app/crop_supply_morphology_repeat_point.py',
    'backend/app/crop_supply_morphology_repeat_point_books.py',
    'backend/app/crop_supply_morphology_repeat_point_core.py',
    'backend/app/crop_supply_morphology_repeat_proofs.py',
    'backend/app/crop_supply_morphology_repeat_resume.py',
    'backend/app/crop_supply_morphology_resume.py',
    'backend/app/crop_supply_morphology_rhs.py',
    'backend/app/crop_supply_morphology_stage.py',
    'backend/app/crop_supply_morphology_successor_books.py',
    'backend/app/crop_supply_morphology_successor_context.py',
    'backend/app/crop_supply_morphology_successor_context_proofs.py',
    'backend/app/crop_supply_morphology_successor_resume.py',
    'backend/app/job_store.py',
    'backend/app/thermal_run_store.py',
)
SOURCE_PATHS = (*MODEL_SOURCE_PATHS,
    'backend/app/crop_supply_morphology_artifact_projection.py',
    'backend/app/crop_supply_morphology_artifact_reader.py',
    'backend/app/crop_supply_morphology_artifact_producer.py')
FLAGS = {'schema_version': 'supply-morphology-research-artifact-v1',
    'scope': 'software_research_only', 'G0_G4': 'not_assessed', 'R2': 'not_approved',
    'time_kind': 'synthetic_model_clock_not_observation',
    'claim_scope': 'stored_synthetic_supply_limited_morphology_only'}
ROOT_FIELDS = {*FLAGS, 'code_sha256', 'source_blobs', 'root_inputs', 'selection',
    'initial_binding', 'source_rights', 'redistribution_authorized',
    'segments', 'frames', 'terminal', 'shoot_base_temperature'}
CONTEXT_VERSION = 'supply-morphology-repeat-context-v2'
AUTHORITY_VERSION = 'supply-morphology-repeat-authority-research-v2'
MODEL_VERSION = 'supply-morphology-repeat-continuation-research-v1'
CP_VERSION = 'supply-morphology-repeat-checkpoint-v1'
_LOADED_QC_SHA256 = MappingProxyType({
    'backend/app/' + name + '.py': sha256(Path(__file__).with_name(name + '.py').read_bytes()).hexdigest()
    for name in ('crop_supply_morphology_artifact_reader', 'crop_supply_morphology_artifact_projection',
                 'crop_supply_morphology_repeat_encoding', 'crop_leaf_carbon_stock_artifact_reader',
                 'crop_rational_morphology_artifact_reader', 'crop_morphology_artifact_reader',
                 'crop_morphology_artifact_io', 'content_access', 'thermal_run_store', 'job_store')
})


class SupplyMorphologyArtifactHold(MorphologyArtifactHold):
    pass


def _digest(value):
    return sha256(_canonical(value)).hexdigest()


def _pins():
    root = Path(__file__).resolve().parents[2]
    try:
        pins = {name: sha256((root / name).read_bytes()).hexdigest() for name in SOURCE_PATHS}
        _need(all(pins[name] == digest for name, digest in _LOADED_QC_SHA256.items()),
              'CODE_HOLD: loaded QC modules must match current source bytes')
        return pins
    except OSError:
        raise SupplyMorphologyArtifactHold('CODE_HOLD: original artifact/model sources required') from None


def _read(store, digest, raws, maximum=MAX):
    _hash(digest)
    before = _metadata(os.stat(digest, dir_fd=store._fd, follow_symlinks=False))
    raw = store.get(digest, maximum=maximum)
    after = _metadata(os.stat(digest, dir_fd=store._fd, follow_symlinks=False))
    _need(before == after, 'STORAGE_HOLD: artifact file replaced during read')
    if digest in raws:
        _need(raws[digest] == (raw, before), 'STORAGE_HOLD: original file identity and bytes required')
    raws[digest] = (raw, before)
    return raw


def _source(store, descriptor, raws, maximum=MAX):
    _closed(descriptor, {'sha256', 'bytes'})
    _need(type(descriptor['bytes']) is int and 1 <= descriptor['bytes'] <= maximum,
          'CAPACITY_HOLD: bounded original blob descriptor required')
    raw = _read(store, descriptor['sha256'], raws, maximum)
    _need(len(raw) == descriptor['bytes'], 'HASH_HOLD: original descriptor byte length required')
    return raw


def _fence(store, manifest, raws):
    _need(_pins() == manifest['code_sha256'], 'CODE_HOLD: original current artifact/model code required')
    store._guard()
    for digest, (raw, metadata) in raws.items():
        current = _metadata(os.stat(digest, dir_fd=store._fd, follow_symlinks=False))
        _need(current == metadata and store.get(digest, maximum=len(raw)) == raw,
              'STORAGE_HOLD: file changed after projection')
    store._guard()


def _rights(value):
    _closed(value, {'declaration_id', 'revision', 'declared_at_utc', 'ownership_asserted',
                    'access', 'store', 'use', 'transform', 'display', 'redistribute'})
    for name in ('declaration_id', 'revision'):
        _id(value[name])
    _utc(value['declared_at_utc'])
    _need(all(value[name] is True for name in ('ownership_asserted', 'access', 'store', 'use', 'transform', 'display'))
          and type(value['redistribute']) is bool, 'RIGHTS_HOLD: current embedded research grants required')


POINT_RECEIPT_FIELDS = frozenset((
    'G0_G4', 'after_birth_baselines', 'after_costs',
    'after_derived', 'after_geometry_baselines', 'after_organs',
    'after_program', 'after_rates', 'after_stage',
    'after_state', 'after_state_layout', 'at',
    'before_candidate', 'before_candidate_sha256', 'birth_stage_version',
    'calculation_sha256', 'candidate_new_RHS_evaluations', 'candidate_reused',
    'candidate_stage_evaluations_in_point_call', 'candidate_work_scope', 'checkpoint_sha256',
    'context_sha256', 'current_validation_RHS_evaluations', 'effects',
    'elapsed_seconds_advanced', 'flow_components', 'global_prefix_adoption',
    'growth_costs', 'initialization_scope', 'input_sha256',
    'inputs', 'integrator_checkpoint', 'leaf_receipts',
    'model_version', 'new_birth_baselines', 'past_intervals_reintegrated',
    'point_balances', 'point_flows_exact', 'point_order',
    'point_stage_RHS_evaluations', 'policy', 'post_point_global_ledgers_preview',
    'post_point_lifetime_transfers_exact_preview', 'post_point_point_totals_exact_preview', 'preview_scope',
    'proposal_sha256', 'redistribution_authorized', 'schedule_adoption',
    'scope', 'seed_compatibility', 'source_code_sha256',
    'source_event', 'time_kind',
))
CANDIDATE_RECEIPT_FIELDS = frozenset((
    'G0_G4', 'at', 'calculation_sha256',
    'checkpoint_sha256', 'context_sha256', 'current_validation_RHS_evaluations',
    'dense_candidate', 'integrator_checkpoint', 'ledger_rule',
    'model_version', 'new_RHS_evaluations', 'new_organs_created',
    'numerical_root_interval', 'partial_interval_seconds_exact', 'past_intervals_reintegrated',
    'proposal_sha256', 'redistribution_authorized', 'refinement_scope',
    'schedule_consumed', 'scope', 'selection_policy',
    'source_code_sha256', 'source_interval', 'source_next_sequence',
    'source_prefix', 'source_stage_sha256', 'stage',
    'state_layout', 'threshold_exact', 'time_kind',
))

CP_FIELDS = {'G0_G4', 'at', 'branch_integrated_transfers', 'branch_ledgers', 'branch_steps',
    'context_sha256', 'event_sequence', 'geometry_diagnostics', 'global_ledgers', 'grid_index',
    'last_confirmed', 'lifetime_transfers_exact', 'model_version', 'origin_context_sha256',
    'output_cursor', 'output_prefix_link', 'output_prefix_sha256', 'phase', 'point_sha256',
    'point_totals_exact', 'redistribution_authorized', 'schedule', 'scope', 'seed_checkpoint_sha256',
    'source_code_sha256', 'transfer_origins', 'version'}


def _context_value(raw, model_pins):
    value = _parse(raw, MAX)
    _closed(value, {'version', 'descriptor', 'root_checkpoint', 'receipts'})
    descriptor = value['descriptor']
    _closed(descriptor, {'version', 'model_version', 'source_code_sha256', 'origin_context_sha256',
        'root_checkpoint_sha256', 'point_sha256', 'receipt_sha256', 'seed', 'scope', 'G0_G4'})
    _need(_canonical(value) == raw and value['version'] == CONTEXT_VERSION
        and descriptor['version'] == CONTEXT_VERSION and descriptor['model_version'] == AUTHORITY_VERSION
        and descriptor['scope'] == 'software_research_only' and descriptor['G0_G4'] == 'not_assessed'
        and descriptor['source_code_sha256'] == model_pins, 'CONTEXT_HOLD: original canonical repeated authority required')
    for name in ('origin_context_sha256', 'root_checkpoint_sha256', 'point_sha256'):
        _hash(descriptor[name])
    _need(type(value['receipts']) is list and type(descriptor['receipt_sha256']) is list
        and len(value['receipts']) == len(descriptor['receipt_sha256']) <= 511
        and _digest(value['root_checkpoint']) == descriptor['root_checkpoint_sha256'],
        'CONTEXT_HOLD: original root checkpoint and flat receipt references required')
    for packed, digest in zip(value['receipts'], descriptor['receipt_sha256'], strict=True):
        _hash(digest)
        _need(packed['receipt_sha256'] == digest, 'RECEIPT_HOLD: original semantic receipt hash required')
    _need(descriptor['point_sha256'] == (descriptor['receipt_sha256'][-1] if value['receipts'] else descriptor['root_checkpoint_sha256']),
          'CONTEXT_HOLD: original last material reference required')
    seed = descriptor['seed']
    numerical = seed['original_numerical']
    _need(type(numerical['step_count']) is int and numerical['step_count'] > 0
        and type(numerical['step_seconds']) is float and isfinite(numerical['step_seconds']) and numerical['step_seconds'] > 0
        and type(numerical['sample_scalar_budget']) is int and numerical['sample_scalar_budget'] == 32768
        and all(type(seed[name]) is int and seed[name] >= 0 for name in ('event_sequence','output_cursor'))
        and type(seed['redistribution_authorized']) is bool, 'TIME_HOLD: original typed numerical/cursor declaration required')
    at = projection.x(seed['initial_sample']['at']['elapsed_seconds_exact'], 's')
    dt, count = Fraction(numerical['step_seconds']), numerical['step_count']
    completed = int(at // dt)
    grid = seed['original_grid_position']
    _need(0 <= completed <= count and at <= dt * count
        and type(grid['completed_grid_index']) is int and grid['completed_grid_index'] == completed
        and type(grid['at_original_grid']) is bool and grid['at_original_grid'] is (at == dt * completed),
        'TIME_HOLD: actual original fractional grid position required')
    return value


def _checkpoint_value(raw, context, context_sha, previous, model_pins, shoot_base):
    value = _parse(raw, CP_MAX)
    _closed(value, CP_FIELDS)
    seed = context['descriptor']['seed']
    _need(_canonical(value) == raw and value['version'] == CP_VERSION and value['model_version'] == MODEL_VERSION
        and value['context_sha256'] == context_sha and value['source_code_sha256'] == model_pins
        and value['origin_context_sha256'] == context['descriptor']['origin_context_sha256']
        and value['point_sha256'] == context['descriptor']['point_sha256']
        and value['seed_checkpoint_sha256'] == _digest({'version': AUTHORITY_VERSION, 'context_sha256': context_sha, 'seed': seed})
        and value['scope'] == 'software_research_only' and value['G0_G4'] == 'not_assessed',
        'CHECKPOINT_HOLD: original repeated checkpoint authority and claim scope required')
    steps = value['branch_steps']
    _need(type(steps) is int and steps >= 0 and type(value['grid_index']) is int
        and type(value['event_sequence']) is int and type(value['output_cursor']) is int,
        'CHECKPOINT_HOLD: original integer endpoint/cursor counters required')
    numerical = seed['original_numerical']
    grid = seed['original_grid_position']['completed_grid_index'] + steps
    at = projection.x(seed['initial_sample']['at']['elapsed_seconds_exact'], 's') if steps == 0 else Fraction(numerical['step_seconds']) * grid
    _need(grid == value['grid_index'] and grid <= numerical['step_count']
        and value['at'] == value['last_confirmed']['at']
        and value['at']['time_origin_utc'] == seed['initial_sample']['at']['time_origin_utc']
        and projection.x(value['at']['elapsed_seconds_exact'], 's') == at
        and value['event_sequence'] == seed['event_sequence'] and value['output_cursor'] == seed['output_cursor'] + steps
        and value['phase'] == ('fractional_after_compatible_material_point' if steps == 0 else 'original_grid_endpoint')
        and value['redistribution_authorized'] is seed['redistribution_authorized'],
        'TIME_HOLD: exact original grid/time/event/cursor/phase required')
    branch = value['branch_integrated_transfers']
    _closed(branch, set(seed['lifetime_transfers_exact']))
    _closed(value['lifetime_transfers_exact'], set(branch))
    for name, quantity in branch.items():
        unit = seed['lifetime_transfers_exact'][name]['unit']
        _closed(quantity, {'value', 'unit'})
        _need(quantity['unit'] == unit and type(quantity['value']) is float and isfinite(quantity['value']),
              'UNIT_HOLD: original finite branch transfer required')
        _need(projection.x(value['lifetime_transfers_exact'][name], unit)
            == projection.x(seed['lifetime_transfers_exact'][name], unit) + Fraction(quantity['value']),
            'QC_HOLD: exact original lifetime transfer composition required')
    _need(value['point_totals_exact'] == seed['point_totals_exact'] and value['transfer_origins'] == seed['transfer_origins'],
          'ORIGIN_HOLD: original point totals and transfer origins required')
    schedule = deepcopy(seed['schedule'])
    duration = at - projection.x(seed['initial_sample']['at']['elapsed_seconds_exact'], 's')
    air = Fraction(branch['indoor_air_temperature_time']['value'])
    age = projection.x(schedule['age_exact'], 'degC_day') + (air - Fraction(shoot_base) * duration) / 86400
    schedule['age_exact'] = projection.q(age, 'degC_day')
    _need(value['schedule'] == schedule and age < projection.x(schedule['next_threshold_exact'], 'degC_day'),
          'CLOCK_HOLD: actual unconsumed threshold and branch clock required')
    if previous is None:
        _need(steps == 0 and value['last_confirmed'] == seed['initial_sample']
            and all(quantity['value'] == 0. for quantity in branch.values())
            and value['output_prefix_link'] is None and value['output_prefix_sha256'] == seed['output_prefix_sha256'],
            'PREFIX_HOLD: exact initial material checkpoint required')
    else:
        link = {'previous_output_prefix_sha256': previous['output_prefix_sha256'], 'sample_sha256': _digest(value['last_confirmed'])}
        prefix = _digest({'context_sha256': context_sha, 'seed_checkpoint_sha256': value['seed_checkpoint_sha256'],
            'previous': previous['output_prefix_sha256'], 'sample_sha256': link['sample_sha256'], 'steps': steps,
            'phase': 'original_grid_endpoint', 'model_version': MODEL_VERSION})
        _need(steps == previous['branch_steps'] + 1 and value['output_prefix_link'] == link
            and value['output_prefix_sha256'] == prefix, 'PREFIX_HOLD: complete consecutive confirmed endpoints required')
    projection.ledgers(value['branch_ledgers'], seed['global_ledgers'])
    return value



def _transition(previous_context, context, previous_cp, model_pins):
    old = previous_context['descriptor']['seed']
    seed = context['descriptor']['seed']
    previous_sha = _digest(previous_context)
    _need(context['root_checkpoint'] == previous_context['root_checkpoint']
        and context['descriptor']['origin_context_sha256'] == previous_context['descriptor']['origin_context_sha256']
        and len(context['receipts']) == len(previous_context['receipts']) + 1
        and context['receipts'][:-1] == previous_context['receipts']
        and context['descriptor']['receipt_sha256'][:-1] == previous_context['descriptor']['receipt_sha256'],
        'LINEAGE_HOLD: actual single next material adoption required')
    receipt = encoding.unpack(old, context['receipts'][-1], model_pins)
    _closed(receipt, POINT_RECEIPT_FIELDS)
    before = receipt['before_candidate']
    _closed(before, CANDIDATE_RECEIPT_FIELDS)
    for value, version in [(receipt, 'supply-morphology-repeat-compact-material-receipt-v1'),
                           (before, 'supply-morphology-repeat-compact-candidate-receipt-v1')]:
        _need(value['model_version'] == version and value['source_code_sha256'] == model_pins
            and value['calculation_sha256'] == _digest({k:v for k,v in value.items() if k != 'calculation_sha256'})
            and value['scope'] == 'software_research_only' and value['G0_G4'] == 'not_assessed',
            'RECEIPT_HOLD: original compact material/candidate hash and scope required')
    point_sha = _digest(receipt)
    _need(point_sha == context['descriptor']['point_sha256']
        and before['context_sha256'] == receipt['context_sha256'] == previous_sha
        and before['source_prefix'] == previous_cp
        and before['checkpoint_sha256'] == receipt['checkpoint_sha256'] == _digest(previous_cp)
        and before['integrator_checkpoint'] is None and receipt['integrator_checkpoint'] is None
        and before['schedule_consumed'] is False and before['new_organs_created'] is False,
        'RECEIPT_HOLD: original unadopted before-candidate and genuine last CP link required')
    inputs, event = receipt['inputs'], receipt['source_event']
    _rights(inputs['rights'])
    _need(receipt['input_sha256'] == _digest(inputs) and inputs['context_sha256'] == previous_sha
        and inputs['checkpoint_sha256'] == _digest(previous_cp)
        and inputs['candidate_sha256'] == receipt['before_candidate_sha256'] == before['proposal_sha256']
        and inputs['source_event_id'] == event['source_event_id']
        and type(event['sequence']) is int and inputs['source_threshold_sequence'] == event['sequence'] == previous_cp['schedule']['next_sequence']
        and inputs['source_threshold_exact'] == event['threshold_exact'] == previous_cp['schedule']['next_threshold_exact'],
        'EVENT_HOLD: exact first pending source event and original inputs required')
    mapping = {'program':'after_program', 'organs':'after_organs', 'costs':'after_costs',
        'state_layout':'after_state_layout', 'birth_bases':'after_birth_baselines', 'geometry_baselines':'after_geometry_baselines',
        'global_ledgers':'post_point_global_ledgers_preview', 'lifetime_transfers_exact':'post_point_lifetime_transfers_exact_preview',
        'point_totals_exact':'post_point_point_totals_exact_preview'}
    _need(all(seed[name] == receipt[source] for name, source in mapping.items()),
          'RECEIPT_HOLD: original after-material state metadata and accounts required')
    sample = {'at':receipt['at'], 'state':receipt['after_state'], 'derived':receipt['after_derived']}
    dense = before['dense_candidate']
    dense_snapshot = {name:dense[name] for name in ('at', 'state', 'derived')}
    _need(seed['initial_sample'] == sample and receipt['at'] == before['at'] == dense['at']
        and receipt['at']['time_origin_utc'] == previous_cp['at']['time_origin_utc']
        and projection.x(receipt['at']['elapsed_seconds_exact'], 's') > projection.x(previous_cp['at']['elapsed_seconds_exact'], 's')
        and receipt['after_stage']['derived'] == receipt['after_derived']
        and seed['event_sequence'] == previous_cp['event_sequence'] + 1
        and seed['output_cursor'] == previous_cp['output_cursor'] + 2
        and seed['original_numerical'] == old['original_numerical']
        and seed['transfer_origins'] == old['transfer_origins']
        and len(seed['organs']['internodes']) == len(old['organs']['internodes']) + 1
        and len(seed['organs']['leaves']) == len(old['organs']['leaves']) + (inputs['leaf'] is not None),
        'STATE_HOLD: original single material effect, clocks and grid required')
    for kind in ('leaves', 'internodes'):
        origins = old['geometry_baselines'][kind]
        _need(seed['geometry_baselines'][kind][:len(origins)] == origins,
              'ORIGIN_HOLD: existing grown geometry origins cannot be reset')
    def prefix(previous, snapshot, sequence, phase):
        return _digest({'previous_output_prefix_sha256':previous, 'sample_sha256':_digest(snapshot),
            'event_sequence':sequence, 'phase':phase, 'material_point_sha256':point_sha, 'version':AUTHORITY_VERSION})
    before_prefix = prefix(previous_cp['output_prefix_sha256'], dense_snapshot, previous_cp['event_sequence'], 'fractional_before_compatible_material_point')
    after_prefix = prefix(before_prefix, sample, seed['event_sequence'], 'fractional_after_compatible_material_point')
    _need(seed['source_output_prefix_sha256'] == previous_cp['output_prefix_sha256']
        and seed['before_material_prefix_sha256'] == before_prefix and seed['output_prefix_sha256'] == after_prefix,
        'PREFIX_HOLD: original before/after material order and exact prefix required')
    schedule = seed['schedule']
    spacing = projection.x(old['schedule']['next_threshold_exact'], 'degC_day') - projection.x(old['schedule']['consumed_threshold_exact'], 'degC_day')
    threshold = projection.x(event['threshold_exact'], 'degC_day')
    _need(spacing > 0 and schedule['consumed_event_id'] == event['source_event_id']
        and schedule['consumed_sequence'] == event['sequence'] and schedule['consumed_threshold_exact'] == event['threshold_exact']
        and schedule['next_sequence'] == event['sequence'] + 1
        and projection.x(schedule['next_threshold_exact'], 'degC_day') == threshold + spacing
        and schedule['age_exact'] == dense['shoot_age_exact']
        and threshold <= projection.x(schedule['age_exact'], 'degC_day') < threshold + spacing,
        'SCHEDULE_HOLD: exactly one original schedule consumption required')
    _need(receipt['redistribution_authorized'] is (old['redistribution_authorized'] and inputs['rights']['redistribute'])
        and seed['redistribution_authorized'] is receipt['redistribution_authorized'],
        'RIGHTS_HOLD: material operation cannot escalate redistribution')
    return receipt



def _frame(projected, context_sha, checkpoint_sha, receipt_sha, index, phase, sequence, cursor, prefix):
    _need(type(index) is int and 0 <= index < 512, 'CAPACITY_HOLD: bounded stored frame index required')
    return {**FLAGS, 'schema_version':'supply-morphology-replay-frame-v1', 'index':index,
        'context_sha256':context_sha, 'checkpoint_sha256':checkpoint_sha, 'receipt_sha256':receipt_sha,
        'at':deepcopy(projected['snapshot']['at']), 'phase':phase, 'event_sequence':sequence,
        'output_cursor':cursor, 'output_prefix_sha256':prefix, **projected}


def frame_descriptor(frame):
    return {name:deepcopy(frame[name]) for name in ('index','context_sha256','checkpoint_sha256','receipt_sha256',
        'at','phase','event_sequence','output_cursor','output_prefix_sha256')} | {
        'frame_sha256':_digest(frame), 'state_sha256':_digest(frame['snapshot']['state'])}


def _frame_graph(store, manifest, raws):
    segments = manifest['segments']
    _need(type(segments) is list and 1 <= len(segments) <= 512, 'CAPACITY_HOLD: bounded nonempty stored segment list required')
    model_pins = {name:manifest['code_sha256'][name] for name in MODEL_SOURCE_PATHS}
    frames, scalar_count = [], 0
    previous_context = previous_cp = None
    for segment in segments:
        _closed(segment, {'context', 'checkpoints'})
        context_raw = _source(store, segment['context'], raws)
        context = _context_value(context_raw, model_pins)
        context_sha = segment['context']['sha256']
        seed = context['descriptor']['seed']
        if previous_context is not None:
            receipt = _transition(previous_context, context, previous_cp, model_pins)
            before = receipt['before_candidate']['dense_candidate']
            snapshot = {name:before[name] for name in ('at','state','derived')}
            projected = projection.project(previous_context['descriptor']['seed'], snapshot,
                before['pending_lifetime_transfers_exact'], before['geometry_diagnostics'], before['global_ledgers'])
            frames.append(_frame(projected, _digest(previous_context), None, _digest(receipt), len(frames),
                'fractional_before_compatible_material_point', previous_cp['event_sequence'],
                previous_cp['output_cursor'] + 1, seed['before_material_prefix_sha256']))
            scalar_count += len(snapshot['state'])
        checkpoints = segment['checkpoints']
        _need(type(checkpoints) is list and 1 <= len(checkpoints) <= 512, 'CAPACITY_HOLD: complete bounded checkpoint list required')
        prior = None
        for descriptor in checkpoints:
            raw = _source(store, descriptor, raws, CP_MAX)
            cp = _checkpoint_value(raw, context, context_sha, prior, model_pins, manifest['shoot_base_temperature'])
            projected = projection.project(seed, cp['last_confirmed'], cp['lifetime_transfers_exact'],
                cp['geometry_diagnostics'], cp['global_ledgers'])
            frames.append(_frame(projected, context_sha, descriptor['sha256'], None, len(frames),
                cp['phase'], cp['event_sequence'], cp['output_cursor'], cp['output_prefix_sha256']))
            scalar_count += len(cp['last_confirmed']['state'])
            _need(len(frames) <= 512 and scalar_count <= 32768, 'CAPACITY_HOLD: original frame/scalar caps required')
            prior = cp
        previous_context, previous_cp = context, prior
    _need(all(projection.x(left['at']['elapsed_seconds_exact'], 's') <= projection.x(right['at']['elapsed_seconds_exact'], 's')
              and left['at']['time_origin_utc'] == right['at']['time_origin_utc']
              and left['output_cursor'] + 1 == right['output_cursor']
              for left,right in zip(frames,frames[1:])), 'ORDER_HOLD: original complete ordered frame/prefix chain required')
    return frames, previous_context, previous_cp


def _sources(store, manifest, raws):
    descriptors = manifest['source_blobs']
    _need(type(descriptors) is list and 1 <= len(descriptors) <= 4096
        and len({v['sha256'] for v in descriptors}) == len(descriptors), 'CAPACITY_HOLD: bounded distinct original source blobs required')
    for descriptor in descriptors:
        _source(store, descriptor, raws, 16 * 1024**2)
    source_hashes = {v['sha256'] for v in descriptors}
    inputs = manifest['root_inputs']
    _closed(inputs, {'request','program','seed','manifest','origin_context','license_notice',*carbon.PROFILE_SHA})
    raw_inputs = {name:_source(store, descriptor, raws) for name,descriptor in inputs.items()}
    for name, digest in {**carbon.PROFILE_SHA, 'license_notice':carbon.NOTICE_SHA}.items():
        _need(inputs[name]['sha256'] == digest, 'PROFILE_HOLD: original reference profile and license notice required')
    selection = manifest['selection']
    _closed(selection, {'crop_root_sha256','stem_root_sha256','stem_start_index','binding_declaration'})
    binding = _parse(_source(store, manifest['initial_binding'], raws), MAX)
    _need(binding['calculation_sha256'] == _digest({k:v for k,v in binding.items() if k != 'calculation_sha256'})
        and binding['scope'] == 'software_research_only' and binding['G0_G4'] == 'not_assessed'
        and selection['binding_declaration'] == binding['declaration']
        and binding['source_rights'] == manifest['source_rights'], 'SOURCE_HOLD: original explicit initial binding and grants required')
    _rights(binding['source_rights']['declaration'])
    cmraw = _read(store, selection['crop_root_sha256'], raws)
    cm = _parse(cmraw, MAX)
    _, _, _, _, _, crop_raws = carbon._graph(store, cm)
    _need({sha256(v).hexdigest() for v in crop_raws.values()} <= source_hashes,
          'SOURCE_HOLD: complete original crop source archive required')
    sm = stem._load_manifest(store, selection['stem_root_sha256'])
    _need(sm['code_sha256'] == {name:manifest['code_sha256'][name] for name in stem.SOURCE_PATHS}, 'CODE_HOLD: original stem source code required')
    index = selection['stem_start_index']
    _need(type(index) is int and 0 <= index < len(sm['samples']), 'SOURCE_HOLD: actual selected stem index required')
    selected = sm['samples'][index]
    raw = _read(store, selected['result_sha256'], raws)
    result = _parse(raw, MAX)
    stem._state(result['state'])
    _need(binding['crop_selection']['root_sha256'] == selection['crop_root_sha256']
        and binding['crop_selection']['state_sha256'] == cm['initial_state_sha256']
        and binding['crop_selection']['checkpoint_sha256'] == cm['samples'][0]['checkpoint_sha256']
        and binding['crop_selection']['program_sha256'] == cm['sources']['program']['sha256']
        and binding['stem_selection']['root_sha256'] == selection['stem_root_sha256']
        and binding['stem_selection']['index'] == index
        and binding['stem_selection']['result_sha256'] == selected['result_sha256']
        and binding['stem_selection']['state_sha256'] == _digest(result['state']) == selected['state_sha256']
        and binding['stem_selection']['source_state'] == result['state']
        and manifest['source_rights']['crop'] == cm['source_rights']
        and manifest['source_rights']['stem'] == sm['program_rights'], 'SOURCE_HOLD: exact original selected inputs and current grants required')
    for grant in manifest['source_rights'].values():
        _need(grant['use'] is True and grant['display'] is True and type(grant['redistribute']) is bool,
              'RIGHTS_HOLD: original stored source use/display/redistribution scope required')
    return raw_inputs, binding



def _load(store, root_sha256, *, unpublished_raw=None):
    raws = {}
    raw = _read(store, root_sha256, raws) if unpublished_raw is None else unpublished_raw
    _need(sha256(raw).hexdigest() == root_sha256 and len(raw) <= MAX, 'HASH_HOLD: trusted original bounded root required')
    manifest = _parse(raw, MAX)
    _closed(manifest, ROOT_FIELDS)
    _need(_canonical(manifest) == raw and all(manifest[k] == v for k,v in FLAGS.items()),
          'SCOPE_HOLD: original canonical synthetic artifact scope required')
    _closed(manifest['code_sha256'], SOURCE_PATHS)
    _need(manifest['code_sha256'] == _pins(), 'CODE_HOLD: current original artifact/model code required')
    store._usage()
    _need(type(manifest['shoot_base_temperature']) is float and isfinite(manifest['shoot_base_temperature']),
          'CLOCK_HOLD: original finite shoot base required')
    inputs, binding = _sources(store, manifest, raws)
    _need(manifest['shoot_base_temperature'] == binding['stem_selection']['source_state']['timeline_state']['base_temperature']['value'],
          'CLOCK_HOLD: original selected shoot base required')
    frames, last_context, last_cp = _frame_graph(store, manifest, raws)
    first = _context_value(_source(store, manifest['segments'][0]['context'], raws),
                           {name:manifest['code_sha256'][name] for name in MODEL_SOURCE_PATHS})
    _need(first['descriptor']['origin_context_sha256'] == manifest['root_inputs']['origin_context']['sha256'],
          'SOURCE_HOLD: original genuine predecessor bytes required')
    expected = [frame_descriptor(frame) for frame in frames]
    _need(_canonical(manifest['frames']) == _canonical(expected), 'FRAME_HOLD: exact original frame order, values, identities and hashes required')
    authorized = all(v['redistribute'] for v in manifest['source_rights'].values()) and last_context['descriptor']['seed']['redistribution_authorized']
    _need(type(manifest['redistribution_authorized']) is bool and manifest['redistribution_authorized'] is authorized,
          'RIGHTS_HOLD: source/material redistribution restrictions required')
    terminal = manifest['terminal']
    _closed(terminal, {'status','hold'})
    _need(terminal['status'] in ('completed','hold'), 'STATUS_HOLD: explicit completed or held software prefix required')
    if terminal['status'] == 'completed':
        numerical = last_context['descriptor']['seed']['original_numerical']
        _need(terminal['hold'] is None and last_cp['grid_index'] == numerical['step_count']
            and projection.x(last_cp['at']['elapsed_seconds_exact'], 's') == Fraction(numerical['step_seconds']) * numerical['step_count'],
            'STATUS_HOLD: actual original horizon required for completion')
    else:
        _need(type(terminal['hold']) is str and 1 <= len(terminal['hold']) <= 1024
            and ':' in terminal['hold'] and terminal['hold'].split(':',1)[0].endswith('_HOLD'),
            'STATUS_HOLD: original explicit hold reason required')
    _fence(store, manifest, raws)
    return manifest, frames, raws


def _read_result(directory, access, root_sha256, index):
    try:
        _hash(root_sha256)
        with MorphologyBlobStore(directory, access) as store:
            manifest, frames, raws = _load(store, root_sha256)
            if index is None:
                result = deepcopy(manifest)
            else:
                _need(index < len(frames), 'INDEX_HOLD: existing stored frame required')
                result = {**frames[index], 'artifact_sha256':root_sha256,
                    'source_rights':deepcopy(manifest['source_rights']),
                    'redistribution_authorized':manifest['redistribution_authorized'],
                    'terminal':deepcopy(manifest['terminal'])}
            _need(len(_canonical(result)) <= MAX, 'CAPACITY_HOLD: bounded original replay response required')
            _fence(store, manifest, raws)
            return result
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise SupplyMorphologyArtifactHold(str(error)) from None


def read_supply_morphology_manifest(directory, access, root_sha256):
    return _read_result(directory, access, root_sha256, None)


def read_supply_morphology_frame(directory, access, root_sha256, *, index):
    _need(type(index) is int and 0 <= index < 512, 'INDEX_HOLD: explicit bounded integer frame index required')
    return _read_result(directory, access, root_sha256, index)
