"""Explicit two-model configuration and current original result assembly."""
from dataclasses import asdict, replace
from datetime import timedelta
from hashlib import sha256
from itertools import product
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest

from app import crop_greenhouse_ventilation_operator_config as loader
from app import crop_climate_joint_operator_config as joint_loader
from app import calculation_operator_config as calculation
from app import operator_config as original
from test_operator_config import private_config, store, isolated_assembly
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_api_crop_greenhouse_ventilation_replay import database_cleanup
from test_crop_greenhouse_ventilation_execution_runtime import served, SCOPES, TOKEN, NOW
from test_crop_greenhouse_ventilation_execution_query import forbid
from test_deterministic_job_discovery import persisted_digest
from test_crop_greenhouse_ventilation_result_store import (
    login_database, original_login_scope, login_scope, authoring, farm_setup, profiles)
import test_crop_greenhouse_ventilation_result_store as ventilation
import test_crop_climate_joint_result_store as joint

FLAGS = (loader.JOINT_EXECUTION_FLAG, loader.JOINT_PREFIX_FLAG,
         loader.EXECUTION_FLAG, loader.PREFIX_FLAG)


@pytest.fixture
def mixed_config(private_config):
    path, doc = private_config
    doc.update(config_version=loader.MIXED_PREFIX_VERSION, **dict.fromkeys(FLAGS, True))
    doc['policy'].update(crop_cycle_result_storage=True,
        crop_climate_joint_result_storage=True, crop_greenhouse_ventilation_result_storage=True)
    store(path, doc)
    return path, doc


@pytest.mark.parametrize('joint,ventilation', tuple(product(
    [(False, False), (True, False), (True, True)], repeat=2)))
def test_explicit_two_model_flags(mixed_config, monkeypatch, joint, ventilation):
    path, doc = mixed_config
    doc.update(zip(FLAGS, (*joint, *ventilation)))
    store(path, doc); calls = isolated_assembly(monkeypatch)
    assert loader.load_ventilation_api_runtime(path)[0] == 'assembled'
    assert tuple(getattr(calls[0], flag) for flag in FLAGS) == (*joint, *ventilation)


@pytest.mark.parametrize('flag', FLAGS)
@pytest.mark.parametrize('invalid', [None, 0, 1, 'true', [], {}])
def test_two_model_flags_do_not_coerce(mixed_config, monkeypatch, flag, invalid):
    path, doc = mixed_config; doc[flag] = invalid; store(path, doc)
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: pytest.fail('invalid import'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_ventilation_api_runtime(path)


@pytest.mark.parametrize('fault', [*FLAGS, 'extra', 'joint-policy-missing', 'joint-policy-false',
    'ventilation-policy-false', 'cycle-policy-false', 'joint-execution-false', 'ventilation-execution-false'])
def test_two_model_dependencies_reject_before_factory(mixed_config, monkeypatch, fault):
    path, doc = mixed_config
    if fault in FLAGS: del doc[fault]
    elif fault == 'extra': doc['unknown'] = True
    elif fault == 'joint-policy-missing': del doc['policy'][original.JOINT_RESULT_FLAG]
    elif fault.endswith('policy-false'):
        key = {'joint-policy-false': original.JOINT_RESULT_FLAG,
               'ventilation-policy-false': loader.FLAG, 'cycle-policy-false': 'crop_cycle_result_storage'}[fault]
        doc['policy'][key] = False
    else: doc[loader.JOINT_EXECUTION_FLAG if fault.startswith('joint-') else loader.EXECUTION_FLAG] = False
    store(path, doc)
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: pytest.fail('invalid import'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_ventilation_api_runtime(path)


@pytest.mark.parametrize('load', [original.load_api_runtime, calculation.load_calculation_api_runtime,
                                joint_loader.load_joint_api_runtime])
def test_older_loaders_reject_mixed_version(mixed_config, load):
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        load(mixed_config[0])


@pytest.mark.parametrize('version', [loader.VERSION, loader.EXECUTION_VERSION, loader.PREFIX_VERSION])
def test_old_ventilation_versions_reject_new_joint_fields(mixed_config, monkeypatch, version):
    path, doc = mixed_config; doc['config_version'] = version; store(path, doc)
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: pytest.fail('invalid import'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_ventilation_api_runtime(path)


def save(name, value):
    root = os.environ.get('OSSF_JOINT_VENTILATION_RUNTIME_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as stream:
            os.fchmod(stream.fileno(), 0o400)
            json.dump(value, stream, sort_keys=True); stream.flush(); os.fsync(stream.fileno())


@pytest.fixture
def native_pair(authoring, profiles, mixed_config, tls_files, database_cleanup,
                tmp_path, monkeypatch, request):
    from app.crop_climate_joint_current_query import JointCropClimateCurrentQuery
    from app.crop_greenhouse_ventilation_current_query import VentilationCurrentQuery
    from app.crop_cycle_farm_binding import CycleFarmBinding
    from app.crop_cycle_server_custody import CycleServerCustody
    from app.crop_cycle_result_store import CycleCropResultStore
    from app.market_source_store import MarketSourceStore
    from app.http_identity import BearerGrant, BearerRegistry, current_principal, token_digest
    from test_crop_cycle_artifact import PROFILES, NOTICE
    from test_crop_cycle_farm_binding import SyntheticInputRights
    seeds = {}
    for name, reference, query_type in [('joint', joint, JointCropClimateCurrentQuery),
                                      ('ventilation', ventilation, VentilationCurrentQuery)]:
        directory = tmp_path/name; directory.mkdir(mode=0o700)
        setup = reference.producer.setup.__wrapped__(authoring, directory, profiles, request, monkeypatch)
        seed, raw, value, done = reference.ready(setup)
        value[4]['scopes'].update(SCOPES)
        record = seed.put('tenant-1', raw); farm = json.loads(raw)['farm']
        expected = {view:query_type(seed).read('tenant-1', record['result_id'], farm, view=view)
                    for view in ('summary', 'samples', 'events')}
        seeds[name] = SimpleNamespace(store=seed, raw=raw, value=value, record=record,
            expected=expected, farm=farm, query_type=query_type, status=json.loads(done)['status'])
    jobs = seeds['joint'].store.jobs
    assert seeds['ventilation'].store.jobs is jobs
    farms = seeds['joint'].store.server.binding.farms; research = farms.replay.owned_research
    legacy_root = tmp_path/'legacy'; legacy_root.mkdir(mode=0o700)
    def unused(*args): pytest.fail('mixed runtime resolved unrelated legacy inputs')
    unused.version = 'owned-mixed-runtime-unused-v1'
    def legacy_factory(*, farm_authoring_service):
        binding = CycleFarmBinding(farm_authoring_service, **PROFILES, notice_raw=NOTICE,
                                   input_rights=SyntheticInputRights())
        server = CycleServerCustody(binding, legacy_root, input_resolver=unused,
                                   integrity_key=b'owned-mixed-unused-server-'+b's'*32)
        return CycleCropResultStore(server, integrity_key=b'owned-mixed-unused-registry-'+b'd'*32)
    def result_factory(seed):
        def build(*, farm_authoring_service):
            original = seed.store.server
            binding = type(original.binding)(farm_authoring_service, original.binding.input_authority,
                                             input_rights=seed.value[-1])
            server = type(original)(binding, original.directory, input_resolver=original.input_resolver,
                                    integrity_key=original.integrity_key)
            return type(seed.store)(server, integrity_key=seed.store.integrity_key)
        return build
    def sources(*, principal_provider):
        return MarketSourceStore(jobs._dsn, jobs.schema, principal_provider=principal_provider,
                                 runtime_identity=jobs.runtime_identity)
    cert, key, _ = tls_files
    descriptor = jobs._content_directory(create=True); os.close(descriptor)
    cfg = config(policy=jobs.runtime_identity[0], dsn=jobs._dsn, artifact_root=jobs.artifact_root,
        certificate=cert, private_key=key, port=0, **dict.fromkeys(FLAGS, True))
    grant = BearerGrant(token_digest(TOKEN), 'tenant-1', SCOPES,
                        NOW-timedelta(seconds=1), NOW+timedelta(hours=1))
    clock = {'now':NOW}
    deps = dependencies(research_registry=research.catalog, owned_fixture_registry=research.registry,
        owned_research_contexts=dict(research._contexts), market_scope_resolver=farms.replay.thermal.holds._scope_resolver,
        market_source_factory=sources, bearer_registry=BearerRegistry((grant,), clock=lambda:clock['now']),
        crop_cycle_result_store_factory=legacy_factory,
        crop_climate_joint_result_store_factory=result_factory(seeds['joint']),
        crop_climate_joint_current_query_factory=lambda *, result_store: JointCropClimateCurrentQuery(result_store),
        crop_greenhouse_ventilation_result_store_factory=result_factory(seeds['ventilation']),
        crop_greenhouse_ventilation_current_query_factory=lambda *, result_store: VentilationCurrentQuery(result_store))
    path, doc = mixed_config
    doc.update(policy=asdict(cfg.policy), artifact_root=str(cfg.artifact_root), certificate=str(cert), private_key=str(key), port=0)
    for field, raw in [('dsn_file', cfg.dsn.encode()), ('thermal_gate_key_file', cfg.thermal_gate_key),
                       ('market_hold_key_file', cfg.market_hold_key)]: Path(doc[field]).write_bytes(raw)
    store(path, doc)
    options = {'deps':deps}
    def factory(*, config):
        assert config == cfg
        return options['deps']
    monkeypatch.setitem(sys.modules, 'trusted_operator', SimpleNamespace(dependencies=factory))
    files = {p:sha256(p.read_bytes()).hexdigest() for p in
        [path, cert, key, *(Path(doc[f]) for f in ('dsn_file', 'thermal_gate_key_file', 'market_hold_key_file'))]}
    for seed in seeds.values():
        files.update({p:sha256(p.read_bytes()).hexdigest() for root in [seed.value[2][0], seed.store.server.directory]
                      for p in root.rglob('*') if p.is_file()})
    yield SimpleNamespace(path=path, config=cfg, deps=deps, seeds=seeds, jobs=jobs, options=options, clock=clock)
    assert {p:sha256(p.read_bytes()).hexdigest() for p in files} == files
    assert not list(legacy_root.iterdir()) and current_principal() is None


def deny_joint_writes(patch, calls):
    calls['joint.put'] = 0
    def denied(*args, **kwargs):
        calls['joint.put'] += 1
        pytest.fail('mixed read registered a joint result')
    patch.setattr(joint.store.JointCropClimateResultStore, 'put', denied)
    return joint.producer.reference.forbid(patch)


@ventilation.pytestmark
@pytest.mark.parametrize('native_pair', [None, 'hold'], indirect=True)
def test_actual_two_models_TLS_original_results_execution_and_prefix(native_pair, monkeypatch):
    c = native_pair; runtime = loader.load_ventilation_api_runtime(c.path)
    for name in c.seeds:
        results = getattr(runtime, name+'_crop_results'); execution = getattr(runtime, name+'_execution_query')
        assert results.jobs is runtime.jobs and results.server.binding.farms is runtime.farm_authoring
        assert execution.results is results and execution.checkpoints is getattr(runtime, name+'_execution_checkpoints')
        assert getattr(runtime, name+'_prefix_query').query is execution
        assert len({results.integrity_key, results.server.integrity_key,
                    results.server.binding.input_authority.integrity_key}) == 3
    with runtime.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    with served(runtime, c.config.certificate) as (send, replies):
        jobs = {}
        for name, seed in c.seeds.items():
            model = 'crop-climate-joint' if name == 'joint' else 'crop-greenhouse-ventilation'
            status, raw = send('POST', '/v1/'+model+'-executions', seed.raw)
            assert status == 202
            jobs[name] = (json.loads(raw)['job_id'], model)
        assert len({job_id for job_id, _ in jobs.values()}) == 2
        before = persisted_digest(c.jobs)
        with monkeypatch.context() as patch:
            calls = forbid(patch); old_calls = deny_joint_writes(patch, calls)
            for name, seed in c.seeds.items():
                job_id, model = jobs[name]
                path = '/v1/'+model+'-research-results/'+seed.record['result_id']+'?'+urlencode(seed.farm)
                for view, expected in seed.expected.items():
                    status, raw = send('GET', path+('' if view == 'summary' else '&view='+view))
                    assert status == 200 and raw == expected
                path = '/v1/jobs/'+job_id+'/'+model+'-execution'
                status, raw = send('GET', path)
                assert status == 200 and json.loads(raw)['job']['state'] == 'queued'
                status, raw = send('GET', path+'/prefix')
                assert status == 200 and json.loads(raw)['prefix_status'] == 'none'
                seed.value[-1].allowed = False
                try:
                    status, _ = send('GET', '/v1/'+model+'-research-results/'+seed.record['result_id']+'?'+urlencode(seed.farm))
                    assert status == 422
                finally: seed.value[-1].allowed = True
                status, raw = send('GET', '/v1/'+model+'-research-results/'+seed.record['result_id']+'?'+urlencode(seed.farm))
                assert status == 200 and raw == seed.expected['summary']
                import importlib
                public = importlib.import_module(seed.query_type.__module__).public
                encode = public._public_bytes
                for phase in ('rights', 'account'):
                    seen = []
                    def serialized(value):
                        raw = encode(value); seen.append(1)
                        if len(seen) == 2:
                            if phase == 'rights': seed.value[-1].allowed = False
                            else: c.clock['now'] = NOW+timedelta(hours=1)
                        return raw
                    try:
                        with monkeypatch.context() as late:
                            late.setattr(public, '_public_bytes', serialized)
                            status, _ = send('GET', '/v1/'+model+'-research-results/'+seed.record['result_id']+'?'+urlencode(seed.farm))
                        assert len(seen) == 2 and status == (422 if phase == 'rights' else 401)
                    finally: seed.value[-1].allowed = True; c.clock['now'] = NOW
            assert not any(calls.values()) and not any(old_calls.values())
        assert persisted_digest(c.jobs) == before
        for job_id, model in jobs.values():
            status, raw = send('POST', '/v1/jobs/'+job_id+'/'+model+'-execution/cancel')
            value = json.loads(raw)
            assert status == 200 and value['cancel_accepted'] is True and value['job']['state'] == 'canceled'
    save('native-'+c.seeds['joint'].status, {'actual_SCRAM':True, 'verified_TLS':True,
        'same_jobs_farms_principal':True, 'two_models':True, 'original_wire_UTC':True,
        'status':c.seeds['joint'].status, 'per_model_three_distinct_keys':True,
        'queued_prefix_none_despite_private_completed_artifact':True,
        'current_rights_rejected_restored':True, 'late_rights_and_account_both_models':True,
        'queued_cancel_both_models':True,
        'read_calls':calls, 'joint_read_calls':old_calls, 'replies':replies,
        'automatic_worker_started':False, 'G0_G4':'not_assessed'})


@ventilation.pytestmark
def test_actual_rejected_mixed_assembly_and_runtime_grants(native_pair, login_scope, monkeypatch):
    from app.api_runtime import ApiRuntime
    from psycopg import sql
    from test_api_crop_greenhouse_ventilation_route import fd_inventory
    c = native_pair; initial = fd_inventory(); rejected = []
    with monkeypatch.context() as patch:
        calls = forbid(patch); old_calls = deny_joint_writes(patch, calls)
        for name in c.seeds:
            prefix = 'crop_climate_joint' if name == 'joint' else 'crop_greenhouse_ventilation'
            other = c.seeds['ventilation' if name == 'joint' else 'joint']
            for suffix, invalid in [('result_store_factory', None), ('current_query_factory', None),
                    ('result_store_factory', lambda **_: object()),
                    ('result_store_factory', lambda **_: other.store),
                    ('current_query_factory', lambda **_: object()),
                    ('current_query_factory', lambda **_: other.query_type(other.store))]:
                c.options['deps'] = replace(c.deps, **{prefix+'_'+suffix:invalid})
                with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
                    loader.load_ventilation_api_runtime(c.path)
                assert fd_inventory() == initial
                rejected.append(name+'-'+suffix)
            seed = c.seeds[name]
            for fault in ('server-input-key', 'registry-input-key', 'registry-server-key'):
                def reused_key_factory(*, farm_authoring_service):
                    original_server = seed.store.server
                    binding = type(original_server.binding)(farm_authoring_service,
                        original_server.binding.input_authority, input_rights=seed.value[-1])
                    input_key = binding.input_authority.integrity_key
                    server = type(original_server)(binding, original_server.directory,
                        input_resolver=original_server.input_resolver,
                        integrity_key=input_key if fault == 'server-input-key' else original_server.integrity_key)
                    return type(seed.store)(server, integrity_key=input_key if fault == 'registry-input-key'
                        else server.integrity_key if fault == 'registry-server-key' else seed.store.integrity_key)
                c.options['deps'] = replace(c.deps, **{prefix+'_result_store_factory':reused_key_factory})
                with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
                    loader.load_ventilation_api_runtime(c.path)
                assert fd_inventory() == initial
                rejected.append(name+'-'+fault)
            c.options['deps'] = c.deps
            import importlib
            with monkeypatch.context() as pin:
                pin.setattr(importlib.import_module(seed.query_type.__module__), 'CODE_SHA256', '0'*64)
                with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
                    loader.load_ventilation_api_runtime(c.path)
                assert fd_inventory() == initial
                rejected.append(name+'-model-code-pin')
        c.options['deps'] = c.deps
        base, policy, _ = login_scope
        for name, reference in [('joint', joint), ('ventilation', ventilation)]:
            def grant(verb):
                with base.connect() as conn:
                    conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
                    conn.execute(sql.SQL(verb+' SELECT ON {} '+('TO' if verb == 'GRANT' else 'FROM')+' {}').format(
                        sql.Identifier(policy.schema, reference.schema.TABLE), sql.Identifier(policy.roles['authority'])))
            grant('REVOKE')
            try:
                with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
                    loader.load_ventilation_api_runtime(c.path)
                rejected.append(name+'-revoked-SELECT')
            finally: grant('GRANT')
        runtime = loader.load_ventilation_api_runtime(c.path)
        disabled = ApiRuntime(replace(c.config, **dict.fromkeys(FLAGS, False)), c.deps)
        for name in c.seeds:
            assert getattr(runtime, name+'_prefix_query') is not None
            assert getattr(disabled, name+'_crop_query') is not None
            assert getattr(disabled, name+'_execution_query') is None
            assert getattr(disabled, name+'_prefix_query') is None
        assert not any(calls.values()) and not any(old_calls.values()) and fd_inventory() == initial
    save('rejected-assembly', {'rejected':rejected, 'both_rebuilt_after_restore':True,
        'disabled_execution_prefix_none':True, 'read_calls':calls, 'joint_read_calls':old_calls,
        'FD':[len(initial),len(fd_inventory())], 'G0_G4':'not_assessed'})
