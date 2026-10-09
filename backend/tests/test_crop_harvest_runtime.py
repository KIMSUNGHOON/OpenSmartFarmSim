"""Explicit harvest reader assembly; actual transport and protected restore follow."""
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from types import SimpleNamespace

import psycopg
from psycopg import errors, sql
import pytest

from app import api, api_runtime as runtime
from app.api_openapi import _SchemaOnlyStores, contract_document, contract_bytes, CONTRACT_PATH
from app.http_identity import current_principal
from test_api_runtime import config, dependencies, policy
from test_api_crop_cycle_route import protect
from test_api_crop_harvest_route import get
from test_crop_harvest import save_native
from test_crop_harvest_registry import harvest_scope
from test_crop_harvest_current_query import forbid_all_reads_math
from test_crop_cycle_calculation_runtime import audit_database
from test_crop_cycle_calculation_result_store_farms import login_scope, original_login_scope
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from test_api_serve import tls_files
from login_database import login_database


@pytest.mark.parametrize('old,calc,store,query', [
    (False,False,False,False), (True,False,False,False), (False,True,True,True),
    (True,True,False,False), (True,True,True,False), (True,True,False,True)])
def test_missing_calculation_prerequisites_refuse_before_connections(monkeypatch, old, calc, store, query):
    calls = []
    def factory(**_): calls.append('factory')
    monkeypatch.setattr(runtime, 'JobStore', lambda *_, **__: calls.append('connection'))
    selected = replace(policy(), crop_cycle_result_storage=old, crop_cycle_calculation_result_storage=calc)
    deps = dependencies(crop_cycle_result_store_factory=factory if old else None,
        crop_cycle_calculation_result_store_factory=factory if store else None,
        crop_cycle_calculation_current_query_factory=factory if query else None,
        crop_harvest_current_query_factory=factory)
    with pytest.raises(ValueError, match='^API runtime assembly rejected$'):
        runtime.ApiRuntime(config(policy=selected), deps)
    assert calls == []


@pytest.mark.parametrize('value', [True, 0, 'owned-private-factory', object()])
def test_noncallable_factory_is_closed(value):
    with pytest.raises(ValueError, match='^API runtime dependencies rejected$'):
        dependencies(crop_harvest_current_query_factory=value)


def test_default_factory_is_disabled_and_explicit_factory_hidden():
    deps = dependencies(); assert deps.crop_harvest_current_query_factory is None
    selected = replace(deps, crop_harvest_current_query_factory=lambda **_: None)
    assert 'crop_harvest_current_query_factory' not in repr(selected)


def test_create_app_forwards_explicit_reader_and_default_is_authenticated_unavailable(monkeypatch):
    seen = []; original = api.install_harvest_routes; stores = _SchemaOnlyStores()
    def capture(*args, **kwargs): seen.append(kwargs)
    monkeypatch.setattr(api, 'install_harvest_routes', capture)
    query = object()
    api.create_app(stores, stores, stores, stores, principal_provider=current_principal, crop_harvest_current_query=query)
    assert len(seen) == 1 and seen[0]['query'] is query and seen[0]['jobs'] is stores
    assert seen[0]['principal_provider'] is current_principal and seen[0]['farms'] is None
    monkeypatch.setattr(api, 'install_harvest_routes', original)
    app = protect(api.create_app(stores, stores, stores, stores, principal_provider=current_principal))
    case = SimpleNamespace(app=app, result_id='crop-harvest-registered-result-v1:'+'a'*64,
        farm={'scenario_id':'owned','scenario_revision':'1','registration_sha256':'a'*64,'crop_id':'owned'})
    assert get(case)[0] == 503 and get(case, headers=[])[0] == 401


def test_standard_openapi_includes_harvest_and_matches_generated_contract():
    doc = contract_document(); operation = doc['paths']['/v1/crop-harvest-research-results/{result_id}']['get']
    assert operation['operationId'] == 'getHarvestResearchResult'
    assert operation['security'] == [{'ServiceBearer': []}]
    assert CONTRACT_PATH.read_bytes() == contract_bytes()


@pytest.mark.parametrize('first', ['app.api_runtime', 'app.api', 'app.calculation_operator_config'])
def test_fresh_import_preserves_lazy_calculation_and_no_connections(first):
    code = '''import importlib,json,os,socket,sys,psycopg
calls=[]
def forbidden(*a,**k):
 calls.append(True);raise AssertionError('connection during import')
psycopg.connect=forbidden;socket.create_connection=forbidden
before=len(os.listdir('/proc/self/fd'))
importlib.import_module(sys.argv[1])
from app.api_openapi import contract_document
assert '/v1/crop-harvest-research-results/{result_id}' in contract_document()['paths']
assert not calls and before==len(os.listdir('/proc/self/fd'))
assert all(n not in sys.modules for n in ['app.crop_harvest_current_query','app.crop_harvest_registry','app.crop_cycle_calculation_context'])
print(json.dumps({'first':sys.argv[1],'connection_calls':0,'FD_before_after':[before,before],'calculation_modules_loaded':False}))
'''
    child = subprocess.run([sys.executable, '-c', code, first], capture_output=True, text=True, timeout=30)
    assert child.returncode == 0 and child.stderr == ''
    save_native('harvest-runtime-import-'+first.rsplit('.',1)[-1]+'.json',
        {'original_child_exit_code':child.returncode, **json.loads(child.stdout)})


@pytest.mark.parametrize('original_login_scope', [{'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_cycle_result_storage':True}], indirect=True)
def test_actual_scram_reader_same_endpoint_farm_reassembly_denials_and_no_calculation(
        authoring, harvest_scope, tls_files, tmp_path, monkeypatch, audit_database, login_database):
    from app import crop_cycle_calculation_context as engine
    from app import crop_cycle_calculation_result_store as storage
    from app import crop_cycle_calculation_current_query as parent_query
    from app import crop_cycle_result_store as legacy_store
    from app import crop_cycle_server_custody as legacy_server
    from app import crop_harvest_current_query as current
    from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
    from app.crop_cycle_farm_binding import CycleFarmBinding
    from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
    from app.market_source_store import MarketSourceStore
    from test_crop_cycle_artifact import program, PROFILES, NOTICE
    from test_crop_cycle_farm_binding import SyntheticInputRights
    from test_crop_cycle_input_evidence import authority
    registry = current.registry; scope, dsns, harvest_root = harvest_scope
    farms, _, _ = authoring; jobs = farms.replay.jobs; research = farms.replay.owned_research
    issuer = authority(); rights = SyntheticInputRights(); inputs = tmp_path/'inputs'
    p = program('empty-entry'); anchors = p.pop('output_times')
    receipt = engine.inputs.write_input_packet(inputs, **p, anchors=anchors, outputs=anchors,
        **PROFILES, program_id='owned-harvest-runtime-input')
    for path in inputs.iterdir(): path.chmod(0o400)
    input_proof = issuer.issue(inputs, receipt['root_sha256'])
    crop_root = tmp_path/'calculation-server'; old_root = tmp_path/'legacy-server'
    for path in (crop_root, old_root): path.mkdir(mode=0o700)
    server_key = b'owned-runtime-server-'+b's'*32; db_key = b'owned-runtime-db-'+b'd'*32
    result_key = b'owned-runtime-result-'+b'r'*32; harvest_key = b'owned-runtime-harvest-'+b'h'*32
    class Resolver:
        version = 'owned-harvest-runtime-unused-resolver-v1'
        def __call__(self, *_, **__): pytest.fail('assembly resolved crop inputs/results')
    def make_store(selected_farms):
        binding = CalculationFarmBinding(selected_farms, issuer, input_rights=rights)
        server = storage.server.CalculationServerCustody(binding, crop_root, input_resolver=Resolver(), integrity_key=server_key)
        return storage.CalculationCycleCropResultStore(server, integrity_key=db_key)
    def crop_factory(*, farm_authoring_service): return make_store(farm_authoring_service)
    def make_query(store):
        evidence = CalculationResultEvidenceAuthority(issuer, integrity_key=result_key,
            issuer_id='owned-harvest-runtime', key_id='result-v1')
        return parent_query.CalculationCurrentCycleQuery(store, evidence, evidence_resolver=Resolver())
    def query_factory(*, result_store): return make_query(result_store)
    def legacy_factory(*, farm_authoring_service):
        binding = CycleFarmBinding(farm_authoring_service, **PROFILES, notice_raw=NOTICE, input_rights=rights)
        server = legacy_server.CycleServerCustody(binding, old_root, input_resolver=Resolver(), integrity_key=server_key)
        return legacy_store.CycleCropResultStore(server, integrity_key=db_key)
    def source_factory(*, principal_provider):
        return MarketSourceStore(jobs._dsn, jobs.schema, principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    def make_harvest(query, *, role=None, key=harvest_key):
        store = registry.HarvestRegistry(query, scope, harvest_root,
            dsn=dsns[role or scope.reader], integrity_key=key)
        return current.HarvestCurrentQuery(store)
    def harvest_factory(*, calculation_current_query): return make_harvest(calculation_current_query)
    def counts():
        with jobs.connect() as conn:
            result = {name:conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table(name))).fetchone()['n']
                for name in ('jobs','job_events','crop_cycle_research_results','crop_cycle_verified_research_results')}
        with psycopg.connect(dsns[scope.reader]) as conn:
            result['harvest_rows'] = conn.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(scope.schema,registry.schema.TABLE))).fetchone()[0]
        return result
    def input_state():
        return {p.name:(sha256(p.read_bytes()).hexdigest(),p.stat().st_mode,p.stat().st_ino) for p in inputs.iterdir()}
    descriptor = jobs._content_directory(create=True); os.close(descriptor)
    before = counts(); original_inputs = input_state(); fd_before = len(os.listdir('/proc/self/fd'))
    cert, key, _ = tls_files
    cfg = config(policy=jobs.runtime_identity[0], dsn=jobs._dsn, artifact_root=jobs.artifact_root,
        certificate=cert, private_key=key, host='127.0.0.1', port=0)
    deps = dependencies(research_registry=research.catalog, owned_fixture_registry=research.registry,
        owned_research_contexts=dict(research._contexts), market_scope_resolver=farms.replay.thermal.holds._scope_resolver,
        market_source_factory=source_factory, crop_cycle_result_store_factory=legacy_factory,
        crop_cycle_calculation_result_store_factory=crop_factory, crop_cycle_calculation_current_query_factory=query_factory,
        crop_harvest_current_query_factory=harvest_factory)
    forbid_all_reads_math(monkeypatch)
    def forbidden(*_, **__): pytest.fail('assembly parsed/calculated/published crop output')
    for module,name in ((engine.inputs,'open_input_packet'), (engine.legacy,'prepare_context'),
            (engine,'open_calculation_context'), (engine,'advance_chunk'),
            (storage.artifact,'open_artifact'), (storage.artifact,'_validate_delta'),
            (storage.server.CalculationServerCustody,'advance'), (storage.CalculationCycleCropResultStore,'put'),
            (legacy_server.CycleServerCustody,'advance'), (legacy_store.CycleCropResultStore,'put')):
        monkeypatch.setattr(module,name,forbidden)
    original_app = runtime.create_app; forwarded = []
    def capture_app(*args, **kwargs): forwarded.append(kwargs); return original_app(*args, **kwargs)
    monkeypatch.setattr(runtime, 'create_app', capture_app)
    started = perf_counter(); selected = runtime.ApiRuntime(cfg, deps); seconds = perf_counter()-started
    query = selected.harvest_crop_query; store = selected.harvest_crop_results
    assert forwarded[-1]['crop_harvest_current_query'] is query and query.store is store
    assert store.query is selected.calculation_cycle_crop_query and store.role == scope.reader
    assert store.query.store.jobs is selected.jobs and store.query.store.server.binding.farms is selected.farm_authoring
    assert selected.jobs.principal_provider is current_principal
    assert len({store.integrity_key,store.query.store.integrity_key,store.query.store.server.integrity_key,
        issuer.integrity_key,store.query.authority.integrity_key}) == 5
    with store._connection() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
        endpoint = [conn.info.host,conn.info.port,conn.info.dbname]
        with pytest.raises(errors.InsufficientPrivilege):
            with conn.transaction():conn.execute(sql.SQL('INSERT INTO {} DEFAULT VALUES').format(sql.Identifier(scope.schema,registry.schema.TABLE)))
    rebuilt = runtime.ApiRuntime(cfg, deps)
    assert rebuilt.harvest_crop_query is not query and rebuilt.harvest_crop_query.store.query is rebuilt.calculation_cycle_crop_query
    assert rebuilt.harvest_crop_query.store.query.store.jobs is rebuilt.jobs
    assert 'owned-runtime-' not in repr(selected) and 'harvest_crop' not in repr(selected)
    disabled = runtime.ApiRuntime(cfg, replace(deps, crop_harvest_current_query_factory=None))
    assert disabled.harvest_crop_query is disabled.harvest_crop_results is None
    def changed_query(*, calculation_current_query): return make_harvest(make_query(calculation_current_query.store))
    def publisher(*, calculation_current_query): return make_harvest(calculation_current_query,role=scope.publisher)
    def changed_key(*, calculation_current_query):
        value = make_harvest(calculation_current_query); value.store.integrity_key += b'-changed'; return value
    def changed_policy(*, calculation_current_query, field):
        value = make_harvest(calculation_current_query)
        value.store.policy = replace(scope, **{field:cfg.policy.schema if field=='schema' else 'foreign_database'})
        return value
    cases = [('untyped-query',lambda **_:object()), ('different-parent-query',changed_query),
        ('publisher',publisher), ('changed-key',changed_key),
        ('different-database-policy',lambda **kw:changed_policy(**kw,field='database')),
        ('parent-schema-policy',lambda **kw:changed_policy(**kw,field='schema')),
        ('reused-parent-key',lambda *,calculation_current_query:make_harvest(calculation_current_query,key=db_key))]
    denied = []
    for name,factory in cases:
        with pytest.raises(ValueError, match='^API runtime assembly rejected$'):
            runtime.ApiRuntime(cfg, replace(deps,crop_harvest_current_query_factory=factory))
        denied.append(name); assert len(os.listdir('/proc/self/fd')) == fd_before and counts() == before
    original_connection = registry.HarvestRegistry._connection
    @contextmanager
    def changed_endpoint(self, *args, **kwargs):
        with original_connection(self,*args,**kwargs) as conn:
            yield SimpleNamespace(info=SimpleNamespace(host=conn.info.host,port=conn.info.port+1,dbname=conn.info.dbname))
    with monkeypatch.context() as patch:
        patch.setattr(registry.HarvestRegistry,'_connection',changed_endpoint)
        with pytest.raises(ValueError, match='^API runtime assembly rejected$'):runtime.ApiRuntime(cfg,deps)
    denied.append('owned-endpoint-metadata-fault-after-real-SCRAM')
    with psycopg.connect(login_database['admin']) as conn:
        conn.execute(sql.SQL('GRANT INSERT ON {} TO {}').format(sql.Identifier(scope.schema,registry.schema.TABLE),sql.Identifier(scope.reader)))
    try:
        with pytest.raises(ValueError, match='^API runtime assembly rejected$'):runtime.ApiRuntime(cfg,deps)
        denied.append('actual-extra-reader-grant')
    finally:
        with psycopg.connect(login_database['admin']) as conn:
            conn.execute(sql.SQL('REVOKE INSERT ON {} FROM {}').format(sql.Identifier(scope.schema,registry.schema.TABLE),sql.Identifier(scope.reader)))
    passfile = Path(store._passfile); passfile.chmod(0o644)
    try:
        with pytest.raises(ValueError, match='^API runtime assembly rejected$'):runtime.ApiRuntime(cfg,deps)
        denied.append('actual-unsafe-passfile-mode')
    finally:passfile.chmod(0o600)
    assert input_state() == original_inputs and counts() == before and len(os.listdir('/proc/self/fd')) == fd_before
    assert not any(list(root.iterdir()) for root in (crop_root,old_root,harvest_root))
    assert before['crop_cycle_research_results'] == before['crop_cycle_verified_research_results'] == before['harvest_rows'] == 0
    save_native('harvest-runtime-scram.json', {'scope':'actual_SCRAM_assembly_zero_crop_outputs_no_HTTP_or_protected_fresh_restore',
        'actual_scram':True,'normal_assembly_seconds':seconds,'same_jobs_farm_query_principal':True,
        'same_authenticated_endpoint':endpoint,'reader_only_insert_denied':True,'independent_keys':5,
        'same_process_reconstruction':True,'default_disabled_preserved':True,'denied_cases':denied,
        'counts_before':before,'counts_after':counts(),'input_proof_sha256':sha256(input_proof).hexdigest(),
        'inputs_unchanged':True,'parser_RHS_regeneration_registration_proof_calls_after_preparation':0,
        'FD_before_after':[fd_before,fd_before],'gates':'not_assessed'})
