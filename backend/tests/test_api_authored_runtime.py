"""Standard HTTPS authored read assembly, with explicitly synthetic test authority."""

from datetime import datetime, timedelta, timezone
from dataclasses import replace
import http.client
import json
from pathlib import Path
import ssl
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api_authored_thermal import AUTHORED_READ_SCOPES
from app.api_runtime import ApiRuntime
from app.farm_authoring_storage import FarmAuthoringService
from app.farm_authored_run_store import AuthoredRunStore
from app.http_identity import BearerGrant, BearerRegistry, current_principal, token_digest
from app.market_source_store import MarketSourceStore
from app.owned_fixture_registry import OwnedFixtureRegistry
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_farm_authored_simulation_worker import _admit
from login_database import login_database, login_scope


ROOT = Path(__file__).resolve().parents[2]
PROFILE = [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True,
    'authored_release_storage': True, 'authored_run_storage': True}]


@pytest.mark.parametrize('login_scope', PROFILE, indirect=True)
def test_standard_https_reads_owned_authored_run_and_holds_stale_evidence(
        login_scope, tls_files, tmp_path):
    jobs, _, packet, preparer, original_store, job, worker = _admit(login_scope, tmp_path)
    assert worker.run_once(str(job['job_id'])).state == 'succeeded'
    cert, key, _ = tls_files
    now = datetime.now(timezone.utc)
    tokens = {name: ('synthetic-authored-https-' + name + '-' + 'x' * 32).encode()
        for name in ('owner', 'denied', 'foreign')}
    grants = tuple(BearerGrant(token_digest(raw), tenant, frozenset(scopes),
        now - timedelta(seconds=1), now + timedelta(minutes=10))
        for name, raw, tenant, scopes in (
            ('owner', tokens['owner'], 'tenant-a', AUTHORED_READ_SCOPES),
            ('denied', tokens['denied'], 'tenant-a',
                tuple(scope for scope in AUTHORED_READ_SCOPES if scope != 'authored_run_read')),
            ('foreign', tokens['foreign'], 'tenant-b', AUTHORED_READ_SCOPES)))
    source_factory = lambda *, principal_provider: MarketSourceStore(
        jobs._dsn, jobs.schema, principal_provider=principal_provider,
        runtime_identity=jobs.runtime_identity)
    base_deps = dependencies()
    registry = base_deps.research_registry
    contexts = {next(iter(registry._scopes)): 'context-1'}
    seen = []

    def authored_factory(*, job_store, farm_scenario_service, gate_key):
        assert job_store is not jobs and job_store.principal_provider is current_principal
        assert gate_key == original_store.gate_key
        seen.append((job_store, farm_scenario_service))
        preparer.authoring = FarmAuthoringService(farm_scenario_service)
        preparer.release_store.jobs = job_store
        return AuthoredRunStore(preparer, gate_key)

    runtime_config = config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key,
        port=0, authored_run_gate_key=original_store.gate_key)
    runtime_deps = dependencies(research_registry=registry,
        bearer_registry=BearerRegistry(grants), market_source_factory=source_factory,
        owned_fixture_registry=OwnedFixtureRegistry(ROOT),
        owned_research_contexts=contexts, authored_run_store_factory=authored_factory)
    with pytest.raises(ValueError, match='^API runtime assembly rejected$'):
        ApiRuntime(runtime_config, replace(runtime_deps,
            authored_run_store_factory=lambda **_: object()))
    with pytest.raises(ValueError, match='^API runtime assembly rejected$'):
        ApiRuntime(runtime_config, replace(runtime_deps,
            authored_run_store_factory=lambda **_: original_store))
    def wrong_key_factory(**kwargs):
        result = authored_factory(**kwargs)
        result.gate_key = b'synthetic-wrong-gate-key-' + b'z' * 32
        return result
    with pytest.raises(ValueError, match='^API runtime assembly rejected$'):
        ApiRuntime(runtime_config, replace(runtime_deps,
            authored_run_store_factory=wrong_key_factory))
    seen.clear()
    runtime = ApiRuntime(runtime_config, runtime_deps)
    assert seen == [(runtime.jobs, runtime.farm_scenarios)]
    assert runtime.authored_runs.jobs is runtime.jobs
    assert runtime.authored_runs.preparer.authoring.replay is runtime.farm_scenarios
    assert type(runtime.farm_authoring) is FarmAuthoringService
    assert runtime.farm_authoring.replay is runtime.farm_scenarios
    server = runtime.service.server()
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 15
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline
            time.sleep(0.01)
        port = server.servers[0].sockets[0].getsockname()[1]
        context = ssl.create_default_context(cafile=str(cert))

        def call(path, bearer='owner'):
            conn = http.client.HTTPSConnection('127.0.0.1', port, timeout=30, context=context)
            try:
                headers = {} if bearer is None else {
                    'Authorization': 'Bearer ' + tokens[bearer].decode()}
                conn.request('GET', path, headers=headers)
                response = conn.getresponse()
                assert response.getheader('cache-control') == 'no-store'
                return response.status, json.loads(response.read())
            finally:
                conn.close()

        job_path = f"/v1/jobs/{job['job_id']}/authored-run"
        run_path = '/v1/authored-runs/' + packet.run_id
        assert call(job_path, bearer=None)[0] == 401
        assert call(job_path, bearer='denied')[0] == 403
        assert call(job_path, bearer='foreign')[0] == 404
        status, summary = call(job_path)
        assert status == 200 and summary['run_id'] == packet.run_id
        assert summary['claim_scope'] == 'synthetic_thermal_replay_only'
        assert call(run_path) == (200, summary)
        status, series = call(run_path + '/series')
        assert status == 200 and series['run_id'] == packet.run_id
        assert len(series['points']) == 120
        assert series['points'][-1]['at_utc'] == summary['end_utc']
        preparer.prepare = lambda *_: None
        assert call(job_path)[0] == 503
        assert call(run_path)[0] == 503
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        assert not thread.is_alive()
