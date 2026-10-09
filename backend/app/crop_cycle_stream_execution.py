"""Actual fixed crop equations over bounded, immutable synthetic input pages."""
from dataclasses import dataclass, field
from datetime import timedelta
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import platform
from types import SimpleNamespace

from . import crop_cycle_continuation as short
from . import crop_cycle_input_stream as inputs
from . import crop_plant_startup_integration as physical

VERSION = 'crop-cycle-stream-execution-research-v1'
CHECKPOINT_VERSION = 'crop-cycle-stream-checkpoint-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_CHECKPOINT_BYTES = 65536
MAX_INDEX_PAGES = 3072
_TOKEN = object()
_canonical = short._canonical
_hash = short._hash


class CycleStreamExecutionRejected(ValueError):
    """Invalid execution identity, position or budget; no crop step started."""


def _need(condition, reason):
    if not condition:
        raise CycleStreamExecutionRejected(reason)


@dataclass(frozen=True)
class _Page:
    cursor: bytes | None
    previous: str | None
    steps: int


@dataclass(frozen=True)
class StreamContext:
    reader: inputs.InputPacket
    _manifest: bytes
    _initial: bytes
    _initial_clock: bytes
    start_at: str
    segment_count: int
    index: tuple
    seed: tuple
    planned_steps: int
    boundary_count: int
    root_sha256: str
    growth_profile: physical.plant.ReferenceParameters
    cohort_profile: physical.fruit.ReferenceFruitCohortParameters
    transport_profile: physical.transport.ReferenceFruitTransportParameters
    _token: object = field(repr=False)
    _cache: dict = field(default_factory=dict, repr=False, compare=False)

    @property
    def manifest(self):
        return json.loads(self._manifest)


def prepare_context(reader, *, growth_profile, cohort_profile, transport_profile):
    _need(type(reader) is inputs.InputPacket and not reader.closed,
          'CONTEXT_HOLD: open preflighted input reader required')
    _need(type(growth_profile) is physical.plant.ReferenceParameters
          and type(cohort_profile) is physical.fruit.ReferenceFruitCohortParameters
          and type(transport_profile) is physical.transport.ReferenceFruitTransportParameters,
          'PROFILE_HOLD: exact pinned profiles required')
    root = reader.manifest
    profiles = {k:p.sha256 for k,p in (
        ('growth_profile',growth_profile),('cohort_profile',cohort_profile),('transport_profile',transport_profile))}
    _need(root['profile_sha256'] == profiles and _hash(root) == reader.root_sha256,
          'CONTEXT_HOLD: input/profile mismatch')
    index = []; cursor = None; previous = None; steps = 0; count = 0
    h = root['solver']['max_step_seconds']
    while True:
        _need(len(index) < MAX_INDEX_PAGES, 'RESOURCE_HOLD: grid index page limit')
        index.append(_Page(None if cursor is None else _canonical(cursor),previous,steps))
        page = reader.boundary_page(cursor)
        for row in page['boundaries']:
            if previous is not None:
                span = int((physical._utc(row['at'])-physical._utc(previous)).total_seconds())
                steps += (span+h-1)//h
            previous = row['at']; count += 1
        cursor = page['cursor']
        if page['complete']:
            break
    plan = reader.plan
    _need(steps == plan['planned_steps'] and count == plan['boundaries']
          and steps <= root['solver']['max_steps'], 'CONTEXT_HOLD: original grid plan mismatch')
    grid = [{'cursor':None if p.cursor is None else json.loads(p.cursor),
             'previous':p.previous,'steps':p.steps} for p in index]
    initial = root['initial_state']['values']
    seed = tuple([initial[k]['value'] for k in physical.PLANT]
                 + [q['value'] for k in physical.ARRAY_UNITS for q in initial[k]]
                 + [0.0]*len(physical.FLUX))
    manifest = {
        'engine_version':VERSION,'scope':'software_research_only',
        'physical_program_version':physical.PROGRAM_VERSION,'rate_model_version':physical.coupled.MODEL_VERSION,
        'input_root_sha256':reader.root_sha256,'calculation_sha256':reader.calculation_sha256,
        'grid_index_sha256':_hash(grid),'grid_page_records':inputs.BLOCK_RECORDS,
        'planned_steps':steps,'boundary_count':count,
        'code_sha256':{'stream_execution':CODE_SHA256,'continuation':short.CODE_SHA256,'input_stream':inputs.CODE_SHA256},
        'physical_code_sha256':dict(physical.CODE_HASHES),'profile_sha256':profiles,
        'policy_sha256':physical.startup.POLICY_SHA256,'allocation_policy_sha256':physical.allocation.POLICY_SHA256,
        'solver':root['solver'],'python_version':platform.python_version(),
        'time_rule':'UTC_POSIX_whole_seconds_v1',
        'temperature_sum_method':'analytic_piecewise_constant_fraction_v1',
    }
    clock = reader.segment(0)['clock']
    initial_clock = {'segment_start':clock['start'],'prefix':clock['prefix'],'slope':clock['slope']}
    return StreamContext(reader,_canonical(manifest),_canonical(root['initial_state']),_canonical(initial_clock),
        root['period']['start'],plan['counts']['segments'],tuple(index),seed,
        steps,count,_hash(manifest),growth_profile,cohort_profile,transport_profile,_TOKEN)


def _require_context(context):
    _need(type(context) is StreamContext and context._token is _TOKEN,
          'CONTEXT_HOLD: prepared context required')
    _need(not context.reader.closed,'CONTEXT_HOLD: input reader closed')
    manifest = context.manifest
    _need(_hash(manifest) == context.root_sha256
          and manifest['input_root_sha256'] == context.reader.root_sha256
          and manifest['calculation_sha256'] == context.reader.calculation_sha256
          and manifest['planned_steps'] == context.planned_steps
          and manifest['boundary_count'] == context.boundary_count
          and manifest['code_sha256'] == {'stream_execution':CODE_SHA256,'continuation':short.CODE_SHA256,'input_stream':inputs.CODE_SHA256}
          and manifest['physical_code_sha256'] == physical.CODE_HASHES
          and manifest['policy_sha256'] == physical.startup.POLICY_SHA256
          and manifest['allocation_policy_sha256'] == physical.allocation.POLICY_SHA256
          and manifest['python_version'] == platform.python_version()
          and manifest['profile_sha256'] == {k:p.sha256 for k,p in (
              ('growth_profile',context.growth_profile),('cohort_profile',context.cohort_profile),
              ('transport_profile',context.transport_profile))},'CONTEXT_HOLD: changed input/code/profile/policy/environment')


def _boundary(context, index):
    _need(type(index) is int and 0 <= index < context.boundary_count,'CHECKPOINT_HOLD: boundary out of range')
    page_index, offset = divmod(index,inputs.BLOCK_RECORDS)
    cached = context._cache.get('grid')
    if cached is None or cached[0] != page_index:
        base = context.index[page_index]
        cursor = None if base.cursor is None else json.loads(base.cursor)
        page = context.reader.boundary_page(cursor)
        positions = {k:0 for k in inputs.KINDS} if cursor is None else dict(cursor['positions'])
        previous = base.previous; steps = base.steps; rows = []
        h = context.manifest['solver']['max_step_seconds']
        for row in page['boundaries']:
            if previous is not None:
                span = int((physical._utc(row['at'])-physical._utc(previous)).total_seconds())
                steps += (span+h-1)//h
            for kind,selected in (('segments',row['forcing_end']),('anchors',row['anchor']),
                                  ('events',row['event'] is not None),('outputs',row['output'])):
                positions[kind] += int(selected)
            rows.append({**row,'previous':previous,'steps':steps,'positions':dict(positions)})
            previous = row['at']
        context._cache['grid'] = (page_index,rows)
    return context._cache['grid'][1][offset]


def _evaluator(context, active):
    cached = context._cache.get('evaluator')
    if cached is None or cached[0] != active:
        value = context.reader.segment(active); clock = value['clock']
        fraction = lambda q:Fraction(int(q['numerator']),int(q['denominator']))
        adapter = SimpleNamespace(
            program={'initial_state':json.loads(context._initial),'segments':[value['segment']]},
            clocks=((physical._utc(clock['start']),fraction(clock['prefix']),fraction(clock['slope'])),),
            seed=context.seed,growth_profile=context.growth_profile,cohort_profile=context.cohort_profile,
            transport_profile=context.transport_profile)
        context._cache['evaluator'] = (active,short._Evaluator(adapter),{
            'segment_start':clock['start'],'prefix':clock['prefix'],'slope':clock['slope']})
    return context._cache['evaluator'][1]


def _clock_record(context,active):
    _evaluator(context,active)
    return json.loads(_canonical(context._cache['evaluator'][2]))


def _seal(checkpoint):
    checkpoint['checkpoint_sha256'] = _hash({k:v for k,v in checkpoint.items() if k != 'checkpoint_sha256'})
    return checkpoint


def start(context):
    _require_context(context)
    return _seal({
        'version':CHECKPOINT_VERSION,'root_sha256':context.root_sha256,
        'calculated_state_id':'calculated-state:'+_hash(json.loads(context._initial)),
        'y':list(context.seed),'seed':list(context.seed),'at':context.start_at,
        'steps':0,'event_count':0,'active_segment':0,'boundary_cursor':0,
        'output_cursor':0,'event_cursor':0,'phase':'initial-ready','sequence':0,
        'parent_sha256':None,'output_prefix_sha256':_hash([]),'event_prefix_sha256':_hash([]),
        'clock':json.loads(context._initial_clock),
    })


def _validate_checkpoint(context,checkpoint):
    _require_context(context)
    identity = start(context)
    _need(type(checkpoint) is dict and set(checkpoint) == set(identity),'CHECKPOINT_HOLD: closed checkpoint required')
    try:
        _need(len(_canonical(checkpoint)) <= MAX_CHECKPOINT_BYTES,'RESOURCE_HOLD: checkpoint too large')
        _need(checkpoint['checkpoint_sha256'] == _hash({k:v for k,v in checkpoint.items() if k != 'checkpoint_sha256'}),
              'CHECKPOINT_HOLD: hash mismatch')
        for key in ('version','root_sha256','calculated_state_id','seed'):
            _need(_canonical(checkpoint[key]) == _canonical(identity[key]),'CHECKPOINT_HOLD: identity/seed mismatch')
        for key in ('y','seed'):
            _need(type(checkpoint[key]) is list and len(checkpoint[key]) == 121
                  and all(type(v) is float and isfinite(v) and v >= 0 for v in checkpoint[key]),
                  'CHECKPOINT_HOLD: finite nonnegative float64 vector required')
        for key in ('steps','event_count','active_segment','boundary_cursor','output_cursor','event_cursor','sequence'):
            _need(type(checkpoint[key]) is int and checkpoint[key] >= 0,'CHECKPOINT_HOLD: integer counter required')
        for key in ('output_prefix_sha256','event_prefix_sha256'):
            _need(short._digest(checkpoint[key]),'CHECKPOINT_HOLD: prefix SHA required')
        phase = checkpoint['phase']; cursor = checkpoint['boundary_cursor']; at = physical._utc(checkpoint['at'])
        _need(type(phase) is str and phase in ('initial-ready','step-end','boundary-committed'),'CHECKPOINT_HOLD: phase mismatch')
        if phase == 'initial-ready':
            _need(checkpoint == identity,'CHECKPOINT_HOLD: initial position mismatch')
            return
        _need(1 <= cursor <= context.boundary_count,'CHECKPOINT_HOLD: global boundary cursor mismatch')
        previous = _boundary(context,cursor-1); steps = previous['steps']
        previous_at = physical._utc(previous['at']); h = context.manifest['solver']['max_step_seconds']
        if phase == 'step-end':
            _need(cursor < context.boundary_count,'CHECKPOINT_HOLD: no original interval remaining')
            target = physical._utc(_boundary(context,cursor)['at'])
            elapsed = (at-previous_at).total_seconds(); span = int((target-previous_at).total_seconds())
            _need(elapsed.is_integer() and 0 < elapsed <= span and (elapsed % h == 0 or elapsed == span),
                  'CHECKPOINT_HOLD: position outside original grid')
            steps += (int(elapsed)+h-1)//h
        else:
            _need(at == previous_at,'CHECKPOINT_HOLD: committed position mismatch')
        positions = previous['positions']
        active = min(positions['segments'],context.segment_count-1)
        expected = {'steps':steps,'event_count':positions['events'],'event_cursor':positions['events'],
                    'output_cursor':positions['outputs'],'active_segment':active,'sequence':steps+cursor}
        _need(all(checkpoint[k] == v for k,v in expected.items()),'CHECKPOINT_HOLD: global counters mismatch')
        _need(short._digest(checkpoint['parent_sha256']),'CHECKPOINT_HOLD: parent SHA required')
        _need(_canonical(checkpoint['clock']) == _canonical(_clock_record(context,active)),
              'CHECKPOINT_HOLD: exact original clock mismatch')
        for key,count in (('output_prefix_sha256',positions['outputs']),('event_prefix_sha256',positions['events'])):
            if count == 0:
                _need(checkpoint[key] == _hash([]),'CHECKPOINT_HOLD: empty prefix mismatch')
        y = checkpoint['y']; evaluator = _evaluator(context,active)
        _need(y[4].hex() == evaluator.clock(y,at,0,'checkpoint')[4].hex(),'CHECKPOINT_HOLD: temperature sum mismatch')
        physical._guard(y,at,'checkpoint')
        physical._ledger(y,context.seed,steps+positions['events'],at,context.growth_profile.values['cFruitG'])
    except CycleStreamExecutionRejected:
        raise
    except (ValueError,OverflowError,TypeError,RecursionError,physical._EvaluationHold) as exc:
        raise CycleStreamExecutionRejected('CHECKPOINT_HOLD: invalid checkpoint') from exc


def checkpoint_bytes(context,checkpoint):
    _validate_checkpoint(context,checkpoint)
    return _canonical(checkpoint)


def restore_checkpoint(context,raw_bytes):
    _need(type(raw_bytes) is bytes and len(raw_bytes) <= MAX_CHECKPOINT_BYTES,
          'RESOURCE_HOLD: bounded checkpoint bytes required')
    def pairs(items):
        value = {}
        for key,child in items:
            _need(key not in value,'CHECKPOINT_HOLD: duplicate JSON key'); value[key] = child
        return value
    def constant(value):
        raise CycleStreamExecutionRejected('CHECKPOINT_HOLD: nonfinite JSON constant')
    try:
        checkpoint = json.loads(raw_bytes.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
    except (ValueError,UnicodeDecodeError,RecursionError) as exc:
        raise CycleStreamExecutionRejected('CHECKPOINT_HOLD: invalid UTF-8 JSON') from exc
    _validate_checkpoint(context,checkpoint)
    return checkpoint


def _confirmed(context,checkpoint):
    if checkpoint['phase'] == 'initial-ready':
        return None
    phase = 'step-end'
    if checkpoint['phase'] == 'boundary-committed':
        row = _boundary(context,checkpoint['boundary_cursor']-1)
        phase = 'boundary-after-event' if row['event'] is not None else 'boundary'
    evaluator = _evaluator(context,checkpoint['active_segment'])
    return {**evaluator.snapshot(checkpoint['y'],physical._utc(checkpoint['at']),
                               checkpoint['steps']+checkpoint['event_count']),'phase':phase}


def advance_chunk(context,checkpoint,budget):
    _need(type(budget) is dict and set(budget) == {'max_steps','max_transitions'}
          and all(type(v) is int and 1 <= v <= 10000 for v in budget.values()),
          'RESOURCE_HOLD: bounded integer chunk budgets required')
    _validate_checkpoint(context,checkpoint)
    _need(checkpoint['boundary_cursor'] < context.boundary_count,'CHECKPOINT_HOLD: already completed')
    cp = json.loads(_canonical(checkpoint)); at = physical._utc(cp['at']); y = cp['y']
    steps_at_entry = cp['steps']; transitions = 0; samples = []; events = []
    last_confirmed = _confirmed(context,cp); status = 'yielded'; hold = None
    hmax = context.manifest['solver']['max_step_seconds']
    segment_count = context.segment_count
    try:
        while transitions < budget['max_transitions'] and cp['steps']-steps_at_entry < budget['max_steps']:
            row = _boundary(context,cp['boundary_cursor']); boundary = physical._utc(row['at'])
            active = cp['active_segment']; evaluator = _evaluator(context,active)
            if at < boundary:
                h = min(hmax,int((boundary-at).total_seconds()))
                half = at+timedelta(seconds=h/2); end = at+timedelta(seconds=h)
                k1 = evaluator.rhs(y,at,0,'rk4-k1')
                k2 = evaluator.rhs([v+h*d/2 for v,d in zip(y,k1,strict=True)],half,0,'rk4-k2')
                k3 = evaluator.rhs([v+h*d/2 for v,d in zip(y,k2,strict=True)],half,0,'rk4-k3')
                k4 = evaluator.rhs([v+h*d for v,d in zip(y,k3,strict=True)],end,0,'rk4-k4')
                candidate = physical._advance(y,(k1,k2,k3,k4),h,end)
                candidate = evaluator.clock(candidate,end,0,'step-end')
                evaluator.rhs(candidate,end,0,'step-end')
                evaluator.snapshot(candidate,end,cp['steps']+cp['event_count']+1)
                y,at = candidate,end; cp['steps'] += 1; cp['phase'] = 'step-end'
            else:
                if row['forcing_end'] and active+1 < segment_count:
                    active += 1; evaluator = _evaluator(context,active)
                physical._guard(y,at,'boundary')
                event = row['event']; candidate,removed = evaluator.remove_event(y,event,at)
                evaluator.rhs(candidate,at,0,'boundary-after-event' if event else 'boundary')
                evaluator.snapshot(candidate,at,cp['steps']+cp['event_count']+bool(event))
                if event:
                    record = {'at':physical._stamp(at),'input_id':event['removals']['input_id'],
                              'before':physical._state(y),'after':physical._state(candidate),'removed':removed}
                    events.append(record); short._prefix(cp,'event_prefix_sha256','event_cursor',record)
                    cp['event_count'] += 1
                y = candidate; cp['active_segment'] = active; cp['boundary_cursor'] += 1
                cp['phase'] = 'boundary-committed'
                if row['output']:
                    sample = evaluator.snapshot(y,at,cp['steps']+cp['event_count'])
                    samples.append(sample); short._prefix(cp,'output_prefix_sha256','output_cursor',sample)
            cp['y'] = y; cp['at'] = physical._stamp(at); cp['sequence'] += 1
            cp['clock'] = _clock_record(context,cp['active_segment'])
            last_confirmed = _confirmed(context,cp); transitions += 1
            if cp['boundary_cursor'] == context.boundary_count:
                status = 'completed'; break
    except physical._EvaluationHold as exc:
        status = 'hold'; hold = {'at':physical._stamp(exc.at),'phase':exc.phase,'reason':exc.reason}
    cp['parent_sha256'] = checkpoint['checkpoint_sha256']
    result = {'status':status,'scope':'software_research_only','manifest':context.manifest,
              'checkpoint':None if hold else _seal(cp),'steps':cp['steps'],'planned_steps':context.planned_steps,
              'output_start':checkpoint['output_cursor'],'event_start':checkpoint['event_cursor'],
              'samples':samples,'events':events}
    if hold:
        result.update(hold=hold,last_confirmed=last_confirmed)
    return result
