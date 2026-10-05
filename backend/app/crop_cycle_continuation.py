"""Pure, bounded continuation of the fixed startup research equations."""
from dataclasses import dataclass
from datetime import timedelta
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum, isfinite
from pathlib import Path
import platform

from . import crop_plant_startup_integration as physical

VERSION = 'crop-cycle-continuation-research-v1'
CHECKPOINT_VERSION = 'crop-cycle-checkpoint-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_CHECKPOINT_BYTES = 65536


class CycleContinuationRejected(ValueError):
    """An invalid context, checkpoint or chunk budget; no execution started."""


def _need(condition, reason):
    if not condition:
        raise CycleContinuationRejected(reason)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _hash(value):
    return sha256(_canonical(value)).hexdigest()


def _fraction(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


@dataclass(frozen=True)
class CycleContext:
    _program: bytes
    _manifest: bytes
    boundaries: tuple
    clocks: tuple
    seed: tuple
    planned_steps: int
    root_sha256: str
    growth_profile: physical.plant.ReferenceParameters
    cohort_profile: physical.fruit.ReferenceFruitCohortParameters
    transport_profile: physical.transport.ReferenceFruitTransportParameters

    @property
    def program(self):
        return json.loads(self._program)

    @property
    def manifest(self):
        return json.loads(self._manifest)


def prepare_context(*, initial_state, segments, events, output_times, solver,
                    growth_profile, cohort_profile, transport_profile):
    _need(type(growth_profile) is physical.plant.ReferenceParameters
          and type(cohort_profile) is physical.fruit.ReferenceFruitCohortParameters
          and type(transport_profile) is physical.transport.ReferenceFruitTransportParameters,
          'PROFILE_HOLD: pinned profiles required')
    try:
        program, boundaries, planned = physical.legacy._prepare(initial_state, segments, events, output_times, solver)
    except physical.legacy.PlantCohortIntegrationHold as exc:
        raise CycleContinuationRejected(str(exc)) from exc
    initial = program['initial_state']['values']
    seed = tuple([initial[k]['value'] for k in physical.PLANT]
                 + [q['value'] for k in physical.ARRAY_UNITS for q in initial[k]]
                 + [0.0] * len(physical.FLUX))
    clocks = []
    total = Fraction.from_float(seed[4])
    for segment in program['segments']:
        begin, end = physical._utc(segment['start']), physical._utc(segment['end'])
        slope = Fraction.from_float(segment['forcing']['values']['canopy_temperature']['value']) / Fraction.from_float(growth_profile.values['seconds_per_day'])
        clocks.append((begin, total, slope))
        total += slope * int((end - begin).total_seconds())
    manifest = {
        'engine_version': VERSION, 'scope': 'software_research_only',
        'physical_program_version': physical.PROGRAM_VERSION,
        'rate_model_version': physical.coupled.MODEL_VERSION,
        'code_sha256': {'continuation': CODE_SHA256}, 'physical_code_sha256': dict(physical.CODE_HASHES),
        'profile_sha256': {k: p.sha256 for k, p in (
            ('growth_profile', growth_profile), ('cohort_profile', cohort_profile), ('transport_profile', transport_profile))},
        'policy_sha256': physical.startup.POLICY_SHA256,
        'allocation_policy_sha256': physical.allocation.POLICY_SHA256,
        'solver': program['solver'], 'python_version': platform.python_version(),
        'time_rule': 'UTC_POSIX_whole_seconds_v1',
        'temperature_sum_method': 'analytic_piecewise_constant_fraction_v1',
        'normalized_program_sha256': _hash(program),
    }
    root = _hash({'program': program, 'manifest': manifest})
    return CycleContext(_canonical(program), _canonical(manifest), tuple(boundaries), tuple(clocks),
                        seed, planned, root, growth_profile, cohort_profile, transport_profile)


def _require_context(context):
    _need(type(context) is CycleContext, 'CONTEXT_HOLD: prepared context required')
    _need(context.manifest['code_sha256']['continuation'] == CODE_SHA256,
          'CONTEXT_HOLD: changed continuation code')


def _clock_record(context, active):
    start, prefix, slope = context.clocks[active]
    return {'segment_start': physical._stamp(start), 'prefix': _fraction(prefix), 'slope': _fraction(slope)}


def _seal(checkpoint):
    checkpoint['checkpoint_sha256'] = _hash({k: v for k, v in checkpoint.items() if k != 'checkpoint_sha256'})
    return checkpoint


def start(context):
    _require_context(context)
    return _seal({
        'version': CHECKPOINT_VERSION, 'root_sha256': context.root_sha256,
        'calculated_state_id': 'calculated-state:' + _hash(context.program['initial_state']),
        'y': list(context.seed), 'seed': list(context.seed), 'at': physical._stamp(context.boundaries[0]),
        'steps': 0, 'event_count': 0, 'active_segment': 0, 'boundary_cursor': 0,
        'output_cursor': 0, 'event_cursor': 0, 'phase': 'initial-ready', 'sequence': 0,
        'parent_sha256': None, 'output_prefix_sha256': _hash([]), 'event_prefix_sha256': _hash([]),
        'clock': _clock_record(context, 0),
    })


def _validate_checkpoint(context, checkpoint):
    _require_context(context)
    _need(type(checkpoint) is dict and set(checkpoint) == set(start(context)),
          'CHECKPOINT_HOLD: closed checkpoint required')
    try:
        _need(checkpoint == start(context), 'CHECKPOINT_HOLD: initial position/identity mismatch')
    except (ValueError, OverflowError, TypeError) as exc:
        raise CycleContinuationRejected('CHECKPOINT_HOLD: invalid checkpoint') from exc


def checkpoint_bytes(context, checkpoint):
    _validate_checkpoint(context, checkpoint)
    raw = _canonical(checkpoint)
    _need(len(raw) <= MAX_CHECKPOINT_BYTES, 'RESOURCE_HOLD: checkpoint too large')
    return raw


def restore_checkpoint(context, raw_bytes):
    _need(type(raw_bytes) is bytes and len(raw_bytes) <= MAX_CHECKPOINT_BYTES,
          'RESOURCE_HOLD: bounded checkpoint bytes required')
    def pairs(items):
        value = {}
        for key, child in items:
            _need(key not in value, 'CHECKPOINT_HOLD: duplicate key')
            value[key] = child
        return value
    def constant(value):
        raise CycleContinuationRejected('CHECKPOINT_HOLD: nonfinite JSON constant')
    try:
        checkpoint = json.loads(raw_bytes, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, RecursionError, UnicodeDecodeError) as exc:
        raise CycleContinuationRejected('CHECKPOINT_HOLD: invalid JSON') from exc
    _validate_checkpoint(context, checkpoint)
    return checkpoint
