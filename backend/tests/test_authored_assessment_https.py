"""Actual TLS/Bearer/SCRAM authored assessment; fake CLI and test reviewers."""

from copy import copy
from datetime import datetime, timedelta, timezone
import http.client
import json
from pathlib import Path
import ssl
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api_runtime import ApiRuntime
from app.authored_economic_execution import AUTHORED_ECONOMIC_SCOPES
from app.calculation_assessment import ADMISSION_SCOPES
from app.farm_authoring_storage import FarmAuthoringService
from app.farm_authored_release_store import AuthoredReleaseStore
from app.farm_authored_review import FarmAuthoredReviewService
from app.farm_authored_run import AuthoredRunPreparer
from app.farm_authored_run_store import AuthoredRunStore
from app.http_identity import BearerGrant, BearerRegistry, token_digest
from app.market_source_store import MarketSourceStore
from app.owned_fixture_registry import OwnedFixtureRegistry
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_authored_calculation_assessment import (authored_pair, authored_economic, authoring,
    farm_setup, login_database, login_scope, PROFILE, assessment_cli)


ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


def test_standard_https_admits_authored_pair_and_reads_persisted_cli_hold(
        authored_pair, tls_files, tmp_path):
    service, _, intent, _, _, _ = authored_pair
    jobs = service.jobs
    cert, key, _ = tls_files
    now = datetime.now(timezone.utc)
    tokens = {name: ('synthetic-authored-assessment-' + name + '-' + 'x' * 32).encode()
        for name in ('owner', 'denied', 'foreign')}
    scopes = set((*ADMISSION_SCOPES, *AUTHORED_ECONOMIC_SCOPES, 'auditor'))
    grants = tuple(BearerGrant(token_digest(tokens[name]), tenant, frozenset(allowed),
        now - timedelta(seconds=1), now + timedelta(minutes=20))
        for name, tenant, allowed in (
            ('owner', 'tenant-1', scopes),
            ('denied', 'tenant-1', scopes - {'authored_run_read'}),
            ('foreign', 'other-tenant', scopes)))
    source_factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    original_preparer = service.authored_run_store.preparer

    def authored_factory(*, job_store, farm_scenario_service, gate_key):
        author = FarmAuthoringService(farm_scenario_service)
        completion = copy(original_preparer.release_store.verifier.completion)
        completion.review = FarmAuthoredReviewService(author)
        completion.jobs, completion.runs = job_store, farm_scenario_service.thermal.runs
        verifier = copy(original_preparer.release_store.verifier)
        verifier.completion = completion
        store = AuthoredReleaseStore(verifier)
        return AuthoredRunStore(AuthoredRunPreparer(author, store), gate_key)

    holds = service.scenario_store.holds
    farm = service.farm_scenario_service
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key, port=0,
        authored_run_gate_key=service.authored_run_store.gate_key,
        thermal_gate_key=service.runs._gate_key, market_hold_key=holds._key),
        dependencies(research_registry=farm.registry, bearer_registry=BearerRegistry(grants),
            market_source_factory=source_factory, market_scope_resolver=holds._scope_resolver,
            owned_fixture_registry=OwnedFixtureRegistry(ROOT),
            owned_research_contexts={next(iter(farm.registry._scopes)): 'context-1'},
            authored_run_store_factory=authored_factory))
    assert runtime.assessments.authored_run_store is runtime.authored_runs
    assert runtime.assessments.economic.authored_run_store is runtime.authored_runs
    server = runtime.service.server()
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    responses = []
    try:
        deadline = time.monotonic() + 15
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline
            time.sleep(0.01)
        port = server.servers[0].sockets[0].getsockname()[1]
        trust = ssl.create_default_context(cafile=str(cert))

        def call(path, *, bearer='owner', body=None):
            conn = http.client.HTTPSConnection('127.0.0.1', port, timeout=30, context=trust)
            try:
                headers = {} if bearer is None else {'Authorization': 'Bearer ' + tokens[bearer].decode()}
                if body is not None:
                    headers['Content-Type'] = 'application/json'
                started = time.monotonic()
                conn.request('POST' if body is not None else 'GET', path,
                    body=json.dumps(body) if body is not None else None, headers=headers)
                response = conn.getresponse()
                data = json.loads(response.read())
                elapsed = time.monotonic() - started
                assert response.getheader('cache-control') == 'no-store'
                responses.append((response.status, elapsed))
                return response.status, data
            finally:
                conn.close()

        assert call('/v1/assessments', body=intent, bearer=None)[0] == 401
        assert call('/v1/assessments', body=intent, bearer='denied')[0] == 403
        assert call('/v1/assessments', body=intent, bearer='foreign')[0] == 422
        status, admitted = call('/v1/assessments', body=intent)
        assert status == 202 and admitted['state'] == 'queued'
        assert call('/v1/assessments', body=intent) == (status, admitted)
        cli, _ = assessment_cli(service, tmp_path)
        lease = jobs.claim(300, tenant_id='tenant-1', job_id=admitted['job_id'], allowed_stages=('assessment',))
        outcome = cli._run_claimed(lease)
        assert outcome.state == 'hold' and outcome.decision_id, outcome.reason_code
        base = f"/v1/jobs/{admitted['job_id']}"
        status, job = call(base)
        assert status == 200 and job['state'] == 'hold'
        status, report = call(base + '/hold-report')
        assert status == 200 and report['missing_evidence'] == list(service.MISSING_EVIDENCE)
        assert report['missing_evidence_count'] == 6
        parent_base = '/v1/jobs/' + intent['run_job_id']
        status, selected = call(parent_base + '/authored-economic-input')
        assert status == 200 and selected['verification'] == 'requires_admission_recheck'
        assert selected['calculation_input']['thermal_job_id'] == intent['run_job_id']
        status, history = call(parent_base + '/authored-financial-history')
        assert status == 200 and history['verification'] == 'requires_current_read'
        assert history['run_id'] == selected['thermal_run']['run_id']
        assert {item['job']['job_id'] for item in history['items']} == {
            admitted['job_id'], intent['economic_job_id']}
        assert call('/v1/assessments', body=intent)[1]['state'] == 'hold'
        assert jobs.get_publication('tenant-1', admitted['job_id']) is None
        assert len(responses) == 10 and all(elapsed < 30 for _, elapsed in responses)
        print('authored_assessment_https=' + json.dumps({'responses': len(responses),
            'hold_count': report['missing_evidence_count'],
            'max_response_seconds': round(max(elapsed for _, elapsed in responses), 3),
            'client_timeout_seconds': 30, 'cli': 'synthetic_test_executable'}))
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        assert not thread.is_alive()
