"""Operator factories for the owned, two-model loopback preview."""
from dataclasses import asdict, replace
from contextlib import contextmanager, ExitStack
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from types import ModuleType
import fcntl
import json
import os
import stat
import time

from app import operator_config
from app.crop_execution_worker_selection import select_crop_execution_loop
from app.crop_climate_joint_server_custody import JointServerCustody, JointCustodyPending
from app.crop_greenhouse_ventilation_current_query import VentilationCurrentQuery
from app.crop_greenhouse_ventilation_execution import VentilationExecutionService, INPUT_VERSION
from app.crop_greenhouse_ventilation_execution_checkpoint import VentilationExecutionCheckpointStore
from app.crop_greenhouse_ventilation_execution_worker import VentilationExecutionWorker
from app.crop_greenhouse_ventilation_farm_binding import VentilationFarmBinding, RIGHTS_VERSION
from app.crop_greenhouse_ventilation_input_evidence import VentilationInputEvidenceAuthority
from app.crop_greenhouse_ventilation_result_store import VentilationResultStore
from app.crop_greenhouse_ventilation_server_custody import VentilationServerCustody, VentilationCustodyPending
from app.crop_result_store import WRITE_SCOPES
from app.runtime_roles import RuntimeLoginPolicy

DIRECTORY = Path(__file__).resolve().parent
VERSION = 'owned-joint-ventilation-preview-runtime-v1'
FIELDS = {'runtime_version', 'original_operator', 'original_operator_sha256',
          'original_runtime_sha256', 'policy', 'ventilation', 'scopes', 'auth', 'worker_chunk_budget'}
VENTILATION_FIELDS = {'input_key', 'custody_key', 'result_key', 'custody',
                      'inputs', 'rights_file', 'reviews_file'}


def bind_registration_budget(farm_authoring_service, path):
    """Serialize nested validation reads across this preview's three processes."""
    from app.farm_authoring_storage import FarmAuthoringService
    path = Path(path)
    parent = path.parent.lstat()
    if (type(farm_authoring_service) is not FarmAuthoringService or not path.is_absolute()
            or not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid()
            or parent.st_mode & 0o077):
        raise ValueError('owned registration budget rejected')
    original = farm_authoring_service.read_registration
    if getattr(original, '__func__', None) is not FarmAuthoringService.read_registration:
        raise ValueError('owned registration budget already bound')
    def read(*args, **kwargs):
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
                raise ValueError('owned registration budget rejected')
            deadline = time.monotonic()+10
            while True:
                try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB); break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise ValueError('owned registration budget busy') from None
                    time.sleep(.025)
            current = path.stat(follow_symlinks=False)
            if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
                raise ValueError('owned registration budget changed')
            return original(*args, **kwargs)
        finally:
            os.close(fd)
    farm_authoring_service.read_registration = read
    return farm_authoring_service


def bind_worker_custody_wait(server):
    """Wait for a reader before entering custody; never replay an entered session."""
    pending = {JointServerCustody:JointCustodyPending,
               VentilationServerCustody:VentilationCustodyPending}.get(type(server))
    if pending is None or getattr(server._open, '__func__', None) is not type(server)._open:
        raise ValueError('owned worker custody wait rejected')
    original = server._open
    @contextmanager
    def opened(*args, **kwargs):
        with ExitStack() as stack:
            deadline = time.monotonic()+30
            while True:
                try:
                    session = stack.enter_context(original(*args, **kwargs))
                    break
                except pending:
                    if time.monotonic() >= deadline: raise
                    time.sleep(.025)
            yield session
    server._open = opened
    return server


def private(path):
    return json.loads(operator_config._private_bytes(path, maximum=2*1024**2),
        object_pairs_hook=operator_config._object, parse_constant=operator_config._constant)


def load():
    value = private(DIRECTORY/'runtime.private.json')
    if (type(value) is not dict or value.keys() != FIELDS or value['runtime_version'] != VERSION
            or type(value['ventilation']) is not dict or value['ventilation'].keys() != VENTILATION_FIELDS
            or type(value['auth']) is not dict or value['auth'].keys() != {'token_digest', 'issued_at', 'expires_at'}
            or type(value['worker_chunk_budget']) is not int or not 1 <= value['worker_chunk_budget'] <= 128):
        raise ValueError('owned mixed preview configuration rejected')
    path = operator_config._path(value['original_operator'])
    raw = operator_config._private_bytes(path, maximum=65536)
    if sha256(raw).hexdigest() != value['original_operator_sha256']:
        raise ValueError('owned original operator changed')
    original = ModuleType('preserved_joint_live_operator')
    original.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), original.__dict__)
    original_raw = operator_config._private_bytes(path.parent/'runtime.private.json', maximum=2*1024**2)
    if sha256(original_raw).hexdigest() != value['original_runtime_sha256']:
        raise ValueError('owned original runtime changed')
    previous = original.load()
    policy = RuntimeLoginPolicy(**value['policy'])
    expected = replace(RuntimeLoginPolicy(**previous['policy']), crop_greenhouse_ventilation_result_storage=True)
    scopes = sorted(set(previous['scopes']) | set(WRITE_SCOPES)
        | {'metadata', 'simulation_create', 'simulation_execute', 'cancel'})
    if (policy != expected or value['policy'] != asdict(expected) or value['scopes'] != scopes
            or value['auth']['token_digest'] != previous['token_digest']):
        raise ValueError('owned mixed preview authority changed')
    return value, previous, original


class Rights:
    policy_version = 'owned-ventilation-preview-rights-v1'

    def __init__(self, path):
        self.path = Path(path)

    def __call__(self, tenant, declaration, source, use):
        return (tenant == 'tenant-1' and declaration['schema_version'] == RIGHTS_VERSION
            and declaration['input_source_sha256'] == source and private(self.path).get(source) is True
            and use in ('research_calculation', 'research_display'))


class Resolver:
    version = 'owned-ventilation-preview-inputs-v1'

    def __init__(self, inputs):
        self.inputs = inputs

    def __call__(self, tenant, source, evidence):
        item = self.inputs[source]
        raw = operator_config._private_bytes(item['proof'], maximum=2*1024**2)
        if tenant != 'tenant-1' or sha256(raw).hexdigest() != evidence:
            raise ValueError('owned ventilation preview input rejected')
        return Path(item['directory']), raw


def ventilation_store(farms, config, *, wait_for_custody=False):
    bind_registration_budget(farms, DIRECTORY/'registration-budget.lock')
    value = config['ventilation']
    authority = VentilationInputEvidenceAuthority(integrity_key=bytes.fromhex(value['input_key']),
        issuer_id='owned-preview-ventilation', key_id='owned-preview-ventilation-v1',
        review_resolver=lambda identity: private(value['reviews_file'])[identity])
    binding = VentilationFarmBinding(farms, authority, input_rights=Rights(value['rights_file']))
    server = VentilationServerCustody(binding, Path(value['custody']), input_resolver=Resolver(value['inputs']),
        integrity_key=bytes.fromhex(value['custody_key']))
    if wait_for_custody: bind_worker_custody_wait(server)
    return VentilationResultStore(server, integrity_key=bytes.fromhex(value['result_key']))


def dependencies(*, config):
    value, _, original = load()
    if config.policy != RuntimeLoginPolicy(**value['policy']):
        raise ValueError('owned mixed preview policy mismatch')
    auth = value['auth']
    grant = original.BearerGrant(auth['token_digest'], 'tenant-1', frozenset(value['scopes']),
        datetime.fromisoformat(auth['issued_at']), datetime.fromisoformat(auth['expires_at']))
    return replace(original.dependencies(config=config),
        bearer_registry=original.BearerRegistry((grant,)),
        crop_greenhouse_ventilation_result_store_factory=lambda *, farm_authoring_service:
            ventilation_store(farm_authoring_service, value),
        crop_greenhouse_ventilation_current_query_factory=lambda *, result_store: VentilationCurrentQuery(result_store))


def farms(value, previous, original):
    policy = RuntimeLoginPolicy(**value['policy'])
    principal = dict(previous['service_principal'])
    principal['scopes'] = set(principal['scopes']) | set(value['scopes'])
    options = {'runtime_identity':(policy, 'authority'), 'principal_provider':lambda:principal}
    dsn, schema = previous['dsn'], policy.schema
    jobs = original.JobStore(dsn, schema, Path(previous['artifacts']), audit_runtime_grants=True, **options)
    sources = original.MarketSourceStore(dsn, schema, **options)
    runs = original.ThermalRunStore(dsn, schema, gate_key=bytes.fromhex(previous['thermal_key']),
        release_verifier=lambda *_:None, context_verifier=original.context_verifier, **options)
    holds = original.MarketHoldStore(dsn, schema, context_store=runs,
        scope_resolver=lambda *_:dict(previous['scope']), signing_key=bytes.fromhex(previous['market_key']), **options)
    candidates = original.MarketCandidateStore(dsn, schema,
        original._MarketSources(sources, holds, principal_provider=options['principal_provider']), **options)
    research = original.registry(previous)
    owned = original.OwnedResearchService(jobs, runs, research, original.OwnedFixtureRegistry(Path(previous['root'])),
        {next(iter(research._scopes)):'context-1'})
    replay = original.FarmReplayScenarioService(jobs, original.ThermalScenarioStore(runs, holds),
        candidates, research, owned_research=owned)
    return original.FarmAuthoringService(replay)


def worker_joint():
    value, previous, original = load()
    def build():
        bound_farms = bind_registration_budget(farms(value, previous, original), DIRECTORY/'registration-budget.lock')
        store = original.result_store(bound_farms, previous)
        bind_worker_custody_wait(store.server)
        admission = original.JointCropClimateExecutionService(store.server.binding, input_resolver=store.server.input_resolver)
        worker = original.JointExecutionWorker(original.JointExecutionCheckpointStore(admission, store.server), store,
            tenant_id='tenant-1', chunk_budget=value['worker_chunk_budget'])
        return original.DeterministicWorkerLoop(worker, input_versions=frozenset({original.INPUT_VERSION}), page_size=50)
    return select_crop_execution_loop('crop-climate-joint', joint_factory=build)


def worker_ventilation():
    value, previous, original = load()
    def build():
        store = ventilation_store(farms(value, previous, original), value, wait_for_custody=True)
        admission = VentilationExecutionService(store.server.binding, input_resolver=store.server.input_resolver)
        worker = VentilationExecutionWorker(VentilationExecutionCheckpointStore(admission, store.server), store,
            tenant_id='tenant-1', chunk_budget=value['worker_chunk_budget'])
        return original.DeterministicWorkerLoop(worker, input_versions=frozenset({INPUT_VERSION}), page_size=50)
    return select_crop_execution_loop('crop-greenhouse-ventilation', ventilation_factory=build)
