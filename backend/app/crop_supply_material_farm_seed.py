"""Produce original seed artifacts from a current owned Farm input, with guarded writes."""
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import dataclass, field
from functools import wraps
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import NamedTuple
from types import MethodType

from . import crop_supply_material_farm_inputs as inputs
from . import crop_leaf_carbon_stock_artifact_reader as carbon
from . import crop_leaf_carbon_stock_continuation as continuation
from . import crop_rational_morphology_artifact_reader as stem
from . import crop_rational_morphology_artifact_producer as original_stem
from . import crop_rational_shoot_inventory as inventory
from . import crop_stem_root_initial_binding as initial
from .crop_growth_rates import ReferenceParameters as Growth
from .crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from .crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from .crop_canopy_exchange import ReferenceParameters as Exchange
from .crop_morphology_artifact_io import MorphologyBlobStore
from .content_access import ContentAccess

VERSION = 'supply-material-farm-seed-v1'
MAX_WITNESS_BYTES = 2*1024**2
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_ROOT = Path(__file__).resolve().parents[2]
_PINS = {**inputs._PINS, **initial._pins(),
    'backend/app/crop_supply_material_farm_seed.py': CODE_SHA256}
_PROFILE_FILES = {'growth_profile': 'crop-growth-reference-parameters-v1.json',
    'cohort_profile': 'crop-fruit-cohort-reference-parameters-v1.json',
    'transport_profile': 'crop-fruit-transport-reference-parameters-v1.json',
    'exchange_profile': 'crop-canopy-exchange-reference-parameters-v1.json'}
_PROFILE_TYPES = {'growth_profile': Growth, 'cohort_profile': Cohort,
    'transport_profile': Transport, 'exchange_profile': Exchange}
_FILE_PINS = {'fixtures/'+_PROFILE_FILES[k]: v for k, v in carbon.PROFILE_SHA.items()}
_FILE_PINS[carbon.NOTICE_PATH] = carbon.NOTICE_SHA
_TOKEN = object()
_ACTIVE = ContextVar('owned_material_seed_directory', default=None)
_ACCESS_METHODS = tuple((name, ContentAccess.__dict__[name]) for name in
    ('validate', 'prepare_new', 'require_writer'))
_STORE_CLOSE = MorphologyBlobStore.close
_STORE_GUARD = MorphologyBlobStore._guard


class MaterialFarmSeedHold(ValueError):
    pass


def _need(value):
    if not value:
        raise MaterialFarmSeedHold('owned material Farm seed unavailable')


def _checked(fn):
    @wraps(fn)
    def run(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (PermissionError, MaterialFarmSeedHold):
            raise
        except Exception:
            raise MaterialFarmSeedHold('owned material Farm seed unavailable') from None
    return run


def _profiles():
    return {key: _PROFILE_TYPES[key]((_ROOT/'fixtures'/name).read_bytes())
        for key, name in _PROFILE_FILES.items()}


def _check_profiles(profiles):
    _need(type(profiles) is dict and set(profiles) == set(_PROFILE_TYPES))
    for key, cls in _PROFILE_TYPES.items():
        value = profiles[key]
        _need(type(value) is cls and value.sha256 == carbon.PROFILE_SHA[key]
            and sha256(value.raw_bytes).hexdigest() == value.sha256
            and vars(value) == vars(cls(value.raw_bytes)))


def _identity(fn):
    original = getattr(fn, '__wrapped__', None)
    return (fn, getattr(fn, '__code__', None), original, getattr(original, '__code__', None))


def _access_dispatch(access):
    _need(type(access) is ContentAccess)
    for name, original in _ACCESS_METHODS:
        _need(ContentAccess.__dict__.get(name) is original)
        actual = getattr(access, name)
        _need(type(actual) is MethodType and actual.__self__ is access and actual.__func__ is original)


def _directory_identity(path, access):
    _access_dispatch(access)
    _need(path.is_absolute() and path.absolute() == path.resolve() and not path.is_symlink())
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        _ACCESS_METHODS[0][1](access, fd, directory=True)
        info = os.fstat(fd)
        return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid)
    finally:
        os.close(fd)


@contextmanager
def _selection(owner, tenant):
    _need(_ACTIVE.get() is None)
    token = _ACTIVE.set((owner, tenant, None, None))
    try:
        yield
    finally:
        _ACTIVE.reset(token)


@dataclass(frozen=True, eq=False)
class VerifiedMaterialFarmSeed:
    _context: object = field(repr=False)
    _binding: bytes = field(repr=False)
    _witness: bytes = field(repr=False)
    _token: object = field(repr=False)

    @property
    def context(self):
        _need(self._token is _TOKEN)
        return self._context

    @property
    def initial_binding_bytes(self):
        _need(self._token is _TOKEN)
        return self._binding

    @property
    def witness(self):
        _need(self._token is _TOKEN)
        return json.loads(self._witness)

    @property
    def carbon_root_sha256(self):
        return self.witness['source']['carbon_root_sha256']

    @property
    def stem_root_sha256(self):
        return self.witness['source']['stem_root_sha256']


class _Program(NamedTuple):
    capture: object
    pointers: object
    guard: object
    operation: object
    put: object
    directory: object
    store: object
    carbon: object
    stem: object
    link: object
    close_store: object
    guard_store: object


def _namespace():
    functions = (_namespace, _need, _profiles, _check_profiles, _identity, _access_dispatch,
        _directory_identity, _selection,
        continuation.prepare_context, continuation._context, continuation.start,
        continuation.advance_chunk, continuation.checkpoint_bytes,
        inventory.advance_rational_shoot_internode_inventory, original_stem._forcing,
        initial.crop.prepare_context, initial.crop._context, initial.bind_initial_stem_carbon,
        carbon._graph, carbon._fence, carbon._pins, carbon.read_leaf_carbon_stock_manifest,
        stem.read_rational_morphology_manifest, stem.read_rational_morphology_frame,
        MorphologyBlobStore.__init__, MorphologyBlobStore.put, MorphologyBlobStore.get,
        MorphologyBlobStore.close, MorphologyBlobStore._guard,
        ContentAccess.validate, ContentAccess.prepare_new, ContentAccess.require_writer,
        inputs.MaterialFarmInputService.current, inputs._scope, inputs._raw, inputs._digest,
        VerifiedMaterialFarmSeed.context.fget, VerifiedMaterialFarmSeed.initial_binding_bytes.fget,
        VerifiedMaterialFarmSeed.witness.fget, VerifiedMaterialFarmSeed.carbon_root_sha256.fget,
        VerifiedMaterialFarmSeed.stem_root_sha256.fget,
        MaterialFarmSeedProducer.produce, MaterialFarmSeedProducer._link)
    return (tuple(_identity(fn) for fn in functions), _TOKEN, _Program, VerifiedMaterialFarmSeed,
        VERSION, CODE_SHA256, MAX_WITNESS_BYTES, tuple(sorted(_PINS.items())),
        tuple(sorted(_FILE_PINS.items())), tuple(sorted(_PROFILE_FILES.items())),
        tuple(_PROFILE_TYPES.items()), tuple(sorted(carbon.PROFILE_SHA.items())),
        Path, sha256, MorphologyBlobStore, ContentAccess, inputs.PRODUCE_SCOPES, _ACTIVE,
        _ACCESS_METHODS, MethodType, _STORE_CLOSE, _STORE_GUARD)


class MaterialFarmSeedProducer:
    @_checked
    def __init__(self, service, directory, access):
        _need(type(self) is MaterialFarmSeedProducer and type(service) is inputs.MaterialFarmInputService
            and type(access) is ContentAccess)
        path = Path(directory)
        _need(path.is_absolute() and not path.is_symlink() and path.absolute() == path.resolve())
        original = service.jobs.artifact_root.resolve()
        _need(path != original and original not in path.parents and path not in original.parents)
        self.service, self.directory, self.access = service, path, access
        self.__input_program = service._program
        self.__current = type(service).current
        self._program = self.__program = MaterialFarmSeedProducer._capture_program(self)
        self._namespace = _namespace()
        self._fixed = self.__program.pointers(self, self.__program)
        self.__program.guard(self, self.__program, None, None)

    def _capture_program(self):
        own = tuple(getattr(getattr(self, name), '__func__', getattr(self, name)) for name in
            ('_capture_program', '_pointers', '_guard', '_operation', '_put', '_directory',
             '_store', '_carbon', '_stem', '_link'))
        return _Program(*own, _STORE_CLOSE, _STORE_GUARD)

    def _pointers(self, program):
        _access_dispatch(self.access)
        path = self.directory
        _need(type(path) is type(Path()) and path.is_absolute() and path.absolute() == path.resolve()
            and not path.is_symlink())
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            _ACCESS_METHODS[0][1](self.access, fd, directory=True)
            info = os.fstat(fd)
            identity = (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid)
        finally:
            os.close(fd)
        return (self.service, self.service._program, self.service.jobs, self.service.jobs.artifact_root,
            self.directory, self.access, self._program,
            identity, tuple(_identity(fn) for fn in program.capture(self)),
            _identity(getattr(self.produce, '__func__', self.produce)),
            _identity(getattr(self.service.current, '__func__', self.service.current)),
            _namespace())

    def _guard(self, program, tenant, original):
        _need(type(self) is MaterialFarmSeedProducer and self._namespace == _namespace()
            and program.pointers(self, program) == self._fixed
            and MAX_WITNESS_BYTES == 2*1024**2
            and all(sha256((_ROOT/path).read_bytes()).hexdigest() == digest
                for path, digest in (*_PINS.items(), *_FILE_PINS.items())))
        self.__input_program.guard(self.service, self.__input_program, tenant,
            inputs.PRODUCE_SCOPES if tenant is not None else ())
        active = _ACTIVE.get()
        if active is not None:
            _need(active[0] is self and active[1] == tenant)
            if active[2] is not None:
                _need(_directory_identity(active[2], self.access) == active[3])
        if original is not None:
            _need(type(original) is inputs.VerifiedMaterialFarmInput)
            row = original.witness['owned_input']
            current = self.__current(self.service, tenant, row['job_id'], row['input_sha256'])
            _need(current.input_bytes == original.input_bytes and current.witness == original.witness)

    def _operation(self, captured, tenant, original, fn, *args, profiles=None, **kwargs):
        captured.guard(self, captured, tenant, original)
        if profiles is not None: _check_profiles(profiles)
        result = fn(*args, **kwargs)
        if profiles is not None: _check_profiles(profiles)
        captured.guard(self, captured, tenant, original)
        return result

    def _put(self, program, tenant, original, store, raw, maximum):
        _need(type(store) is MorphologyBlobStore
            and getattr(store.put, '__func__', None) is MorphologyBlobStore.put)
        result = program.operation(self, program, tenant, original, store.put, raw, maximum=maximum)
        _need(result == sha256(raw).hexdigest())
        return result

    def _directory(self, program, tenant, original):
        program.guard(self, program, tenant, original)
        path = self.directory/original.witness['owned_input']['input_sha256']
        created = False
        try:
            os.mkdir(path, 0o750)
            created = True
        except FileExistsError:
            pass
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            if created:
                _access_dispatch(self.access)
                _ACCESS_METHODS[1][1](self.access, fd, directory=True)
            else:
                _access_dispatch(self.access)
                _ACCESS_METHODS[0][1](self.access, fd, directory=True)
        finally:
            os.close(fd)
        _need(path.absolute() == path.resolve())
        active = _ACTIVE.get()
        _need(active is not None and active[:2] == (self, tenant) and active[2] is None)
        _ACTIVE.set((self, tenant, path, _directory_identity(path, self.access)))
        program.guard(self, program, tenant, original)
        return path

    @contextmanager
    def _store(self, program, tenant, original, directory):
        program.guard(self, program, tenant, original)
        store = MorphologyBlobStore(directory, self.access, write=True)
        try:
            program.guard(self, program, tenant, original)
            yield store
            program.guard(self, program, tenant, original)
            program.guard_store(store)
            program.guard(self, program, tenant, original)
        finally:
            program.close_store(store)

    def _carbon(self, program, tenant, original, directory, profiles):
        packet = original.request['source']['carbon_stock_inputs']
        encoded = carbon._canonical(packet); pins = carbon._pins()
        context = program.operation(self, program, tenant, original, continuation.prepare_context,
            program=packet['program'], step_seconds=packet['step_seconds'], step_count=packet['step_count'],
            profiles=profiles, **profiles)
        program.operation(self, program, tenant, original, continuation._context, context, profiles=profiles)
        sources = {'inputs': encoded, 'request': context._request, 'program': context._program,
            'context': context._manifest, 'seed': context._seed,
            'license_notice': (_ROOT/carbon.NOTICE_PATH).read_bytes(),
            **{key: value.raw_bytes for key, value in profiles.items()}}
        with program.store(self, program, tenant, original, directory) as store:
            descriptors = {key: {'sha256': program.put(self, program, tenant, original, store, raw, carbon.MAX),
                'bytes': len(raw)} for key, raw in sources.items()}
            cp = program.operation(self, program, tenant, original, continuation.start, context, profiles=profiles)
            samples = []; previous = None
            for index in range(packet['step_count']+1):
                _need(carbon._pins() == pins)
                if index:
                    chunk = program.operation(self, program, tenant, original,
                        continuation.advance_chunk, context, cp, 1, profiles=profiles)
                    _need(chunk['status'] in ('yielded', 'completed') and chunk['checkpoint'] is not None)
                    cp = chunk['checkpoint']
                raw = program.operation(self, program, tenant, original,
                    continuation.checkpoint_bytes, context, cp, profiles=profiles)
                sample = cp.value['last_confirmed']
                digest = program.put(self, program, tenant, original, store, raw, carbon.CHECKPOINT_MAX)
                samples.append({'index': index, 'elapsed_seconds_exact': carbon._offset(packet['step_seconds'], index),
                    'checkpoint_sha256': digest, 'checkpoint_bytes': len(raw),
                    'sample_sha256': carbon._digest(sample), 'state_sha256': carbon._digest(sample['state']),
                    'previous_checkpoint_sha256': previous})
                previous = digest
            manifest = {**carbon.ROOT_CONSTANTS, 'input_id': packet['input_id'], 'source_rights': packet['rights'],
                'time_origin_utc': packet['time_origin_utc'], 'sources': descriptors, 'code_sha256': pins,
                'context_sha256': context.root_sha256, 'initial_state_sha256': samples[0]['state_sha256'],
                'terminal_state_sha256': samples[-1]['state_sha256'], 'samples': samples}
            _, _, _, _, _, raws = carbon._graph(store, manifest)
            _need(all(store.get(sha256(raw).hexdigest(), maximum=carbon.MAX) == raw for raw in sources.values()))
            program.operation(self, program, tenant, original, continuation._context, context, profiles=profiles)
            carbon._fence(store, manifest, raws)
            return program.put(self, program, tenant, original, store, carbon._canonical(manifest), carbon.MAX)

    def _stem(self, program, tenant, original, directory):
        packet = original.request['source']['stem_program']; encoded = stem._canonical(packet)
        pins = {name: _PINS[name] for name in stem.SOURCE_PATHS}
        state = packet['initial_state']; descriptors = []
        with program.store(self, program, tenant, original, directory) as store:
            program_sha = program.put(self, program, tenant, original, store, encoded, stem.PROGRAM_MAX)
            for index, at in enumerate(packet['output_times']):
                before = inputs._digest(state)
                result = program.operation(self, program, tenant, original,
                    inventory.advance_rational_shoot_internode_inventory, inputs={
                        'input_id': inputs._digest({'program_id': packet['program_id'], 'output_at': at}),
                        'state': state, 'segments': original_stem._forcing(packet['segments'], state['timeline_state']['at'], at)})
                raw = stem._canonical(result)
                result_sha = program.put(self, program, tenant, original, store, raw, stem.RESULT_MAX)
                state = result['state']
                descriptors.append({'index': index, 'at': at, 'result_sha256': result_sha, 'result_bytes': len(raw),
                    'input_state_sha256': before, 'state_sha256': inputs._digest(state), 'input_sha256': result['input_sha256']})
            manifest = {**stem.ROOT_CONSTANTS, 'program_sha256': program_sha, 'program_bytes': len(encoded),
                'initial_state_sha256': inputs._digest(packet['initial_state']), 'program_rights': packet['rights'],
                'code_sha256': pins, 'samples': descriptors, 'terminal_state_sha256': inputs._digest(state)}
            return program.put(self, program, tenant, original, store, stem._canonical(manifest), stem.ROOT_MAX)

    @_checked
    def _link(self, verified_input, *, context, carbon_root_sha256, stem_root_sha256, initial_binding_bytes):
        program = self.__program
        _need(type(verified_input) is inputs.VerifiedMaterialFarmInput)
        tenant = verified_input.witness['tenant_id']
        program.guard(self, program, tenant, verified_input)
        packet = verified_input.request['source']; witness = verified_input.witness
        path = self.directory/witness['owned_input']['input_sha256']
        cm = program.operation(self, program, tenant, verified_input,
            carbon.read_leaf_carbon_stock_manifest, path/'carbon', self.access, carbon_root_sha256)
        sm = program.operation(self, program, tenant, verified_input,
            stem.read_rational_morphology_manifest, path/'stem', self.access, stem_root_sha256)
        _need(cm['sources']['inputs']['sha256'] == inputs._digest(packet['carbon_stock_inputs'])
            and sm['program_sha256'] == inputs._digest(packet['stem_program'])
            and cm['source_rights'] == packet['carbon_stock_inputs']['rights']
            and sm['program_rights'] == packet['stem_program']['rights']
            and cm['code_sha256'] == {key: _PINS[key] for key in carbon.SOURCE_PATHS}
            and sm['code_sha256'] == {key: _PINS[key] for key in stem.SOURCE_PATHS}
            and type(context) is initial.crop.Context and context._request == inputs._raw(packet['individual_program'])
            and cm['time_origin_utc'] == packet['carbon_stock_inputs']['time_origin_utc'])
        profiles = initial.crop._profiles(context)
        _, _, manifest = program.operation(self, program, tenant, verified_input,
            initial.crop._context, context, profiles=profiles)
        numerical = manifest['numerical']
        _need(type(numerical['step_seconds']) is float
            and numerical['step_seconds'] == float(packet['numerical']['step_seconds'])
            and type(numerical['step_count']) is int
            and numerical['step_count'] == packet['numerical']['step_count'])
        _need({key: value.sha256 for key, value in profiles.items()} == packet['profile_sha256'])
        index = packet['stem_start_index']
        if index == -1:
            state_sha = sm['initial_state_sha256']
        else:
            program.operation(self, program, tenant, verified_input, stem.read_rational_morphology_frame,
                path/'stem', self.access, stem_root_sha256, index=index)
            state_sha = sm['samples'][index]['state_sha256']
        declaration = {'schema_version': 'stem-root-initial-source-binding-input-v1',
            'input_id': 'owned-material-seed-'+witness['owned_input']['input_sha256'], 'origin': 'synthetic',
            'context_sha256': context.root_sha256, 'crop_root_sha256': carbon_root_sha256,
            'crop_initial_state_sha256': cm['initial_state_sha256'], 'stem_root_sha256': stem_root_sha256,
            'stem_start_index': index, 'stem_source_state_sha256': state_sha,
            'time_origin_utc': cm['time_origin_utc'], 'model_floor_area': deepcopy(packet['individual_program']['model_floor_area']),
            'tracking_basis': deepcopy(packet['tracking_basis']), 'rights': deepcopy(packet['carbon_stock_inputs']['rights']),
            'reviewer': verified_input.request['rights']['reviewer']}
        proof = program.operation(self, program, tenant, verified_input, initial.bind_initial_stem_carbon,
            context, path/'carbon', path/'stem', self.access, crop_root_sha256=carbon_root_sha256,
            stem_root_sha256=stem_root_sha256, stem_start_index=index, declaration=declaration, profiles=profiles)
        _need(type(initial_binding_bytes) is bytes and 0 < len(initial_binding_bytes) <= MAX_WITNESS_BYTES
            and inputs._raw(proof) == initial_binding_bytes)
        program.guard(self, program, tenant, verified_input)
        return {'carbon_root_sha256': carbon_root_sha256, 'stem_root_sha256': stem_root_sha256,
            'stem_start_index': index, 'selected_stem_state_sha256': state_sha,
            'individual_context_sha256': context.root_sha256,
            'individual_request_sha256': sha256(context._request).hexdigest(),
            'individual_program_sha256': sha256(context._program).hexdigest(),
            'individual_seed_sha256': sha256(context._seed).hexdigest(),
            'initial_binding_sha256': sha256(initial_binding_bytes).hexdigest()}

    @_checked
    def produce(self, tenant, job_id, expected_input_sha256):
        p = self.__program
        p.guard(self, p, tenant, None)
        original = self.__current(self.service, tenant, job_id, expected_input_sha256)
        with inputs._scope(self.service.farms, tenant, original.request['farm']), _selection(self, tenant):
            p.guard(self, p, tenant, original)
            path = p.directory(self, p, tenant, original)
            profiles = p.operation(self, p, tenant, original, _profiles)
            cr = p.carbon(self, p, tenant, original, path/'carbon', profiles)
            sr = p.stem(self, p, tenant, original, path/'stem')
            packet = original.request['source']
            context = p.operation(self, p, tenant, original, initial.crop.prepare_context,
                program=packet['individual_program'], **packet['numerical'], profiles=profiles, **profiles)
            cm = p.operation(self, p, tenant, original, carbon.read_leaf_carbon_stock_manifest,
                path/'carbon', self.access, cr)
            sm = p.operation(self, p, tenant, original, stem.read_rational_morphology_manifest,
                path/'stem', self.access, sr)
            index = packet['stem_start_index']
            declaration = {'schema_version': 'stem-root-initial-source-binding-input-v1',
                'input_id': 'owned-material-seed-'+expected_input_sha256, 'origin': 'synthetic',
                'context_sha256': context.root_sha256, 'crop_root_sha256': cr,
                'crop_initial_state_sha256': cm['initial_state_sha256'], 'stem_root_sha256': sr,
                'stem_start_index': index, 'stem_source_state_sha256': sm['initial_state_sha256'] if index == -1
                    else sm['samples'][index]['state_sha256'],
                'time_origin_utc': cm['time_origin_utc'], 'model_floor_area': deepcopy(packet['individual_program']['model_floor_area']),
                'tracking_basis': deepcopy(packet['tracking_basis']), 'rights': deepcopy(packet['carbon_stock_inputs']['rights']),
                'reviewer': original.request['rights']['reviewer']}
            proof = p.operation(self, p, tenant, original, initial.bind_initial_stem_carbon,
                context, path/'carbon', path/'stem', self.access, crop_root_sha256=cr,
                stem_root_sha256=sr, stem_start_index=index, declaration=declaration, profiles=profiles)
            binding_raw = inputs._raw(proof)
            source = p.link(self, original, context=context, carbon_root_sha256=cr,
                stem_root_sha256=sr, initial_binding_bytes=binding_raw)
            row = original.witness['owned_input']
            witness = {'schema_version': 'supply-material-farm-seed-witness-v1', 'tenant_id': tenant,
                'farm': original.request['farm'], 'owned_input': row,
                'content_witness_sha256': original.witness['content_witness_sha256'],
                'resolved_witness_sha256': inputs._digest(original.witness), 'source': source,
                'producer': {'version': VERSION, 'code_sha256': dict(_PINS),
                    'original_dependency_sha256': {'carbon_stock': cm['code_sha256'], 'stem': sm['code_sha256']}},
                'effective_rights': {'use': True, 'display': True, 'redistribute': False},
                'scope': 'synthetic_farm_bound_initial_inputs_only',
                'profile_applicability': 'unvalidated_for_registered_crop', 'ex_ante_validity': 'not_established',
                'recording_vs_farm_decision': 'before_or_at' if inputs._time(row['created_at']) <=
                    inputs._time(original.witness['content_witness']['registration']['decision_at']) else 'after',
                'G0_G4': 'not_assessed', 'R2': 'not_approved'}
            encoded = inputs._raw(witness)
            _need(len(encoded) <= MAX_WITNESS_BYTES and len(binding_raw) <= MAX_WITNESS_BYTES)
            p.guard(self, p, tenant, original)
            result = VerifiedMaterialFarmSeed(context, binding_raw, encoded, _TOKEN)
        p.guard(self, p, tenant, original)
        return result
