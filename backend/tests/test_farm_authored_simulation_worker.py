"""A leased authored simulation closes with its immutable Run or holds."""

import json
from hashlib import sha256
from pathlib import Path
import sys

from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.farm_authored_run import AuthoredRunHold
from app.farm_authored_simulation import AuthoredSimulationService
from app.farm_authored_simulation_worker import AuthoredSimulationWorker
from test_farm_authored_run_store import _authored_store_setup
from login_database import login_database, login_scope


PROFILE = [{'authored_release_storage': True, 'authored_run_storage': True}]


def _admit(login_scope, tmp_path):
    _, jobs, proof, packet, preparer, store = _authored_store_setup(
        login_scope, tmp_path)
    jobs.principal_provider()['scopes'].add('simulation_create')
    service = AuthoredSimulationService(preparer, store)
    job = service.submit('tenant-a', proof.review_job_id, 'farm-1', 'r1',
                         proof.registration_sha256, 'authored-worker-test')
    worker = AuthoredSimulationWorker(store, tenant_id='tenant-a')
    return jobs, proof, packet, preparer, store, job, worker


def _count(jobs):
    with jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
            jobs._table('authored_thermal_runs'))).fetchone()['n']


@pytest.mark.parametrize('login_scope', PROFILE, indirect=True)
def test_worker_commits_exact_run_receipt_and_job_once(login_scope, tmp_path):
    jobs, proof, packet, _, store, job, worker = _admit(login_scope, tmp_path)
    neighbor = jobs.submit('tenant-a', 'simulation', {
        'input_version': 'thermal-simulation-input-v1', 'different': True},
        'fixed-fixture-neighbor')
    assert worker.run_once(str(neighbor['job_id'])) is None
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'succeeded' and result.run_id == packet.run_id
    assert worker.run_once(str(job['job_id'])) is None
    assert _count(jobs) == 1
    assert jobs.get_job('tenant-a', job['job_id'])['state'] == 'succeeded'
    assert jobs.get_job('tenant-a', neighbor['job_id'])['state'] == 'queued'
    run = store.get_run('tenant-a', packet.run_id)
    receipt_raw = jobs.read_artifact('tenant-a', job['job_id'])
    receipt = json.loads(receipt_raw)
    assert run['trace_raws'] == packet.trace_raws
    assert receipt['run_id'] == run['run_id']
    assert receipt['publication_sha256'] == sha256(run['report_raw']).hexdigest()
    assert jobs.get_publication('tenant-a', job['job_id'])['artifact_sha256'] == (
        sha256(receipt_raw).hexdigest())
    assert [row['state'] for row in jobs.list_attempt_outcomes(
        'tenant-a', job['job_id'])] == ['succeeded']


@pytest.mark.parametrize('login_scope', PROFILE, indirect=True)
def test_cancel_after_preparation_has_no_run(login_scope, tmp_path):
    jobs, _, packet, preparer, _, job, worker = _admit(login_scope, tmp_path)
    jobs.principal_provider()['scopes'].add('cancel')
    def cancel(*args):
        assert jobs.cancel('tenant-a', job['job_id'])
        return packet
    preparer.prepare = cancel
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'canceled' and _count(jobs) == 0
    assert jobs.get_publication('tenant-a', job['job_id']) is None


@pytest.mark.parametrize('login_scope', PROFILE, indirect=True)
def test_missing_current_release_holds_without_run(login_scope, tmp_path):
    jobs, _, _, preparer, _, job, worker = _admit(login_scope, tmp_path)
    def revoked(*args):
        raise AuthoredRunHold('test revoked release')
    preparer.prepare = revoked
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'hold' and result.reason_code == 'authored_run_hold'
    assert _count(jobs) == 0
    assert jobs.get_publication('tenant-a', job['job_id']) is None


@pytest.mark.parametrize('login_scope', PROFILE, indirect=True)
def test_release_change_during_publication_holds_without_run(login_scope,
        tmp_path):
    jobs, _, packet, preparer, _, job, worker = _admit(login_scope, tmp_path)
    calls = 0
    def changes(*args):
        nonlocal calls
        calls += 1
        if calls == 1:
            return packet
        raise AuthoredRunHold('test release changed before commit')
    preparer.prepare = changes
    result = worker.run_once(str(job['job_id']))
    assert calls == 2 and result.state == 'hold'
    assert _count(jobs) == 0
    assert jobs.get_publication('tenant-a', job['job_id']) is None


@pytest.mark.parametrize('login_scope', PROFILE, indirect=True)
def test_error_after_run_insert_rolls_back_and_records_attempt(login_scope,
        tmp_path, monkeypatch):
    jobs, _, _, _, store, job, worker = _admit(login_scope, tmp_path)
    original = store._publish_in_transaction
    def break_after_insert(*args):
        original(*args)
        raise RuntimeError('synthetic process failure')
    monkeypatch.setattr(store, '_publish_in_transaction', break_after_insert)
    result = worker.run_once(str(job['job_id']))
    assert result.state in ('queued', 'unclosed')
    assert _count(jobs) == 0
    assert jobs.get_publication('tenant-a', job['job_id']) is None


@pytest.mark.parametrize('login_scope', PROFILE, indirect=True)
def test_expired_lease_after_run_insert_rolls_back(login_scope, tmp_path,
        monkeypatch):
    jobs, _, _, _, store, job, worker = _admit(login_scope, tmp_path)
    original = store._publish_in_transaction
    def expire_after_insert(*args):
        stored = original(*args)
        conn = args[0]
        conn.execute(sql.SQL("""
            UPDATE {} SET lease_until=clock_timestamp()-interval '1 second'
            WHERE tenant_id=%s AND job_id=%s
        """).format(jobs._table('jobs')), ('tenant-a', job['job_id']))
        return stored
    monkeypatch.setattr(store, '_publish_in_transaction', expire_after_insert)
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'unclosed' and result.reason_code == (
        'authored_simulation_lease_lost')
    assert _count(jobs) == 0
    assert jobs.get_publication('tenant-a', job['job_id']) is None


@pytest.mark.parametrize('login_scope', PROFILE, indirect=True)
def test_invalid_authored_input_is_fatal_without_run(login_scope, tmp_path):
    jobs, _, _, _, _, _, worker = _admit(login_scope, tmp_path)
    bad = jobs.submit('tenant-a', 'simulation', {
        'input_version': 'authored-thermal-simulation-input-v1',
        'tenant_id': 'tenant-a', 'unexpected': True}, 'bad-authored-input')
    result = worker.run_once(str(bad['job_id']))
    assert result.state == 'failed'
    assert result.reason_code == 'authored_simulation_input_rejected'
    assert _count(jobs) == 0
