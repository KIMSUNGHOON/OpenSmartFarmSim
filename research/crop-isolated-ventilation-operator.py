"""Factories for a separate, owned synthetic ventilation API and consumer."""
from dataclasses import asdict, replace
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from types import ModuleType

from app.api_runtime import ApiRuntimeDependencies
from app.runtime_roles import RuntimeLoginPolicy
from app.crop_result_store import WRITE_SCOPES
import isolated_ventilation_support as support

DIRECTORY = Path(__file__).resolve().parent
VERSION = 'owned-isolated-ventilation-runtime-v1'


def load():
    value = support.private(DIRECTORY/'runtime.private.json')
    if (value.keys() != support.FIELDS | {'dsn', 'artifacts', 'legacy'}
            or value['runtime_version'] != VERSION
            or value['ventilation'].keys() != support.VENTILATION_FIELDS
            or value['auth'].keys() != {'token_digest', 'issued_at', 'expires_at'}
            or type(value['worker_chunk_budget']) is not int or value['worker_chunk_budget'] != 8):
        raise ValueError('isolated preview configuration rejected')
    path = support.operator_config._path(value['original_operator'])
    raw = support.operator_config._private_bytes(path, maximum=65536)
    previous_raw = support.operator_config._private_bytes(path.parent/'runtime.private.json', maximum=2*1024**2)
    if (sha256(raw).hexdigest() != value['original_operator_sha256']
            or sha256(previous_raw).hexdigest() != value['original_runtime_sha256']):
        raise ValueError('isolated preview original changed')
    original = ModuleType('isolated_preview_original')
    original.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), original.__dict__)
    previous = original.load()
    old = RuntimeLoginPolicy(**previous['policy'])
    policy = RuntimeLoginPolicy(**value['policy'])
    expected = replace(old, schema=policy.schema, owner=policy.owner, prefix=policy.prefix,
        crop_climate_joint_result_storage=False, crop_greenhouse_ventilation_result_storage=True)
    scopes = sorted(set(previous['scopes']) | set(WRITE_SCOPES)
        | {'metadata', 'simulation_create', 'simulation_execute', 'cancel'})
    from psycopg.conninfo import conninfo_to_dict
    dsn = conninfo_to_dict(value['dsn'])
    if (policy != expected or value['policy'] != asdict(expected)
            or any(getattr(policy, name) == getattr(old, name) for name in ('schema', 'owner', 'prefix'))
            or value['scopes'] != scopes
            or value['auth'] != {name: previous[name] for name in value['auth']}
            or dsn.get('user') != policy.roles['authority'] or dsn.get('dbname') != policy.database
            or dsn.get('host') != '127.0.0.1' or dsn.get('require_auth') != 'scram-sha-256'):
        raise ValueError('isolated preview authority rejected')
    for name in (value['artifacts'], value['legacy'], value['ventilation']['custody'], dsn['passfile']):
        local = support.operator_config._path(name)
        local.relative_to(DIRECTORY)
        if local.is_symlink():
            raise ValueError('isolated preview path rejected')
    return value, {**previous, **{name: value[name] for name in ('dsn', 'artifacts', 'legacy')}}, original


def dependencies(*, config):
    value, previous, original = load()
    policy = RuntimeLoginPolicy(**value['policy'])
    if (config.policy != policy or config.dsn != value['dsn']
            or config.artifact_root != Path(value['artifacts'])
            or config.crop_climate_joint_execution or config.crop_climate_joint_prefix):
        raise ValueError('isolated preview API binding rejected')
    def sources(*, principal_provider):
        return original.MarketSourceStore(config.dsn, policy.schema,
            principal_provider=principal_provider, runtime_identity=(policy, 'authority'))
    def unused(*args):
        raise ValueError('isolated preview legacy input unavailable')
    unused.version = 'owned-preview-unused-legacy-v1'
    def legacy(*, farm_authoring_service):
        binding = original.CycleFarmBinding(farm_authoring_service, **original.PROFILES,
            notice_raw=original.NOTICE, input_rights=original.Rights())
        server = original.CycleServerCustody(binding, Path(previous['legacy']), input_resolver=unused,
            integrity_key=bytes.fromhex(previous['custody_key']))
        return original.CycleCropResultStore(server, integrity_key=bytes.fromhex(previous['result_key']))
    auth = value['auth']
    grant = original.BearerGrant(auth['token_digest'], 'tenant-1', frozenset(value['scopes']),
        datetime.fromisoformat(auth['issued_at']), datetime.fromisoformat(auth['expires_at']))
    registry = original.registry(previous)
    return ApiRuntimeDependencies(research_registry=registry, bearer_registry=original.BearerRegistry((grant,)),
        context_verifier=original.context_verifier, release_verifier=lambda *_: None,
        market_scope_resolver=lambda *_: dict(previous['scope']), market_source_factory=sources,
        owned_fixture_registry=original.OwnedFixtureRegistry(Path(previous['root'])),
        owned_research_contexts={next(iter(registry._scopes)): 'context-1'},
        crop_cycle_result_store_factory=legacy,
        crop_greenhouse_ventilation_result_store_factory=lambda *, farm_authoring_service:
            support.ventilation_store(farm_authoring_service, value),
        crop_greenhouse_ventilation_current_query_factory=lambda *, result_store:
            support.VentilationCurrentQuery(result_store))


def worker():
    value, previous, original = load()
    def build():
        store = support.ventilation_store(support.farms(value, previous, original), value, wait_for_custody=True)
        admission = support.VentilationExecutionService(store.server.binding, input_resolver=store.server.input_resolver)
        worker = support.VentilationExecutionWorker(support.VentilationExecutionCheckpointStore(admission, store.server),
            store, tenant_id='tenant-1', chunk_budget=value['worker_chunk_budget'])
        return original.DeterministicWorkerLoop(worker, input_versions=frozenset({support.INPUT_VERSION}), page_size=50)
    return support.select_crop_execution_loop('crop-greenhouse-ventilation', ventilation_factory=build)
