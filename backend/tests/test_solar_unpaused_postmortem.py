"""Owned fixture postmortems must expose only stored metadata and stay read only."""
import json
from pathlib import Path

import psycopg
import pytest

from test_crop_greenhouse_solar_execution_query import (
    setup, worker_setup, producer_setup, authoring, profiles, login_database,
    original_login_scope, login_scope, query_cleanup, confirm, persisted_digest, forbid)
import test_crop_greenhouse_solar_execution_query as reference


@reference.reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
def test_owned_postmortem_reads_actual_checkpoint_without_calculation_or_mutation(setup, login_database, tmp_path, monkeypatch):
    import solar_unpaused_postmortem as model
    query, worker, job_id, raw, _ = setup
    lease = confirm(worker, job_id)
    worker.server.advance('tenant-1', raw, budget=2)
    accepted = worker.checkpoints.confirm('tenant-1', job_id,
        attempt=lease['attempt'], lease_token=lease['lease_token'])
    with psycopg.connect(login_database['admin']) as owner:
        data_directory = Path(owner.execute('SHOW data_directory').fetchone()[0])
    config = tmp_path/'cluster.private.json'
    config.write_text(json.dumps({'root':str(tmp_path), 'database':login_database,
        'private':'controlled_secret_never_export'}));config.chmod(0o600)
    before = persisted_digest(worker.jobs)
    connections = []; connect = psycopg.connect
    def observed(*args, **kwargs):
        conn = connect(*args, **kwargs);connections.append(conn);return conn
    with monkeypatch.context() as patch:
        calls = forbid(patch);patch.setattr(model.psycopg, 'connect', observed)
        result = model.read_stored_checkpoint(config, data_directory)
        with pytest.raises(ValueError):
            model.read_stored_checkpoint(config, data_directory.with_name('another-data-directory'))
        assert all(n == 0 for n in calls.values())
    assert connections and all(conn.closed for conn in connections)
    assert result['job']['state'] == 'simulating' and result['job']['attempt'] == 1
    expected = accepted['checkpoint']
    assert result['stored_checkpoint'] == {k:expected[k] for k in (
        'steps','planned_steps','status','computed_through_utc','publication_sequence')}
    assert result['transaction_read_only'] is True and result['owned_cluster_identity_verified'] is True
    assert result['transaction_isolation'] == 'repeatable read'
    assert result['rights_or_gate_approval'] is False and result['normal_execution_accepted'] is False
    encoded = json.dumps(result)
    assert all(value not in encoded for value in ('controlled_secret_never_export',
        login_database['admin'],str(tmp_path),'lease_token','input_bytes','tenant-1',job_id))
    assert persisted_digest(worker.jobs) == before


@pytest.mark.parametrize('skip', ['live_actor', 'original_normal_proof'])
def test_harness_skips_metadata_until_actors_stopped_and_only_on_failure(tmp_path, monkeypatch, skip):
    from types import SimpleNamespace
    import crop_greenhouse_solar_unpaused_smoke as harness
    import solar_unpaused_postmortem as metadata
    monkeypatch.setattr(metadata, 'read_stored_checkpoint', lambda *args:pytest.fail('unexpected fixture read'))
    if skip == 'original_normal_proof':
        (tmp_path/'unpaused-normal.private.json').write_text('{}')
    process = SimpleNamespace(poll=lambda:None if skip == 'live_actor' else -15)
    harness.collect_stopped_checkpoint(tmp_path, [(process,tmp_path/'api.private.py')], tmp_path/'data')
    assert not (tmp_path/'failure-checkpoint-diagnostics.json').exists()


def test_harness_collects_only_after_actual_process_exit(tmp_path, monkeypatch):
    import subprocess
    import sys
    import crop_greenhouse_solar_unpaused_smoke as harness
    import solar_unpaused_postmortem as metadata
    process = subprocess.Popen([sys.executable, '-B', '-c', 'pass'],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert process.wait(timeout=5) == 0
    calls = []
    def recorded(config, data):
        calls.append((config, data))
        return {'stored_checkpoint':{'steps':3}, 'normal_execution_accepted':False}
    monkeypatch.setattr(metadata, 'read_stored_checkpoint', recorded)
    monkeypatch.setenv('GITHUB_SHA', '1'*40)
    monkeypatch.setenv('GITHUB_RUN_ID', 'local-condition-test')
    harness.collect_stopped_checkpoint(tmp_path, [(process,tmp_path/'api.private.py')], tmp_path/'data')
    path = tmp_path/'failure-checkpoint-diagnostics.json'
    value = json.loads(path.read_bytes())
    assert calls == [(tmp_path/'cluster.private.json', tmp_path/'data')]
    assert value['actors_stopped_before_collection'] is True
    assert value['normal_execution_accepted'] is False and value['metadata']['stored_checkpoint']['steps'] == 3
    assert path.stat().st_mode & 0o777 == 0o400
