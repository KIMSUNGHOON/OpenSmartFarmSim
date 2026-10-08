"""Genuine import target for owned, private harvest HTTPS test configuration."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path

from app import crop_harvest_runtime_factory as reader_config

VERSION = 'owned-harvest-https-dependencies-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
TOKENS = {name: ('owned-harvest-https-' + name + '-' + 't' * 32).encode()
          for name in ('owner', 'foreign', 'denied')}


class Evidence:
    def __init__(self, directory, input_file, result_file):
        from test_crop_harvest_current_query import FreshEvidence
        self.version = FreshEvidence.version
        self.directory, self.input_file, self.result_file = Path(directory), input_file, result_file

    def __call__(self, tenant, packet):
        from test_crop_harvest_current_query import runtime_module
        assert tenant == 'tenant-1'
        return {'input_directory': self.directory,
            'input_evidence_raw': runtime_module().private_bytes(self.input_file),
            'result_evidence_raw': reader_config.private._private_bytes(self.result_file, maximum=8 * 1024**2)}


def dependencies(*, config):
    from app import crop_cycle_calculation_result_store as storage
    from app import crop_cycle_calculation_current_query as current
    from app import crop_cycle_result_store as legacy
    from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
    from app.crop_cycle_farm_binding import CycleFarmBinding
    from app.crop_cycle_input_evidence import InputEvidenceAuthority
    from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
    from app.crop_result_store import READ_SCOPES
    from app.http_identity import BearerGrant, BearerRegistry, token_digest
    from app.market_source_store import MarketSourceStore
    from app.owned_fixture_registry import OwnedFixtureRegistry
    from app.research_registry import ResearchRegistry
    from test_api_runtime import dependencies as assemble
    from test_crop_cycle_artifact import PROFILES, NOTICE
    from test_crop_harvest_current_query import runtime_module, FreshRights

    private = reader_config.private
    raw = private._private_bytes(os.environ['OSSF_OWNED_HARVEST_TLS_BUNDLE'], maximum=65536)
    bundle = json.loads(raw)
    assert sha256(raw).hexdigest() == os.environ['OSSF_OWNED_HARVEST_TLS_BUNDLE_SHA256']
    assert bundle['version'] == VERSION and bundle['scope'] == 'owned_synthetic_actual_HTTPS_only'
    assert bundle['module_sha256'] == CODE_SHA256 == sha256(Path(__file__).read_bytes()).hexdigest()
    assert bundle['reader_factory_sha256'] == reader_config.CODE_SHA256
    for path, digest in bundle['static_sha256'].items():
        assert sha256(private._private_bytes(path, maximum=65536)).hexdigest() == digest
    runtime = runtime_module()
    value_raw = runtime.private_bytes(bundle['registered_runtime_config'])
    assert sha256(value_raw).hexdigest() == bundle['registered_runtime_sha256']
    value = json.loads(value_raw)
    assert value['scope'] == 'owned_synthetic_only' and value['code_sha256'] == runtime.CODE_SHA256
    assert all(sha256(runtime.private_bytes(p)).hexdigest() == h for p, h in value['static_sha256'].items())
    key = lambda name: private._private_bytes(bundle[name], minimum=32, maximum=4096)
    issuer = InputEvidenceAuthority(PROFILES, NOTICE,
        integrity_key=runtime.private_bytes(value['keys']['input']),
        issuer_id=value['input']['issuer_id'], key_id=value['input']['key_id'])
    rights = FreshRights(value['rights_file'])
    resolver = runtime.Resolver(value['input'], value['resolver_version'])
    result_authority = CalculationResultEvidenceAuthority(issuer, integrity_key=key('result_key'),
        issuer_id='owned-harvest-read', key_id='result-v1')
    evidence = Evidence(value['input']['directory'], value['input']['evidence_file'], bundle['result_evidence'])

    def crop_factory(*, farm_authoring_service):
        binding = CalculationFarmBinding(farm_authoring_service, issuer, input_rights=rights)
        server = storage.server.CalculationServerCustody(binding, Path(value['server_directory']),
            input_resolver=resolver, integrity_key=runtime.private_bytes(value['keys']['server']))
        return storage.CalculationCycleCropResultStore(server, integrity_key=key('parent_key'))

    def query_factory(*, result_store):
        return current.CalculationCurrentCycleQuery(result_store, result_authority, evidence_resolver=evidence)

    class UnusedLegacy:
        version = 'owned-harvest-https-unused-legacy-v1'
        def __call__(self, *_, **__):
            raise AssertionError('harvest HTTPS used legacy crop computation')

    def legacy_factory(*, farm_authoring_service):
        binding = CycleFarmBinding(farm_authoring_service, **PROFILES, notice_raw=NOTICE, input_rights=rights)
        server = legacy.server.CycleServerCustody(binding, Path(bundle['legacy_directory']),
            input_resolver=UnusedLegacy(), integrity_key=runtime.private_bytes(value['keys']['server']))
        return legacy.CycleCropResultStore(server, integrity_key=key('parent_key'))

    def sources(*, principal_provider):
        return MarketSourceStore(config.dsn, config.policy.schema, principal_provider=principal_provider,
            runtime_identity=(config.policy, 'authority'))

    def clock():
        control = json.loads(private._private_bytes(bundle['clock_file'], maximum=64))
        assert type(control) is dict and set(control) == {'expired'} and type(control['expired']) is bool
        return datetime.now(timezone.utc) + (timedelta(days=2) if control['expired'] else timedelta())

    now = datetime.now(timezone.utc)
    grants = tuple(BearerGrant(token_digest(TOKENS[name]), tenant, frozenset(scopes),
        now - timedelta(seconds=1), now + timedelta(hours=1)) for name, tenant, scopes in
        (('owner', 'tenant-1', READ_SCOPES), ('foreign', 'foreign', READ_SCOPES),
         ('denied', 'tenant-1', READ_SCOPES[:-1])))
    catalog = ResearchRegistry(runtime.private_bytes(value['registry_file']), value['registry_sha256'])
    return assemble(research_registry=catalog, bearer_registry=BearerRegistry(grants, clock=clock),
        owned_fixture_registry=OwnedFixtureRegistry(Path(value['owned_fixture_root'])),
        owned_research_contexts={next(iter(catalog._scopes)): value['owned_context_id']},
        market_scope_resolver=lambda *_: json.loads(runtime.private_bytes(value['market_scope_file'])),
        market_source_factory=sources, crop_cycle_result_store_factory=legacy_factory,
        crop_cycle_calculation_result_store_factory=crop_factory,
        crop_cycle_calculation_current_query_factory=query_factory,
        crop_harvest_current_query_factory=reader_config.load_harvest_current_query_factory(bundle['reader_config']))
