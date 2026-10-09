"""Targeted claims and recovery must not consume neighboring model inputs."""

from uuid import uuid4
import pytest
from psycopg import sql

from test_jobs import pg_store


def test_claim_only_the_requested_tenant_stage_and_job(pg_store):
    earlier = pg_store.submit('tenant-a', 'simulation', {'fixture': 'other-model'}, 'earlier')
    target = pg_store.submit('tenant-a', 'simulation', {'fixture': 'thermal'}, 'target')
    assert pg_store.claim(60, tenant_id='tenant-b', allowed_stages=('simulation',), job_id=str(target['job_id'])) is None
    assert pg_store.claim(60, tenant_id='tenant-a', allowed_stages=('research',), job_id=str(target['job_id'])) is None
    claimed = pg_store.claim(60, tenant_id='tenant-a', allowed_stages=('simulation',), job_id=str(target['job_id']))
    assert claimed['job_id'] == target['job_id']
    assert pg_store.get_job('tenant-a', earlier['job_id'])['state'] == 'queued'


def test_targeted_recovery_leaves_other_expired_attempt_untouched(pg_store):
    other = pg_store.submit('tenant-a', 'simulation', {'fixture': 'other'}, 'other')
    target = pg_store.submit('tenant-a', 'simulation', {'fixture': 'target'}, 'target')
    first = pg_store.claim(60)
    second = pg_store.claim(60)
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second'").format(pg_store._table('jobs')))
    reclaimed = pg_store.claim(60, tenant_id='tenant-a', allowed_stages=('simulation',), job_id=str(target['job_id']))
    assert reclaimed['job_id'] == target['job_id'] and reclaimed['attempt'] == 2
    unchanged = pg_store.get_job('tenant-a', other['job_id'])
    assert unchanged['attempt_count'] == 1 and unchanged['state'] == 'simulating'
    assert len(pg_store.list_attempt_outcomes('tenant-a', target['job_id'])) == 1
    assert pg_store.list_attempt_outcomes('tenant-a', other['job_id']) == []


@pytest.mark.parametrize('value', [1, '', 'not-a-uuid', 'AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA', uuid4()])
def test_target_id_is_an_explicit_canonical_uuid(pg_store, value):
    with pytest.raises(ValueError, match='invalid claim job scope'):
        pg_store.claim(60, job_id=value)
