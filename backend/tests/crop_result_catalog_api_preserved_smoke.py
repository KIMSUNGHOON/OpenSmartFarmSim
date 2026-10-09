"""Manual restored SCRAM/HTTPS catalogue acceptance; owned synthetic metadata only."""
from contextlib import ExitStack
from collections import Counter
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import http.client
import importlib.util
import json
import os
from pathlib import Path
import secrets
import ssl
import stat
import threading
from time import monotonic, sleep
from unittest.mock import patch
from urllib.parse import urlencode

import psycopg
from psycopg import sql

from app.api_runtime import ApiRuntime, ApiRuntimeConfig
from app import api_crop_result_catalog as public
from app import crop_result_catalog as catalog
from app import crop_cycle_result_store as legacy
from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
from app.crop_cycle_farm_binding import CycleFarmBinding
from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
from app.crop_result_store import READ_SCOPES
from app.http_identity import BearerGrant, BearerRegistry, token_digest
from app.market_source_store import MarketSourceStore
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.research_registry import ResearchRegistry
from app.runtime_roles import RuntimeLoginPolicy
from crop_result_catalog_preserved_smoke import inventory, replace_control
from test_api_runtime import dependencies
from test_api_serve import tls_files
from test_crop_cycle_artifact import PROFILES, NOTICE


def descriptors():
    found=[]
    for path in Path('/proc/self/fd').iterdir():
        try:
            info=os.fstat(int(path.name))
            found.append((info.st_dev,info.st_ino,stat.S_IFMT(info.st_mode),os.readlink(path)))
        except (OSError,ValueError):pass
    return Counter(found)


def test_restored_catalogue_actual_https_original_metadata_and_many_growth_rows(request):
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location('catalogue_api_saved_storage',
        root/'research/crop-harvest-storage-preservation.py')
    h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
    path = Path(os.environ['OSSF_CROP_CATALOG_STORAGE'])
    digest = os.environ['OSSF_CROP_CATALOG_STORAGE_SHA256']
    stage = Path(os.environ['OSSF_CROP_CATALOG_STAGE']); stage.mkdir(mode=0o700, exist_ok=True)
    value = h.checked(path, digest)
    parent = h.backup.checked(value['parent_backup'], value['parent_backup_sha256'])
    source = Path(value['parent_backup']).parent
    original_config = json.loads(h.runtime.private_bytes(source/'original-runtime.private'))
    roots = [path.parent, source, Path(original_config['input']['directory']),
             Path(original_config['server_directory']), Path(value['registry_directory'])]
    seed = None
    if os.environ.get('OSSF_CROP_CATALOG_PREPARED'):
        seed_path = Path(os.environ['OSSF_CROP_CATALOG_PREPARED'])
        raw = h.runtime.private_bytes(seed_path)
        assert sha256(raw).hexdigest() == os.environ['OSSF_CROP_CATALOG_PREPARED_SHA256']
        seed = json.loads(raw); assert seed['scope'] == 'owned_native_v1_prepared_DB_only'
        dump = seed_path.parent/'database.private.dump'
        assert dump.stat().st_size == seed['raw_dump_bytes'] < 512*1024**2
        assert sha256(h.runtime.private_bytes(dump)).hexdigest() == seed['dump_sha256']
        seed_preparation = Path(seed['normal_preparation_file'])
        raw = h.runtime.private_bytes(seed_preparation)
        assert sha256(raw).hexdigest() == seed['normal_preparation_sha256']
        seed_items = json.loads(raw)['prepared_growth_results']; assert len(seed_items) == 20
        roots.extend((seed_path.parent, seed_preparation, seed_preparation.parent/'prepared-custody'))
    original = inventory(roots); fd_before = len(os.listdir('/proc/self/fd')); descriptors_before=descriptors()
    observations = []; preparation = []; farm = parent['farm']; tenant = 'tenant-1'
    def save(name, document): h.backup.write(stage/name, h.canonical(document))
    save('source-inventory.private.json', {'entries':original,'FD_count':fd_before,
        'descriptors':[{'identity':key,'count':count} for key,count in descriptors_before.items()]})
    with h.restored_storage(value, stage/'restore') as context:
        if seed is not None:
            h.backup.command(Path(parent['binary'])/'pg_restore', ['--no-password', '--exit-on-error',
                '--clean', '--if-exists', '--dbname', context['admin'], dump], stage, 'prepared-DB-restore')
        doc = json.loads(h.runtime.private_bytes(context['config']))
        for field in ('principal', 'rights'):
            target = stage/(field+'.private')
            h.backup.write(target, h.runtime.private_bytes(doc[field+'_file']))
            doc[field+'_file'] = str(target)
        for name in ('job-artifacts', 'unused-legacy', 'prepared-custody'):
            (stage/name).mkdir(mode=0o700)
        doc['artifact_root'] = str(stage/'job-artifacts')
        config_path = stage/'runtime.private.json'; raw = h.canonical(doc)
        h.backup.write(config_path, raw)
        context = {**context, 'config': config_path, 'config_sha256': sha256(raw).hexdigest()}
        saved = h.reader(path, digest, context); original_query = saved.store.query
        original_row = original_query.store._find(tenant, result_id=parent['original_record']['result_id'])
        assert original_row['payload_sha256'] == parent['original_record']['payload_sha256']
        # Normal producers write exclusively into this clone and a new owned custody directory.
        storage = catalog.calculation.storage
        prepared_store = original_query.store
        if seed is not None:
            preparation.extend(seed_items)
            assert len(seed['records']) == 21
            assert {entry['result_id'] for entry in seed['records']} == {
                original_row['result_id'], *(entry['result_id'] for entry in preparation)}
            for entry in seed['records']:
                row = prepared_store._find(tenant, result_id=entry['result_id'])
                packet = prepared_store._row(row, tenant, farm)
                assert row['payload_sha256'] == entry['payload_sha256']
                assert row['recorded_at'].isoformat() == entry['recorded_at']
                assert packet['artifact']['status'] == 'completed'
        else:
            server, request_raw = h.runtime.load_runtime(config_path, context['config_sha256'])
            prepared_server = storage.server.CalculationServerCustody(server.binding, stage/'prepared-custody',
                input_resolver=server.input_resolver, integrity_key=server.integrity_key)
            prepared_store = storage.CalculationCycleCropResultStore(prepared_server,
                integrity_key=h.runtime.private_bytes(source/'DB-key.private'))
            for number in range(20):
                body = json.loads(request_raw); body['study_id'] = 'owned-catalogue-api-'+str(number)
                body['revision'] = 'r1'; raw = h.canonical(body); started = monotonic()
                progress = json.loads(prepared_server.advance(tenant, raw,
                    budget={'max_steps': 10000, 'max_transitions': 4096}))
                record = prepared_store.put(tenant, raw)
                assert progress['status'] == 'completed' and progress['steps'] == 120
                preparation.append({'result_id': record['result_id'], 'steps': progress['steps'],
                                    'seconds': monotonic()-started})
        save('preparation.private.json', {'scope': 'owned_normal_synthetic_producers_only',
            'prepared_growth_results': preparation, 'original_growth_row_unchanged':
            prepared_store._find(tenant, result_id=original_row['result_id']) == original_row,
            'reused_original_preparation_without_recalculation': seed is not None,
            'selection_or_result_evidence_issued_for_prepared_rows': False})
        authority = original_query.store.server.binding.input_authority
        def crop_factory(*, farm_authoring_service):
            binding = CalculationFarmBinding(farm_authoring_service, authority,
                input_rights=h.runtime.Rights(doc['rights_file']))
            selected = storage.server.CalculationServerCustody(binding, Path(doc['server_directory']),
                input_resolver=h.runtime.Resolver(doc['input'], doc['resolver_version']),
                integrity_key=h.runtime.private_bytes(doc['keys']['server']))
            return storage.CalculationCycleCropResultStore(selected,
                integrity_key=h.runtime.private_bytes(source/'DB-key.private'))
        def query_factory(*, result_store):
            issuer = CalculationResultEvidenceAuthority(authority,
                integrity_key=h.runtime.private_bytes(source/'result-key.private'),
                issuer_id='owned-parent-backup-result', key_id='result-v1')
            return catalog.calculation.CalculationCurrentCycleQuery(result_store, issuer,
                evidence_resolver=original_query.evidence_resolver)
        class Unused:
            version = 'owned-catalogue-api-unused-legacy-v1'
            def __call__(self, *args, **kwargs): raise AssertionError('catalogue used legacy values')
        def legacy_factory(*, farm_authoring_service):
            binding = CycleFarmBinding(farm_authoring_service, **PROFILES, notice_raw=NOTICE,
                input_rights=h.runtime.Rights(doc['rights_file']))
            selected = legacy.server.CycleServerCustody(binding, stage/'unused-legacy',
                input_resolver=Unused(), integrity_key=h.runtime.private_bytes(doc['keys']['server']))
            return legacy.CycleCropResultStore(selected, integrity_key=h.runtime.private_bytes(source/'DB-key.private'))
        def harvest_factory(*, calculation_current_query):
            return h.query.HarvestCurrentQuery(h.registry.HarvestRegistry(calculation_current_query,
                saved.store.policy, Path(value['registry_directory']), dsn=saved.store._dsn,
                integrity_key=h.runtime.private_bytes(path.parent/'harvest-key.private')))
        cert, key, _ = request.getfixturevalue('tls_files')
        cfg = ApiRuntimeConfig(policy=RuntimeLoginPolicy(**doc['policy']),
            dsn=h.runtime.private_bytes(doc['dsn_file']).decode(), artifact_root=stage/'job-artifacts',
            certificate=cert, private_key=key, port=0,
            thermal_gate_key=h.runtime.private_bytes(doc['keys']['thermal']),
            market_hold_key=h.runtime.private_bytes(doc['keys']['market']))
        def sources(*, principal_provider):
            return MarketSourceStore(cfg.dsn, cfg.policy.schema, principal_provider=principal_provider,
                runtime_identity=(cfg.policy, 'authority'))
        registry = ResearchRegistry(h.runtime.private_bytes(doc['registry_file']), doc['registry_sha256'])
        now = datetime.now(timezone.utc)
        tokens = {name: secrets.token_urlsafe(32).encode() for name in ('owner', 'foreign', 'denied')}
        grants = tuple(BearerGrant(token_digest(tokens[name]), who, frozenset(scopes),
            now-timedelta(seconds=1), now+timedelta(minutes=15)) for name, who, scopes in
            (('owner', tenant, READ_SCOPES), ('foreign', 'foreign', READ_SCOPES),
             ('denied', tenant, READ_SCOPES[:-1])))
        deps = dependencies(research_registry=registry, bearer_registry=BearerRegistry(grants),
            owned_fixture_registry=OwnedFixtureRegistry(Path(doc['owned_fixture_root'])),
            owned_research_contexts={next(iter(registry._scopes)): doc['owned_context_id']},
            market_scope_resolver=lambda *_: json.loads(h.runtime.private_bytes(doc['market_scope_file'])),
            market_source_factory=sources, crop_cycle_result_store_factory=legacy_factory,
            crop_cycle_calculation_result_store_factory=crop_factory,
            crop_cycle_calculation_current_query_factory=query_factory,
            crop_harvest_current_query_factory=harvest_factory)
        runtime = ApiRuntime(cfg, deps)
        def forbidden(*args, **kwargs): raise AssertionError('metadata read calculated/read/published crop values')
        with ExitStack() as guard:
            guard.enter_context(h.backup.readonly_guard()); guard.enter_context(h.read_guard())
            for target, name in ((catalog.calculation.CalculationCurrentCycleQuery, 'open'),
                    (catalog.harvest.HarvestCurrentQuery, 'open'),
                    (catalog.calculation.results, 'open_calculation_result_read_context')):
                guard.enter_context(patch.object(target, name, forbidden))
            https = runtime.service.server(); thread = threading.Thread(target=https.run, daemon=True)
            thread.start()
            try:
                deadline = monotonic()+15
                while not https.started:
                    assert thread.is_alive() and monotonic() < deadline; sleep(.02)
                port = https.servers[0].sockets[0].getsockname()[1]
                trust = ssl.create_default_context(cafile=str(cert))
                def call(kind=catalog.KINDS[0], *, bearer='owner', cursor=None, **filters):
                    query = {'kind': kind, **farm, **filters}
                    if cursor is not None:
                        query.update(before_recorded_at=cursor['recorded_at'], before_result_id=cursor['result_id'])
                    connection = http.client.HTTPSConnection('127.0.0.1', port, context=trust, timeout=30)
                    started = monotonic()
                    try:
                        connection.request('GET', public.PATH+'?'+urlencode(query), headers={} if bearer is None
                            else {'Authorization': 'Bearer '+tokens[bearer].decode()})
                        response = connection.getresponse(); raw = response.read(); elapsed = monotonic()-started
                        assert elapsed < 30 and len(raw) <= public.MAX_RESPONSE_BYTES
                        assert response.getheader('cache-control') == 'no-store'
                        if response.status == 200:
                            assert response.getheader('x-ossf-crop-catalog-code-sha256') == catalog.CODE_SHA256
                            assert response.getheader('x-ossf-crop-catalog-projection-sha256') == public.CODE_SHA256
                        observations.append({'kind': kind, 'requested_limit': filters.get('limit', 10),
                            'status': response.status, 'seconds': elapsed, 'bytes': len(raw),
                            'body_sha256': sha256(raw).hexdigest(), 'request_query': query})
                        assert not any(token in raw for token in tokens.values())
                        h.backup.write(stage/('http-body-'+str(len(observations))+'.private.json'), raw)
                        return response.status, json.loads(raw)
                    except Exception as exc:
                        observations.append({'kind': kind, 'requested_limit': filters.get('limit', 10),
                            'exception_type': type(exc).__name__, 'seconds': monotonic()-started})
                        raise
                    finally:
                        connection.close()
                        save('http-observations-'+str(len(observations))+'.private.json', {'observations': observations})
                assert call(bearer=None)[0] == 401 and call(bearer='denied')[0] == 403
                assert call(bearer='foreign')[0] == 422
                for changes in ({'crop_id': 'absent'}, {'registration_sha256': '0'*64}):
                    assert call(**changes)[0] == 422
                status, growth = call(); assert status == 200 and len(growth['items']) == 10
                status, first = call(limit=20); assert status == 200 and len(first['items']) == 20
                status, last = call(limit=20, cursor=first['next_cursor'])
                assert status == 200 and len(last['items']) == 1 and last['next_cursor'] is None
                all_items = first['items']+last['items']
                expected_ids = {original_row['result_id'], *(item['result_id'] for item in preparation)}
                assert len({item['result_id'] for item in all_items}) == 21
                assert {item['result_id'] for item in all_items} == expected_ids
                item = next(item for item in all_items if item['result_id'] == original_row['result_id'])
                assert item['recorded_at'] == catalog._time(original_row['recorded_at'])
                assert item['sample_count'] == 3 and item['event_count'] == 3
                status, harvest = call(catalog.KINDS[1], limit=20)
                assert status == 200 and len(harvest['items']) == 1 and harvest['next_cursor'] is None
                item = harvest['items'][0]
                assert item['result_id'] == value['original_record']['result_id'] and item['row_count'] == 5
                assert item['recorded_at'] == catalog._time(datetime.fromisoformat(value['original_record']['recorded_at']))
                assert item['parent_result_id'] == original_row['result_id']
                control = Path(doc['rights_file']); raw = h.runtime.private_bytes(control)
                def withdraw(*args, **kwargs):
                    result = encode(*args, **kwargs)
                    replace_control(control, h.canonical({**json.loads(raw), 'allowed': False}))
                    return result
                encode = public._public_bytes
                try:
                    with patch.object(public, '_public_bytes', withdraw): assert call(limit=1)[0] == 422
                    assert call(catalog.KINDS[1])[0] == 422
                finally: replace_control(control, raw)
                # Equal timestamps are an explicit owner mutation of new synthetic fixture rows only.
                table = sql.Identifier(cfg.policy.schema, storage.schema.TABLE)
                tied_at = datetime.now(timezone.utc)
                with psycopg.connect(context['admin']) as conn:
                    conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(table))
                    conn.execute(sql.SQL('UPDATE {} SET recorded_at=%s WHERE result_id=ANY(%s)').format(table),
                        (tied_at, [entry['result_id'] for entry in preparation]))
                    conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER USER').format(table))
                status, first = call(limit=10); assert status == 200
                status, second = call(limit=10, cursor=first['next_cursor']); assert status == 200
                status, last = call(limit=10, cursor=second['next_cursor']); assert status == 200
                assert [x['result_id'] for x in first['items']+second['items']] == sorted(
                    [x['result_id'] for x in preparation], reverse=True)
                assert len(last['items']) == 1 and last['items'][0]['result_id'] == original_row['result_id']
                assert prepared_store._find(tenant, result_id=original_row['result_id']) == original_row
            finally:
                https.should_exit = True; thread.join(timeout=120)
                assert not thread.is_alive()
    assert not (stage/'restore/data/postmaster.pid').exists()
    descriptors_after=descriptors()
    assert inventory(roots) == original and not (descriptors_after-descriptors_before)
    save('accepted.private.json', {'status': 'catalogue_api_local_only',
        'http_observations': observations, 'normal_prepared_growth_results': len(preparation),
        'original_growth_and_harvest_preserved': True, 'maximum_growth_page_items': 20,
        'harvest_actual_items': 1, 'tie_fixture_owner_mutated_new_rows_only': True,
        'read_phase_value_read_RHS_proof_publication_calls': 0, 'source_entries_unchanged': len(original),
        'FD_before_after': [fd_before, len(os.listdir('/proc/self/fd'))], 'restored_postmaster_absent': True,
        'new_file_descriptor_identities':0,
        'UI_live_progress_and_G0_G4': 'not_assessed', 'actual_crop_Runs': 0})
