"""Operator factories for the isolated, owned synthetic execution preview."""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import json

from app.api_runtime import ApiRuntimeDependencies
from app.crop_climate_joint_current_query import JointCropClimateCurrentQuery
from app.crop_climate_joint_execution_worker import JointExecutionWorker
from app.crop_climate_joint_execution import JointCropClimateExecutionService, INPUT_VERSION
from app.crop_climate_joint_execution_checkpoint import JointExecutionCheckpointStore
from app.crop_climate_joint_farm_binding import JointFarmBinding, RIGHTS_VERSION
from app.crop_climate_joint_input_evidence import JointInputEvidenceAuthority
from app.crop_climate_joint_result_store import JointCropClimateResultStore
from app.crop_climate_joint_server_custody import JointServerCustody
from app.crop_cycle_farm_binding import CycleFarmBinding
from app.crop_cycle_result_store import CycleCropResultStore
from app.crop_cycle_server_custody import CycleServerCustody
from app.deterministic_work import DeterministicWorkerLoop
from app.farm_authoring_storage import FarmAuthoringService
from app.farm_replay_scenario import FarmReplayScenarioService
from app.http_identity import BearerGrant, BearerRegistry
from app.job_store import JobStore
from app.market_candidate_store import MarketCandidateStore
from app.market_hold_store import MarketHoldStore
from app.api_market_source import _MarketSources
from app.market_source_store import MarketSourceStore
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.owned_research import OwnedResearchService
from app.research_registry import ResearchRegistry
from app.runtime_roles import RuntimeLoginPolicy
from app.thermal_run_store import ThermalRunStore
from app.thermal_scenario_store import ThermalScenarioStore
from test_market_hold_store import context_verifier
from test_crop_cycle_artifact import PROFILES, NOTICE


DIRECTORY = Path(__file__).resolve().parent


def private(name):
    path = DIRECTORY/name
    stat = path.lstat()
    if not path.is_file() or path.is_symlink() or stat.st_mode & 0o077 or stat.st_size > 2*1024**2:
        raise ValueError('owned preview configuration rejected')
    return json.loads(path.read_bytes())


def load():
    return private('runtime.private.json')


def registry(p):
    raw = p['registry_raw'].encode()
    return ResearchRegistry(raw, sha256(raw).hexdigest())


class Rights:
    policy_version = 'owned-joint-preview-rights-v1'

    def __call__(self, tenant, declaration, source, use):
        return (tenant == 'tenant-1' and declaration['schema_version'] == RIGHTS_VERSION
            and declaration['input_source_sha256'] == source
            and private('rights.private.json').get(source) is True
            and use in ('research_calculation', 'research_display'))


class Resolver:
    version = 'owned-joint-preview-inputs-v1'

    def __init__(self, p):
        self.inputs = p['inputs']

    def __call__(self, tenant, source, evidence):
        item = self.inputs[source]
        raw = Path(item['proof']).read_bytes()
        if tenant != 'tenant-1' or sha256(raw).hexdigest() != evidence:
            raise ValueError('owned preview input rejected')
        return Path(item['directory']), raw


def result_store(farms, p):
    authority = JointInputEvidenceAuthority(integrity_key=bytes.fromhex(p['input_key']),
        issuer_id='owned-preview', key_id='owned-preview-v1',
        review_resolver=lambda identity: private('reviews.private.json')[identity])
    binding = JointFarmBinding(farms, authority, input_rights=Rights())
    server = JointServerCustody(binding, Path(p['custody']), input_resolver=Resolver(p),
        integrity_key=bytes.fromhex(p['custody_key']))
    return JointCropClimateResultStore(server, integrity_key=bytes.fromhex(p['result_key']))


def dependencies(*, config):
    p = load(); identity = (config.policy, 'authority')
    def sources(*, principal_provider):
        return MarketSourceStore(config.dsn, config.policy.schema,
            principal_provider=principal_provider, runtime_identity=identity)
    def joint(*, farm_authoring_service):
        return result_store(farm_authoring_service, p)
    def unused(*args):
        raise ValueError('owned preview legacy input unavailable')
    unused.version = 'owned-preview-unused-legacy-v1'
    def legacy(*, farm_authoring_service):
        binding = CycleFarmBinding(farm_authoring_service, **PROFILES, notice_raw=NOTICE, input_rights=Rights())
        server = CycleServerCustody(binding, Path(p['legacy']), input_resolver=unused,
            integrity_key=bytes.fromhex(p['custody_key']))
        return CycleCropResultStore(server, integrity_key=bytes.fromhex(p['result_key']))
    grant = BearerGrant(p['token_digest'], 'tenant-1', frozenset(p['scopes']),
        datetime.fromisoformat(p['issued_at']), datetime.fromisoformat(p['expires_at']))
    research = registry(p)
    return ApiRuntimeDependencies(research_registry=research, bearer_registry=BearerRegistry((grant,)),
        context_verifier=context_verifier, release_verifier=lambda *_: None,
        market_scope_resolver=lambda *_: dict(p['scope']), market_source_factory=sources,
        owned_fixture_registry=OwnedFixtureRegistry(Path(p['root'])),
        owned_research_contexts={next(iter(research._scopes)): 'context-1'},
        crop_cycle_result_store_factory=legacy, crop_climate_joint_result_store_factory=joint,
        crop_climate_joint_current_query_factory=lambda *, result_store: JointCropClimateCurrentQuery(result_store))


def worker():
    p = load(); policy = RuntimeLoginPolicy(**p['policy']); identity = (policy, 'authority')
    principal = dict(p['service_principal']); principal['scopes'] = set(principal['scopes'])
    kw = {'runtime_identity': identity, 'principal_provider': lambda: principal}
    dsn = p['dsn']; schema = policy.schema
    jobs = JobStore(dsn, schema, Path(p['artifacts']), audit_runtime_grants=True, **kw)
    sources = MarketSourceStore(dsn, schema, **kw)
    runs = ThermalRunStore(dsn, schema, gate_key=bytes.fromhex(p['thermal_key']),
        release_verifier=lambda *_: None, context_verifier=context_verifier, **kw)
    holds = MarketHoldStore(dsn, schema, context_store=runs, scope_resolver=lambda *_: dict(p['scope']),
        signing_key=bytes.fromhex(p['market_key']), **kw)
    candidates = MarketCandidateStore(dsn, schema, _MarketSources(sources, holds, principal_provider=kw['principal_provider']), **kw)
    research = registry(p)
    owned = OwnedResearchService(jobs, runs, research, OwnedFixtureRegistry(Path(p['root'])),
        {next(iter(research._scopes)): 'context-1'})
    replay = FarmReplayScenarioService(jobs, ThermalScenarioStore(runs, holds), candidates, research, owned_research=owned)
    store = result_store(FarmAuthoringService(replay), p)
    admission = JointCropClimateExecutionService(store.server.binding, input_resolver=store.server.input_resolver)
    worker = JointExecutionWorker(JointExecutionCheckpointStore(admission, store.server), store,
        tenant_id='tenant-1', chunk_budget=p.get('worker_chunk_budget', 16))
    return DeterministicWorkerLoop(worker, input_versions=frozenset({INPUT_VERSION}), page_size=50)
