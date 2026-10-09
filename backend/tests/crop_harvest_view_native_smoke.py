"""Manual owned same-DB harvest/crop HTTPS and actual built App/WebGL."""
import asyncio
import ctypes
import gc
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import select
import subprocess
import threading
from time import monotonic, sleep
from urllib.parse import parse_qs

import pytest
from psycopg import sql

from app import api_crop_cycle_calculation_replay as crop_public
from app import calculation_operator_config as loader
from app.http_identity import current_principal
from test_crop_harvest_runtime_tls import (http_case, server_setup, bound_setup, harvest_scope,
    login_scope, original_login_scope, authoring, farm_setup, login_database, custody_fds,
    fd_inventory, forbid_all_reads_math, query, save_native, replace_control, InputEvidenceAuthority)
from test_crop_harvest import native_cleanup
from crop_cycle_registered_replay_smoke import consumer, tls_files, loopback_tls_files
from crop_cycle_registered_terminal_publication_smoke import module as publication_module
import crop_harvest_tls_fixture as owned

ROOT = Path(__file__).resolve().parents[2]


class Observation:
    def __init__(self, app):
        self.app = app; self.active = self.peak = 0; self.responses = []
        self.hold_next = False; self.entered = threading.Event(); self.release = threading.Event()

    async def __call__(self, scope, receive, send):
        prefixes = ('/v1/crop-cycle-calculation-research-results/', '/v1/crop-harvest-research-results/')
        if scope['type'] != 'http' or not scope['path'].startswith(prefixes):
            return await self.app(scope, receive, send)
        self.active += 1; self.peak = max(self.peak, self.active); started = monotonic()
        q = parse_qs(scope['query_string'].decode('ascii')); digest = sha256()
        row = {'endpoint': 'harvest' if scope['path'].startswith(prefixes[1]) else 'crop',
            'view': q.get('view', ['summary'])[0], 'offset': q.get('offset', [None])[0],
            'status': None, 'bytes': 0, 'complete': False, 'delayed': False}
        async def observed_send(message):
            if message['type'] == 'http.response.start':
                row['status'] = message['status']
                row['cache'] = dict(message['headers']).get(b'cache-control', b'').decode()
            if message['type'] == 'http.response.body':
                body = message.get('body', b''); row['bytes'] += len(body); digest.update(body)
                row['complete'] = not message.get('more_body', False)
            await send(message)
        try:
            if self.hold_next and row['endpoint'] == 'harvest' and row['view'] == 'summary':
                self.hold_next = False; row['delayed'] = True; self.entered.set()
                assert await asyncio.to_thread(self.release.wait, 15), 'owned delayed request not released'
            return await self.app(scope, receive, observed_send)
        finally:
            row.update(seconds=monotonic()-started, body_sha256=digest.hexdigest())
            self.responses.append(row); self.active -= 1


def test_native_harvest_consumer_import_has_no_resource_side_effects(monkeypatch):
    import psycopg
    import socket
    def forbidden(*_, **__): raise AssertionError('native consumer import started a resource')
    monkeypatch.setattr(psycopg, 'connect', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(threading.Thread, 'start', forbidden)
    spec = importlib.util.spec_from_file_location('owned_harvest_native_import', Path(__file__))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    assert callable(module.test_same_registered_DB_harvest_HTTPS_native_WebGL)


@pytest.mark.parametrize('original_login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)
def test_same_registered_DB_harvest_HTTPS_native_WebGL(http_case, server_setup, native_cleanup, monkeypatch):
    c = http_case; expected = server_setup[4]; support = consumer(); publisher = publication_module()
    source = json.loads(c.record['payload_raw'])['source']; parent_id = source['result_id']
    selected = loader.load_calculation_api_runtime(c.path)
    assert selected.harvest_crop_results.query is selected.calculation_cycle_crop_query
    assert selected.calculation_cycle_crop_results.jobs is selected.jobs
    prepared = c.reader.query.read('tenant-1', parent_id, c.farm)
    summary = crop_public.project_calculation_cycle_result(prepared['record'], prepared['terminal']).model_dump(mode='json')
    samples = c.reader.query.read('tenant-1', parent_id, c.farm, kind='samples', start=0, limit=7)
    assert samples['page']['records'] == expected['samples'] and len(expected['samples']) == 3
    assert len(expected['events']) == 4 and len(c.rows) == 6
    assert summary['reference']['context_sha256'] == source['math_manifest_sha256']
    data = {'crop_summary': summary, 'samples': expected['samples'], 'rows': c.rows,
        'harvest_result_id': c.record['result_id'], 'whole_summary': c.summary}
    def counts():
        with c.jobs.connect() as conn:
            endpoint = (conn.info.host, conn.info.port, conn.info.dbname)
            result = {name: conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(c.jobs._table(name))).fetchone()['n']
                for name in ('jobs', 'job_events', 'crop_cycle_verified_research_results', 'thermal_g1_runs')}
        with c.reader._connection() as conn:
            assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
            assert endpoint == (conn.info.host, conn.info.port, conn.info.dbname)
            result['harvest_rows'] = conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                sql.Identifier(c.reader.policy.schema, query.registry.schema.TABLE))).fetchone()['n']
        return result
    def inventory():
        paths = set(c.private_paths)
        paths.update(p for root in c.roots for p in root.rglob('*') if p.is_file())
        return {str(p): (sha256(p.read_bytes()).hexdigest(), p.stat().st_mode, p.stat().st_ino) for p in paths}
    before = counts(); files_before = inventory(); original_rights = publisher.runtime.private_bytes(c.rights_path)
    assert before['crop_cycle_verified_research_results'] == before['harvest_rows'] == 1
    assert custody_fds(c.roots) == 0
    forbid_all_reads_math(monkeypatch)
    def forbidden(*_, **__): raise AssertionError('native GET calculated/issued/published crop data')
    for module, name in ((query.current.server.CalculationServerCustody, 'advance'),
            (query.current.storage.CalculationCycleCropResultStore, 'put'),
            (InputEvidenceAuthority, 'issue')):
        monkeypatch.setattr(module, name, forbidden)
    https = selected.service.server(); observed = Observation(https.config.app); https.config.app = observed
    fds = fd_inventory(); thread = threading.Thread(target=https.run, daemon=True); thread.start()
    evidence = Path(os.environ['OSSF_REMOVAL_LEDGER_EVIDENCE']); log = evidence/'harvest-native-browser.log'
    browser = None; report = command = frontend = None; started = monotonic(); communicated = False
    try:
        deadline = monotonic()+15
        while not https.started:
            assert thread.is_alive() and monotonic() < deadline; sleep(.01)
        api_port = https.servers[0].sockets[0].getsockname()[1]
        with support.production_frontend(f'https://127.0.0.1:{api_port}', c.cfg.certificate,
                c.cfg.private_key, publisher, evidence) as (web_port, frontend):
            def rss():
                return next(int(line.split()[1])*1024 for line in Path('/proc/self/status').read_text().splitlines()
                    if line.startswith('VmRSS:'))
            memory_before = rss(); collected = gc.collect()
            trim = ctypes.CDLL(None).malloc_trim; trim.argtypes = [ctypes.c_size_t]; trim.restype = ctypes.c_int
            trimmed = trim(0)
            save_native('harvest-native-parent-memory.json', {'phase':'before_browser','before_RSS_bytes':memory_before,
                'after_RSS_bytes':rss(),'Python_gc_collected':collected,'glibc_malloc_trim_return':trimmed,
                'scope':'owned_Linux_test_process_only_not_production_memory_claim'})
            argv = ['node', '--expose-gc', '--max-old-space-size=64', '--max-semi-space-size=2',
                'e2e/harvest-replay-native-smoke.mjs', f'https://127.0.0.1:{web_port}', str(evidence/'screens')]
            env = {k: os.environ[k] for k in ('PATH','HOME','LANG','PLAYWRIGHT_BROWSERS_PATH','TMPDIR') if k in os.environ}
            with log.open('xb') as errors:
                os.fchmod(errors.fileno(), 0o600)
                browser = subprocess.Popen(argv, cwd=ROOT/'web', env=env, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=errors, text=True)
                identity = publisher.supervisor.identity(browser.pid)
                def send(value): browser.stdin.write(json.dumps(value)+'\n'); browser.stdin.flush()
                def receive(stage, timeout):
                    assert select.select([browser.stdout], [], [], timeout)[0], 'owned browser stage timeout: '+stage
                    raw = browser.stdout.readline(); assert raw, 'owned browser ended: '+stage
                    value = json.loads(raw); assert value['stage'] == stage; return value
                send({'data': data, 'tokens': {k:v.decode() for k,v in owned.TOKENS.items()}})
                receive('geometry_verified', 240)
                replace_control(c.rights_path, {**c.rights, 'research_display': False}); send({'stage':'rights_revoked'})
                receive('rights_denied', 45)
                replace_control(c.rights_path, json.loads(original_rights)); send({'stage':'rights_restored'})
                receive('restored_verified', 120)
                observed.hold_next = True; send({'stage':'hold_next_summary'})
                receive('held_request_started', 15); assert observed.entered.wait(10)
                send({'stage':'cancel_now'}); receive('canceled_account_changed', 15)
                observed.release.set(); deadline = monotonic()+30
                while observed.active:
                    assert monotonic() < deadline; sleep(.01)
                send({'stage':'old_request_settled'}); report = receive('verified', 60)
                browser.communicate(timeout=15); communicated = True; assert browser.returncode == 0
                errors.flush(); os.fsync(errors.fileno())
                command = {'argv':argv, 'worker':identity, 'actual_exit_code':browser.returncode,
                    'stderr_log_sha256':sha256(log.read_bytes()).hexdigest(), 'seconds':monotonic()-started}
            assert not any(token.decode() in json.dumps(report) for token in owned.TOKENS.values())
            assert report['verified_rows'] == 6 and report['verified_sample_indices'] == [0,1,2]
            assert report['actual_WebGL'] and report['errors'] == [] and report['peak_active_reads'] == observed.peak == 1
            assert observed.active == 0 and all(r['complete'] and r['seconds'] < 30 and r['bytes'] <= 2*1024**2
                and r['cache'] == 'no-store' for r in observed.responses)
            assert len(observed.responses) == len(report['network'])
            assert len([r for r in observed.responses if r['delayed']]) == 1
            assert {(r['endpoint'],r['status']) for r in observed.responses if r['status'] == 403} == {('crop',403),('harvest',403)}
            assert any(r['endpoint']=='harvest' and r['status']==422 for r in observed.responses)
            assert counts() == before and current_principal() is None
    finally:
        observed.release.set(); replace_control(c.rights_path, json.loads(original_rights))
        if browser is not None:
            if browser.poll() is None:
                assert publisher.supervisor.identity(browser.pid) == identity; browser.kill()
            if not communicated: browser.communicate(timeout=15)
            log.chmod(0o400)
            save_native('harvest-native-browser-command.json', {'argv':argv,'worker':identity,
                'actual_exit_code':browser.returncode,'stderr_log_sha256':sha256(log.read_bytes()).hexdigest()})
        https.should_exit = True; thread.join(timeout=15); assert not thread.is_alive()
    assert fd_inventory() == fds and custody_fds(c.roots) == 0
    assert inventory() == files_before and counts() == before
    save_native('harvest-native-verified.json', {'scope':'owned_same_DB_synthetic_harvest_actual_App_WebGL',
        'actual_same_DB_SCRAM':True,'protected_real_dependency_import':True,'parent_result_id':parent_id,
        'harvest_result_id':c.record['result_id'],'source':source,'browser':report,'browser_command':command,
        'frontend_command':frontend,'server_responses':observed.responses,'server_peak_active_reads':observed.peak,
        'counts_before':before,'counts_after':counts(),'original_120_steps':c.actual_steps,
        'read_RHS_generation_issue_publication_calls':0,'source_bytes_modes_inodes_preserved':True,
        'FD_identity_preserved':True,'HTTPS_joined':True,'actual_coefficients_adopted':0,'actual_crop_Runs':0,
        'gates':'not_assessed','full166_mass_load_accepted':False})
