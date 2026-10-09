"""A signed authored candidate becomes only a scoped simulation intent."""

from dataclasses import replace
from pathlib import Path
import sys

from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.farm_authored_release_store import AuthoredReleaseStore
from app.farm_authored_run import AuthoredRunPreparer, build_authored_run_packet
from app.farm_authored_run_store import AuthoredRunStore
from app.farm_authored_simulation import (AuthoredSimulationHold,
    AuthoredSimulationService)
from app.job_store import JobStore
from test_farm_authored_run import _released_candidate
from login_database import login_database, login_scope


@pytest.mark.parametrize('login_scope', [{
    'authored_release_storage': True, 'authored_run_storage': True,
}], indirect=True)
def test_authored_admission_is_idempotent_and_current_evidence_bound(
        login_scope, tmp_path, monkeypatch):
    _, policy, dsns = login_scope
    scopes = {'metadata', 'simulation_create'}
    provider = lambda: {'authenticated': True, 'tenant_id': 'tenant-1',
                        'scopes': scopes}
    jobs = JobStore(dsns['authority'], policy.schema, tmp_path / 'artifacts',
        principal_provider=provider, runtime_identity=(policy, 'authority'),
        audit_runtime_grants=True)
    candidate, release = _released_candidate(tmp_path / 'release-root')
    packet = build_authored_run_packet(candidate, release, tenant='tenant-1',
        scenario_id='farm-1', revision='r1',
        registration_sha256=candidate.registration_sha256)
    release_store = object.__new__(AuthoredReleaseStore)
    release_store.jobs = jobs
    preparer = object.__new__(AuthoredRunPreparer)
    preparer.release_store = release_store
    preparer._binding = lambda: None
    preparer.prepare = lambda *args: packet
    store = object.__new__(AuthoredRunStore)
    store.preparer, store.jobs = preparer, jobs
    service = AuthoredSimulationService(preparer, store)
    args = ('tenant-1', '11111111-1111-4111-8111-111111111111',
            'farm-1', 'r1', candidate.registration_sha256, 'authored-intent')
    first = service.submit(*args)
    again = service.submit(*args)
    assert first['job_id'] == again['job_id'] and first['state'] == 'queued'
    with jobs.connect() as conn:
        assert conn.execute(sql.SQL("""
            SELECT count(*) AS n FROM {} WHERE tenant_id=%s AND stage='simulation'
        """).format(jobs._table('jobs')), ('tenant-1',)).fetchone()['n'] == 1
    with pytest.raises(AuthoredSimulationHold):
        service.submit('tenant-2', *args[1:])
    scopes.remove('simulation_create')
    with pytest.raises(AuthoredSimulationHold):
        service.submit(*args)
    scopes.add('simulation_create')
    preparer.prepare = lambda *unused: replace(packet, run_id='wrong')
    with pytest.raises(AuthoredSimulationHold):
        service.submit(*args)
    preparer.prepare = lambda *unused: packet
    original_submit = jobs.submit
    def change_during_insert(*items, **options):
        preparer.prepare = lambda *unused: replace(packet, run_id='wrong')
        return original_submit(*items, **options)
    monkeypatch.setattr(jobs, 'submit', change_during_insert)
    with pytest.raises(AuthoredSimulationHold):
        service.submit(*args[:-1], 'changed-during-insert')
    with jobs.connect() as conn:
        assert conn.execute(sql.SQL("""
            SELECT count(*) AS n FROM {} WHERE tenant_id=%s AND stage='simulation'
        """).format(jobs._table('jobs')), ('tenant-1',)).fetchone()['n'] == 1
