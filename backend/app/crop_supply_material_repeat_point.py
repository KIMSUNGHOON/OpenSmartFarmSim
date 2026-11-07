"""Source-bound successor candidates using the original material mathematics."""
from contextlib import contextmanager
import fcntl
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import stat
import sys
import time
from types import SimpleNamespace
from typing import NamedTuple

from . import crop_supply_material_owner as original
from .content_access import ContentAccess
from .crop_morphology_artifact_io import MorphologyBlobStore, MorphologyArtifactHold
from . import job_store as jobs

old = original.point
base, kernel, locator = original.base, original.kernel, old.candidate.locator
state_math, books = old.candidate, old.candidate.books
q, x, need, raw, digest = base.q, base.x, base._need, base._raw, base._hash
FLAGS = dict(base.FLAGS)
VERSION = 'supply-material-successor-point-research-v1'
POLICY = 'explicit-compatible-successor-seed-on-active-forcing-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
INPUT_MAX = old.INPUT_MAX
ERRORS = (OSError, ValueError, TypeError, KeyError, OverflowError, ZeroDivisionError)
DEPENDENCIES = (
    'crop_supply_material_owner', 'crop_supply_material_point', 'crop_supply_material_proof',
    'crop_supply_forcing_owner', 'crop_supply_forcing_threshold', 'crop_supply_forcing_threshold_state',
    'crop_supply_threshold_state_books', 'crop_supply_forcing_interval', 'crop_supply_season',
    'crop_funded_event_time', 'crop_supply_morphology_point_core',
    'crop_supply_morphology_repeat_point_books', 'crop_supply_morphology_birth_stage',
    'crop_morphology_artifact_io', 'content_access',
)


def _signature(module):
    functions = []
    for name, value in vars(module).items():
        if inspect.isfunction(value):
            functions.append((name, value, value.__code__))
        elif inspect.isclass(value) and value.__module__ == module.__name__:
            functions.append((name, value, tuple((k, v,
                v.__code__ if inspect.isfunction(v) else v.__func__.__code__ if isinstance(v, (staticmethod, classmethod))
                else tuple((f, f.__code__) for f in (v.fget, v.fset, v.fdel) if f is not None))
                for k, v in vars(value).items()
                if inspect.isfunction(v) or isinstance(v, (staticmethod, classmethod, property)))))
        elif name in ('VERSION', 'POLICY', 'CODE_SHA256', 'FLAGS', 'LIMITS', '_TOKEN') or name.endswith('_FIELDS'):
            captured = tuple(sorted(value.items())) if type(value) is dict else frozenset(value) if type(value) is set else value
            functions.append((name, captured))
    return tuple(functions)


def _dependencies():
    return {'backend/app/' + name + '.py': sha256(Path(sys.modules[__package__ + '.' + name].__file__).read_bytes()).hexdigest()
            for name in DEPENDENCIES}


_DEPENDENCY_SHA = _dependencies()
_DEPENDENCY_SIGNATURE = {name: _signature(sys.modules[__package__ + '.' + name]) for name in DEPENDENCIES}
_EXTRA_DEPENDENCY_FIELDS = tuple((module, sha256(Path(module.__file__).read_bytes()).hexdigest(), _signature(module))
    for module in (jobs, base.reader))
_ACCESS_METHODS = {name: getattr(ContentAccess, name) for name in ('validate', 'prepare_new', 'require_writer')}
_CLOSE = MorphologyBlobStore.close
_STAGE = base.stage.evaluate
_TOKEN = object()


def _capture_acquisition(job_module=jobs, job_class=jobs.JobStore, store_class=MorphologyBlobStore,
                         access_class=ContentAccess, lock_module=fcntl, os_module=os):
    return (globals().get('jobs'), vars(job_module).get('JobStore'),
        vars(job_class).get('__init__'), vars(job_class).get('_content_directory'),
        vars(job_module).get('_open_directory_nofollow'), globals().get('MorphologyBlobStore'),
        vars(store_class).get('_guard'), vars(store_class).get('close'), globals().get('ContentAccess'),
        vars(access_class).get('validate'), vars(access_class).get('prepare_new'), vars(access_class).get('require_writer'),
        globals().get('fcntl'), vars(lock_module).get('flock'), globals().get('os'), vars(os_module).get('close'), object.__new__,
        vars(lock_module).get('LOCK_EX'), vars(lock_module).get('LOCK_NB'),
        tuple((value, value.__code__) for value in (vars(job_class).get('__init__'),
            vars(job_class).get('_content_directory'), vars(job_module).get('_open_directory_nofollow'),
            vars(store_class).get('_guard'), vars(store_class).get('close'),
            vars(access_class).get('validate'), vars(access_class).get('prepare_new'),
            vars(access_class).get('require_writer')) if inspect.isfunction(value)))


_ACQUISITION_FIELDS = _capture_acquisition()
_CANONICAL_READ_FIELDS = (2 * 1024**2, base._get.__defaults__)


def _code_metadata(modules, assertion=need):
    root = Path(base.reader.__file__).resolve().parents[2]
    paths = {root / name for name in base.reader.SOURCE_PATHS}
    paths.update(Path(sys.modules[__package__ + '.' + name].__file__) for name in DEPENDENCIES)
    paths.update(Path(module.__file__) for module in modules)
    result = []
    for path in sorted(paths):
        info = path.stat(follow_symlinks=False)
        assertion(stat.S_ISREG(info.st_mode), 'CODE_HOLD: original regular implementation files required')
        result.append((str(path), info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
                       info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns))
    return tuple(result)


def _code(signature=_signature, metadata=None, file_metadata=_code_metadata, assertion=need, acquisition=_ACQUISITION_FIELDS, capture=_capture_acquisition, extra=_EXTRA_DEPENDENCY_FIELDS):
    from . import crop_supply_material_repeat_owner as owner
    from . import crop_supply_material_repeat_proof as proof
    modules = (sys.modules[__name__], owner, proof)
    before = file_metadata(modules)
    if metadata is not None:
        assertion(before == metadata, 'CODE_HOLD: validated implementation file identity changed')
    for module in modules:
        assertion(sha256(Path(module.__file__).read_bytes()).hexdigest() == module.CODE_SHA256
             and signature(module) == module._SIGNATURE, 'CODE_HOLD: unchanged successor implementation required')
    assertion(_dependencies() == _DEPENDENCY_SHA, 'CODE_HOLD: original dependency bytes changed')
    for name, expected in _DEPENDENCY_SIGNATURE.items():
        assertion(signature(sys.modules[__package__ + '.' + name]) == expected,
             'CODE_HOLD: original numerical or policy dispatch changed')
    assertion(base.stage.evaluate is _STAGE, 'CODE_HOLD: original stage evaluator required')
    assertion(capture() == acquisition, 'CODE_HOLD: fixed real-store acquisition dispatch required')
    for module, expected_hash, expected_signature in extra:
        assertion(sha256(Path(module.__file__).read_bytes()).hexdigest() == expected_hash
             and signature(module) == expected_signature, 'CODE_HOLD: fixed source admission/storage helpers required')
    assertion(type(base.PAGE_MAX) is int and base.PAGE_MAX == _CANONICAL_READ_FIELDS[0]
         and base._get.__defaults__ is _CANONICAL_READ_FIELDS[1]
         and type(_CANONICAL_READ_FIELDS[1]) is tuple and len(_CANONICAL_READ_FIELDS[1]) == 1
         and type(_CANONICAL_READ_FIELDS[1][0]) is int and _CANONICAL_READ_FIELDS[1][0] == _CANONICAL_READ_FIELDS[0],
         'CODE_HOLD: original canonical source limits/defaults required')
    if metadata is None:
        old._code()
    assertion(file_metadata(modules) == before, 'CODE_HOLD: implementation changed during validation')
    return before


class _Algebra(NamedTuple):
    source: bytes
    current: bytes
    basis: bytes
    pending: str
    tolerance: bytes
    observations: bytes
    derived: bytes
    inputs: bytes | None
    after_stage: bytes | None
    token: object


class _Meter:
    def __init__(self, *, cancelled=None, wall_seconds=60, request=None):
        self.started = time.monotonic()
        self.deadline = self.started + (wall_seconds if type(wall_seconds) is int and 1 <= wall_seconds <= 60 else 60)
        self.cancelled = cancelled
        self.steps, self.rhs, self.records, self.bytes = 128, 1024, 128, base.PAGE_MAX
        self.invalid = None
        try:
            need(type(wall_seconds) is int and 1 <= wall_seconds <= 60
                 and (cancelled is None or callable(cancelled)), 'BUDGET_HOLD: bounded whole-call controls required')
            if request is not None:
                need(type(request) is base.AdvanceRequest, 'BUDGET_HOLD: original bounded request required')
                for name, maximum in [('step_budget', 128), ('rhs_budget', 1024), ('record_budget', 128),
                                      ('byte_budget', base.PAGE_MAX), ('wall_seconds', 60)]:
                    need(type(getattr(request, name)) is int and 1 <= getattr(request, name) <= maximum,
                         'BUDGET_HOLD: bounded ' + name + ' required')
                self.steps, self.rhs = request.step_budget, request.rhs_budget
                self.records, self.bytes = request.record_budget, request.byte_budget
        except ERRORS as error:
            self.invalid = error
        self.p = {k: 0 for k in ('positive_segments_attempted', 'actual_RHS_evaluations', 'record_units_reserved',
            'record_units_committed', 'bytes_reserved', 'bytes_emitted', 'CAS_puts_attempted',
            'CAS_puts_completed', 'root_bisections', 'past_confirmed_intervals_reintegrated')}
        self.p.update(stage='admission', failed_RHS_count_unreported=False, failed_put_effect_unknown=False)
        self.check = None
        self.code_metadata = None
        self.algebra = None
        self.algebra_hits = 0

    def fence(self, stage=None, code=_code):
        try:
            if self.invalid is not None:
                raise self.invalid
            if stage is not None:
                self.p['stage'] = stage
            self.code_metadata = code(metadata=self.code_metadata)
            need(time.monotonic() <= self.deadline, 'WALL_HOLD: shared successor deadline exhausted')
            if self.cancelled is not None:
                need(self.cancelled() is False, 'CANCELLED_HOLD: successor calculation cancelled')
                code(metadata=self.code_metadata)
            if self.check is not None:
                self.check()
            code(metadata=self.code_metadata)
            need(time.monotonic() <= self.deadline, 'WALL_HOLD: shared successor deadline exhausted')
        except BaseException:
            self.algebra = None
            raise

    def segment(self):
        self.fence()
        need(self.p['positive_segments_attempted'] < self.steps, 'BUDGET_HOLD: positive segment budget exhausted')
        self.p['positive_segments_attempted'] += 1

    def evaluate(self, math, state, stage, evaluator=_STAGE):
        self.fence(stage)
        need(self.p['actual_RHS_evaluations'] < self.rhs, 'BUDGET_HOLD: shared RHS budget exhausted')
        need(state[104] >= math.basis['shoot_base_temperature'], 'TEMPERATURE_DOMAIN_HOLD: air below shoot base')
        values = [math.data[k] for k in ('program', 'organs', 'costs')]
        snapshot = raw(values)
        self.p['actual_RHS_evaluations'] += 1
        try:
            result = evaluator(values[0], tuple(state), values[1], values[2], math.profiles)
            need(snapshot == raw(values), 'SOURCE_HOLD: numerical evaluator changed immutable inputs')
            self.fence()
            return result
        except BaseException:
            self.algebra = None
            raise

    def reserve(self, values, records):
        self.fence('publication')
        cost = sum(len(raw(v, maximum)) for v, maximum in values)
        need(self.p['record_units_reserved'] + records <= self.records
             and self.p['bytes_reserved'] + cost <= self.bytes, 'BUDGET_HOLD: publication batch exceeds call budget')
        self.p['record_units_reserved'] += records
        self.p['bytes_reserved'] += cost
        return cost


def _directory(path):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts and path.resolve() == path,
         'STORAGE_HOLD: fixed absolute nonsymlink directory required')
    info = path.stat()
    need(stat.S_ISDIR(info.st_mode), 'STORAGE_HOLD: actual directory required')
    return (str(path), info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid)


def _workspace_snapshot(workspace):
    forcing = workspace.forcing_workspace
    root = forcing.source_workspace
    access = workspace.access
    need(type(workspace) is original.Workspace and type(access) is ContentAccess
         and forcing.access is access and root.access is access, 'STORAGE_HOLD: one original concrete file policy required')
    for name, expected in _ACCESS_METHODS.items():
        method = getattr(access, name)
        need(getattr(method, '__self__', None) is access and getattr(method, '__func__', None) is expected,
             'CODE_HOLD: unchanged concrete access dispatch required')
    paths = [root.source_directory, root.archive_directory, forcing.archive_directory, workspace.archive_directory]
    return (tuple((id(v), tuple(vars(v).items())) for v in (workspace, forcing, root, access)),
            tuple(_directory(p) for p in paths))




def _open_store_v2(directory, access, *, write, meter, acquisition=_ACQUISITION_FIELDS):
    meter.fence('source_validation')
    job_class, initialize, content_directory = acquisition[1], acquisition[2], acquisition[3]
    store_class, guard, close_fd = acquisition[5], acquisition[6], acquisition[15]
    store = acquisition[16](store_class)
    state = vars(store)
    state['_fd'] = None
    try:
        need(type(access) is acquisition[8] and type(write) is bool, 'STORAGE_HOLD: explicit file policy required')
        directory = Path(directory)
        need(directory.is_absolute() and '..' not in directory.parts, 'STORAGE_HOLD: absolute artifact path required')
        store._access, store._write = access, write
        job = acquisition[16](job_class)
        initialize(job, 'not-used-for-morphology-files', 'morphology_research', directory, content_access=access)
        store._jobs = job
        meter.fence()
        store._fd = content_directory(job, create=write)
        meter.fence()
        if write:
            acquisition[13](store._fd, acquisition[17] | acquisition[18])
        meter.fence()
        guard(store)
        meter.fence()
        return store
    except BaseException as error:
        fd = state['_fd']
        if fd is not None:
            close_fd(fd)
            state['_fd'] = None
        if isinstance(error, (OSError, ValueError, TypeError)) and not str(error).startswith(
                ('CODE_HOLD:', 'CANCELLED_HOLD:', 'WALL_HOLD:', 'BUDGET_HOLD:')):
            raise MorphologyArtifactHold('STORAGE_HOLD: owned artifact directory unavailable') from None
        raise


@contextmanager
def _source_archive_v2(directory, access, *, write, meter, close_fd=_ACQUISITION_FIELDS[15]):
    store = _open_store_v2(directory, access, write=write, meter=meter)
    state = vars(store)
    try:
        meter.fence()
        yield store
        meter.fence()
    finally:
        fd = state['_fd']
        if fd is not None:
            close_fd(fd)
            state['_fd'] = None


@contextmanager
def _base_source_session_v2(definition_ref, workspace, meter):
    meter.fence('source_validation')
    base._code()
    base._need(type(workspace) is base.Workspace and type(workspace.access) is base.ContentAccess, 'STORAGE_HOLD: explicit owned season workspace required')
    base._need(base.Path(workspace.source_directory).resolve() != base.Path(workspace.archive_directory).resolve(), 'STORAGE_HOLD: original source and new archive must be separate')
    with _source_archive_v2(workspace.archive_directory, workspace.access, write=True, meter=meter) as archive:
        archive._usage()
        s = base.SimpleNamespace(archive=archive, archive_witnesses={}, definition_ref=definition_ref, workspace=workspace)
        d = base._get(s, definition_ref, base.CURRENT_MAX)
        base.reader._closed(d, {'schema_version', 'source', 'code_sha256', 'method', 'stop_at', 'forcing_span', 'rights', *base.FLAGS})
        base._need(d['schema_version'] == 'supply-season-definition-v1' and all((d[k] == v for k, v in base.FLAGS.items())), 'SCOPE_HOLD: explicit synthetic season definition required')
        base._need(d['code_sha256'] == base.CODE_SHA256, 'CODE_HOLD: selected season code required')
        base.reader._closed(d['source'], {'artifact_sha256', 'frame_index'})
        base.reader._closed(d['rights'], {'use', 'display', 'redistribute'})
        base._need(all((type(v) is bool for v in d['rights'].values())) and d['rights']['use'], 'RIGHTS_HOLD: explicit current use required')
        with _source_archive_v2(workspace.source_directory, workspace.access, write=False, meter=meter) as source:
            manifest, frames, witnesses = base.reader._load(source, d['source']['artifact_sha256'])
            index = d['source']['frame_index']
            base._need(type(index) is int and 0 <= index < len(frames), 'INDEX_HOLD: existing source frame required')
            f = frames[index]
            base._need(f['checkpoint_sha256'] is not None and f['phase'] == 'original_grid_endpoint', 'SOURCE_HOLD: this version imports original grid checkpoint frames only')
            original = base.json.loads(witnesses[f['checkpoint_sha256']][0])
            context = base.json.loads(witnesses[f['context_sha256']][0])
            seed = context['descriptor']['seed']
            basis = {'schema_version': 'supply-season-basis-v1', 'source': base.deepcopy(d['source']), 'source_checkpoint_sha256': f['checkpoint_sha256'], 'seed': seed, 'root_program': base.json.loads(witnesses[manifest['root_inputs']['program']['sha256']][0]), 'root_seed': base.json.loads(witnesses[manifest['root_inputs']['seed']['sha256']][0]), 'shoot_base_temperature': manifest['shoot_base_temperature'], 'profile_sha256': {name: manifest['root_inputs'][name]['sha256'] for name in ('growth_profile', 'cohort_profile', 'transport_profile', 'exchange_profile')}}
            span = d['forcing_span']
            base.reader._closed(span, {'begin', 'end', 'forcing_and_fruit_entry_sha256'})
            dt = base.Fraction(seed['original_numerical']['step_seconds'])
            begin, end = (base.x(span['begin'], 's'), base.x(d['stop_at'], 's'))
            forcing = {k: seed['program']['scenario'][k] for k in ('forcing', 'fruit_entry')}
            base._need(begin == base.x(f['at']['elapsed_seconds_exact'], 's') and begin < end == base.x(span['end'], 's') and (dt > 0) and (end % dt == begin % dt == 0) and ((end - begin) / dt <= base.MAX_HISTORY_STEPS), 'TIME_HOLD: bounded original-grid constant forcing coverage required')
            base._need(d['method'] == seed['original_numerical']['method'] and span['forcing_and_fruit_entry_sha256'] == base._hash(forcing), 'FORCING_HOLD: explicitly pinned original constant forcing and fruit entry required')
            base._need(not d['rights']['redistribute'] or manifest['redistribution_authorized'], 'RIGHTS_HOLD: definition cannot escalate source redistribution')
            s.source, s.manifest, s.source_witnesses = (source, manifest, witnesses)
            s.definition, s.original, s.basis, s.dt = (d, original, basis, dt)
            s.profiles = {name: cls(witnesses[manifest['root_inputs'][name]['sha256']][0]) for name, cls in [('growth_profile', base.growth.ReferenceParameters), ('cohort_profile', base.cohort.ReferenceFruitCohortParameters), ('transport_profile', base.transport.ReferenceFruitTransportParameters), ('exchange_profile', base.exchange.ReferenceParameters)]}
            indices = {row['compartment_id']: i for i, row in enumerate(seed['program']['stem_root_compartments'])}
            s.data = {**basis, 'program': seed['program'], 'organs': seed['organs'], 'costs': seed['costs'], 'profiles': s.profiles, 'stem_stock_indices': [indices[row['compartment_id']] for row in seed['organs']['internodes']]}
            s.units = base.books.flux_units(s.data['program'], s.data['organs'])
            meter.fence()
            yield s


@contextmanager
def _forcing_source_session_v2(definition_ref, workspace, meter):
    meter.fence('source_validation')
    original.forcing._code()
    original.forcing.need(type(workspace) is original.forcing.Workspace and type(workspace.source_workspace) is original.forcing.base.Workspace and (type(workspace.access) is original.forcing.ContentAccess), 'STORAGE_HOLD: trusted source/new archive configuration required')
    old = workspace.source_workspace
    original.forcing.need(original.forcing.Path(workspace.archive_directory).resolve() not in (original.forcing.Path(old.source_directory).resolve(), original.forcing.Path(old.archive_directory).resolve()), 'STORAGE_HOLD: new owner archive must be separate from source stores')
    with _source_archive_v2(workspace.archive_directory, workspace.access, write=True, meter=meter) as archive:
        s = original.forcing.SimpleNamespace(archive=archive, archive_witnesses={}, definition_ref=definition_ref, workspace=workspace)
        archive._usage()
        s.definition = original.forcing.get(s, definition_ref)
        original.forcing._definition_head(s.definition)
        source = s.definition['source']
        original.forcing.base.reader._closed(source, {'definition_sha256', 'cursor_sha256'})
        with _base_source_session_v2(source['definition_sha256'], old, meter) as origin:
            _, current = original.forcing.base._restore(origin, source['cursor_sha256'])
            original.forcing.base._check(origin)
            s.origin = origin
            s.source_current = current
            s.math_basis = origin.basis
            s.profiles = origin.profiles
            s.basis = {'schema_version': 'supply-forcing-owner-basis-v1', 'source': original.forcing.deepcopy(source), 'source_current_sha256': original.forcing.digest(current), 'source_rights': original.forcing.deepcopy(origin.definition['rights']), 'source_arithmetic_code_sha256': original.forcing.base.CODE_SHA256, 'arithmetic_basis': original.forcing.deepcopy(origin.basis)}
            original.forcing._plan(s)
            meter.fence()
            yield s


@contextmanager
def _material_source_session_v2(definition_ref, workspace, meter):
    meter.fence('source_validation')
    original._code()
    original._workspace(workspace)
    with _source_archive_v2(workspace.archive_directory, workspace.access, write=True, meter=meter) as store:
        s = original.SimpleNamespace(archive=store, archive_witnesses={}, workspace=workspace, definition_ref=definition_ref)
        s.definition = original.get(s, definition_ref)
        d = s.definition
        original.base.reader._closed(d, {'schema_version', *original.FLAGS, 'code_sha256', 'proof_code_sha256', 'source', 'pending_page_sha256', 'time_tolerance_seconds_exact', 'inputs', 'expected_point_sha256', 'point_sha256'})
        original.need(d['schema_version'] == 'supply-material-definition-v1' and d['code_sha256'] == original.CODE_SHA256 and (d['proof_code_sha256'] == original.PROOF_SHA256) and all((d[k] == v for k, v in original.FLAGS.items())), 'SCOPE_HOLD: exact material definition required')
        original.base.reader._closed(d['source'], {'definition_sha256', 'cursor_sha256'})
        with _forcing_source_session_v2(d['source']['definition_sha256'], workspace.forcing_workspace, meter) as parent:
            _, current = original.forcing._restore(parent, d['source']['cursor_sha256'])
            source = original.point._source(parent, current)
            value = original.get(s, d['point_sha256'])
            original.need(d['inputs']['cursor_sha256'] == d['source']['cursor_sha256'], 'SOURCE_HOLD: actual forcing cursor required')
            original.proof.verify(parent, current, source, d, value)
            basis, records = original._derive(parent, current, source, value, definition_ref)
            s.parent = parent
            s.source_current = current
            s.point = value
            s.math_basis = basis
            s.origins = records
            s.profiles = parent.profiles
            s.basis = {'schema_version': 'supply-material-owner-basis-v1', 'source': original.deepcopy(d['source']), 'source_current_sha256': original.digest(current), 'point_sha256': d['point_sha256'], 'numeric_basis': basis, 'origin_records': records}
            s.spans = parent.spans
            s.grid = original.Fraction(basis['seed']['original_numerical']['step_seconds'])
            s.stop = parent.stop
            s.rights = original.deepcopy(value['effective_rights'])
            s.basis_raw = original.raw(s.basis)
            meter.fence()
            yield s

class _CanonicalReads(NamedTuple):
    sessions: tuple
    archives: tuple
    validated: dict


def _canonical_reads(s):
    sessions = (s.parent.origin, s.parent, s)
    return _CanonicalReads(sessions, tuple(v.archive for v in sessions), {})


def _archive_recheck_v3(s, index, reads):
    need(type(base.PAGE_MAX) is int and base.PAGE_MAX == _CANONICAL_READ_FIELDS[0]
         and base._get.__defaults__ is _CANONICAL_READ_FIELDS[1]
         and type(_CANONICAL_READ_FIELDS[1]) is tuple and len(_CANONICAL_READ_FIELDS[1]) == 1
         and type(_CANONICAL_READ_FIELDS[1][0]) is int and _CANONICAL_READ_FIELDS[1][0] == _CANONICAL_READ_FIELDS[0],
         'CODE_HOLD: original canonical source limits/defaults required')
    maximum = base.PAGE_MAX if index == 0 else _CANONICAL_READ_FIELDS[1][0]
    for reference in list(s.archive_witnesses):
        base.reader._hash(reference)
        before = base._metadata(os.stat(reference, dir_fd=s.archive._fd, follow_symlinks=False))
        data = s.archive.get(reference, maximum=maximum)
        after = base._metadata(os.stat(reference, dir_fd=s.archive._fd, follow_symlinks=False))
        need(before == after and (reference not in s.archive_witnesses or s.archive_witnesses[reference] == before),
             'STORAGE_HOLD: original season record identity required')
        s.archive_witnesses[reference] = before
        key = (index, reference)
        if key in reads.validated:
            need(type(data) is bytes and 1 <= len(data) <= maximum
                 and type(reads.validated[key]) is bytes and data == reads.validated[key],
                 'STORAGE_HOLD: canonical source record bytes changed')
        else:
            value = base.reader._parse(data, maximum)
            need(base._raw(value, maximum) == data, 'INPUT_HOLD: canonical season record required')
            if sum(map(len, reads.validated.values())) + len(data) <= maximum:
                reads.validated[key] = data


def _source_recheck_v3(s, reads):
    need(type(reads) is _CanonicalReads and len(reads.sessions) == len(reads.archives) == 3
         and s is reads.sessions[2] and s.parent is reads.sessions[1] and s.parent.origin is reads.sessions[0]
         and all(v.archive is a for v, a in zip(reads.sessions, reads.archives, strict=True)),
         'SOURCE_HOLD: canonical validation belongs to the actual held source chain')
    parent, origin = s.parent, s.parent.origin
    original._code()
    original.forcing._code()
    base._code()
    base.reader._fence(origin.source, origin.manifest, origin.source_witnesses)
    _archive_recheck_v3(origin, 0, reads)
    origin.archive._guard()
    origin.archive._usage()
    need(original.forcing.digest(parent.definition) == parent.definition_ref
         and parent.math_basis == parent.basis['arithmetic_basis']
         and original.forcing.digest(parent.source_current) == parent.basis['source_current_sha256'],
         'SOURCE_HOLD: unchanged admitted in-memory source/definition required')
    _archive_recheck_v3(parent, 1, reads)
    parent.archive._guard()
    parent.archive._usage()
    need(original.digest(s.definition) == s.definition_ref and s.math_basis == s.basis['numeric_basis']
         and original.digest(s.point) == s.definition['point_sha256']
         and original.digest(s.source_current) == s.basis['source_current_sha256']
         and original.raw(s.basis) == s.basis_raw,
         'SOURCE_HOLD: unchanged admitted material source required')
    _archive_recheck_v3(s, 2, reads)
    s.archive._guard()
    s.archive._usage()


@contextmanager
def _source(handle, meter):
    from . import crop_supply_material_repeat_owner as owner
    if type(handle) is owner.Handle:
        with owner._session(handle._definition, handle._workspace, meter) as s:
            cursor, current = owner._restore(s, handle.cursor_sha256, meter)
            need(raw(cursor, base.CURRENT_MAX) == handle._cursor and raw(current, base.CURRENT_MAX) == handle._current
                 and raw(s.basis) == handle._basis and handle._token is owner._TOKEN,
                 'CONTEXT_HOLD: exact genuine repeat handle required')
            yield s, current
        return
    need(type(handle) is original.Handle and handle._token is original._TOKEN,
         'CONTEXT_HOLD: genuine material or repeated-material source required')
    meter.fence()
    before = _workspace_snapshot(handle._workspace)
    with _material_source_session_v2(handle._definition, handle._workspace, meter) as s:
        cursor, current = original._restore(s, handle.cursor_sha256)
        need(raw(cursor, base.CURRENT_MAX) == handle._cursor and raw(current, base.CURRENT_MAX) == handle._current
             and raw(s.basis) == handle._basis, 'CONTEXT_HOLD: exact original material handle bytes required')
        s.origin = s.parent.origin
        previous = meter.check
        canonical_reads = _canonical_reads(s)
        def check():
            need(_workspace_snapshot(handle._workspace) == before, 'SOURCE_HOLD: original workspace changed')
            _source_recheck_v3(s, canonical_reads)
        meter.check = check
        try:
            meter.fence('source_validation')
            yield s, current
            meter.fence()
        finally:
            meter.check = previous


def _ref(s, current, cursor):
    return {'owner_version': original.VERSION if type(s.workspace) is original.Workspace else 'supply-material-repeat-owner-research-v1',
            'definition_sha256': s.definition_ref, 'cursor_sha256': cursor,
            'current_sha256': digest(current), 'basis_sha256': digest(s.basis)}


def _event_data(s, current):
    binding_sha = s.origin.manifest['initial_binding']['sha256']
    binding = json.loads(s.origin.source_witnesses[binding_sha][0])
    source = binding['stem_selection']['source_state']
    timeline, schedule = source['timeline_state'], current['numeric']['schedule']
    need(schedule['source_schedule_id'] == timeline['schedule_id']
         and s.math_basis['shoot_base_temperature'] == timeline['base_temperature']['value'],
         'SOURCE_HOLD: original shoot timeline/base required')
    spacing = x(timeline['phyllochron_exact'], 'degC_day')
    need(type(schedule['next_sequence']) is int and spacing > 0
         and schedule['next_sequence'] == schedule['consumed_sequence'] + 1
         and x(schedule['next_threshold_exact'], 'degC_day') == x(schedule['consumed_threshold_exact'], 'degC_day') + spacing,
         'EVENT_HOLD: first actual unconsumed schedule item required')
    identifier = old.material.source_ids._digest(old._entity(timeline, schedule['consumed_sequence'], schedule['consumed_threshold_exact']))
    need(schedule['consumed_event_id'] == 'shoot-event:' + identifier, 'SOURCE_HOLD: actual consumed source identity required')
    entity = old._entity(timeline, schedule['next_sequence'], schedule['next_threshold_exact'])
    identifier = old.material.source_ids._digest(entity)
    event = {'entity': entity, 'source_event_id': 'shoot-event:' + identifier,
        'internode_event_id': 'shoot-event:' + identifier + '/internode', 'leaf_event_id': 'shoot-event:' + identifier + '/leaf',
        'internode_id': 'internode:' + identifier,
        'leaf_id': 'leaf:' + old.material.source_ids._digest({**entity, 'organ': 'leaf', 'slot': 0}),
        'sequence': schedule['next_sequence'], 'threshold_exact': deepcopy(schedule['next_threshold_exact'])}
    seed = s.math_basis['seed']; program, organs = seed['program'], seed['organs']
    events = {v['event_id'] for rows in organs.values() if type(rows) is list for v in rows if 'event_id' in v}
    nodes = [v['compartment_id'] for v in program['stem_root_compartments']]
    leaves = [v['leaf_id'] for v in program['leaves']]
    need(not events.intersection(event[k] for k in ('source_event_id', 'internode_event_id', 'leaf_event_id'))
         and event['internode_id'] not in nodes and event['leaf_id'] not in leaves, 'EVENT_HOLD: next IDs must be unused')
    return {'initial_binding_sha256': binding_sha, 'timeline': deepcopy(timeline), 'event': event,
        'emergence_profile': deepcopy(source['emergence_profile']),
        'parent_internode_ids': [v['compartment_id'] for v in program['stem_root_compartments'] if v['kind'] == 'internode'],
        'existing_ids': {'internode_ids': nodes, 'leaf_ids': leaves, 'event_ids': sorted(v for v in events if v is not None)}}


def _failure(schema, source, error, meter, historical=None):
    return {**FLAGS, 'schema_version': schema, 'model_version': VERSION, 'code_sha256': CODE_SHA256,
        'status': 'hold', 'hold': base._reason(error), 'source': source, 'progress': deepcopy(meter.p),
        'historical_cursor_sha256': historical, 'authority_hold': None,
        'checkpoint_issued': False, 'history_committed': False, 'material_consumed': False}


def _pending(s, current, source, reference):
    page = base._get(s, reference)
    base.reader._closed(page, {'schema_version', 'definition_sha256', 'previous_cursor_sha256', 'interval', 'schedule', 'material_consumed'})
    expected = 'supply-material-pending-page-v1' if source['owner_version'] == original.VERSION else 'supply-material-repeat-pending-page-v1'
    need(page['schema_version'] == expected and page['definition_sha256'] == source['definition_sha256']
         and page['previous_cursor_sha256'] == source['cursor_sha256'] and page['material_consumed'] is False,
         'SOURCE_HOLD: actual material pending source required')
    math = original.proof.math_view(s.math_basis, s.spans[current['span_index']], s.profiles)
    right = original.forcing._right(s, current)
    _, _, schedule = original.proof.trace_values(math, current['numeric'], page['interval'], right)
    need(raw(schedule) == raw(page['schedule'])
         and x(schedule['age_exact'], 'degC_day') >= x(schedule['next_threshold_exact'], 'degC_day'),
         'EVENT_HOLD: actual first pending interval required')
    return page, math


def _interval(s, current, meter):
    math = original.proof.math_view(s.math_basis, s.spans[current['span_index']], s.profiles)
    n = current['numeric']; left = x(n['at']['elapsed_seconds_exact'], 's')
    right = original.forcing._right(s, current)
    meter.segment()
    def evaluate(state, label):
        value = meter.evaluate(math, state, 'pending_replay')
        return tuple(value['rates']), tuple(base.books.flux(math.data['program'], state, value, math.data['organs'])), value['derived']
    first = meter.evaluate(math, tuple(n['last_confirmed']['state']), 'pending_replay')
    need(raw(first['derived']) == raw(n['last_confirmed']['derived']), 'STATE_HOLD: unchanged current RHS required')
    state, totals, rates, flows, derived, trace = state_math._rk4(tuple(n['last_confirmed']['state']),
        tuple(n['branch_integrated_transfers'][k]['value'] for k in math.units), tuple(first['rates']),
        tuple(base.books.flux(math.data['program'], n['last_confirmed']['state'], first, math.data['organs'])), right-left, left, evaluate)
    trace['flux_order'] = [{'name': k, 'unit': v} for k, v in math.units.items()]
    schedule = base._clock(math, totals, right)
    trace['shoot_clock_certificate'] = base.arithmetic._interval_clock(math.data, n, trace, schedule)
    return state, totals, derived, trace, schedule


def _root(s, current, trace, tolerance, meter):
    tolerance = x(tolerance, 's'); need(tolerance > 0, 'TIME_HOLD: positive exact tolerance required')
    n = current['numeric']; span = s.spans[current['span_index']]
    left, right = x(trace['left_elapsed_seconds_exact'], 's'), x(trace['right_elapsed_seconds_exact'], 's')
    coefficients = locator.event._thermal_polynomial(tuple(Fraction(v['state'][104]) for v in trace['stages']), right-left,
        Fraction(s.math_basis['shoot_base_temperature']), x(n['schedule']['age_exact'], 'degC_day'),
        x(n['schedule']['next_threshold_exact'], 'degC_day'))
    p = {'bisections': 0}; meter.fence('root_isolation')
    try:
        lo, hi = locator._isolate(coefficients, right-left, tolerance, meter.fence, p)
    finally:
        meter.p['root_bisections'] += p['bisections']
    order = locator._order(left, right, x(span['start'], 's'), x(span['end'], 's') if current['span_index'] < len(s.spans)-1 else None, coefficients)
    need(order['material_forcing_order_resolved'], 'ORDER_HOLD: unresolved material/forcing order')
    at = left + hi*(right-left)
    need(current['span_index'] == len(s.spans)-1 or at < x(span['end'], 's'), 'ORDER_HOLD: refine root before forcing edge')
    math = original.proof.math_view(s.math_basis, span, s.profiles)
    _, _, schedule = original.proof.trace_values(math, n, trace, right)
    result = {'schema_version': 'supply-material-successor-root-certificate-v1',
        'interval_left_exact': q(left, 's'), 'interval_right_exact': q(right, 's'), 'time_tolerance_seconds_exact': q(tolerance, 's'),
        'polynomial_residual_coefficients_exact': [q(v, 'degC_day') for v in coefficients],
        'minimum_derivative_per_theta_exact': q(locator.event._minimum_derivative(coefficients), 'degC_day'),
        'ideal_cubic_minus_accumulated_endpoint_age_exact': q(locator.event._value(coefficients, Fraction(1))-
            (x(schedule['age_exact'], 'degC_day')-x(n['schedule']['next_threshold_exact'], 'degC_day')), 'degC_day'),
        'method_reference': locator.event.METHOD_REFERENCE,
        'method': 'classical_rk4_third_order_continuous_extension_eq28_exact_rational_bisection',
        'claim_scope': 'root_isolation_in_this_numerical_polynomial_not_physical_time_or_discretization_error',
        'root': {'time_origin_utc': n['at']['time_origin_utc'], 'lower_elapsed_seconds_exact': q(left+lo*(right-left), 's'),
            'upper_elapsed_seconds_exact': q(at, 's'), 'width_seconds_exact': q((hi-lo)*(right-left), 's'),
            'lower_thermal_residual_exact': q(locator.event._value(coefficients,lo), 'degC_day'),
            'upper_thermal_residual_exact': q(locator.event._value(coefficients,hi), 'degC_day')}, 'order': order}
    return result, hi, p['bisections']


def _candidate(s, current, source, pending, tolerance, meter):
    page, math = _pending(s, current, source, pending)
    start = meter.p['actual_RHS_evaluations']
    _, _, _, replay, schedule = _interval(s, current, meter)
    need(raw(replay) == raw(page['interval']) and raw(schedule) == raw(page['schedule']), 'REPLAY_HOLD: original pending interval differs')
    replay_work = meter.p['actual_RHS_evaluations'] - start
    root, theta, bisections = _root(s, current, replay, tolerance, meter)
    left = x(current['at']['elapsed_seconds_exact'], 's'); at = x(root['root']['upper_elapsed_seconds_exact'], 's')
    duration = at-left; dt = x(replay['step_seconds_exact'], 's'); n = current['numeric']; rows = replay['stages']
    state = tuple(n['last_confirmed']['state']); zero = (0.,)*len(math.units)
    weights = state_math.old._weights(theta)
    dense_state = base.combine(state, tuple(tuple(v['rates']) for v in rows), weights, dt)
    partial = base.combine(zero, tuple(tuple(v['flux']) for v in rows), weights, dt)
    start = meter.p['actual_RHS_evaluations']
    def evaluate(y, label):
        value = meter.evaluate(math, y, 'dense_refinements')
        return tuple(value['rates']), tuple(base.books.flux(math.data['program'], y, value, math.data['organs'])), value['derived']
    _, _, derived = evaluate(dense_state, 'dense_candidate')
    dense = books.packet(math, n, dense_state, partial, derived, at, 1)
    need(dense['represented_threshold_status'] == 'crossed', 'ROUNDING_HOLD: dense clock must cross without snapping')
    refinements = []
    for count in (1, 2, 4):
        y, totals = state, zero; rates, flow = tuple(rows[0]['rates']), tuple(rows[0]['flux']); intervals = []
        for i in range(count):
            y, totals, rates, flow, derived, interval = state_math._rk4(y, totals, rates, flow, duration/count, left+i*duration/count, evaluate)
            intervals.append(interval)
            packet = books.packet(math, n, y, totals, derived, left+(i+1)*duration/count, i+1)
        refinements.append({'substeps': count, 'step_seconds_exact': q(duration/count, 's'), 'intervals': intervals, **packet})
    dense_work = meter.p['actual_RHS_evaluations'] - start
    coordinates = deepcopy(math.data['seed']['state_layout'])
    coordinate_rows = base.arithmetic.resume._coordinates({'initial': {'state_layout': coordinates, 'state': state}, 'program': math.data['program']})
    _, _, differences = state_math._differences([dense, *refinements])
    state_rows = differences([v['state'] for v in [dense,*refinements]], [r['unit'] for r in coordinate_rows])
    for row, coordinate in zip(state_rows, coordinate_rows, strict=True): row['coordinate'] = coordinate
    transfer_rows = differences([[packet['partial_interval_transfers'][name]['value'] for name in math.units] for packet in [dense,*refinements]], list(math.units.values()))
    for row, name in zip(transfer_rows, math.units, strict=True): row['name'] = name
    result = {**FLAGS, 'schema_version': 'supply-material-successor-candidate-v1', 'model_version': VERSION, 'code_sha256': CODE_SHA256,
        'status': 'candidate_ready', 'hold': None, 'source': deepcopy(source), 'effective_rights': deepcopy(current['effective_rights']),
        'pending_page_sha256': pending, 'source_schedule': deepcopy(n['schedule']), 'source_interval': deepcopy(replay),
        'root_certificate': root, 'state_layout': coordinates, 'state_coordinates': coordinate_rows, 'at': deepcopy(dense['at']),
        'selection_policy': 'certified_dense_root_upper_bound_no_threshold_snap', 'dense_candidate': dense, 'refinements': refinements,
        'state_differences': state_rows, 'transfer_differences': transfer_rows,
        'account_rule': 'exact_source_plus_partial_residual_and_unchanged_budget_sum',
        'diagnostic_scope': 'same_time_local_differences_not_certified_ODE_or_agronomic_error',
        'work': {'interval_replay_RHS_evaluations': replay_work, 'dense_state_RHS_evaluations': dense_work,
            'point_stage_RHS_evaluations': 0, 'root_bisections': bisections},
        'checkpoint_issued': False, 'history_committed': False, 'material_consumed': False}
    result['calculation_sha256'] = digest(result); raw(result); meter.fence('final_source_check')
    observations = {'dense_derived': deepcopy(dense['derived']),
        'refinements': [{k: deepcopy(v[k]) for k in ('substeps','step_seconds_exact','intervals','derived')} for v in refinements]}
    derived_parts = {'root_certificate': deepcopy(root),
        'dense_candidate': {k: deepcopy(v) for k,v in dense.items() if k != 'derived'},
        'refinements': [{k: deepcopy(v) for k,v in packet.items() if k not in ('intervals','derived')} for packet in refinements],
        'work': deepcopy(result['work'])}
    meter.algebra = _Algebra(raw(source), raw(current, base.CURRENT_MAX), raw(s.basis), pending,
        raw(root['time_tolerance_seconds_exact']), raw(observations), raw(derived_parts), None, None, _TOKEN)
    return result


def _head(s, current, source, event, value, pending):
    base.reader._closed(value, old.FIELDS | {'source_owner_version'})
    need(value['schema_version'] == 'supply-material-successor-point-input-v1' and value['origin'] == 'synthetic'
         and value['policy'] == POLICY and value['parameter_source'] == 'own_declared_synthetic_assumptions', 'SCOPE_HOLD: explicit synthetic successor required')
    need(value['source_owner_version'] == source['owner_version'] and value['cursor_sha256'] == source['cursor_sha256']
         and value['definition_sha256'] == source['definition_sha256'] and value['pending_page_sha256'] == pending
         and value['initial_binding_sha256'] == event['initial_binding_sha256'], 'SOURCE_HOLD: exact successor anchors required')
    for key in ('input_id', 'parameter_revision', 'reviewer', 'parent_internode_id'): base.reader._id(value[key])
    for key in ('definition_sha256','cursor_sha256','pending_page_sha256','candidate_sha256','initial_binding_sha256'): base.reader._hash(value[key])
    original.forcing._rights(value['rights']); need(value['rights']['use'], 'RIGHTS_HOLD: successor use required')
    old._provenance(value)
    e = event['event']
    need(value['source_event_id'] == e['source_event_id'] and type(value['source_threshold_sequence']) is int
         and value['source_threshold_sequence'] == e['sequence'] and value['source_threshold_exact'] == e['threshold_exact'], 'EVENT_HOLD: first actual event required')
    need(value['parent_internode_id'] in event['parent_internode_ids'], 'PARENT_HOLD: actual existing internode required')
    need(old.material.arithmetic._quantity(value['model_floor_area'], 'm2_floor') == s.math_basis['seed']['program']['model_floor_area']['value'], 'BASIS_HOLD: original floor required')


def _point_data(s, current, event, inputs, candidate, evaluate):
    math = original.proof.math_view(s.math_basis, s.spans[current['span_index']], s.profiles)
    data = math.data; data['initial'] = {'organs': data['seed']['organs'], 'state_layout': data['seed']['state_layout']}
    before = deepcopy(candidate['dense_candidate'])
    numbers = {'dense_candidate': {**before, 'global_ledgers': deepcopy(before['pending_global_ledgers'])},
        'at': deepcopy(candidate['at']), 'source_prefix': {'event_sequence': current['numeric']['event_sequence']}}
    seeds = old._seeds(s, event, inputs)
    jump = old.material.apply(None, data, numbers, inputs, event['event'], seeds, evaluate)
    preview = old.point_books.calculate(None, data, numbers, jump)
    layout = {**deepcopy(data['seed']['state_layout']), 'original': old.material.source.stock.short._layout(jump['program']),
        'original_prefix_length': 106+3*len(jump['program']['leaves'])+len(jump['program']['stem_root_compartments']),
        'internode_ids': [v['compartment_id'] for v in jump['organs']['internodes']]}
    return {'before_dense': before, 'source_event': deepcopy(event['event']), 'source_schedule': deepcopy(current['numeric']['schedule']),
        'source_transfer_origins': deepcopy(current['numeric']['transfer_origins']), 'at': deepcopy(candidate['at']),
        'after_program': jump['program'], 'after_state': jump['state'], 'after_rates': deepcopy(jump['evaluation']['rates']),
        'after_stage': jump['evaluation'], 'after_derived': deepcopy(jump['evaluation']['derived']), 'after_organs': jump['organs'],
        'after_costs': jump['costs'], 'after_state_layout': layout, 'seed_compatibility': seeds['compatibility'],
        'new_birth_baselines': jump['new_birth_baselines'], 'flow_components': jump['components'], 'growth_costs': jump['growth_costs'],
        'leaf_receipts': jump['leaf_receipts'], 'point_order': ['internode','leaf'] if inputs['leaf'] is not None else ['internode'], **preview}


def _calculate_point(s, current, source, pending, tolerance, inputs, meter):
    snapshot = raw(inputs, INPUT_MAX); value = json.loads(snapshot); event = _event_data(s, current)
    _head(s, current, source, event, value, pending)
    candidate = _candidate(s, current, source, pending, tolerance, meter)
    need(value['candidate_sha256'] == candidate['calculation_sha256'] and value['at_elapsed_seconds_exact'] == candidate['at']['elapsed_seconds_exact'], 'POINT_HOLD: exact candidate/time required')
    age = x(candidate['dense_candidate']['shoot_age_exact'], 'degC_day'); threshold = x(event['event']['threshold_exact'], 'degC_day')
    need(threshold <= age < threshold+x(event['timeline']['phyllochron_exact'], 'degC_day'), 'EVENT_HOLD: one threshold only')
    start = meter.p['actual_RHS_evaluations']
    def evaluate(program, state, organs, costs):
        math = SimpleNamespace(data={'program': program, 'organs': organs, 'costs': costs}, basis=s.math_basis, profiles=s.profiles)
        return meter.evaluate(math, state, 'material_stage')
    data = _point_data(s, current, event, value, candidate, evaluate)
    work = deepcopy(candidate['work']); work['point_stage_RHS_evaluations'] = meter.p['actual_RHS_evaluations']-start
    result = {**FLAGS, 'schema_version': 'supply-material-successor-point-result-v1', 'model_version': VERSION, 'code_sha256': CODE_SHA256,
        'status': 'point_ready', 'hold': None, 'policy': POLICY, 'source': deepcopy(source), 'pending_page_sha256': pending,
        'initial_binding_sha256': event['initial_binding_sha256'], 'input_sha256': sha256(snapshot).hexdigest(), 'inputs': value,
        'candidate_sha256': candidate['calculation_sha256'], 'candidate': candidate,
        'effective_rights': {k: current['effective_rights'][k] and value['rights'][k] for k in current['effective_rights']},
        'point_data': data, 'work': work, 'elapsed_seconds_advanced': q(0, 's'), 'schedule_adoption': 'not_performed',
        'checkpoint_issued': False, 'history_committed': False, 'material_consumed': False}
    result['calculation_sha256'] = digest(result); raw(result)
    meter.fence('final_source_check'); need(raw(inputs, INPUT_MAX) == snapshot, 'SOURCE_HOLD: caller successor input changed')
    meter.algebra = meter.algebra._replace(inputs=snapshot, after_stage=raw(data['after_stage']))
    return result


def describe_successor_source(handle):
    meter = _Meter(); source = None
    try:
        with _source(handle, meter) as (s, current):
            source = _ref(s, current, handle.cursor_sha256); event = _event_data(s, current)
            result = {**FLAGS, 'schema_version': 'supply-material-successor-source-v1', 'model_version': VERSION, 'code_sha256': CODE_SHA256,
                'source': source, **{k: deepcopy(event[k]) for k in ('initial_binding_sha256','event','timeline','existing_ids')}}
            meter.reserve([(result, base.PAGE_MAX)], 1); meter.fence('final_source_check'); return result
    except ERRORS as error:
        return _failure('supply-material-successor-source-v1', source, error, meter)


def calculate_successor_candidate(handle, pending_page_sha256, time_tolerance_seconds_exact, *, cancelled=None, wall_seconds=60):
    meter = _Meter(cancelled=cancelled, wall_seconds=wall_seconds); source = None
    try:
        with _source(handle, meter) as (s, current):
            source = _ref(s, current, handle.cursor_sha256)
            result = _candidate(s, current, source, pending_page_sha256, time_tolerance_seconds_exact, meter)
            meter.reserve([(result, base.PAGE_MAX)], 1); meter.fence('final_source_check'); return result
    except ERRORS as error:
        return _failure('supply-material-successor-candidate-v1', source, error, meter)


def apply_successor_material_point(handle, pending_page_sha256, time_tolerance_seconds_exact, *, inputs, cancelled=None, wall_seconds=60):
    meter = _Meter(cancelled=cancelled, wall_seconds=wall_seconds); source = None
    try:
        with _source(handle, meter) as (s, current):
            source = _ref(s, current, handle.cursor_sha256)
            result = _calculate_point(s, current, source, pending_page_sha256, time_tolerance_seconds_exact, inputs, meter)
            meter.reserve([(result, base.PAGE_MAX)], 1); meter.fence('final_source_check'); return result
    except ERRORS as error:
        return _failure('supply-material-successor-point-result-v1', source, error, meter)


_SIGNATURE = _signature(sys.modules[__name__])
