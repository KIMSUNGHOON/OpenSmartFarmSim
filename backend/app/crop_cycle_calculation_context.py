"""Separate calculation provenance over authenticated original input checks."""
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import timedelta
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path

from . import crop_cycle_input_evidence as evidence
from . import crop_cycle_input_stream as inputs
from . import crop_cycle_stream_execution as legacy

VERSION = 'crop-cycle-verified-execution-research-v1'
CHECKPOINT_VERSION = 'crop-cycle-verified-checkpoint-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES = {'input_evidence': evidence, 'input_stream': inputs, 'original_execution': legacy}
DEPENDENCY_SHA256 = {name: sha256(Path(module.__file__).read_bytes()).hexdigest()
                     for name, module in _MODULES.items()}
MAX_CHECKPOINT_BYTES = legacy.MAX_CHECKPOINT_BYTES
_TOKEN = object()
physical, short, files = legacy.physical, legacy.short, evidence.files
_canonical, _hash = legacy._canonical, legacy._hash
_boundary, _evaluator = legacy._boundary, legacy._evaluator
_clock_record, _seal, _confirmed = legacy._clock_record, legacy._seal, legacy._confirmed


class CalculationContextHold(ValueError):
    """No calculation result for this input proof, version or checkpoint."""


def _need(condition, reason='CONTEXT_HOLD: verified calculation context unavailable'):
    if not condition:
        raise CalculationContextHold(reason)


def _pins():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
          and {name: sha256(Path(module.__file__).read_bytes()).hexdigest()
               for name, module in _MODULES.items()} == DEPENDENCY_SHA256)


def _manifest(record, raw):
    manifest = json.loads(_canonical(record['manifest']))
    origin_code = deepcopy(manifest['code_sha256'])
    origin_version = manifest['engine_version']
    manifest['engine_version'] = VERSION
    manifest['code_sha256']['stream_execution'] = CODE_SHA256
    manifest['input_validation'] = {
        'version': evidence.VERSION, 'evidence_sha256': sha256(raw).hexdigest(),
        'validated_context_sha256': record['context_sha256'],
        'validation_engine_version': origin_version, 'validation_code_sha256': origin_code,
        'input_evidence_code_sha256': evidence.CODE_SHA256,
        'input_evidence_dependency_sha256': dict(evidence.DEPENDENCY_SHA256),
    }
    return manifest


@dataclass(frozen=True)
class _Page:
    cursor: bytes | None
    previous: str | None
    steps: int


@dataclass(frozen=True)
class CalculationContext:
    reader: object
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
    growth_profile: object
    cohort_profile: object
    transport_profile: object
    _authority: object = field(repr=False)
    _directory: Path = field(repr=False)
    _evidence_raw: bytes = field(repr=False)
    _input_root_sha256: str
    _record_raw: bytes = field(repr=False)
    _inode: tuple = field(repr=False)
    _token: object = field(repr=False)
    _cache: dict = field(default_factory=dict, repr=False, compare=False)

    @property
    def manifest(self):
        return json.loads(self._manifest)

    @property
    def rights_or_gate_approval(self):
        return False

    def __enter__(self):
        try:
            _require_context(self)
            return self
        except BaseException:
            self.close()
            raise

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.reader.close()
        self._cache.clear()

    def recheck(self):
        fd = None
        try:
            _require_context(self)
            fd = files.job_store._open_directory_nofollow(self._directory)
            info = files._secure(fd, directory=True)
            _need((info.st_dev, info.st_ino) == self._inode)
            active = files._secure(self.reader._fd, directory=True)
            _need((active.st_dev, active.st_ino) == self._inode)
            checked = self._authority.verify(self._directory, self._input_root_sha256, self._evidence_raw)
            _need(_canonical(checked.context) == self._record_raw)
        except (evidence.InputEvidenceHold, inputs.CycleInputRejected, files.CycleCustodyHold, OSError) as exc:
            self.close()
            raise CalculationContextHold('CONTEXT_HOLD: current input proof unavailable') from exc
        except BaseException:
            self.close()
            raise
        finally:
            if fd is not None:
                os.close(fd)


def _require_context(context):
    _need(type(context) is CalculationContext and context._token is _TOKEN)
    _pins()
    _need(type(context.reader) is _CalculationPages and not context.reader.closed)
    record = json.loads(context._record_raw)
    manifest = _manifest(record, context._evidence_raw)
    grid = [{'cursor': None if p.cursor is None else json.loads(p.cursor),
             'previous': p.previous, 'steps': p.steps} for p in context.index]
    _need(context._manifest == _canonical(manifest) and context.root_sha256 == _hash(manifest)
          and context.reader.root_sha256 == context._input_root_sha256 == manifest['input_root_sha256']
          and context.reader.calculation_sha256 == manifest['calculation_sha256']
          and context.reader._root == context.reader.manifest
          and context.reader.plan == record['plan']
          and context._initial == _canonical(record['initial'])
          and context._initial_clock == _canonical(record['initial_clock'])
          and context.seed == tuple(record['seed']) and grid == record['index']
          and context.start_at == record['start_at'] and context.segment_count == record['segment_count']
          and context.planned_steps == record['planned_steps'] and context.boundary_count == record['boundary_count']
          and inputs._profiles(growth_profile=context.growth_profile, cohort_profile=context.cohort_profile,
                              transport_profile=context.transport_profile) == manifest['profile_sha256'])


def open_calculation_context(directory, input_root_sha256, evidence_raw, *, authority):
    fd = None
    reader = None
    try:
        _pins()
        _need(type(authority) is evidence.InputEvidenceAuthority)
        verified = authority.verify(directory, input_root_sha256, evidence_raw)
        record = verified.context
        fd = files.job_store._open_directory_nofollow(Path(directory))
        info = files._secure(fd, directory=True)
        root_raw = files._read(fd, 'root.json', inputs.MAX_ROOT_BYTES)
        _need(sha256(root_raw).hexdigest() == input_root_sha256)
        reader = _CalculationPages(fd, root_raw, input_root_sha256, record['plan'],
                                   authority.profiles['growth_profile'].values['seconds_per_day'])
        fd = None
        manifest = _manifest(record, evidence_raw)
        context = CalculationContext(
            reader=reader, _manifest=_canonical(manifest), _initial=_canonical(record['initial']),
            _initial_clock=_canonical(record['initial_clock']), start_at=record['start_at'],
            segment_count=record['segment_count'], index=tuple(_Page(
                None if p['cursor'] is None else _canonical(p['cursor']), p['previous'], p['steps'])
                for p in record['index']), seed=tuple(record['seed']),
            planned_steps=record['planned_steps'], boundary_count=record['boundary_count'],
            root_sha256=_hash(manifest), growth_profile=authority.profiles['growth_profile'],
            cohort_profile=authority.profiles['cohort_profile'], transport_profile=authority.profiles['transport_profile'],
            _authority=authority, _directory=Path(directory), _evidence_raw=evidence_raw,
            _input_root_sha256=input_root_sha256, _record_raw=_canonical(record),
            _inode=(info.st_dev, info.st_ino), _token=_TOKEN)
        context.recheck()
        return context
    except (evidence.InputEvidenceHold, inputs.CycleInputRejected, files.CycleCustodyHold, OSError) as exc:
        if reader is not None:
            reader.close()
        raise CalculationContextHold('CONTEXT_HOLD: verified calculation input unavailable') from exc
    except BaseException:
        if reader is not None:
            reader.close()
        raise
    finally:
        if fd is not None:
            os.close(fd)


def _operation(context, method, *args):
    _need(type(context) is CalculationContext)
    try:
        context.recheck()
        result = method(context, *args)
        context.recheck()
        return result
    except (legacy.CycleStreamExecutionRejected, inputs.CycleInputRejected, files.CycleCustodyHold, OSError) as exc:
        context.close()
        raise CalculationContextHold('CONTEXT_HOLD: calculation input/checkpoint unavailable') from exc
    except BaseException:
        context.close()
        raise


def start(context):
    return _operation(context, _start)


def advance_chunk(context, checkpoint, budget):
    return _operation(context, _advance_chunk, checkpoint, budget)


def checkpoint_bytes(context, checkpoint):
    return _operation(context, _checkpoint_bytes, checkpoint)


def restore_checkpoint(context, raw_bytes):
    return _operation(context, _restore_checkpoint, raw_bytes)


class _CalculationPages:
    def __init__(self, fd, root_raw, root_sha256, plan, seconds):
        self._fd, self._raw, self.root_sha256 = fd, root_raw, root_sha256
        self._root = inputs._json(root_raw)
        self._plan, self._seconds, self._cache = deepcopy(plan), seconds, {}
        self._begin, self._end = (inputs.physical._utc(self._root['period'][key]) for key in ('start','end'))
        self.calculation_sha256 = inputs._hash({**self._root,
            'streams':{name:stream for name,stream in self._root['streams'].items() if name != 'outputs'}})

    @property
    def closed(self):
        return self._fd is None

    @property
    def manifest(self):
        return inputs._json(self._raw)

    @property
    def plan(self):
        return deepcopy(self._plan)

    def close(self):
        if self._fd is not None:
            os.close(self._fd); self._fd = None
        self._cache.clear()

    def _load(self, kind, block_index):
        _need(not self.closed)
        block = self._root['streams'][kind]['blocks'][block_index]
        fd = files._file(self._fd, block['sha256']+'.json')
        try:
            before = files._secure(fd)
            _need(0 < before.st_size <= inputs.MAX_BLOCK_BYTES)
            cached = self._cache.get(kind)
            metadata = files.operator_config._metadata(before)
            if cached is not None and cached[0] == block_index and cached[2] == metadata:
                return cached[1]
            with os.fdopen(fd, 'rb', closefd=False) as handle:
                raw = handle.read(inputs.MAX_BLOCK_BYTES+1)
            after = files._secure(fd)
            _need(len(raw) == before.st_size and metadata == files.operator_config._metadata(after)
                  and sha256(raw).hexdigest() == block['sha256'])
            records = inputs._json(raw)
            _need(type(records) is list and len(records) == block['count'])
            normalized = [inputs._normalise(kind, value) for value in records]
            _need(inputs._canonical(normalized) == raw
                  and block['first_at'] == inputs._time(kind, normalized[0])
                  and block['last_at'] == inputs._time(kind, normalized[-1]))
            self._cache[kind] = (block_index, normalized, metadata)
            return normalized
        finally:
            os.close(fd)

    _record = inputs.InputPacket._record
    record = inputs.InputPacket.record
    segment = inputs.InputPacket.segment
    _next_boundary = inputs.InputPacket._next_boundary
    _count_through = inputs.InputPacket._count_through
    _validate_cursor = inputs.InputPacket._validate_cursor
    cursor_bytes = inputs.InputPacket.cursor_bytes
    restore_cursor = inputs.InputPacket.restore_cursor
    boundary_page = inputs.InputPacket.boundary_page


def _start(context):
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
    identity = _start(context)
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
    except CalculationContextHold:
        raise
    except (ValueError,OverflowError,TypeError,RecursionError,physical._EvaluationHold) as exc:
        raise CalculationContextHold('CHECKPOINT_HOLD: invalid checkpoint') from exc


def _checkpoint_bytes(context,checkpoint):
    _validate_checkpoint(context,checkpoint)
    return _canonical(checkpoint)


def _restore_checkpoint(context,raw_bytes):
    _need(type(raw_bytes) is bytes and len(raw_bytes) <= MAX_CHECKPOINT_BYTES,
          'RESOURCE_HOLD: bounded checkpoint bytes required')
    def pairs(items):
        value = {}
        for key,child in items:
            _need(key not in value,'CHECKPOINT_HOLD: duplicate JSON key'); value[key] = child
        return value
    def constant(value):
        raise CalculationContextHold('CHECKPOINT_HOLD: nonfinite JSON constant')
    try:
        checkpoint = json.loads(raw_bytes.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
    except (ValueError,UnicodeDecodeError,RecursionError) as exc:
        raise CalculationContextHold('CHECKPOINT_HOLD: invalid UTF-8 JSON') from exc
    _validate_checkpoint(context,checkpoint)
    return checkpoint


def _advance_chunk(context,checkpoint,budget):
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
