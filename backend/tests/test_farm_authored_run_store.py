"""Authored Run table is an opt-in authority-only SQL boundary."""

from pathlib import Path
from dataclasses import replace
from hashlib import sha256
import json
import sys

import psycopg
from psycopg import errors, sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.runtime_login import connect_runtime
from app.runtime_roles import RuntimeLoginPolicy, RolePolicyHold, audit_runtime_roles
from app.farm_authored_release_store import AuthoredReleaseStore
from app.farm_authored_run import AuthoredRunPreparer, build_authored_run_packet
from app.farm_authored_run_store import AuthoredRunStore, AuthoredRunStoreHold
from app.job_store import JobStore
from app.jobs import canonical_input_bytes
from test_authored_thermal_candidate import pure
from test_cli_contracts import input_for, resolver
from test_cli_worker import _worker
from test_farm_authored_release import _fixture, _signed
from login_database import login_database, login_scope


def test_run_profile_requires_release_custody():
    with pytest.raises(RolePolicyHold):
        RuntimeLoginPolicy('project', 'owner', 'prefix', 'database',
            authored_run_storage=True)


@pytest.mark.parametrize('login_scope', [{
    'authored_release_storage': True, 'authored_run_storage': True,
}], indirect=True)
def test_authored_run_table_has_only_authority_login(login_scope):
    base, policy, dsns = login_scope
    with base.connect() as conn:
        audit = audit_runtime_roles(conn, policy)
        assert audit['policy_version'] == 'runtime-authored-run-login-policy-v8'
    with connect_runtime(dsns['authority'], policy, 'authority') as conn:
        conn.execute(sql.SQL('SELECT * FROM {} LIMIT 0').format(
            base._table('authored_thermal_runs')))
    for kind in ('request', 'worker', 'supervisor'):
        with connect_runtime(dsns[kind], policy, kind) as conn, pytest.raises(
                errors.InsufficientPrivilege):
            conn.execute(sql.SQL('SELECT * FROM {} LIMIT 0').format(
                base._table('authored_thermal_runs')))


def _authored_store_setup(login_scope, tmp_path):
    base, policy, dsns = login_scope
    approved = lambda job, value: replace(resolver(job, value),
        allow_proceed=True, missing_evidence=())
    worker_jobs, worker = _worker(base, tmp_path, authority=approved)
    review_input = input_for('collection_review')
    review_input.update(decision_context_id='synthetic-authored-run-context',
        decision_at_utc='2026-01-03T00:00:00Z', claim_mode='ex_post_replay',
        decision_time_kind='hypothetical')
    review = worker_jobs.submit('tenant-a', 'collection_review',
        review_input, 'authored-run-review-test')
    assert worker.run_once().state == 'succeeded'
    scopes = {'metadata', 'artifact', 'simulation_execute', 'authored_run_publish',
              'authored_run_read',
              'authored_release_read', 'authored_release_write'}
    provider = lambda: {'authenticated': True, 'tenant_id': 'tenant-a',
                        'scopes': scopes}
    jobs = JobStore(dsns['authority'], policy.schema, tmp_path / 'artifacts',
        principal_provider=provider, runtime_identity=(policy, 'authority'),
        audit_runtime_grants=True)
    candidate = pure()
    trace = json.loads(candidate.trace_raws[0])
    verifier, proof, reviewer, artifacts, _ = _fixture(tmp_path / 'release-root')
    proof = replace(proof, tenant_id='tenant-a',
        review_job_id=str(review['job_id']),
        review_input_sha256=review['input_sha256'],
        registration_sha256=candidate.registration_sha256,
        farm_sha256=trace['farm_sha256'],
        numeric_input_sha256=candidate.numeric_input_sha256,
        binding_sha256=trace['binding_sha256'],
        base_snapshot_id=trace['base_snapshot_id'],
        base_source_sha256=trace['base_source_sha256'],
        candidate_id=candidate.candidate_id,
        code_sha256=candidate.code_sha256,
        trace_sha256=candidate.trace_sha256)
    verifier.completion.jobs = jobs
    verifier.completion.verify = lambda *args: proof
    verifier.evidence_resolver = lambda tenant, ref: (
        artifacts.get(ref) if tenant == 'tenant-a' else None)
    release_store = AuthoredReleaseStore(verifier)
    released = release_store.put('tenant-a', proof.review_job_id,
        proof.registration_sha256, *_signed(verifier, proof, reviewer))
    packet = build_authored_run_packet(candidate, released, tenant='tenant-a',
        scenario_id='farm-1', revision='r1',
        registration_sha256=candidate.registration_sha256)
    preparer = object.__new__(AuthoredRunPreparer)
    preparer.release_store = release_store
    preparer._binding = lambda: None
    preparer.prepare = lambda *args: packet
    store = AuthoredRunStore(preparer, b'synthetic-test-gate-key-' + b'0' * 32)
    return base, jobs, proof, packet, preparer, store


@pytest.mark.parametrize('login_scope', [{
    'authored_release_storage': True, 'authored_run_storage': True,
}], indirect=True)
def test_run_insert_requires_same_transaction_job_publication(login_scope, tmp_path):
    base, jobs, proof, packet, preparer, store = _authored_store_setup(
        login_scope, tmp_path)
    simulation = jobs.submit('tenant-a', 'simulation', {
        'input_version': 'authored-thermal-simulation-input-v1',
        'tenant_id': 'tenant-a', 'scenario_id': 'farm-1',
        'scenario_revision': 'r1',
        'review_job_id': proof.review_job_id,
        'registration_sha256': proof.registration_sha256},
        'authored-run-simulation-test')
    lease = jobs.claim(300, allowed_stages=('simulation',), tenant_id='tenant-a',
        job_id=str(simulation['job_id']))
    raw = jobs.read_input('tenant-a', simulation['job_id'], lease['attempt'],
                          lease['lease_token'])
    args = ('tenant-a', simulation['job_id'], lease['attempt'],
            lease['lease_token'], raw, proof.review_job_id,
            'farm-1', 'r1', proof.registration_sha256, packet)
    with jobs.connect() as conn:
        with pytest.raises(AuthoredRunStoreHold):
            store._publish_in_transaction(conn, *args[:-1], replace(packet,
                trace_raws=(packet.trace_raws[0] + b' ', packet.trace_raws[1])))
    with pytest.raises(psycopg.Error):
        with jobs.connect() as conn:
            store._publish_in_transaction(conn, *args)
    with jobs.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
            jobs._table('authored_thermal_runs'))).fetchone()['n'] == 0
    publication, _ = store._publication('tenant-a', simulation['job_id'],
        lease['attempt'], proof.review_job_id, 'farm-1', 'r1',
        proof.registration_sha256, packet)
    artifact = canonical_input_bytes({
        'receipt_version': 'authored-thermal-simulation-result-v1',
        'status': 'accepted',
        'claim_scope': 'synthetic_thermal_replay_only',
        'run_id': packet.run_id,
        'review_job_id': proof.review_job_id,
        'registration_sha256': proof.registration_sha256,
        'trace_sha256': list(packet.trace_sha256),
        'preparation_sha256': sha256(packet.report_raw).hexdigest(),
        'publication_sha256': sha256(publication).hexdigest()})
    digest = sha256(artifact).hexdigest()
    jobs._durable_artifact(artifact, digest)
    with jobs.connect() as conn:
        stored = store._publish_in_transaction(conn, *args)
        conn.execute(sql.SQL("""
            UPDATE {} SET state='succeeded', lease_token=NULL, lease_until=NULL
            WHERE tenant_id=%s AND job_id=%s
        """).format(jobs._table('jobs')), ('tenant-a', simulation['job_id']))
        jobs._insert_publication(conn, 'tenant-a', simulation['job_id'],
            lease['attempt'], None, digest, len(artifact), {
                'schema_version': '1', 'stage': 'simulation',
                'input_sha256': simulation['input_sha256'],
                'artifact_sha256': digest, 'run_id': packet.run_id})
        jobs._event(conn, 'tenant-a', simulation['job_id'], 'succeeded',
                    lease['attempt'])
        jobs._outcome(conn, 'tenant-a', simulation['job_id'], lease['attempt'],
                      'succeeded', termination_reason='completed')
    assert stored['run_id'] == packet.run_id
    assert store.get_run('tenant-a', packet.run_id)['trace_raws'] == packet.trace_raws
    assert store.get_run('tenant-b', packet.run_id) is None
    catalog = store.list_refs('tenant-a', limit=1)
    assert catalog['next_cursor'] is None
    assert catalog['items'] == [{
        'run_id': packet.run_id, 'simulation_job_id': simulation['job_id'],
        'recorded_at': catalog['items'][0]['recorded_at'],
        'verification': 'requires_current_read'}]
    with pytest.raises(PermissionError):
        store.list_refs('tenant-b')
    assert store.list_refs('tenant-a', before_recorded_at=catalog['items'][0]['recorded_at'],
        before_run_id=packet.run_id)['items'] == []
    with pytest.raises(ValueError):
        store.list_refs('tenant-a', before_run_id=packet.run_id)
    wrong_gate = AuthoredRunStore(preparer, b'different-synthetic-gate-key-' + b'1' * 32)
    with pytest.raises(AuthoredRunStoreHold):
        wrong_gate.get_run('tenant-a', packet.run_id)
    with jobs.connect() as conn:
        row = conn.execute(sql.SQL('SELECT * FROM {}').format(
            jobs._table('authored_thermal_runs'))).fetchone()
        assert row['trace0_raw'] == packet.trace_raws[0]
        assert row['trace1_sha256'] == packet.trace_sha256[1]
        assert row['publication_sha256'] == stored['publication_sha256']
    with base.connect() as conn, pytest.raises(psycopg.Error):
        conn.execute(sql.SQL("UPDATE {} SET scenario_revision='r2'").format(
            jobs._table('authored_thermal_runs')))
    preparer.prepare = lambda *args: None
    assert store.list_refs('tenant-a')['items'][0]['verification'] == 'requires_current_read'
    with pytest.raises(AuthoredRunStoreHold):
        store.get_run('tenant-a', packet.run_id)
    preparer._binding = lambda: (_ for _ in ()).throw(ValueError('unavailable'))
    with pytest.raises(AuthoredRunStoreHold):
        store.list_refs('tenant-a')
