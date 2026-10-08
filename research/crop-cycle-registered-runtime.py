"""Private owned-fixture runtime reconstruction, never a production CLI worker."""
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import signal
import stat

from app import crop_cycle_calculation_context as engine
from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_server_custody as custody
from app import operator_config
from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
from app.crop_cycle_input_evidence import InputEvidenceAuthority
from app.farm_authoring_storage import FarmAuthoringService
from app.farm_replay_scenario import FarmReplayScenarioService
from app.job_store import JobStore
from app.market_source_store import MarketSourceStore
from app.market_hold_store import MarketHoldStore
from app.market_candidate_store import MarketCandidateStore
from app.api_market_source import _MarketSources
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.owned_research import OwnedResearchService
from app.research_registry import ResearchRegistry
from app.runtime_roles import RuntimeLoginPolicy
from app.thermal_run_store import ThermalRunStore, _canonical
from app.thermal_scenario_store import ThermalScenarioStore
from test_crop_cycle_artifact import PROFILES, NOTICE
from test_market_hold_store import context_verifier

VERSION = 'owned-registered-calculation-runtime-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
FIELDS = {'version','scope','code_sha256','policy','dsn_file','artifact_root','registry_file',
    'registry_sha256','owned_fixture_root','owned_context_id','market_scope_file','principal_file',
    'rights_file','keys','input','request_file','request_sha256','server_directory','resolver_version','static_sha256'}


def private_bytes(path):
    path = operator_config._path(str(path))
    parent = custody.job_store._open_directory_nofollow(path.parent)
    try:
        custody._secure(parent, directory=True)
        return custody._read(parent, path.name, 1024*1024)
    finally: os.close(parent)


def write_private(path, raw):
    fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fchmod(stream.fileno(), 0o400); os.fsync(stream.fileno())
    fd = os.open(Path(path).parent, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)


def export_runtime(server, request_raw, directory):
    server.binding._binding()
    if any(p.is_dir() for p in Path(server.directory).iterdir()):
        raise ValueError('new owned runtime declaration required before calculation')
    directory = Path(directory); directory.mkdir(mode=0o700)
    binding = server.binding; farms = binding.farms; replay = farms.replay
    owned = replay.owned_research; holds = replay.thermal.holds; issuer = binding.input_authority
    registrations = [{'tenant_id':s.tenant_id,'point':{'latitude':s.point[0],'longitude':s.point[1]},
        'period_start_utc':s.period_start_utc,'period_end_utc':s.period_end_utc,'goal_id':s.goal_id,
        'provider_ids':list(s.provider_ids)} for s in owned.catalog._scopes.values()]
    registry_raw = _canonical({'registry_version':'research-registry-v1','registrations':registrations})
    assert sha256(registry_raw).hexdigest() == owned.catalog.sha256
    assert len(owned._contexts) == 1
    request = json.loads(request_raw); source = request['input']; tenant = registrations[0]['tenant_id']
    with server.input_resolver(source['root_sha256'], authority=issuer) as context:
        input_directory = context._directory; input_proof = context._evidence_raw
    principal = dict(binding.jobs.principal_provider()); principal['scopes'] = sorted(principal['scopes'])
    market_scope = holds._scope_resolver(tenant, request.get('snapshot_id'), request.get('decision_context_id'))
    files = {'dsn':binding.jobs._dsn.encode(), 'registry':registry_raw, 'market-scope':_canonical(market_scope),
        'principal':_canonical(principal), 'rights':_canonical({'allowed':True}), 'request':request_raw,
        'input-proof':input_proof, 'thermal-key':holds._context_store._gate_key, 'market-key':holds._key,
        'input-key':issuer.integrity_key, 'server-key':server.integrity_key}
    for name, raw in files.items(): write_private(directory/(name+'.private'), raw)
    path = lambda name:str(directory/(name+'.private'))
    fixed = {path(name):sha256(raw).hexdigest() for name,raw in files.items() if name not in ('principal','rights')}
    value = {'version':VERSION,'scope':'owned_synthetic_only','code_sha256':CODE_SHA256,
        'policy':asdict(binding.jobs.runtime_identity[0]),'dsn_file':path('dsn'),
        'artifact_root':str(binding.jobs.artifact_root),'registry_file':path('registry'),
        'registry_sha256':owned.catalog.sha256,'owned_fixture_root':str(owned.registry._root),
        'owned_context_id':next(iter(owned._contexts.values())), 'market_scope_file':path('market-scope'),
        'principal_file':path('principal'),'rights_file':path('rights'),
        'keys':{key:path(key+'-key') for key in ('thermal','market','input','server')},
        'input':{'directory':str(input_directory),'root_sha256':source['root_sha256'],
                 'evidence_file':path('input-proof'),'issuer_id':issuer.issuer_id,'key_id':issuer.key_id},
        'request_file':path('request'),'request_sha256':sha256(request_raw).hexdigest(),
        'server_directory':str(server.directory),'resolver_version':server.input_resolver.version,'static_sha256':fixed}
    raw = _canonical(value); target = directory/'runtime.json'; write_private(target, raw)
    return target, sha256(raw).hexdigest()


class Rights:
    policy_version = 'owned-private-current-input-rights-v1'
    def __init__(self, path): self.path = path
    def __call__(self, *args):
        value = json.loads(private_bytes(self.path))
        if type(value) is not dict or set(value) != {'allowed'} or type(value['allowed']) is not bool:
            raise ValueError('owned rights control rejected')
        return value['allowed']


class Resolver:
    def __init__(self, value, version): self.value, self.version, self.last, self.opened = value, version, None, 0
    def __call__(self, root, *, authority):
        if self.last is not None:
            assert self.last.reader.closed and not self.last._cache and not self.last.reader._cache
        if root != self.value['root_sha256']: raise ValueError('owned input identity mismatch')
        self.last = engine.open_calculation_context(self.value['directory'], root,
            private_bytes(self.value['evidence_file']), authority=authority)
        self.opened += 1
        return self.last


def _assemble(value):
    def principal():
        p = json.loads(private_bytes(value['principal_file']))
        if (type(p) is not dict or set(p) != {'authenticated','tenant_id','scopes'}
                or type(p['authenticated']) is not bool or type(p['tenant_id']) is not str
                or type(p['scopes']) is not list or any(type(s) is not str for s in p['scopes'])):
            raise ValueError('owned principal control rejected')
        return p
    policy = RuntimeLoginPolicy(**value['policy']); identity = (policy,'authority')
    dsn = private_bytes(value['dsn_file']).decode(); keys = {k:private_bytes(p) for k,p in value['keys'].items()}
    jobs = JobStore(dsn, policy.schema, Path(value['artifact_root']), principal_provider=principal,
        runtime_identity=identity, audit_runtime_grants=True)
    runs = ThermalRunStore(dsn, policy.schema, gate_key=keys['thermal'], release_verifier=lambda *_:None,
        context_verifier=context_verifier, principal_provider=principal, runtime_identity=identity)
    holds = MarketHoldStore(dsn, policy.schema, context_store=runs,
        scope_resolver=lambda *_:json.loads(private_bytes(value['market_scope_file'])),
        principal_provider=principal, signing_key=keys['market'], runtime_identity=identity)
    sources = MarketSourceStore(dsn, policy.schema, principal_provider=principal, runtime_identity=identity)
    candidates = MarketCandidateStore(dsn, policy.schema, _MarketSources(sources, holds, principal_provider=principal),
        principal_provider=principal, runtime_identity=identity)
    registry = ResearchRegistry(private_bytes(value['registry_file']), value['registry_sha256'])
    owned = OwnedResearchService(jobs, runs, registry, OwnedFixtureRegistry(Path(value['owned_fixture_root'])),
        {next(iter(registry._scopes)):value['owned_context_id']})
    farms = FarmAuthoringService(FarmReplayScenarioService(jobs, ThermalScenarioStore(runs,holds), candidates, registry, owned))
    p = value['input']; issuer = InputEvidenceAuthority(PROFILES, NOTICE, integrity_key=keys['input'],
        issuer_id=p['issuer_id'], key_id=p['key_id'])
    binding = CalculationFarmBinding(farms, issuer, input_rights=Rights(value['rights_file']))
    resolver = Resolver(p, value['resolver_version'])
    return custody.CalculationServerCustody(binding, Path(value['server_directory']),
        input_resolver=resolver, integrity_key=keys['server']), private_bytes(value['request_file'])


def load_runtime(path, expected_sha256):
    try:
        raw = private_bytes(path); value = json.loads(raw)
        if (sha256(raw).hexdigest() != expected_sha256 or _canonical(value) != raw
                or type(value) is not dict or set(value) != FIELDS or value['version'] != VERSION
                or value['scope'] != 'owned_synthetic_only' or value['code_sha256'] != CODE_SHA256
                or CODE_SHA256 != sha256(Path(__file__).read_bytes()).hexdigest()): raise ValueError()
        if type(value['keys']) is not dict or set(value['keys']) != {'thermal','market','input','server'}: raise ValueError()
        if type(value['input']) is not dict or set(value['input']) != {'directory','root_sha256','evidence_file','issuer_id','key_id'}: raise ValueError()
        fixed = {value[k] for k in ('dsn_file','registry_file','market_scope_file','request_file')}
        fixed.update(value['keys'].values()); fixed.add(value['input']['evidence_file'])
        if type(value['static_sha256']) is not dict or set(value['static_sha256']) != fixed: raise ValueError()
        if any(sha256(private_bytes(p)).hexdigest() != digest for p,digest in value['static_sha256'].items()): raise ValueError()
        if sha256(private_bytes(value['request_file'])).hexdigest() != value['request_sha256']: raise ValueError()
        return _assemble(value)
    except Exception: raise ValueError('owned registered runtime unavailable') from None


def identity():
    fields = Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()
    return {'pid':os.getpid(),'start_ticks':fields[19],
            'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'executable':str(Path('/proc/self/exe').resolve())}


def emit(value):
    print(json.dumps(value,sort_keys=True,allow_nan=False),flush=True)
    if stat.S_ISREG(os.fstat(1).st_mode): os.fsync(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',required=True); parser.add_argument('--sha256',required=True)
    parser.add_argument('--advance',action='store_true'); parser.add_argument('--stop-after-recovery',action='store_true')
    parser.add_argument('--max-steps',type=int,default=7); parser.add_argument('--max-transitions',type=int,default=8)
    args = parser.parse_args(); descriptors = len(os.listdir('/proc/self/fd'))
    server, raw = load_runtime(args.config,args.sha256)
    with server.binding.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    rhs, validate = engine.short._Evaluator.rhs, artifact._validate_delta
    def forbidden(*a,**k): raise AssertionError('recovery ran RHS/delta QC')
    engine.short._Evaluator.rhs = artifact._validate_delta = forbidden
    with server._open('tenant-1',raw,False) as journal:
        progress = json.loads(journal.inspect()); checkpoint = deepcopy(journal.writer._checkpoint)
    engine.short._Evaluator.rhs, artifact._validate_delta = rhs, validate
    emit({'stage':'recovered','worker':identity(),'progress':progress,'checkpoint':checkpoint,
          'RHS_calls':0,'delta_QC_calls':0,'actual_scram_used_password':True})
    if args.stop_after_recovery: signal.raise_signal(signal.SIGSTOP)
    calls = 0
    def measured(*a,**k):
        nonlocal calls
        calls += 1; return rhs(*a,**k)
    engine.short._Evaluator.rhs = measured
    if args.advance:
        progress = json.loads(server.advance('tenant-1',raw,budget={'max_steps':args.max_steps,'max_transitions':args.max_transitions}))
    engine.short._Evaluator.rhs = artifact._validate_delta = forbidden
    with server._open('tenant-1',raw,False) as journal:
        assert json.loads(journal.inspect()) == progress
        checkpoint = deepcopy(journal.writer._checkpoint)
    assert server.input_resolver.last.reader.closed and not server.input_resolver.last._cache and not server.input_resolver.last.reader._cache
    assert len(os.listdir('/proc/self/fd')) == descriptors
    emit({'stage':'result','worker':identity(),'progress':progress,'checkpoint':checkpoint,'actual_RHS_calls':calls,
          'FD_before_after':[descriptors,descriptors],'all_contexts_closed_bounded_last_reference':True,
          'scope':'owned_synthetic_fresh_python_not_product_CLI','gates':'not_assessed'})


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        emit({'stage':'error','error_class':type(exc).__name__}); raise SystemExit(71)
