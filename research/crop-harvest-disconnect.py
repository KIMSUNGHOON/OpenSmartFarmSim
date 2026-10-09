"""Actual pre-body TLS disconnect against an original preserved harvest runtime."""
from contextlib import ExitStack
from hashlib import sha256
import http.client
import importlib.util
import json
import os
from pathlib import Path
import secrets
import ssl
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def run(original_root, manifest, digest, directory, *, expected_status=422):
    assert expected_status in (422, 500)
    directory = Path(directory); directory.mkdir(mode=0o700)
    spec = importlib.util.spec_from_file_location('owned_disconnect_cost', ROOT/'research/crop-harvest-api-cost.py')
    cost = importlib.util.module_from_spec(spec); spec.loader.exec_module(cost)
    saved = cost.original_manifest(original_root, ROOT, manifest, digest, directory)
    storage = cost.load_storage(ROOT, sha256((ROOT/'research/crop-harvest-storage-preservation.py').read_bytes()).hexdigest())
    backup = storage.backup; h = backup.runtime
    from crop_harvest_storage_preservation_smoke import source_inventory
    from test_api_crop_cycle_calculation_tls import fd_inventory
    from app import api_crop_harvest_route as route, crop_harvest_current_query as current
    from app.http_identity import current_principal
    from psycopg import sql
    check = cost.module('owned_disconnect_reconciliation', ROOT/'research/crop-harvest-http-reconciliation.py')
    parent = backup.checked(saved['parent_backup'], saved['parent_backup_sha256'])
    doc = json.loads(h.private_bytes(Path(saved['parent_backup']).parent/'original-runtime.private'))
    roots = [Path(manifest).parent, Path(doc['input']['directory']), Path(doc['server_directory']),
             Path(doc['rights_file']), Path(doc['principal_file'])]
    before = source_inventory(roots); fds = fd_inventory()
    cert, key = cost.certificate(backup, directory)
    tokens = {n: secrets.token_urlsafe(40).encode() for n in ('owner', 'denied', 'foreign')}
    read_calls = []; original_read = route._read_response

    def observed_read(*args, **kwargs):
        read_calls.append(True)
        return original_read(*args, **kwargs)

    def forbidden(*_, **__):
        raise AssertionError('disconnect read attempted calculation, publication or proof')

    class Observation(cost.Observation):
        def __init__(self, app):
            super().__init__(app)
            self.receiving = threading.Event(); self.disconnects = []; self.errors = []

        async def __call__(self, scope, receive, send):
            incomplete = scope['type'] == 'http' and (b'content-length', b'1') in scope['headers']
            async def observed_receive():
                if incomplete: self.receiving.set()
                message = await receive()
                if incomplete:
                    self.disconnects.append({'type': message['type'], 'bytes': len(message.get('body', b'')),
                        'more_body': message.get('more_body')})
                return message
            try:
                return await super().__call__(scope, observed_receive, send)
            except Exception as exc:
                self.errors.append(type(exc).__name__)
                raise

    with ExitStack() as stack:
        stack.enter_context(backup.readonly_guard()); stack.enter_context(storage.read_guard())
        for owner, name in ((h.engine.evidence.InputEvidenceAuthority, 'issue'),
                (storage.query.current.storage.server.CalculationServerCustody, 'advance'),
                (storage.query.current.storage.CalculationCycleCropResultStore, 'put')):
            stack.enter_context(patch.object(owner, name, forbidden))
        stack.enter_context(patch.object(route, '_read_response', observed_read))
        context = stack.enter_context(storage.restored_storage(saved, directory/'database'))
        runtime, original, _, cfg = cost.assemble(storage, saved, manifest, context, directory, tokens, cert, key, 0)
        assert runtime.harvest_crop_query.store.query is runtime.calculation_cycle_crop_query
        assert runtime.calculation_cycle_crop_query.store.jobs is runtime.jobs
        endpoints = []
        for connect in (runtime.jobs.connect, runtime.harvest_crop_query.store._connection):
            with connect() as conn:
                assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
                endpoints.append((conn.info.host, conn.info.port, conn.info.dbname))
        assert endpoints[0] == endpoints[1]

        def counts():
            with runtime.jobs.connect() as conn:
                value = {n: conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                    runtime.jobs._table(n))).fetchone()['n'] for n in (
                        'jobs', 'job_events', 'crop_cycle_verified_research_results', 'thermal_g1_runs')}
            with runtime.harvest_crop_query.store._connection() as conn:
                value['harvest'] = conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                    sql.Identifier(saved['policy']['schema'], storage.registry.schema.TABLE))).fetchone()['n']
            return value

        before_counts = counts(); api = runtime.service.server(); observation = Observation(api.config.app)
        api.config.app = observation
        class Service:
            def server(self): return api
        reconciled = []
        with cost.serving(Service()) as (_, port):
            target = check.target(saved, parent['farm'], 'summary')
            client = http.client.HTTPSConnection('127.0.0.1', port, timeout=5,
                context=ssl.create_default_context(cafile=str(cert)))
            started = time.monotonic()
            try:
                client.putrequest('GET', target)
                client.putheader('Authorization', 'Bearer ' + tokens['owner'].decode())
                client.putheader('Content-Length', '1'); client.putheader('Connection', 'close')
                client.endheaders()
                assert observation.receiving.wait(5)
            finally:
                client.close()
            disconnected = observation.take(0, target)
            assert disconnected['status'] == expected_status and not read_calls
            assert any(v['type'] == 'http.disconnect' for v in observation.disconnects)
            assert all(v['bytes'] == 0 for v in observation.disconnects)
            assert time.monotonic() - started < 10
            assert observation.errors == (['ClientDisconnect'] if expected_status == 500 else [])
            if expected_status == 422:
                error_raw = b'{"error":{"code":"invalid_request","message":"Invalid request"}}'
                assert disconnected['bytes'] == len(error_raw) and disconnected['sha256'] == sha256(error_raw).hexdigest()
            disconnected['client_response_received'] = False
            codes = {'query_version': current.VERSION, 'query_code_sha256': current.CODE_SHA256,
                'query_dependency_sha256': current.DEPENDENCY_SHA256,
                'projection_code_sha256': route.public.CODE_SHA256}

            def probe(label='summary', subject='owner', expected=200):
                target = check.target(saved, parent['farm'], label); index = len(observation.responses)
                response = cost.request(port, cert, target, tokens[subject])
                emitted = observation.take(index, target)
                assert response['status'] == emitted['status'] == expected and emitted['complete']
                assert response['seconds'] < cost.MAX_SECONDS and len(response['raw']) <= cost.MAX_BYTES
                assert emitted['bytes'] == len(response['raw']) and emitted['sha256'] == sha256(response['raw']).hexdigest()
                assert response['headers']['cache-control'] == 'no-store'
                if expected == 200:
                    reconciled.append(check.reconcile(saved, parent['farm'], codes, label, emission=emitted, **response))

            probe()
            if expected_status == 422:
                probe('first'); probe(subject='denied', expected=403); probe(subject='foreign', expected=404)
                rights = runtime.harvest_crop_query.store.query.store.server.binding.input_rights
                original_rights = type(rights).__call__
                def denied(instance, *args):
                    return False if instance is rights else original_rights(instance, *args)
                with patch.object(type(rights), '__call__', denied): probe(expected=422)
                probe()
        assert counts() == before_counts and current_principal() is None
    assert source_inventory(roots) == before and not (directory/'database/data/postmaster.pid').exists()
    deadline = time.monotonic() + 5
    while fd_inventory() != fds and time.monotonic() < deadline: time.sleep(.05)
    assert fd_inventory() == fds
    result = {'scope': 'owned_synthetic_actual_same_DB_TLS_pre_body_disconnect',
        'accepted': expected_status == 422, 'expected_disconnect_status': expected_status,
        'disconnect': disconnected, 'received_disconnect_events': observation.disconnects,
        'query_calls_for_incomplete_request': 0, 'server_errors': observation.errors,
        'server_responses': observation.responses, 'reconciled_normal_responses': reconciled,
        'same_actual_SCRAM_DB': True, 'DB_counts_before_after': [before_counts, before_counts],
        'source_entries': len(before), 'original_sources_preserved': True,
        'FD_before_after': [len(fds), len(fd_inventory())], 'PG_and_HTTPS_stopped': True,
        'RHS_generation_registration_publication_proof_calls': 0, 'shared_controls_changed': False,
        'manifest_sha256': digest, 'actual_crop_Runs': 0, 'G0_G4': 'not_assessed', 'realtime_U3': False}
    backup.write(directory/'disconnect-verified.private.json', backup.canonical(result))
    return result
