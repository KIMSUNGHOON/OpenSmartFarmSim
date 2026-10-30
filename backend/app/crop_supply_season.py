"""Bounded research continuation with current state separate from immutable history.

Only constant, explicitly declared synthetic forcing and existing grid endpoints.
No farm authorization, material adoption, forecasting or whole-season claim.
"""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from fractions import Fraction
from hashlib import sha256
import json
import os
from math import isfinite
from pathlib import Path
import time
from types import SimpleNamespace

from .content_access import ContentAccess
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need, _metadata
from . import crop_supply_morphology_artifact_reader as reader
from . import crop_supply_morphology_birth_stage as stage
from . import crop_supply_morphology_repeat_resume as arithmetic
from . import crop_supply_morphology_repeat_books as books
from . import crop_growth_rates as growth
from . import crop_fruit_cohorts as cohort
from . import crop_fruit_transport as transport
from . import crop_canopy_exchange as exchange

VERSION = 'supply-season-constant-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
CURRENT_MAX = 512 * 1024
PAGE_MAX = 2 * 1024**2
MAX_HISTORY_STEPS = 128
FLAGS = {'scope':'software_research_only','G0_G4':'not_assessed','R2':'not_approved'}
NUMERIC_FIELDS = ('at','branch_steps','grid_index','phase','event_sequence','schedule','last_confirmed',
    'branch_integrated_transfers','lifetime_transfers_exact','point_totals_exact','branch_ledgers',
    'global_ledgers','geometry_diagnostics','transfer_origins','output_cursor','output_prefix_sha256')
_TOKEN = object()
q, x = reader.projection.q, reader.projection.x
combine = arithmetic.source.candidate.old._combine


def _raw(value, maximum=PAGE_MAX):
    raw = reader._canonical(value)
    _need(len(raw) <= maximum, 'CAPACITY_HOLD: bounded season record required')
    return raw


def _hash(value):
    return sha256(_raw(value)).hexdigest()


def _code():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256,
          'CODE_HOLD: unchanged season implementation required')


@dataclass(frozen=True)
class SourceRef:
    artifact_sha256: str
    frame_index: int


@dataclass(frozen=True)
class CursorRef:
    sha256: str


@dataclass(frozen=True)
class Workspace:
    source_directory: Path
    archive_directory: Path
    access: ContentAccess


@dataclass(frozen=True)
class AdvanceRequest:
    stop_at: dict
    step_budget: int = 1
    rhs_budget: int = 1024
    record_budget: int = 128
    byte_budget: int = PAGE_MAX
    wall_seconds: int = 60
    cancelled: object = field(default=None, repr=False)


@dataclass(frozen=True)
class SeasonHandle:
    cursor_sha256: str
    _current: bytes = field(repr=False)
    _basis: bytes = field(repr=False)
    _cursor: bytes = field(repr=False)
    _definition: str = field(repr=False)
    _workspace: Workspace = field(repr=False)
    _token: object = field(repr=False)

    @property
    def current(self):
        return json.loads(self._current)

    @property
    def basis(self):
        return json.loads(self._basis)


@dataclass(frozen=True)
class AdvanceOutcome:
    status: str
    handle: SeasonHandle | None
    hold: str | None
    failed_stage: str | None
    pending: dict | None
    progress: dict
    historical_cursor_sha256: str | None = None
    authority_hold: str | None = None


def _get(s, digest, maximum=PAGE_MAX):
    reader._hash(digest)
    before = _metadata(os.stat(digest, dir_fd=s.archive._fd, follow_symlinks=False))
    raw = s.archive.get(digest, maximum=maximum)
    after = _metadata(os.stat(digest, dir_fd=s.archive._fd, follow_symlinks=False))
    _need(before == after and (digest not in s.archive_witnesses or s.archive_witnesses[digest] == before),
          'STORAGE_HOLD: original season record identity required')
    s.archive_witnesses[digest] = before
    value = reader._parse(raw, maximum)
    _need(_raw(value, maximum) == raw, 'INPUT_HOLD: canonical season record required')
    return value


def _put(s, value, maximum=PAGE_MAX):
    digest = s.archive.put(_raw(value, maximum), maximum=maximum)
    _get(s, digest, maximum)
    return digest


def _check(s):
    _code()
    reader._fence(s.source, s.manifest, s.source_witnesses)
    for digest in list(s.archive_witnesses):
        _get(s, digest, PAGE_MAX)
    s.archive._guard()
    s.archive._usage()


def _initial(s):
    return {**FLAGS, 'schema_version':'supply-season-current-v1',
            **{k:deepcopy(s.original[k]) for k in NUMERIC_FIELDS}}


@contextmanager
def _session(definition_ref, workspace):
    _code()
    _need(type(workspace) is Workspace and type(workspace.access) is ContentAccess,
          'STORAGE_HOLD: explicit owned season workspace required')
    _need(Path(workspace.source_directory).resolve() != Path(workspace.archive_directory).resolve(),
          'STORAGE_HOLD: original source and new archive must be separate')
    with MorphologyBlobStore(workspace.archive_directory, workspace.access, write=True) as archive:
        archive._usage()
        s = SimpleNamespace(archive=archive, archive_witnesses={}, definition_ref=definition_ref, workspace=workspace)
        d = _get(s, definition_ref, CURRENT_MAX)
        reader._closed(d, {'schema_version','source','code_sha256','method','stop_at','forcing_span','rights',*FLAGS})
        _need(d['schema_version'] == 'supply-season-definition-v1' and all(d[k] == v for k,v in FLAGS.items()),
              'SCOPE_HOLD: explicit synthetic season definition required')
        _need(d['code_sha256'] == CODE_SHA256, 'CODE_HOLD: selected season code required')
        reader._closed(d['source'], {'artifact_sha256','frame_index'})
        reader._closed(d['rights'], {'use','display','redistribute'})
        _need(all(type(v) is bool for v in d['rights'].values()) and d['rights']['use'],
              'RIGHTS_HOLD: explicit current use required')
        with MorphologyBlobStore(workspace.source_directory, workspace.access) as source:
            manifest, frames, witnesses = reader._load(source, d['source']['artifact_sha256'])
            index = d['source']['frame_index']
            _need(type(index) is int and 0 <= index < len(frames), 'INDEX_HOLD: existing source frame required')
            f = frames[index]
            _need(f['checkpoint_sha256'] is not None and f['phase'] == 'original_grid_endpoint',
                  'SOURCE_HOLD: this version imports original grid checkpoint frames only')
            original = json.loads(witnesses[f['checkpoint_sha256']][0])
            context = json.loads(witnesses[f['context_sha256']][0])
            seed = context['descriptor']['seed']
            basis = {'schema_version':'supply-season-basis-v1','source':deepcopy(d['source']),
                     'source_checkpoint_sha256':f['checkpoint_sha256'], 'seed':seed,
                     'root_program':json.loads(witnesses[manifest['root_inputs']['program']['sha256']][0]),
                     'root_seed':json.loads(witnesses[manifest['root_inputs']['seed']['sha256']][0]),
                     'shoot_base_temperature':manifest['shoot_base_temperature'],
                     'profile_sha256':{name:manifest['root_inputs'][name]['sha256'] for name in
                                      ('growth_profile','cohort_profile','transport_profile','exchange_profile')}}
            span = d['forcing_span']
            reader._closed(span, {'begin','end','forcing_and_fruit_entry_sha256'})
            dt = Fraction(seed['original_numerical']['step_seconds'])
            begin, end = x(span['begin'],'s'), x(d['stop_at'],'s')
            forcing = {k:seed['program']['scenario'][k] for k in ('forcing','fruit_entry')}
            _need(begin == x(f['at']['elapsed_seconds_exact'],'s') and begin < end == x(span['end'],'s')
                  and dt > 0 and end % dt == begin % dt == 0 and (end-begin)/dt <= MAX_HISTORY_STEPS,
                  'TIME_HOLD: bounded original-grid constant forcing coverage required')
            _need(d['method'] == seed['original_numerical']['method']
                  and span['forcing_and_fruit_entry_sha256'] == _hash(forcing),
                  'FORCING_HOLD: explicitly pinned original constant forcing and fruit entry required')
            _need(not d['rights']['redistribute'] or manifest['redistribution_authorized'],
                  'RIGHTS_HOLD: definition cannot escalate source redistribution')
            s.source, s.manifest, s.source_witnesses = source, manifest, witnesses
            s.definition, s.original, s.basis, s.dt = d, original, basis, dt
            s.profiles = {name:cls(witnesses[manifest['root_inputs'][name]['sha256']][0]) for name,cls in
                          [('growth_profile',growth.ReferenceParameters),('cohort_profile',cohort.ReferenceFruitCohortParameters),
                           ('transport_profile',transport.ReferenceFruitTransportParameters),('exchange_profile',exchange.ReferenceParameters)]}
            indices = {row['compartment_id']:i for i,row in enumerate(seed['program']['stem_root_compartments'])}
            s.data = {**basis, 'program':seed['program'],'organs':seed['organs'],'costs':seed['costs'],
                      'profiles':s.profiles,'stem_stock_indices':[indices[row['compartment_id']] for row in seed['organs']['internodes']]}
            s.units = books.flux_units(s.data['program'], s.data['organs'])
            yield s


def _handle(s, cursor_sha, cursor, current):
    return SeasonHandle(cursor_sha, _raw(current,CURRENT_MAX), _raw(s.basis), _raw(cursor,CURRENT_MAX),
                        s.definition_ref, s.workspace, _TOKEN)


def _cursor(s, current_sha, basis_sha, previous=None, page=None):
    return {**FLAGS,'schema_version':'supply-season-cursor-v1','code_sha256':CODE_SHA256,
            'definition_sha256':s.definition_ref,'basis_sha256':basis_sha,'current_sha256':current_sha,
            'previous_cursor_sha256':previous,'history_page_sha256':page}


def open_season(source_or_cursor_ref, definition_ref, owned_workspace):
    """Admit a checked source frame or restore a caller-trusted stored cursor hash."""
    with _session(definition_ref, owned_workspace) as s:
        if type(source_or_cursor_ref) is SourceRef:
            _need(vars(source_or_cursor_ref) == s.definition['source'], 'SOURCE_HOLD: selected definition source required')
            basis_sha = _put(s, s.basis)
            current = _initial(s)
            current_sha = _put(s, current, CURRENT_MAX)
            cursor = _cursor(s, current_sha, basis_sha)
            cursor_sha = _put(s, cursor, CURRENT_MAX)
        else:
            _need(type(source_or_cursor_ref) is CursorRef, 'CONTEXT_HOLD: source or cursor reference required')
            cursor_sha = source_or_cursor_ref.sha256
            cursor, current = _restore(s, cursor_sha)
        _check(s)
        return _handle(s, cursor_sha, cursor, current)


def _clock(s, totals, at):
    seed = s.data['seed']
    air = Fraction(totals[list(s.units).index('indoor_air_temperature_time')])
    elapsed = at - x(seed['initial_sample']['at']['elapsed_seconds_exact'],'s')
    schedule = deepcopy(seed['schedule'])
    age = x(schedule['age_exact'],'degC_day') + (air-Fraction(s.basis['shoot_base_temperature'])*elapsed)/86400
    _need(age >= x(seed['schedule']['age_exact'],'degC_day'), 'CLOCK_HOLD: monotone original shoot clock required')
    schedule['age_exact'] = q(age,'degC_day')
    return schedule


def _numeric(s, before, state, totals, derived, at):
    steps = before['branch_steps']+1
    # This arithmetic function has an unused context argument; no old-owner capability is supplied.
    local, global_books, diagnostics, lifetime = books.calculate(None,s.data,state,{'derived':derived},totals,steps,at)
    result = deepcopy(before)
    result.update(at={'time_origin_utc':before['at']['time_origin_utc'],'elapsed_seconds_exact':q(at,'s')},
                  branch_steps=steps,grid_index=before['grid_index']+1,phase='original_grid_endpoint',
                  schedule=_clock(s,totals,at),output_cursor=before['output_cursor']+1,
                  branch_integrated_transfers={k:{'value':v,'unit':unit} for (k,unit),v in zip(s.units.items(),totals,strict=True)},
                  lifetime_transfers_exact={k:q(v,s.units[k]) for k,v in lifetime.items()},
                  branch_ledgers=local,global_ledgers=global_books,geometry_diagnostics=diagnostics)
    result['last_confirmed'] = {'at':deepcopy(result['at']),'state':list(state),'derived':deepcopy(derived)}
    result['output_prefix_sha256'] = _hash({'previous':before['output_prefix_sha256'],
        'sample_sha256':_hash(result['last_confirmed']),'branch_steps':steps,
        'definition_sha256':s.definition_ref,'model_version':VERSION})
    _raw(result,CURRENT_MAX)
    return result


def _reason(error):
    if isinstance(error,OSError):
        suffix = f' (errno {error.errno})' if type(error.errno) is int else ''
        return 'STORAGE_HOLD: local artifact I/O failed'+suffix
    message = str(error)
    prefix = message.split(':',1)[0]
    if prefix.endswith('_HOLD') and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_' for c in prefix):
        return message[:1024]
    if isinstance(error,(OverflowError,ZeroDivisionError)):
        return 'NUMERIC_HOLD: unrepresentable season arithmetic'
    return 'INPUT_HOLD: invalid season record or request'


def _vector(value, size):
    _need(type(value) is list and len(value) == size and all(type(v) is float and isfinite(v) for v in value),
          'STATE_HOLD: complete finite binary64 vector required')
    return tuple(value)


def _shape_current(s, current):
    reader._closed(current, {'schema_version',*FLAGS,*NUMERIC_FIELDS})
    _need(current['schema_version'] == 'supply-season-current-v1' and all(current[k] == v for k,v in FLAGS.items()),
          'SCOPE_HOLD: new synthetic family current state required')
    at = x(current['at']['elapsed_seconds_exact'],'s')
    _need(x(s.original['at']['elapsed_seconds_exact'],'s') <= at <= x(s.definition['stop_at'],'s')
          and at % s.dt == 0 and current['at']['time_origin_utc'] == s.original['at']['time_origin_utc']
          and current['last_confirmed']['at'] == current['at'],
          'TIME_HOLD: current state must remain inside declared original-grid forcing coverage')


def _verify_trace(s, before, current, trace):
    reader._closed(trace, {'left_elapsed_seconds_exact','right_elapsed_seconds_exact','step_seconds_exact',
                          'stages','endpoint','flux_order','shoot_clock_certificate'})
    left = x(before['at']['elapsed_seconds_exact'],'s')
    _need(trace['left_elapsed_seconds_exact'] == q(left,'s') and trace['right_elapsed_seconds_exact'] == q(left+s.dt,'s')
          and trace['step_seconds_exact'] == q(s.dt,'s'), 'TIME_HOLD: contiguous original-grid step required')
    y = tuple(before['last_confirmed']['state'])
    _need(type(trace['stages']) is list and len(trace['stages']) == 4, 'TRACE_HOLD: four stored RK stages required')
    rates, flows, previous_rates = [], [], None
    for name,offset,row in zip(('k1','k2','k3','k4'),(0,s.dt/2,s.dt/2,s.dt),trace['stages'],strict=True):
        reader._closed(row, {'stage','at_elapsed_seconds_exact','state','rates','flux'})
        expected = y if previous_rates is None else combine(y,(previous_rates,),(Fraction(1),),offset)
        _need(row['stage'] == name and row['at_elapsed_seconds_exact'] == q(left+offset,'s')
              and _vector(row['state'],len(y)) == expected, 'TRACE_HOLD: exact RK stage state/time order required')
        previous_rates = _vector(row['rates'],len(y))
        rates.append(previous_rates)
        flows.append(_vector(row['flux'],len(s.units)))
    weights = (Fraction(1,6),Fraction(1,3),Fraction(1,3),Fraction(1,6))
    end = combine(y,tuple(rates),weights,s.dt)
    totals = combine(tuple(before['branch_integrated_transfers'][k]['value'] for k in s.units),tuple(flows),weights,s.dt)
    reader._closed(trace['endpoint'], {'state','rates','flux'})
    _need(_vector(trace['endpoint']['state'],len(y)) == end, 'TRACE_HOLD: actual shared-stage endpoint required')
    _vector(trace['endpoint']['rates'],len(y)); _vector(trace['endpoint']['flux'],len(s.units))
    _need(trace['flux_order'] == [{'name':k,'unit':v} for k,v in s.units.items()], 'UNIT_HOLD: original full flux order required')
    expected = _numeric(s,before,end,totals,current['last_confirmed']['derived'],left+s.dt)
    _need(current == expected, 'CHECKPOINT_HOLD: exact state/clock/accumulators/accounts/prefix required')
    certificate = arithmetic._interval_clock(s.data,before,trace,current['schedule'])
    _need(trace['shoot_clock_certificate'] == certificate
          and x(current['schedule']['age_exact'],'degC_day') < x(current['schedule']['next_threshold_exact'],'degC_day'),
          'EVENT_HOLD: stored step cannot consume or skip a pending threshold')


def _restore(s, cursor_sha):
    selected = selected_current = None
    seen = set()
    while True:
        _need(cursor_sha not in seen and len(seen) <= MAX_HISTORY_STEPS, 'CAPACITY_HOLD: bounded acyclic season history required')
        seen.add(cursor_sha)
        cursor = _get(s,cursor_sha,CURRENT_MAX)
        reader._closed(cursor, {'schema_version',*FLAGS,'code_sha256','definition_sha256','basis_sha256',
                               'current_sha256','previous_cursor_sha256','history_page_sha256'})
        _need(cursor == _cursor(s,cursor['current_sha256'],_hash(s.basis),cursor['previous_cursor_sha256'],cursor['history_page_sha256']),
              'CONTEXT_HOLD: original code/definition/basis/claim flags required')
        _need(_get(s,cursor['basis_sha256']) == s.basis, 'SOURCE_HOLD: actual sufficient basis and origins required')
        current = _get(s,cursor['current_sha256'],CURRENT_MAX)
        _shape_current(s,current)
        if selected is None:
            selected, selected_current = cursor, current
        previous = cursor['previous_cursor_sha256']
        if previous is None:
            _need(cursor['history_page_sha256'] is None and current == _initial(s), 'SOURCE_HOLD: actual admitted origin state required')
            break
        parent = _get(s,previous,CURRENT_MAX)
        before = _get(s,parent['current_sha256'],CURRENT_MAX)
        _shape_current(s,before)
        page = _get(s,cursor['history_page_sha256'])
        reader._closed(page, {'schema_version','kind','previous_cursor_sha256','before_current_sha256','after_current_sha256','interval'})
        _need(page['schema_version'] == 'supply-season-history-page-v1' and page['kind'] == 'step'
              and page['previous_cursor_sha256'] == previous and page['before_current_sha256'] == parent['current_sha256']
              and page['after_current_sha256'] == cursor['current_sha256'], 'HISTORY_HOLD: complete ordered current/history references required')
        _verify_trace(s,before,current,page['interval'])
        cursor_sha = previous
    return selected, selected_current


def _request(s, request, current):
    _need(type(request) is AdvanceRequest, 'BUDGET_HOLD: explicit bounded advance request required')
    for name,maximum in [('step_budget',128),('rhs_budget',1024),('record_budget',128),('byte_budget',PAGE_MAX),('wall_seconds',60)]:
        value = getattr(request,name)
        _need(type(value) is int and 1 <= value <= maximum, 'BUDGET_HOLD: bounded '+name+' required')
    _need(request.cancelled is None or callable(request.cancelled), 'BUDGET_HOLD: trusted cancellation probe required')
    stop = x(request.stop_at,'s')
    _need(x(current['at']['elapsed_seconds_exact'],'s') <= stop <= x(s.definition['stop_at'],'s') and stop % s.dt == 0,
          'TIME_HOLD: covered original-grid requested stop required')
    return stop


def _interrupt(request, progress, started):
    _need(time.monotonic()-started <= request.wall_seconds, 'WALL_HOLD: bounded advance time exhausted')
    if request.cancelled is not None:
        _need(request.cancelled() is False, 'CANCELLED_HOLD: calculation cancelled')


def _rhs(s, state, request, progress, started, label):
    progress['stage'] = label
    _interrupt(request,progress,started)
    _need(state[104] >= s.basis['shoot_base_temperature'], 'TEMPERATURE_DOMAIN_HOLD: air below shoot base')
    _need(progress['current_validation_RHS_evaluations']+progress['new_RHS_evaluations'] < request.rhs_budget,
          'BUDGET_HOLD: RHS evaluation budget exhausted')
    key = 'current_validation_RHS_evaluations' if label == 'current_validation' else 'new_RHS_evaluations'
    progress[key] += 1
    inputs = [s.data[k] for k in ('program','organs','costs')]
    snapshot = _raw(inputs)
    result = stage.evaluate(inputs[0],tuple(state),inputs[1],inputs[2],s.profiles)
    _need(_raw(inputs) == snapshot, 'SOURCE_HOLD: stage changed immutable program/organ/cost inputs')
    return result


def _step(s, before, rhs, request, progress, started):
    state = tuple(before['last_confirmed']['state'])
    at = x(before['at']['elapsed_seconds_exact'],'s')
    rows = []
    trial = state
    for name,offset in [('k1',Fraction(0)),('k2',s.dt/2),('k3',s.dt/2),('k4',s.dt)]:
        if name != 'k1':
            trial = combine(state,(tuple(rhs['rates']),),(Fraction(1),),offset)
            rhs = _rhs(s,trial,request,progress,started,name)
        rows.append({'stage':name,'at_elapsed_seconds_exact':q(at+offset,'s'),'state':list(trial),
                     'rates':list(rhs['rates']),'flux':list(books.flux(s.data['program'],trial,rhs,s.data['organs']))})
    weights = (Fraction(1,6),Fraction(1,3),Fraction(1,3),Fraction(1,6))
    end = combine(state,tuple(tuple(row['rates']) for row in rows),weights,s.dt)
    totals = combine(tuple(before['branch_integrated_transfers'][k]['value'] for k in s.units),
                     tuple(tuple(row['flux']) for row in rows),weights,s.dt)
    rhs = _rhs(s,end,request,progress,started,'endpoint')
    trace = {'left_elapsed_seconds_exact':q(at,'s'),'right_elapsed_seconds_exact':q(at+s.dt,'s'),
             'step_seconds_exact':q(s.dt,'s'),'stages':rows,'endpoint':{'state':list(end),'rates':list(rhs['rates']),
             'flux':list(books.flux(s.data['program'],end,rhs,s.data['organs']))},
             'flux_order':[{'name':k,'unit':v} for k,v in s.units.items()]}
    schedule = _clock(s,totals,at+s.dt)
    trace['shoot_clock_certificate'] = arithmetic._interval_clock(s.data,before,trace,schedule)
    return end, totals, rhs, trace, schedule


def advance(handle, request, *, material=None):
    """Advance actual equations; atomically expose only fully checked cursor refs."""
    progress = {'stage':'admission','current_validation_RHS_evaluations':0,'new_RHS_evaluations':0,
                'steps_attempted':0,'records_emitted':0,'bytes_emitted':0,'past_intervals_reintegrated':0}
    confirmed = None
    started = time.monotonic()
    try:
        _need(type(handle) is SeasonHandle and handle._token is _TOKEN, 'CONTEXT_HOLD: genuine new-family handle required')
        with _session(handle._definition,handle._workspace) as s:
            cursor, current = _restore(s,handle.cursor_sha256)
            _need(_raw(cursor,CURRENT_MAX) == handle._cursor and _raw(current,CURRENT_MAX) == handle._current
                  and _raw(s.basis) == handle._basis, 'CONTEXT_HOLD: unchanged actual handle payloads required')
            confirmed = handle
            try:
                _need(material is None, 'MATERIAL_HOLD: this version cannot adopt material declarations')
                stop = _request(s,request,current)
                _check(s)
                rhs = _rhs(s,tuple(current['last_confirmed']['state']),request,progress,started,'current_validation')
                _need(rhs['derived'] == current['last_confirmed']['derived'], 'CHECKPOINT_HOLD: actual current derived values required')
                status, pending = 'yielded', None
                while x(current['at']['elapsed_seconds_exact'],'s') < stop:
                    if (progress['steps_attempted'] >= request.step_budget or progress['records_emitted'] >= request.record_budget
                            or progress['current_validation_RHS_evaluations']+progress['new_RHS_evaluations']+4 > request.rhs_budget):
                        break
                    _interrupt(request,progress,started)
                    progress['steps_attempted'] += 1
                    state, totals, rhs, trace, schedule = _step(s,current,rhs,request,progress,started)
                    if x(schedule['age_exact'],'degC_day') >= x(schedule['next_threshold_exact'],'degC_day'):
                        pending = {'reason':'EVENT_HOLD: next threshold requires refined candidate and explicit material',
                            'left_at':trace['left_elapsed_seconds_exact'],'right_at':trace['right_elapsed_seconds_exact'],
                            'left_age_exact':current['schedule']['age_exact'],'right_age_exact':schedule['age_exact'],
                            'threshold_exact':schedule['next_threshold_exact'],'next_sequence':schedule['next_sequence'],
                            'schedule_consumed':False,'candidate_or_checkpoint_issued':False}
                        page = {'schema_version':'supply-season-pending-page-v1','definition_sha256':s.definition_ref,
                                'previous_cursor_sha256':confirmed.cursor_sha256,'pending':pending,'interval':trace}
                        cost = len(_raw(page))
                        if progress['bytes_emitted']+cost > request.byte_budget:
                            pending = None
                            break
                        progress['stage'] = 'pending_publication'
                        _check(s)
                        digest = _put(s,page)
                        _interrupt(request,progress,started)
                        _check(s)
                        pending = {**pending,'page_sha256':digest}
                        progress['records_emitted'] += 1; progress['bytes_emitted'] += cost
                        status = 'awaiting_material'
                        break
                    progress['stage'] = 'endpoint_books'
                    new = _numeric(s,current,state,totals,rhs['derived'],x(trace['right_elapsed_seconds_exact'],'s'))
                    current_sha = _hash(new)
                    page = {'schema_version':'supply-season-history-page-v1','kind':'step',
                            'previous_cursor_sha256':confirmed.cursor_sha256,'before_current_sha256':cursor['current_sha256'],
                            'after_current_sha256':current_sha,'interval':trace}
                    page_sha = _hash(page)
                    proposed = _cursor(s,current_sha,cursor['basis_sha256'],confirmed.cursor_sha256,page_sha)
                    cost = sum(len(_raw(v)) for v in (new,page,proposed))
                    if progress['bytes_emitted']+cost > request.byte_budget:
                        break
                    progress['stage'] = 'publication'
                    _interrupt(request,progress,started)
                    _check(s)
                    _put(s,new,CURRENT_MAX); _put(s,page); digest = _put(s,proposed,CURRENT_MAX)
                    _interrupt(request,progress,started)
                    _check(s)
                    cursor, current = proposed, new
                    confirmed = _handle(s,digest,cursor,current)
                    progress['records_emitted'] += 1; progress['bytes_emitted'] += cost
                if x(current['at']['elapsed_seconds_exact'],'s') == x(s.definition['stop_at'],'s'):
                    status = 'completed'
                _interrupt(request,progress,started)
                _check(s)
                return AdvanceOutcome(status,confirmed,None,None,pending,deepcopy(progress))
            except (OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError) as error:
                first = _reason(error)
                authority = None
                try:
                    _check(s)
                except (OSError,ValueError,TypeError,KeyError) as late:
                    authority = _reason(late); confirmed = None
                return AdvanceOutcome('hold',confirmed,first,progress['stage'],None,deepcopy(progress),handle.cursor_sha256,authority)
    except (OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError) as error:
        return AdvanceOutcome('hold',None,_reason(error),progress['stage'],None,deepcopy(progress),
                              handle.cursor_sha256 if type(handle) is SeasonHandle else None)
