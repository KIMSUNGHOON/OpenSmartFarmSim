"""Stored synthetic release bytes stay immutable and require authority login."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import sys

import psycopg
from psycopg import errors, sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.farm_authored_release import DOMAIN
from app.farm_authored_release_store import (AuthoredReleaseStore,
    AuthoredReleaseStoreHold, AuthoredReleaseConflict)
from app.job_store import JobStore
from app.jobs import canonical_input_bytes
from app.runtime_login import connect_runtime
from app.runtime_roles import audit_runtime_roles
from test_cli_contracts import input_for, resolver
from test_cli_worker import _worker
from test_farm_authored_release import _fixture, _signed, _iso
from login_database import login_database, login_scope


@pytest.mark.parametrize('login_scope', [{'authored_release_storage': True}], indirect=True)
def test_signed_packet_storage_is_immutable_scoped_and_rechecked(login_scope, tmp_path):
    base, policy, dsns = login_scope
    def approved(job, value):
        return replace(resolver(job, value), allow_proceed=True, missing_evidence=())
    worker_jobs, worker = _worker(base, tmp_path, authority=approved)
    review_input = input_for('collection_review')
    review_input.update(decision_context_id='synthetic-release-context',
        decision_at_utc='2026-01-03T00:00:00Z', claim_mode='ex_post_replay',
        decision_time_kind='hypothetical')
    job = worker_jobs.submit('tenant-a', 'collection_review', review_input,
                             'synthetic-release-storage-test')
    worked = worker.run_once()
    assert worked.state == 'succeeded'
    with base.connect() as conn:
        assert audit_runtime_roles(conn, policy)['policy_version'] == (
            'runtime-authored-release-login-policy-v7')
    principal = lambda: {'authenticated': True, 'tenant_id': 'tenant-a',
                         'scopes': {'authored_release_write', 'authored_release_read'}}
    authority_jobs = JobStore(dsns['authority'], policy.schema, tmp_path / 'artifacts',
        principal_provider=principal, runtime_identity=(policy, 'authority'))
    service, proof, private, artifacts, _ = _fixture(tmp_path / 'release-root')
    proof = replace(proof, tenant_id='tenant-a', review_job_id=str(job['job_id']),
                    review_input_sha256=job['input_sha256'])
    service.completion.jobs = authority_jobs
    service.completion.verify = lambda *args: proof
    service.evidence_resolver = lambda tenant, ref: (
        artifacts.get(ref) if tenant == 'tenant-a' else None)
    store = AuthoredReleaseStore(service)
    packet = _signed(service, proof, private)
    stored = store.put('tenant-a', proof.review_job_id,
                       proof.registration_sha256, *packet)
    assert stored == store.get('tenant-a', proof.review_job_id,
                               proof.registration_sha256)
    assert stored == store.put('tenant-a', proof.review_job_id,
                               proof.registration_sha256, *packet)
    with base.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(base._table('authored_release_packets'))).fetchone()['n'] == 1
    for kind in ('request', 'worker', 'supervisor'):
        with connect_runtime(dsns[kind], policy, kind) as conn, pytest.raises(
                errors.InsufficientPrivilege):
            conn.execute(sql.SQL('SELECT * FROM {} LIMIT 0').format(
                base._table('authored_release_packets')))
    with base.connect() as conn, pytest.raises(psycopg.Error):
        conn.execute(sql.SQL("""
            UPDATE {} SET reviewer='different' WHERE tenant_id=%s AND review_job_id=%s
        """).format(base._table('authored_release_packets')),
            ('tenant-a', proof.review_job_id))
    with pytest.raises(AuthoredReleaseStoreHold):
        store.get('tenant-b', proof.review_job_id, proof.registration_sha256)
    changed = json.loads(packet[0])
    changed['issued_at_utc'] = _iso(datetime.now(timezone.utc) - timedelta(minutes=9))
    other_release = canonical_input_bytes(changed)
    with pytest.raises(AuthoredReleaseConflict):
        store.put('tenant-a', proof.review_job_id, proof.registration_sha256,
                  other_release, private.sign(DOMAIN + other_release),
                  packet[2], packet[3])
    service.completion.verify = lambda *args: replace(proof,
        registration_sha256='0' * 64)
    with pytest.raises(AuthoredReleaseStoreHold):
        store.get('tenant-a', proof.review_job_id, proof.registration_sha256)
    service.completion.verify = lambda *args: proof
    assert store.get('tenant-a', proof.review_job_id,
                     proof.registration_sha256) == stored
