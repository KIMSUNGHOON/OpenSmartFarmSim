"""Actual TLS/Bearer/runtime/SCRAM registration; synthetic source evidence only."""

from datetime import datetime, timedelta, timezone
import http.client
import json
from pathlib import Path
import ssl
import sys
import threading
import time

import pytest
from psycopg import sql

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.api_runtime import ApiRuntime
from app.http_identity import BearerGrant, BearerRegistry, token_digest
from app.market_source_store import MarketSourceStore
from app.farm_replay_scenario import READ_SCOPES, WRITE_SCOPES
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_farm_replay_scenario import farm_setup, login_database, login_scope

pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation':True,
    'market_source_storage':True, 'thermal_scenario_storage':True, 'break_even_calculation':True}], indirect=True)


def test_actual_https_registers_and_revalidates_joined_input(farm_setup, tls_files, login_scope):
    service, body, _ = farm_setup
    jobs = service.jobs
    jobs.artifact_root.mkdir(mode=0o700)
    cert, key, _ = tls_files
    now = datetime.now(timezone.utc)
    token = b'synthetic-farm-http-'+b'f'*32
    reader = b'synthetic-farm-reader-'+b'r'*32
    other = b'synthetic-farm-other-'+b'o'*32
    grants = tuple(BearerGrant(token_digest(value),tenant,frozenset(scopes),
        now-timedelta(seconds=1),now+timedelta(minutes=10)) for value,tenant,scopes in
        ((token,'tenant-1',WRITE_SCOPES),(reader,'tenant-1',READ_SCOPES),(other,'tenant-other',WRITE_SCOPES)))
    factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn,jobs.schema,
        principal_provider=principal_provider,runtime_identity=jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,artifact_root=jobs.artifact_root,
        certificate=cert,private_key=key,port=0),dependencies(research_registry=service.registry,
        bearer_registry=BearerRegistry(grants),market_source_factory=factory,
        market_scope_resolver=service.thermal.holds._scope_resolver))
    assert runtime.farm_scenarios is not None
    server = runtime.service.server()
    thread = threading.Thread(target=server.run,daemon=True)
    thread.start()
    timings = []
    try:
        deadline = time.monotonic()+10
        while not server.started:
            assert thread.is_alive() and time.monotonic()<deadline
            time.sleep(0.01)
        port = server.servers[0].sockets[0].getsockname()[1]
        context = ssl.create_default_context(cafile=str(cert))
        def call(path='/v1/farm-scenarios',*,payload=None,bearer=token):
            conn = http.client.HTTPSConnection('127.0.0.1',port,timeout=30,context=context)
            start = time.monotonic()
            try:
                headers = {'Content-Type':'application/json','X-Tenant-Id':'foreign'}
                if bearer is not None: headers['Authorization'] = 'Bearer '+bearer.decode()
                conn.request('POST' if payload is not None else 'GET',path,
                    json.dumps(payload) if payload is not None else None,headers)
                response = conn.getresponse()
                assert response.getheader('cache-control') == 'no-store'
                return response.status,json.loads(response.read())
            finally:
                timings.append({'method':'POST' if payload is not None else 'GET','seconds':round(time.monotonic()-start,3)})
                conn.close()
        assert call(payload=body,bearer=None)[0] == 401
        assert call(payload=body,bearer=reader)[0] == 403
        status, accepted = call(payload=body)
        assert status == 200 and accepted['intent_job']['state'] == 'queued'
        assert call(payload=body) == (status,accepted)
        path='/v1/farm-scenarios?scenario_id=farm-one&scenario_revision=r1'
        assert call(path,bearer=reader) == (status,accepted)
        assert call(path,bearer=other)[0] == 404
        with jobs.connect() as conn:
            rows = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND input_sha256=%s')
                .format(jobs._table('jobs')),('tenant-1',accepted['scenario_sha256'])).fetchall()
        assert len(rows) == 1 and rows[0]['input_bytes'] == runtime.farm_scenarios.jobs._verified_input(rows[0])
        with login_scope[0].connect() as conn:
            conn.execute(sql.SQL('GRANT SELECT ON {}.jobs TO {}').format(
                sql.Identifier(jobs.schema),sql.Identifier(jobs.runtime_identity[0].roles['worker'])))
        assert call(path,bearer=reader)[0] == 503
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        assert not thread.is_alive()
    print('farm_replay_http_timings='+json.dumps(timings))
