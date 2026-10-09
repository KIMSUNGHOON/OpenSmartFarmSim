"""Pure, bounded continuation of the fixed startup research equations."""
from dataclasses import dataclass
from datetime import timedelta
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum, isfinite
from pathlib import Path
import platform
import re

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
    manifest = context.manifest
    _need(manifest['code_sha256']['continuation'] == CODE_SHA256
          and manifest['physical_code_sha256'] == physical.CODE_HASHES
          and manifest['policy_sha256'] == physical.startup.POLICY_SHA256
          and manifest['allocation_policy_sha256'] == physical.allocation.POLICY_SHA256
          and manifest['python_version'] == platform.python_version(),
          'CONTEXT_HOLD: changed code/policy/environment')
    _need(manifest['profile_sha256'] == {k:p.sha256 for k,p in (
        ('growth_profile',context.growth_profile), ('cohort_profile',context.cohort_profile),
        ('transport_profile',context.transport_profile))}, 'CONTEXT_HOLD: changed profiles')
    _need(context.root_sha256 == _hash({'program':context.program,'manifest':manifest}),
          'CONTEXT_HOLD: root mismatch')


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
        raw = _canonical(checkpoint)
        _need(len(raw) <= MAX_CHECKPOINT_BYTES, 'RESOURCE_HOLD: checkpoint too large')
        _need(checkpoint['checkpoint_sha256'] == _hash({k:v for k,v in checkpoint.items() if k != 'checkpoint_sha256'}),
              'CHECKPOINT_HOLD: hash mismatch')
        identity = start(context)
        for key in ('version', 'root_sha256', 'calculated_state_id', 'seed'):
            _need(_canonical(checkpoint[key]) == _canonical(identity[key]), 'CHECKPOINT_HOLD: root/seed/identity mismatch')
        for key in ('y', 'seed'):
            _need(type(checkpoint[key]) is list and len(checkpoint[key]) == 121
                  and all(type(v) is float and isfinite(v) and v >= 0 for v in checkpoint[key]),
                  'CHECKPOINT_HOLD: finite float64 vector required')
        for key in ('steps', 'event_count', 'active_segment', 'boundary_cursor', 'output_cursor', 'event_cursor', 'sequence'):
            _need(type(checkpoint[key]) is int and checkpoint[key] >= 0, 'CHECKPOINT_HOLD: integer cursor required')
        for key in ('output_prefix_sha256', 'event_prefix_sha256'):
            _need(_digest(checkpoint[key]), 'CHECKPOINT_HOLD: prefix hash required')
        at = physical._utc(checkpoint['at']); phase = checkpoint['phase']; cursor = checkpoint['boundary_cursor']
        program = context.program; h = program['solver']['max_step_seconds']
        _need(phase in ('initial-ready', 'step-end', 'boundary-committed'), 'CHECKPOINT_HOLD: phase mismatch')
        if phase == 'initial-ready':
            _need(cursor == 0 and checkpoint == identity, 'CHECKPOINT_HOLD: initial position mismatch')
            return
        _need(1 <= cursor <= len(context.boundaries), 'CHECKPOINT_HOLD: boundary cursor out of range')
        previous = context.boundaries[cursor - 1]
        steps = sum((int((b-a).total_seconds()) + h-1)//h
                    for a,b in zip(context.boundaries[:cursor-1], context.boundaries[1:cursor]))
        if phase == 'step-end':
            _need(cursor < len(context.boundaries), 'CHECKPOINT_HOLD: no remaining original interval')
            elapsed = int((at-previous).total_seconds()); span = int((context.boundaries[cursor]-previous).total_seconds())
            _need(0 < elapsed <= span and (elapsed % h == 0 or elapsed == span),
                  'CHECKPOINT_HOLD: position outside original grid')
            steps += (elapsed+h-1)//h
        else:
            _need(at == previous, 'CHECKPOINT_HOLD: committed position mismatch')
        events = sum(physical._utc(e['at']) <= previous for e in program['events'])
        outputs = sum(physical._utc(t) <= previous for t in program['output_times'])
        active = sum(physical._utc(s['end']) <= previous for s in program['segments'][:-1])
        expected = {'steps': steps, 'event_count': events, 'event_cursor': events,
                    'output_cursor': outputs, 'active_segment': active, 'sequence': steps+cursor}
        _need(all(checkpoint[k] == v for k,v in expected.items()), 'CHECKPOINT_HOLD: global position/counters mismatch')
        _need(_digest(checkpoint['parent_sha256']), 'CHECKPOINT_HOLD: parent hash required')
        _need(checkpoint['clock'] == _clock_record(context, active), 'CHECKPOINT_HOLD: original exact clock mismatch')
        for key, count in (('output_prefix_sha256', outputs), ('event_prefix_sha256', events)):
            if count == 0:
                _need(checkpoint[key] == _hash([]), 'CHECKPOINT_HOLD: empty prefix mismatch')
        y = checkpoint['y']; evaluator = _Evaluator(context)
        _need(y[4].hex() == evaluator.clock(y, at, active, 'checkpoint')[4].hex(),
              'CHECKPOINT_HOLD: temperature sum mismatch')
        physical._guard(y, at, 'checkpoint')
        physical._ledger(y, context.seed, steps+events, at, context.growth_profile.values['cFruitG'])
    except CycleContinuationRejected:
        raise
    except (ValueError, OverflowError, TypeError, RecursionError, physical._EvaluationHold) as exc:
        raise CycleContinuationRejected('CHECKPOINT_HOLD: invalid checkpoint') from exc


def _digest(value):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None


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
        checkpoint = json.loads(raw_bytes.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, RecursionError, UnicodeDecodeError) as exc:
        raise CycleContinuationRejected('CHECKPOINT_HOLD: invalid JSON') from exc
    _validate_checkpoint(context, checkpoint)
    return checkpoint


class _Evaluator:
    def __init__(self, context):
        self.context = context
        self.program = context.program
        self.calculated_id = 'calculated-state:' + _hash(self.program['initial_state'])

    def clock(self, vector, time, active, phase):
        result = list(vector); start, prefix, slope = self.context.clocks[active]
        try:
            result[4] = float(prefix + slope * Fraction.from_float((time-start).total_seconds()))
        except OverflowError as exc:
            raise physical._EvaluationHold('NUMERIC_HOLD: temperature sum overflow', time, phase) from exc
        return result

    def rhs(self, vector, time, active, phase):
        vector = self.clock(vector, time, active, phase)
        physical._guard(vector, time, phase)
        state = physical._state(vector); segment = self.program['segments'][active]
        plant_state = {'input_id':self.calculated_id, 'origin':'reference_calculation',
                       'values':{k:state[k] for k in physical.PLANT}}
        fruit_state = {'input_id':self.calculated_id, 'origin':'reference_calculation', 'values':{
            **{k:state[k] for k in (*physical.ARRAY_UNITS, *physical.fruit.SCALAR_UNITS)},
            **segment['relative_growth_rate']['values']}}
        ctx = self.context
        try:
            result = physical.coupled.calculate_plant_startup_rates(
                state=plant_state, cohort_state=fruit_state, forcing=segment['forcing'],
                removals=segment['removals'], fruit_entry=segment['fruit_entry'],
                growth_profile=ctx.growth_profile, cohort_profile=ctx.cohort_profile,
                transport_profile=ctx.transport_profile)
            if any(vector[j] > 0 and result['vegetative_maintenance'][k]['value'] == 0
                   for j,k in ((1,'leaf'),(2,'stem_root'))):
                raise physical._EvaluationHold('NUMERIC_HOLD: positive vegetative maintenance underflow', time, phase)
            cohorts = result['cohorts']
            return [result['derivatives'][k]['value'] for k in physical.PLANT] + [
                q['value'] for k in physical.ARRAY_UNITS for q in cohorts['derivatives'][k]] + [
                result['photosynthesis']['value'], result['growth_respiration']['value'],
                result['vegetative_maintenance']['leaf']['value'], result['vegetative_maintenance']['stem_root']['value'],
                result['fruit_maintenance']['value'], result['removals']['leaf']['value'], result['removals']['stem_root']['value'],
                cohorts['terminal_outflow']['fruit_carbohydrate']['value'], cohorts['terminal_outflow']['fruit_number']['value'],
                segment['fruit_entry']['values']['fruit_number_inflow']['value'], 0.0, 0.0,
                result['fruit_startup']['requested_carbohydrate_inflow']['value'],
                result['fruit_startup']['effective_carbohydrate_inflow']['value'],
                result['fruit_startup']['deferred_carbohydrate_inflow']['value'],
                result['fruit_startup']['realized_growth_respiration']['value']]
        except physical.coupled.PlantStartupHold as exc:
            raise physical._EvaluationHold(str(exc), time, phase) from exc

    def snapshot(self, vector, time, operations):
        carbon, number, cb, nb, diagnostics = physical._ledger(
            vector, self.context.seed, operations, time, self.context.growth_profile.values['cFruitG'])
        q = physical._q
        return {'at':physical._stamp(time), 'state':physical._state(vector), 'startup_diagnostics':diagnostics,
            'cumulative':{k:q(v,physical.FLUX_UNITS[k]) for k,v in zip(physical.FLUX,vector[105:],strict=True)},
            'lai':q(self.context.growth_profile.values['sla']*vector[1], 'm2_leaf/m2_floor'),
            'fruit_carbohydrate_total':q(fsum(vector[55:105]),physical.plant.MASS_UNIT),
            'carbon_residual':q(carbon,physical.plant.MASS_UNIT), 'carbon_residual_budget':q(cb,physical.plant.MASS_UNIT),
            'number_residual':q(number,'fruits_equivalent/m2_floor'), 'number_residual_budget':q(nb,'fruits_equivalent/m2_floor')}

    def remove_event(self, y, event, at):
        candidate = list(y)
        if event is None:
            return candidate, None
        values = event['removals']['values']; removed = {k:values[k] for k in ('leaf','stem_root')}
        if any(values[k]['value'] > candidate[j] for j,k in enumerate(('leaf','stem_root'),start=1)):
            raise physical._EvaluationHold('REMOVAL_EXCEEDS_STORAGE_HOLD: event exceeds organ state', at, 'event')
        for j,k in enumerate(('leaf','stem_root'),start=1):
            candidate[j] -= values[k]['value']
        for name, offset in (('fruit_number',5),('fruit_carbohydrate',55)):
            amounts = [y[offset+j]*f['value'] for j,f in enumerate(values['fruit_fraction'])]
            if any(y[offset+j] > 0 and f['value'] > 0 and amounts[j] == 0 for j,f in enumerate(values['fruit_fraction'])):
                raise physical._EvaluationHold('NUMERIC_HOLD: positive event removal underflow', at, 'event')
            for j,value in enumerate(amounts):
                candidate[offset+j] -= value
            removed[name] = [physical._q(v,physical.ARRAY_UNITS[name]) for v in amounts]
        try:
            candidate[115] = fsum((y[115],values['leaf']['value'],values['stem_root']['value'],
                                  *(q['value'] for q in removed['fruit_carbohydrate'])))
            candidate[116] = fsum((y[116],*(q['value'] for q in removed['fruit_number'])))
        except (OverflowError,ValueError) as exc:
            raise physical._EvaluationHold('NUMERIC_HOLD: event accumulation overflow', at, 'event') from exc
        return candidate, removed


def _confirmed(evaluator, checkpoint):
    if checkpoint['phase'] == 'initial-ready':
        return None
    at = physical._utc(checkpoint['at'])
    phase = 'step-end'
    if checkpoint['phase'] == 'boundary-committed':
        phase = 'boundary-after-event' if any(e['at'] == checkpoint['at'] for e in evaluator.program['events']) else 'boundary'
    return {**evaluator.snapshot(checkpoint['y'],at,checkpoint['steps']+checkpoint['event_count']), 'phase':phase}


def _prefix(checkpoint, key, cursor, value):
    checkpoint[key] = _hash({'previous':checkpoint[key], 'sequence':checkpoint[cursor], 'value':value})
    checkpoint[cursor] += 1


def advance_chunk(context, checkpoint, budget):
    _need(type(budget) is dict and set(budget) == {'max_steps','max_transitions'}
          and all(type(v) is int and 1 <= v <= 10000 for v in budget.values()),
          'RESOURCE_HOLD: bounded integer chunk budgets required')
    _validate_checkpoint(context, checkpoint)
    _need(checkpoint['boundary_cursor'] < len(context.boundaries), 'CHECKPOINT_HOLD: already completed')
    cp = json.loads(_canonical(checkpoint)); evaluator = _Evaluator(context); program = evaluator.program
    at = physical._utc(cp['at']); y = cp['y']; steps_at_entry = cp['steps']; transitions = 0
    samples = []; events = []; last_confirmed = _confirmed(evaluator, cp)
    pulses = {physical._utc(e['at']):e for e in program['events']}; requested = set(program['output_times'])
    status = 'yielded'; hold = None
    try:
        while transitions < budget['max_transitions'] and cp['steps']-steps_at_entry < budget['max_steps']:
            boundary = context.boundaries[cp['boundary_cursor']]
            active = cp['active_segment']
            if at < boundary:
                h = min(program['solver']['max_step_seconds'],int((boundary-at).total_seconds()))
                half = at+timedelta(seconds=h/2); end = at+timedelta(seconds=h)
                k1 = evaluator.rhs(y,at,active,'rk4-k1')
                k2 = evaluator.rhs([v+h*d/2 for v,d in zip(y,k1,strict=True)],half,active,'rk4-k2')
                k3 = evaluator.rhs([v+h*d/2 for v,d in zip(y,k2,strict=True)],half,active,'rk4-k3')
                k4 = evaluator.rhs([v+h*d for v,d in zip(y,k3,strict=True)],end,active,'rk4-k4')
                candidate = physical._advance(y,(k1,k2,k3,k4),h,end)
                candidate = evaluator.clock(candidate,end,active,'step-end')
                evaluator.rhs(candidate,end,active,'step-end')
                evaluator.snapshot(candidate,end,cp['steps']+cp['event_count']+1)
                y, at = candidate, end; cp['steps'] += 1; cp['phase'] = 'step-end'
            else:
                if active+1 < len(program['segments']) and at == physical._utc(program['segments'][active]['end']):
                    active += 1
                physical._guard(y,at,'boundary')
                event = pulses.get(at); candidate, removed = evaluator.remove_event(y,event,at)
                evaluator.rhs(candidate,at,active,'boundary-after-event' if event else 'boundary')
                evaluator.snapshot(candidate,at,cp['steps']+cp['event_count']+bool(event))
                if event:
                    record = {'at':physical._stamp(at), 'input_id':event['removals']['input_id'],
                              'before':physical._state(y), 'after':physical._state(candidate), 'removed':removed}
                    events.append(record); _prefix(cp,'event_prefix_sha256','event_cursor',record); cp['event_count'] += 1
                y = candidate; cp['active_segment'] = active; cp['boundary_cursor'] += 1
                cp['phase'] = 'boundary-committed'
                if physical._stamp(at) in requested:
                    sample = evaluator.snapshot(y,at,cp['steps']+cp['event_count'])
                    samples.append(sample); _prefix(cp,'output_prefix_sha256','output_cursor',sample)
            cp['y'] = y; cp['at'] = physical._stamp(at); cp['sequence'] += 1
            cp['clock'] = _clock_record(context,cp['active_segment'])
            last_confirmed = _confirmed(evaluator,cp); transitions += 1
            if cp['boundary_cursor'] == len(context.boundaries):
                status = 'completed'
                break
    except physical._EvaluationHold as exc:
        status = 'hold'; hold = {'at':physical._stamp(exc.at), 'phase':exc.phase, 'reason':exc.reason}
    cp['parent_sha256'] = checkpoint['checkpoint_sha256']
    result = {'status':status, 'scope':'software_research_only', 'manifest':context.manifest,
              'checkpoint':None if hold else _seal(cp), 'steps':cp['steps'], 'planned_steps':context.planned_steps,
              'output_start':checkpoint['output_cursor'], 'event_start':checkpoint['event_cursor'],
              'samples':samples, 'events':events}
    if hold:
        result.update(hold=hold, last_confirmed=last_confirmed)
    return result
