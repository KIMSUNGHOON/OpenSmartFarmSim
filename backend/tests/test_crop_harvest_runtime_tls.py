"""Actual registered harvest HTTP bodies through the protected standard runtime."""
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import http.client
import json
import os
from pathlib import Path
import ssl
import subprocess
import sys
import threading
from time import monotonic, sleep
from types import SimpleNamespace
from urllib.parse import urlencode

import psycopg
from psycopg import sql
import pytest

from app import calculation_operator_config as loader
from app import crop_harvest_current_query as query
from app import crop_harvest_runtime_factory as reader_config
from app import api_crop_harvest_replay as public
from app.crop_cycle_input_evidence import InputEvidenceAuthority
from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
from app.http_identity import current_principal
import crop_harvest_tls_fixture as owned
from test_api_runtime import config
from test_api_serve import tls_files
from test_api_crop_cycle_calculation_tls import custody_fds, fd_inventory
from test_crop_harvest_runtime_factory import private_write, json_raw
from test_crop_harvest import (mass_profile, allocation_profile, server_setup, bound_setup,
    login_scope, original_login_scope, authoring, farm_setup, login_database, save_native)
from test_crop_harvest_registry import harvest_scope
from test_crop_harvest_current_query import (runtime_module, replace_control,
    forbid_all_reads_math, RESULT_KEY, HARVEST_KEY)
from test_crop_cycle_calculation_server_custody_farms import BUDGET
from test_crop_cycle_calculation_result_store_farms import DB_KEY
from test_crop_cycle_calculation_runtime import audit_database

registry = query.registry


def test_owned_dependency_import_opens_no_DB_or_network():
    code = '''import json,os,psycopg,socket
calls=[]
def denied(*a,**k):calls.append(True);raise AssertionError('connection during import')
psycopg.connect=denied;socket.create_connection=denied
before=len(os.listdir('/proc/self/fd'))
import crop_harvest_tls_fixture
assert not calls and before==len(os.listdir('/proc/self/fd'))
print(json.dumps({'connection_calls':0,'FD_before_after':[before,before]}))
'''
    child = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
    assert child.returncode == 0 and child.stderr == ''
    save_native('harvest-tls-import.json', {'original_child_exit_code': child.returncode, **json.loads(child.stdout)})


@pytest.fixture
def http_case(server_setup, bound_setup, harvest_scope, tmp_path, request, monkeypatch):
    original, request_raw, _, _, expected = server_setup
    runtime = runtime_module(); operator = tmp_path / 'operator'; operator.mkdir(mode=0o700)
    protected_runtime = tmp_path / 'registered-runtime'; created = []
    def write(name, raw):
        path = private_write(operator / name, raw); created.append(path); return path
    try:
        runtime_path, runtime_sha = runtime.export_runtime(original, request_raw, protected_runtime)
        context = bound_setup[2]
        assert not context.reader.closed and custody_fds((context._directory,)) == 1
        context.close()
        assert context.reader.closed and not context._cache and custody_fds((context._directory,)) == 0
        save_native('harvest-tls-fixture-reader-close.json', {'unused_fixture_input_reader_FD_before_after': [1, 0],
            'context_closed_after_export_before_HTTP': True, 'input_or_calculation_contract_changed': False})
        value = json.loads(runtime.private_bytes(runtime_path)); rights_path = value['rights_file']
        rights = {'research_calculation': True, 'research_display': True}; replace_control(rights_path, rights)
        server, request_raw = runtime.load_runtime(runtime_path, runtime_sha)
        started = monotonic(); progress = json.loads(server.advance('tenant-1', request_raw, budget=BUDGET))
        assert progress['status'] == 'completed' and progress['steps'] == 120
        parent_store = query.current.storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY)
        parent = parent_store.put('tenant-1', request_raw); packet = json.loads(parent['payload_raw'])
        farm = json.loads(request_raw)['farm']; input_directory = Path(value['input']['directory'])
        for path in input_directory.iterdir(): path.chmod(0o400)
        issuer = CalculationResultEvidenceAuthority(
            server.binding.input_authority, integrity_key=RESULT_KEY, issuer_id='owned-harvest-read', key_id='result-v1')
        result_directory = server.directory / query.current.server._intent_id('tenant-1', json.loads(request_raw)) / 'artifact'
        result_raw = issuer.issue(result_directory, progress['artifact_sha256'], input_directory,
            packet['input_root_sha256'], runtime.private_bytes(value['input']['evidence_file']))
        result_path = write('result-evidence.private', result_raw)
        current = query.current.CalculationCurrentCycleQuery(parent_store, issuer,
            evidence_resolver=owned.Evidence(input_directory, value['input']['evidence_file'], str(result_path)))
        original_parent = current.read('tenant-1', parent['result_id'], farm)
        scope, dsns, directory = harvest_scope
        profile = mass_profile(registry.harvest._source(original_parent))
        profile['segments'][0]['end_at'] = expected['samples'][-1]['at']
        mass_raw = registry._canonical(profile)
        allocation_raw = registry._canonical(allocation_profile(registry.harvest._mass_parameters(mass_raw),
            last_sample=2, last_event=3))
        publisher = registry.HarvestRegistry(current, scope, directory, dsn=dsns[scope.publisher], integrity_key=HARVEST_KEY)
        record = publisher.put('tenant-1', parent['result_id'], farm, mass_raw, allocation_raw)
        reader = registry.HarvestRegistry(current, scope, directory, dsn=dsns[scope.reader], integrity_key=HARVEST_KEY)
        original_full = query.HarvestCurrentQuery(reader).read('tenant-1', record['result_id'], farm, limit=64)
        harvest_packet = json.loads(record['payload_raw']); harvest_directory = directory / harvest_packet['artifact']['key']
        root = json.loads((harvest_directory / (harvest_packet['artifact']['sha256'] + '.json')).read_bytes())
        page_path = harvest_directory / (root['pages'][0]['sha256'] + '.json')
        rows = [row for page in root['pages'] for row in json.loads((harvest_directory / (page['sha256'] + '.json')).read_bytes())]
        assert rows == original_full['page']['records'] and len(rows) == 6
        assert root['summary'] == original_full['summary'] and root['source'] == harvest_packet['source']
        assert root['parameter_raw_utf8'].encode() == mass_raw and root['allocation_raw_utf8'].encode() == allocation_raw
        expected_bytes = {'records': public._public_bytes(public.project_harvest_result(original_full, view='records', limit=64)),
            'summary': public._public_bytes(public.project_harvest_result({**original_full, 'page': None}))}
        jobs = server.binding.jobs; descriptor = jobs._content_directory(create=True); os.close(descriptor)
        cert, tls_key, _ = request.getfixturevalue('tls_files')
        cfg = config(policy=jobs.runtime_identity[0], dsn=jobs._dsn, artifact_root=jobs.artifact_root,
            certificate=cert, private_key=tls_key, thermal_gate_key=runtime.private_bytes(value['keys']['thermal']),
            market_hold_key=runtime.private_bytes(value['keys']['market']), port=0)
        parent_key = write('parent.key', DB_KEY); result_key = write('result.key', RESULT_KEY)
        harvest_key = write('harvest.key', HARVEST_KEY); dsn = write('reader.dsn', dsns[scope.reader].encode())
        reader_path = write('reader.json', json_raw({'config_version': reader_config.VERSION, 'policy': asdict(scope),
            'directory': str(directory), 'reader_dsn_file': str(dsn), 'integrity_key_file': str(harvest_key)}))
        legacy = tmp_path / 'legacy'; legacy.mkdir(mode=0o700)
        clock = write('clock.json', json_raw({'expired': False}))
        doc = {'config_version': loader.VERSION, 'policy': asdict(cfg.policy),
            'dsn_file': str(write('authority.dsn', cfg.dsn.encode())), 'artifact_root': str(cfg.artifact_root),
            'certificate': str(cert), 'private_key': str(tls_key),
            'thermal_gate_key_file': str(write('thermal.key', cfg.thermal_gate_key)),
            'market_hold_key_file': str(write('market.key', cfg.market_hold_key)),
            'authored_run_gate_key_file': None, 'content_access': None, 'host': cfg.host, 'port': cfg.port,
            'dependencies_factory': 'crop_harvest_tls_fixture:dependencies'}
        path = write('api.json', json_raw(doc))
        bundle = {'version': owned.VERSION, 'scope': 'owned_synthetic_actual_HTTPS_only', 'module_sha256': owned.CODE_SHA256,
            'reader_factory_sha256': reader_config.CODE_SHA256, 'registered_runtime_config': str(runtime_path),
            'registered_runtime_sha256': runtime_sha, 'parent_key': str(parent_key), 'result_key': str(result_key),
            'result_evidence': str(result_path), 'legacy_directory': str(legacy), 'clock_file': str(clock),
            'reader_config': str(reader_path),
            'static_sha256': {str(p): sha256(p.read_bytes()).hexdigest() for p in created if p != clock}}
        bundle_path = write('bundle.json', json_raw(bundle))
        monkeypatch.setenv('OSSF_OWNED_HARVEST_TLS_BUNDLE', str(bundle_path))
        monkeypatch.setenv('OSSF_OWNED_HARVEST_TLS_BUNDLE_SHA256', sha256(bundle_path.read_bytes()).hexdigest())
        rights['research_calculation'] = False; replace_control(rights_path, rights)
        yield SimpleNamespace(path=path, cfg=cfg, server=server, jobs=jobs, farm=farm, record=record,
            reader=reader, roots=(server.directory, input_directory, directory), rows=rows, summary=root['summary'],
            rights_path=rights_path, rights=rights, clock=clock, page_path=page_path,
            expected_bytes=expected_bytes, private_paths=[*created, *protected_runtime.iterdir(), cert, tls_key],
            prepare_seconds=monotonic()-started, actual_steps=progress['steps'], input_root=packet['input_root_sha256'])
    finally:
        removed = 0
        for path in [*created, *(protected_runtime.iterdir() if protected_runtime.exists() else [])]:
            if path.is_file(): path.unlink(); removed += 1
        assert not list(operator.iterdir()) and (not protected_runtime.exists() or not list(protected_runtime.iterdir()))
        save_native('harvest-tls-private-cleanup.json', {'protected_files_after': 0, 'removed_file_count': removed})


@pytest.mark.parametrize('original_login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)
def test_actual_protected_standard_runtime_SCRAM_HTTPS_original_rows_restarts_and_withdrawals(
        http_case, audit_database, monkeypatch):
    c = http_case; observed = []; joined = 0
    def counts():
        with c.jobs.connect() as conn:
            result = {name: conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(c.jobs._table(name))).fetchone()['n']
                for name in ('jobs', 'job_events', 'crop_cycle_research_results', 'crop_cycle_verified_research_results', 'thermal_g1_runs')}
            endpoint = (conn.info.host, conn.info.port, conn.info.dbname)
        with c.reader._connection() as conn:
            assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
            assert endpoint == (conn.info.host, conn.info.port, conn.info.dbname)
            result['harvest_rows'] = conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                sql.Identifier(c.reader.policy.schema, registry.schema.TABLE))).fetchone()['n']
        return result
    def inventory():
        files = set(c.private_paths)
        files.update(p for root in c.roots for p in root.rglob('*') if p.is_file())
        return {str(p): (sha256(p.read_bytes()).hexdigest(), p.stat().st_mode, p.stat().st_ino) for p in files}
    def target(view='summary', result_id=None, **pages):
        return '/v1/crop-harvest-research-results/' + (result_id or c.record['result_id']) + '?' + urlencode(
            {**c.farm, 'view': view, **pages})
    before = counts(); files_before = inventory()
    assert custody_fds(c.roots) == 0
    forbid_all_reads_math(monkeypatch)
    def forbidden(*_, **__): raise AssertionError('HTTPS parsed/calculated/issued/published crop data')
    for module, name in ((query.current.server.CalculationServerCustody, 'advance'),
            (query.current.storage.CalculationCycleCropResultStore, 'put'),
            (InputEvidenceAuthority, 'issue')):
        monkeypatch.setattr(module, name, forbidden)
    trust = ssl.create_default_context(cafile=str(c.cfg.certificate))
    logging_before = fd_inventory()
    first_selected = loader.load_calculation_api_runtime(c.path)
    first_https = first_selected.service.server()
    logging_after = fd_inventory()
    closed = {number: value for number, value in logging_before.items() if number not in logging_after}
    assert all(value[0] == '/dev/null' for value in closed.values())
    assert {number: value for number, value in logging_before.items() if number not in closed} == logging_after
    assert custody_fds(c.roots) == 0
    save_native('harvest-tls-logging-initialization.json', {'closed_descriptors': closed,
        'FD_before_after': [len(logging_before), len(logging_after)],
        'remaining_descriptor_targets_devices_inodes_preserved': True, 'custody_FD_after': 0,
        'baseline_after_first_standard_server_construction': True})
    fd_before = len(os.listdir('/proc/self/fd')); fds_before = fd_inventory()
    for restart in range(2):
        selected = first_selected if restart == 0 else loader.load_calculation_api_runtime(c.path)
        assert selected.harvest_crop_query.store is selected.harvest_crop_results
        assert selected.harvest_crop_results.query is selected.calculation_cycle_crop_query
        assert selected.calculation_cycle_crop_results.jobs is selected.jobs
        https = first_https if restart == 0 else selected.service.server()
        thread = threading.Thread(target=https.run, daemon=True); thread.start()
        try:
            deadline = monotonic() + 15
            while not https.started:
                assert thread.is_alive() and monotonic() < deadline; sleep(.01)
            port = https.servers[0].sockets[0].getsockname()[1]
            def call(label, where=None, bearer='owner'):
                connection = http.client.HTTPSConnection('127.0.0.1', port, timeout=30, context=trust)
                try:
                    started = monotonic()
                    connection.request('GET', where or target(), headers={} if bearer is None else
                        {'Authorization': 'Bearer ' + owned.TOKENS[bearer].decode()})
                    response = connection.getresponse(); raw = response.read(); seconds = monotonic() - started
                    observation = {'label': label, 'restart': restart, 'status': response.status,
                        'seconds': seconds, 'bytes': len(raw), 'body_sha256': sha256(raw).hexdigest()}
                    observed.append(observation)
                    save_native('harvest-https-' + label + '-r' + str(restart) + '.json', observation)
                    assert seconds < 30 and len(raw) <= public.MAX_RESPONSE_BYTES
                    assert response.getheader('cache-control') == 'no-store' and custody_fds(c.roots) == 0
                    value = json.loads(raw)
                    assert all(marker not in raw for marker in (b'"tenant_id":', b'"integrity_key":', b'"checkpoint":',
                        b'"integrity_signature":', b'"parameter_raw_utf8":', b'"allocation_raw_utf8":', str(c.path.parent).encode()))
                    if response.status == 200:
                        assert response.getheader('x-ossf-harvest-query-version') == query.VERSION
                        assert response.getheader('x-ossf-harvest-query-code-sha256') == query.CODE_SHA256
                        assert response.getheader('x-ossf-harvest-projection-code-sha256') == public.CODE_SHA256
                        assert value['reference']['gates'] == 'not_assessed' and value['reference']['rights_or_gate_approval'] is False
                    return response.status, value, raw
                finally: connection.close()
            status, value, raw = call('summary'); assert status == 200 and raw == c.expected_bytes['summary']
            assert value['summary'] == c.summary and value['reference']['row_count'] == 6
            if restart == 0:
                status, value, raw = call('records', target('records', limit=64))
                assert status == 200 and raw == c.expected_bytes['records'] and value['page']['records'] == c.rows
                rows = []
                for offset in (0, 3):
                    status, value, _ = call('split-' + str(offset), target('records', offset=offset, limit=3))
                    assert status == 200 and value['page']['offset'] == offset
                    rows.extend(value['page']['records'])
                assert rows == c.rows
                assert call('empty-end', target('records', offset=6, limit=3))[1]['page']['records'] == []
                assert call('unauthenticated', bearer=None)[0] == 401
                assert call('read-scope-denied', bearer='denied')[0] == 403
                assert call('foreign-tenant', bearer='foreign')[0] == 404
                assert call('missing-ID', target(result_id=registry.VERSION + ':' + '0' * 64))[0] == 404
                replace_control(c.rights_path, {**c.rights, 'research_display': False})
                try: assert call('display-withdrawn')[0] == 422
                finally: replace_control(c.rights_path, c.rights)
                with monkeypatch.context() as patch:
                    encode = public._public_bytes
                    def withdraw(projected):
                        raw = encode(projected); replace_control(c.rights_path, {**c.rights, 'research_display': False}); return raw
                    patch.setattr(public, '_public_bytes', withdraw)
                    try: assert call('display-withdrawn-after-projection')[0] == 422
                    finally: replace_control(c.rights_path, c.rights)
                with monkeypatch.context() as patch:
                    encode = public._public_bytes
                    def expire(projected):
                        raw = encode(projected); c.clock.write_bytes(json_raw({'expired': True})); return raw
                    patch.setattr(public, '_public_bytes', expire)
                    try: assert call('owned-clock-expiry-after-projection')[0] == 403
                    finally: c.clock.write_bytes(json_raw({'expired': False}))
                page_raw = c.page_path.read_bytes()
                try:
                    c.page_path.chmod(0o600); c.page_path.write_bytes(page_raw + b' '); c.page_path.chmod(0o400)
                    assert call('changed-stored-page', target('records', limit=64))[0] == 422
                finally:
                    c.page_path.chmod(0o600); c.page_path.write_bytes(page_raw); c.page_path.chmod(0o400)
                head = c.page_path.parent / 'HEAD'; head_raw = head.read_bytes()
                try:
                    head.chmod(0o600); head.write_bytes(head_raw + b' '); head.chmod(0o400)
                    assert call('changed-artifact-HEAD')[0] == 422
                finally:
                    head.chmod(0o600); head.write_bytes(head_raw); head.chmod(0o400)
            assert call('restored-summary')[2] == c.expected_bytes['summary']
        finally:
            https.should_exit = True; thread.join(timeout=15); assert not thread.is_alive(); joined += 1
    assert counts() == before and before['crop_cycle_verified_research_results'] == before['harvest_rows'] == 1
    assert before['thermal_g1_runs'] == before['crop_cycle_research_results'] == 0
    assert inventory() == files_before and custody_fds(c.roots) == 0 and current_principal() is None
    assert len(os.listdir('/proc/self/fd')) == fd_before and fd_inventory() == fds_before
    save_native('harvest-actual-https.json', {'scope': 'owned_synthetic_registered_HTTPS_only', 'actual_same_DB_SCRAM': True,
        'genuine_protected_operator_import_and_standard_ApiRuntime': True, 'joined_servers': joined, 'responses': observed,
        'original_six_rows_and_summary_UTC_units_exact_quantities_preserved': True, 'full_split_and_artifact_equal': True,
        'read_only_display_without_calculation_right': True, 'late_display_withdrawal_and_owned_clock_expiry_denied': True,
        'changed_selected_page_and_HEAD_denied_and_restored': True, 'maximum_full_body_seconds': max(v['seconds'] for v in observed),
        'maximum_full_body_bytes': max(v['bytes'] for v in observed), 'counts_before': before, 'counts_after': counts(),
        'FD_before_after': [fd_before, len(os.listdir('/proc/self/fd'))], 'same_descriptor_targets_devices_inodes': True,
        'protected_source_custody_bytes_modes_inodes_preserved': True, 'prepared_steps': c.actual_steps,
        'prepare_seconds': c.prepare_seconds, 'RHS_parser_generation_issue_publication_calls_during_reads': 0,
        'public_records_raw_utf8': c.expected_bytes['records'].decode(), 'public_summary_raw_utf8': c.expected_bytes['summary'].decode(),
        'actual_coefficients_adopted': 0, 'actual_crop_Runs': 0, 'gates': 'not_assessed'})
