"""Explicit live organ catalogue/HTTPS/WebGL check against a tested static build."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
import json
import mimetypes
import os
from pathlib import Path
import select
import secrets
import ssl
import subprocess
import sys
import threading
import time
from urllib.parse import unquote, urlsplit

import pytest
from psycopg import sql

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'backend'))
from app.api_crop_replay import project_crop_result
from app.api_runtime import ApiRuntime
from app.crop_result_store import CropResultStore, READ_SCOPES
from app.http_identity import BearerGrant, BearerRegistry, token_digest
from app.market_source_store import MarketSourceStore
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_api_crop_replay import CROP_POLICY
from test_crop_result_store import (crop_setup, authoring, farm_setup, login_scope,
    login_database, PROFILE, NOTICE, KEY, raw, put, count)
from test_market_hold_store import context_verifier


def save(path, value):
    with path.open('x') as stream:
        os.fchmod(stream.fileno(), 0o400)
        json.dump(value, stream, sort_keys=True, indent=2)


@contextmanager
def static_frontend(dist, port, cert, key, observations, failures):
    assets = {'/'+str(p.relative_to(dist)):p for p in dist.rglob('*') if p.is_file()}
    assets['/'] = dist/'index.html'
    before = {name:sha256(p.read_bytes()).hexdigest() for name,p in assets.items()}
    trust = ssl.create_default_context(cafile=str(cert))

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, *args):
            pass

        def end_headers(self):
            self.send_header('Connection','close')
            self.close_connection = True
            super().end_headers()

        def do_GET(self):
            parsed = urlsplit(self.path)
            if parsed.path.startswith('/v1/'):
                assert len(observations) < 64
                started = time.monotonic()
                upstream = http.client.HTTPSConnection('127.0.0.1', port, context=trust, timeout=30)
                try:
                    upstream.request('GET', self.path, headers={
                        'Authorization':self.headers.get('Authorization', ''), 'Accept':'application/json'})
                    response = upstream.getresponse()
                    limit = 65536 if parsed.path.startswith('/v1/crop-research-result-catalog') else 2*1024**2
                    wire = response.read(limit+1)
                    assert len(wire) <= limit and response.getheader('Cache-Control') == 'no-store'
                    elapsed = time.monotonic()-started
                    assert elapsed < 30
                    observations.append({'path':self.path, 'method':'GET', 'status':response.status,
                        'bytes':len(wire), 'body_SHA256':sha256(wire).hexdigest(),
                        'full_upstream_seconds':elapsed, 'upstream_TLS_verified':True})
                    self.send_response(response.status)
                    for name,value in response.getheaders():
                        if name.lower() not in ('date','server','connection','transfer-encoding','content-length'):
                            self.send_header(name,value)
                    self.send_header('Content-Length',str(len(wire)))
                    self.end_headers()
                    self.wfile.write(wire)
                except Exception as error:
                    failures.append(type(error).__name__)
                    raise
                finally:
                    upstream.close()
                return
            path = assets.get(unquote(parsed.path))
            if path is None:
                self.send_response(404)
                self.send_header('Content-Length','0')
                self.end_headers()
                return
            wire = path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type',mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            self.send_header('Content-Length',str(len(wire)))
            self.send_header('Cache-Control','no-store')
            self.end_headers()
            self.wfile.write(wire)

        def do_POST(self):
            failures.append('unexpected_write_request')
            self.send_response(405)
            self.send_header('Content-Length','0')
            self.end_headers()

    server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
    server.daemon_threads = False
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(cert,key)
    server.socket = context.wrap_socket(server.socket,server_side=True)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        yield f'https://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        thread.join(timeout=15)
        server.server_close()
        assert not thread.is_alive()
        assert before == {name:sha256(p.read_bytes()).hexdigest() for name,p in assets.items()}


@pytest.mark.parametrize('login_scope',[CROP_POLICY],indirect=True)
def test_live_organ_catalogue_saved_frames_current_rights_and_account(crop_setup,tls_files,tmp_path,monkeypatch):
    evidence = Path(os.environ['OSSF_ORGAN_NATIVE_EVIDENCE'])
    dist = Path(os.environ['OSSF_ORGAN_WEB_DIST']).resolve()
    provenance = json.loads((dist.parent/'build-provenance.json').read_bytes())
    assert provenance['build_commit'] == os.environ['GITHUB_SHA'] and provenance['archive_checked']
    assert provenance['browser_suite'] == 'all'
    assert (dist/'index.html').is_file() and list((dist/'assets').glob('CropResultCatalog-*.js'))
    store,body,_,rights = crop_setup
    record = put(store,body)
    expected = project_crop_result(record).model_dump(mode='json')
    held_body = deepcopy(body)
    held_body['revision'] = 'catalogue-numeric-hold'
    held_body['program']['initial_state']['values']['buffer']['value'] = 0
    held_body['program']['segments'][0]['forcing']['values']['par_above_canopy']['value'] = 0
    held_body['rights']['program_sha256'] = sha256(raw(held_body['program'])).hexdigest()
    held_record = put(store,held_body)
    held = project_crop_result(held_record).model_dump(mode='json')
    assert held['status'] == 'hold' and not held['samples']
    snapshots = {r['result_id']:store._find('tenant-1',result_id=r['result_id']) for r in (record,held_record)}
    jobs,replay = store.jobs,store.farms.replay
    research,holds = replay.owned_research,replay.thermal.holds
    cert,key,_ = tls_files
    now = datetime.now(timezone.utc)
    tokens = {name:secrets.token_urlsafe(40).encode() for name in ('owner','denied')}
    grants = tuple(BearerGrant(token_digest(tokens[name]),'tenant-1',frozenset(scopes),
        now-timedelta(seconds=1),now+timedelta(minutes=15)) for name,scopes in (
        ('owner',set(READ_SCOPES)),('denied',set(READ_SCOPES)-{'crop_result_read'})))

    def source_factory(*,principal_provider):
        return MarketSourceStore(jobs._dsn,jobs.schema,principal_provider=principal_provider,
            runtime_identity=jobs.runtime_identity)

    def crop_factory(*,farm_authoring_service):
        return CropResultStore(farm_authoring_service,PROFILE,NOTICE,program_rights=rights,integrity_key=KEY)

    os.close(jobs._content_directory(create=True))
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,
        artifact_root=jobs.artifact_root,certificate=cert,private_key=key,port=0),
        dependencies(research_registry=research.catalog,bearer_registry=BearerRegistry(grants),
            owned_fixture_registry=research.registry,owned_research_contexts=dict(research._contexts),
            context_verifier=context_verifier,market_scope_resolver=holds._scope_resolver,
            market_source_factory=source_factory,crop_result_store_factory=crop_factory))
    registration = store.farms.get('tenant-1',body['farm']['scenario_id'],body['farm']['scenario_revision'])
    before = count(store)
    def selected_counts():
        with jobs.connect() as conn:
            return {name:conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
                .format(jobs._table(name))).fetchone()['n'] for name in (
                'jobs','job_events','crop_research_results','thermal_g1_runs')}
    before_counts = selected_counts()
    calls = {'put':0,'integrate':0,'RHS':0,'SQL_writes':0}

    def forbidden(name):
        def reject(*args,**kwargs):
            calls[name] += 1
            raise AssertionError('browser query attempted '+name)
        return reject

    monkeypatch.setattr(CropResultStore,'put',forbidden('put'))
    monkeypatch.setattr('app.crop_result_store.integrate_crop',forbidden('integrate'))
    monkeypatch.setattr('app.crop_growth_integration.rates.calculate_rates',forbidden('RHS'))
    import psycopg
    execute = psycopg.Connection.execute

    def no_writes(conn,statement,*args,**kwargs):
        text = statement.as_string(conn) if hasattr(statement,'as_string') else statement
        if text.split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','TRUNCATE','CREATE','ALTER','DROP','GRANT','REVOKE'):
            calls['SQL_writes'] += 1
            raise AssertionError('browser query attempted SQL mutation')
        return execute(conn,statement,*args,**kwargs)

    server = runtime.service.server()
    thread = threading.Thread(target=server.run,daemon=True)
    observations,failures = [],[]
    browser = None
    thread.start()
    try:
        deadline = time.monotonic()+15
        while not server.started:
            assert thread.is_alive() and time.monotonic()<deadline
            time.sleep(.01)
        port = server.servers[0].sockets[0].getsockname()[1]
        with monkeypatch.context() as read_patch:
            read_patch.setattr(psycopg.Connection,'execute',no_writes)
            with static_frontend(dist,port,cert,key,observations,failures) as origin:
                env = {k:os.environ[k] for k in ('PATH','HOME','LANG','PLAYWRIGHT_BROWSERS_PATH') if k in os.environ}
                browser = subprocess.Popen(['node','--max-old-space-size=128','--max-semi-space-size=1',
                    'e2e/real-organ-catalog-smoke.mjs',origin,str(evidence)],cwd=ROOT/'web',env=env,
                    stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                payload = {'tokens':{k:v.decode() for k,v in tokens.items()},'result':expected,'held':held,
                    'farm_job_id':str(registration.intent_job.job_id),
                    'recorded_at':record['recorded_at'].astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z'),
                    'held_recorded_at':held_record['recorded_at'].astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')}
                browser.stdin.write(json.dumps(payload)+'\n')
                browser.stdin.flush()

                def phase(expected_phase,seconds):
                    assert select.select([browser.stdout],[],[],seconds)[0], 'browser phase timeout: '+expected_phase
                    line = browser.stdout.readline()
                    if not line:
                        _,error = browser.communicate(timeout=5)
                        pytest.fail('native browser exited before '+expected_phase+': '+error[-2000:])
                    value = json.loads(line)
                    assert value['stage'] == expected_phase
                    return value

                phase('geometry_verified',90)
                rights.allowed = False
                browser.stdin.write('{"stage":"rights_revoked"}\n')
                browser.stdin.flush()
                phase('rights_hold_verified',45)
                rights.allowed = True
                browser.stdin.write('{"stage":"rights_restored"}\n')
                browser.stdin.flush()
                report = phase('verified',105)
                browser.stdin.close()
                browser.stdin = None
                output,error = browser.communicate(timeout=15)
                assert browser.returncode == 0,error[-2500:]
                assert not output.strip(), 'unexpected duplicate browser protocol output'
                assert report['stage']=='verified' and report['actual_WebGL'] and not report['mock_API_used']
        assert not failures and all(n==0 for n in calls.values())
        assert count(store)==before
        assert selected_counts()==before_counts
        assert {k:store._find('tenant-1',result_id=k) for k in snapshots}==snapshots
        with jobs.connect() as conn:
            assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
            assert conn.execute('SHOW shared_buffers').fetchone()['shared_buffers']=='1MB'
        assert sorted((o['path'],o['status']) for o in observations)==sorted(
            (o['path'],o['status']) for o in report['network'])
        server_rows = [(o['path'],o['status'],o['bytes'],o['body_SHA256']) for o in observations if o['status']==200]
        browser_rows = [(o['path'],o['status'],o['bytes'],o['body_SHA256']) for o in report['network'] if o['body_observed']]
        assert sorted(server_rows)==sorted(browser_rows)
        assert all(o['status'] in (403,422) and not o['body_observed'] and 'body_SHA256' not in o
            for o in report['network'] if o['status']!=200)
        assert any(o['status']==422 for o in observations) and any(o['status']==403 for o in observations)
        result = {'scope':'synthetic live organ catalogue/API/DB/browser software integration',
            'actual_TLS_SCRAM_Bearer':True,'actual_API_DB_browser':True,'mock_API_used':False,
            'test_build':provenance,'browser':report,'responses':observations,'proxy_errors':failures,
            'row_count_before_after':[before,count(store)],'original_rows_payloads_signatures_unchanged':True,
            'selected_DB_counts_before_after':[before_counts,selected_counts()],
            'query_calls':calls,'actual_crop_Runs':0,'G0_G4':'not_assessed','WSL_capacity_accepted':False,
            'all_response_statuses_matched':True,'successful_response_bodies_matched':True,
            'denied_responses_browser_headers_only':True,
            'owned_postgres_shared_buffers':'1MB',
            'historical_preserved_row_compatibility_accepted':False,'U1_accepted':False,'deployed':False}
    finally:
        rights.allowed = True
        if browser is not None and browser.poll() is None:
            browser.kill()
            browser.communicate(timeout=5)
        server.should_exit = True
        thread.join(timeout=15)
        assert not thread.is_alive()
    result['HTTPS_server_joined'] = True
    save(evidence/'native-organ.json',result)
