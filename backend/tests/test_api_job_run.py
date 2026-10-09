"""Completed thermal jobs discover their verified replay; synthetic evidence only."""

from copy import deepcopy
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import asyncio
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.jobs import canonical_input_bytes
from test_api_job_status import get, UnusedMarketResultStore
from test_api_thermal_run import UnusedMarketHoldStore
from test_thermal_simulation_worker import simulation_setup
from login_database import login_database, login_scope
from test_api_serve import tls_files


def application(setup):
    _, _, runs, jobs, _, _, principal, _ = setup
    return create_app(jobs, UnusedMarketHoldStore(), runs, UnusedMarketResultStore(),
                      principal_provider=lambda: principal)


def test_job_discovers_same_public_run_after_atomic_completion(simulation_setup):
    worker, _, _, _, job, _, principal, _ = simulation_setup
    app = application(simulation_setup)
    path = f"/v1/jobs/{job['job_id']}/run"
    assert get(app, path)[0] == 404
    result = worker.run_once(str(job['job_id']))
    status, summary = get(app, path)
    assert status == 200 and summary['run_id'] == result.run_id
    assert summary == get(app, f'/v1/runs/{result.run_id}')[1]
    assert summary['synthetic'] and summary['temporal_provenance'] == 'ex_post_replay'
    assert 'report_raw' not in summary and 'decision_id' not in summary and 'review_job_id' not in summary
    principal['tenant_id'] = 'tenant-b'
    assert get(app, path)[0] == 404


@pytest.mark.parametrize('scope', ['metadata', 'artifact', 'thermal_run_read'])
def test_required_scope_denied_before_store_reads(simulation_setup, monkeypatch, scope):
    _, _, _, jobs, job, _, principal, _ = simulation_setup
    principal['scopes'].remove(scope)
    def refuse(*_): raise AssertionError('unauthorized store read')
    monkeypatch.setattr(jobs, 'get_job', refuse)
    assert get(application(simulation_setup), f"/v1/jobs/{job['job_id']}/run")[0] == 403


@pytest.mark.parametrize('fault', ['publication', 'manifest_type', 'input', 'receipt_extra', 'receipt_review',
    'noncanonical', 'report_hash', 'trace_hash', 'context', 'missing_run'])
def test_inconsistent_completion_never_returns_a_run(simulation_setup, monkeypatch, fault):
    worker, _, runs, jobs, job, _, _, _ = simulation_setup
    result = worker.run_once(str(job['job_id']))
    if fault == 'publication':
        record = jobs.get_publication('tenant-a', job['job_id']) | {'attempt': 999}
        monkeypatch.setattr(jobs, 'get_publication', lambda *_: record)
    elif fault == 'manifest_type':
        record = jobs.get_publication('tenant-a', job['job_id'])
        record['manifest']['attempt'] = True
        monkeypatch.setattr(jobs, 'get_publication', lambda *_: record)
    elif fault == 'input':
        record = jobs.get_job('tenant-a', job['job_id']) | {'input_sha256': '0'*64}
        monkeypatch.setattr(jobs, 'get_job', lambda *_: record)
    elif fault.startswith('receipt') or fault == 'noncanonical':
        receipt = json.loads(jobs.read_artifact('tenant-a', job['job_id']))
        if fault == 'receipt_extra': receipt['not_public'] = 'never-display-this'
        if fault == 'receipt_review': receipt['review_job_id'] = '00000000-0000-0000-0000-000000000000'
        raw = (json.dumps(receipt, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
               if fault != 'noncanonical' else json.dumps(receipt).encode())
        record = jobs.get_publication('tenant-a', job['job_id'])
        record.update(artifact_sha256=sha256(raw).hexdigest(), artifact_size=len(raw))
        record['manifest']['artifact_sha256'] = record['artifact_sha256']
        monkeypatch.setattr(jobs, 'get_publication', lambda *_: record)
        monkeypatch.setattr(jobs, 'read_artifact', lambda *_: raw)
    else:
        stored = deepcopy(runs.get_run('tenant-a', result.run_id))
        if fault == 'report_hash': stored['report_raw'] = b'private corrupt report'
        if fault == 'trace_hash': stored['trace_raws'] = (b'private corrupt trace', stored['trace_raws'][1])
        if fault == 'context': stored['report']['decision_context_id'] = 'private wrong context'
        monkeypatch.setattr(runs, 'get_run', lambda *_: None if fault == 'missing_run' else stored)
    status, error = get(application(simulation_setup), f"/v1/jobs/{job['job_id']}/run")
    assert status == 503
    assert error == {'error': {'code': 'store_unavailable', 'message': 'Job Run unavailable'}}


def test_held_and_other_stage_jobs_have_no_run(simulation_setup):
    worker, publisher, _, jobs, job, data, _, _ = simulation_setup
    publisher.execution_verifier = lambda *_: False
    assert worker.run_once(str(job['job_id'])).state == 'hold'
    app = application(simulation_setup)
    assert get(app, f"/v1/jobs/{job['job_id']}/run")[0] == 404
    other = jobs.submit('tenant-a', 'collection', data, 'other-stage')
    assert get(app, f"/v1/jobs/{other['job_id']}/run")[0] == 404


def test_oversized_publication_is_rejected_before_artifact_read(simulation_setup, monkeypatch):
    worker, _, _, jobs, job, _, _, _ = simulation_setup
    assert worker.run_once(str(job['job_id'])).state == 'succeeded'
    record = jobs.get_publication('tenant-a', job['job_id']) | {'artifact_size': 4097}
    calls = []
    monkeypatch.setattr(jobs, 'get_publication', lambda *_: record)
    monkeypatch.setattr(jobs, 'read_artifact', lambda *_: calls.append('read'))
    assert get(application(simulation_setup), f"/v1/jobs/{job['job_id']}/run")[0] == 503
    assert calls == []


@pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'break_even_calculation': True}], indirect=True)
def test_fresh_api_runtime_resolves_persisted_completion_under_bearer_identity(simulation_setup, tls_files):
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerGrant, BearerRegistry, token_digest, current_principal
    from test_api_runtime import config, dependencies
    from test_http_identity import request
    worker, _, runs, jobs, job, _, _, _ = simulation_setup
    result = worker.run_once(str(job['job_id']))
    token = b'synthetic-job-run-bearer-'+b'r'*32
    now = datetime.now(timezone.utc)
    registry = BearerRegistry((BearerGrant(token_digest(token), 'tenant-a',
        frozenset({'metadata', 'artifact', 'thermal_run_read'}), now-timedelta(seconds=1), now+timedelta(minutes=5)),))
    cert, key, _ = tls_files
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key, thermal_gate_key=runs._gate_key),
        dependencies(bearer_registry=registry, context_verifier=runs._context_verifier,
                     release_verifier=runs._release_verifier))
    path = f"/v1/jobs/{job['job_id']}/run"
    assert asyncio.run(request(runtime.service.app, path=path))[0] == 401
    status, summary, headers = asyncio.run(request(runtime.service.app, path=path,
        headers=[(b'authorization', b'Bearer '+token), (b'x-tenant-id', b'tenant-b')]))
    assert status == 200 and summary['run_id'] == result.run_id
    assert headers[b'cache-control'] == b'no-store' and current_principal() is None
