"""Actual SCRAM reads of accepted, immutable, nonterminal joint pages."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from app import crop_climate_joint_prefix as model
from test_crop_climate_joint_execution_query import (
    setup as progress_setup, worker_setup, producer_setup as original_producer_setup, authoring, farm_setup,
    profiles, login_database, original_login_scope, login_scope, query_cleanup)
import test_crop_climate_joint_execution_query as reference

pytestmark = [reference.reference.pytestmark, pytest.mark.usefixtures('query_cleanup')]


@pytest.fixture
def producer_setup(authoring, tmp_path, profiles, request, monkeypatch):
    original = original_producer_setup.__wrapped__
    if getattr(request, 'param', None) != 'dense':
        return original(authoring, tmp_path, profiles, request, monkeypatch)
    producer = reference.reference.producer
    case = deepcopy(producer.reference.inputs.reference.reference.CASES[6])
    case.update(step_count=64, output_steps=list(range(65)))
    packet = producer.reference.inputs.packet
    with monkeypatch.context() as patch:
        patch.setattr(producer.reference.inputs, 'packet', lambda directory, profiles, origin=None: packet(directory, profiles, case, origin))
        return original(authoring, tmp_path, profiles, request, monkeypatch)


@pytest.fixture
def setup(progress_setup):
    query, worker, job_id, raw, value = progress_setup
    return model.JointExecutionPrefixQuery(query), worker, job_id, raw, value


def save(name, value):
    root = os.environ.get('OSSF_JOINT_PREFIX_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400)
            json.dump(value, f, sort_keys=True, indent=2)
            f.flush(); os.fsync(f.fileno())


def read(query, job_id, **kw):
    record = query.read('tenant-1', job_id, **kw)
    assert type(record) is model.PrefixRead
    assert sha256(record.payload_raw).hexdigest() == record.payload_sha256
    result = json.loads(record.payload_raw)
    assert record.payload_raw == model.storage._canonical(result) and len(record.payload_raw) <= model.MAX_READ_BYTES
    assert result['version'] == model.VERSION and result['G0_G4'] == 'not_assessed'
    return result


def selector(result):
    return {k: result['selection']['checkpoint'][k] for k in ('publication_sequence', 'head_sha256', 'proof_sha256')}


def advance(worker, job_id, raw, lease, budget):
    progress = json.loads(worker.server.advance('tenant-1', raw, budget=budget))
    accepted = worker.checkpoints.confirm('tenant-1', job_id, attempt=lease['attempt'], lease_token=lease['lease_token'])
    return progress, accepted


def writable(value):
    value[4]['scopes'].update({'simulation_execute', 'crop_result_write'})


def test_running_original_pages_and_sparse_utc(setup, monkeypatch):
    query, worker, job_id, raw, value = setup
    c = model.custody.continuation; ctx = value[2][2]._context
    expected = c.advance_chunk(ctx, c.start(ctx), 128)
    lease = reference.confirm(worker, job_id)
    progress, accepted = advance(worker, job_id, raw, lease, 8)
    assert progress['status'] == 'yielded' and progress['steps'] == 7
    reference.readonly(value)
    before = reference.persisted_digest(worker.jobs); fd = len(os.listdir('/proc/self/fd'))
    durations = []; page_hashes = {}; page_bytes = {}; packet_bytes = {}
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch)
        began = time.monotonic(); summary = read(query, job_id); durations.append(time.monotonic()-began)
        packet_bytes['summary'] = len(model.storage._canonical(summary))
        pin = selector(summary)
        assert summary['job']['state'] == 'simulating' and summary['prefix_status'] == 'accepted'
        assert summary['selection']['checkpoint'] == accepted['checkpoint']
        assert summary['selection']['checkpoint_recorded_at'] == model.execution._utc(accepted['recorded_at'])
        assert summary['selection']['checkpoint_attempt'] == lease['attempt']
        for kind in ('samples', 'events'):
            began = time.monotonic(); data = read(query, job_id, selector=pin, view=kind); durations.append(time.monotonic()-began)
            page = data['page']; rows = [r for r in expected[kind] if r['step_index'] <= progress['steps']]
            assert model.execution._same([r['value'] for r in page['records']], rows)
            assert [r['time']['at'] for r in page['records']] == [model.custody.clock.at_index(value[2][2], r['step_index']) for r in rows]
            assert data['selection'] == summary['selection'] and data['summary'] is None
            assert page['total'] == progress['counts'][kind] == len(rows) and page['next_offset'] is None
            page_hashes[kind] = sha256(model.storage._canonical(page)).hexdigest()
            page_bytes[kind] = len(model.storage._canonical(page))
            packet_bytes[kind] = len(model.storage._canonical(data))
            end = read(query, job_id, selector=pin, view=kind, start=page['total'])['page']
            assert end['records'] == [] and end['next_offset'] is None
        assert summary['selection']['checkpoint']['computed_through_utc'] == progress['times']['last_confirmed']['at']
        assert summary['summary']['last_sample_utc'] < progress['times']['last_confirmed']['at']
        assert all(n == 0 for n in calls.values())
    assert reference.persisted_digest(worker.jobs) == before and len(os.listdir('/proc/self/fd')) == fd
    with worker.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    save('running', {'actual_scram': True, 'steps': 7, 'counts': progress['counts'], 'selector': pin,
        'computed_through_utc': progress['times']['last_confirmed']['at'], 'summary': summary['summary'],
        'original_values_and_UTC': True, 'page_sha256': page_hashes, 'read_seconds': durations,
        'page_bytes': page_bytes, 'internal_packet_bytes': packet_bytes,
        'calls': calls, 'DB_unchanged': True, 'FD_unchanged': True})


def test_older_accepted_after_private_and_confirmed_tails_retry_and_fresh(setup, tmp_path, monkeypatch):
    query, worker, job_id, raw, value = setup
    lease = reference.confirm(worker, job_id)
    progress, first = advance(worker, job_id, raw, lease, 2)
    pin = {k: first['checkpoint'][k] for k in ('publication_sequence', 'head_sha256', 'proof_sha256')}
    private = json.loads(worker.server.advance('tenant-1', raw, budget=2))
    unaccepted = {'publication_sequence': 2, **{k: private[k] for k in ('head_sha256', 'proof_sha256')}}
    reference.readonly(value)
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch)
        old = read(query, job_id)
        assert selector(old) == pin and old['selection']['checkpoint']['counts'] == progress['counts']
        assert json.loads(query.query.read('tenant-1', job_id))['checkpoint_status'] == 'unavailable'
        with pytest.raises(model.JointPrefixSelectionConflict):
            query.read('tenant-1', job_id, selector=unaccepted, view='samples')
        assert all(n == 0 for n in calls.values())
    writable(value)
    second = worker.checkpoints.confirm('tenant-1', job_id, attempt=1, lease_token=lease['lease_token'])
    reference.reference.expire(worker, job_id); lease = reference.confirm(worker, job_id)
    duplicate = worker.checkpoints.confirm('tenant-1', job_id, attempt=lease['attempt'], lease_token=lease['lease_token'])
    assert duplicate == second and lease['attempt'] == 2
    reference.readonly(value); before = reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch)
        prior = read(query, job_id, selector=pin)
        assert prior['selection'] == old['selection'] and prior['summary'] == old['summary']
        assert prior['job']['attempt_count'] == 2 and prior['selection']['checkpoint_attempt'] == 1
        latest = read(query, job_id)
        assert latest['selection']['checkpoint']['publication_sequence'] == 2
        assert latest['selection']['checkpoint_recorded_at'] == model.execution._utc(second['recorded_at'])
        page = read(query, job_id, selector=pin, view='samples')['page']
        assert page['total'] == progress['counts']['samples']
        assert all(n == 0 for n in calls.values())
    pack = reference.reference.producer.fresh_pack(tmp_path, value, worker.server.inspect('tenant-1', raw), worker.server)
    p = json.loads(pack.read_bytes()); p.update(job_id=job_id, phase='reader', selector=pin, expected=prior)
    pack.write_text(json.dumps(p))
    script = reference.reference.FRESH_WORKER.split('with MonkeyPatch.context()')[0] + '''
import test_crop_climate_joint_execution_query as q
from app import crop_climate_joint_prefix as m
prefix=m.JointExecutionPrefixQuery(q.model.JointExecutionQuery(checkpoint_store,result_store))
before=q.persisted_digest(jobs)
with MonkeyPatch.context() as patch:
 calls=q.forbid(patch);record=prefix.read('tenant-1',p['job_id'],selector=p['selector'])
 actual=json.loads(record.payload_raw);expected=p['expected'];actual.pop('observed_at');expected.pop('observed_at')
 assert q.model._same(actual,expected) and all(n==0 for n in calls.values())
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
assert q.persisted_digest(jobs)==before
print(json.dumps({'actual_scram':True,'same_original_record_except_observation':True,'calls':calls,'DB_unchanged':True}))
'''
    try:
        child = subprocess.run([sys.executable, '-B', '-c', script, str(pack)], capture_output=True,
            stdin=subprocess.DEVNULL, timeout=120, env=dict(os.environ, PYTHONPATH=reference.reference.producer.FRESH_PYTHONPATH))
        assert child.returncode == 0, child.stderr.decode()
        fresh = json.loads(child.stdout)
    finally:
        pack.unlink(); (tmp_path/'proof.private.json').unlink()
    assert reference.persisted_digest(worker.jobs) == before
    save('older', {'old_selector': pin, 'new_publication_sequence': 2, 'private_tail_not_adopted': True,
        'earliest_attempt_and_time_preserved': True, 'calls': calls, 'fresh': fresh, 'DB_unchanged': True})


def test_signed_rollback_behind_latest_acceptance_rejects_old_selector(setup, monkeypatch):
    query, worker, job_id, raw, value = setup
    lease = reference.confirm(worker, job_id); _, first = advance(worker, job_id, raw, lease, 2)
    _, artifact, _ = reference.reference.producer.locations(worker.server, raw)
    path = artifact/'HEAD'; first_head = path.read_bytes()
    pin = {k: first['checkpoint'][k] for k in ('publication_sequence', 'head_sha256', 'proof_sha256')}
    _, second = advance(worker, job_id, raw, lease, 2)
    latest_head = path.read_bytes(); mode = path.stat().st_mode & 0o777
    assert first_head != latest_head and second['checkpoint']['publication_sequence'] == 2
    reference.readonly(value); before = reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch)
        assert selector(read(query, job_id, selector=pin)) == pin
        try:
            path.chmod(0o600); path.write_bytes(first_head); path.chmod(mode)
            for chosen in (None, pin):
                with pytest.raises(model.JointPrefixHold): query.read('tenant-1', job_id, selector=chosen)
        finally:
            path.chmod(0o600); path.write_bytes(latest_head); path.chmod(mode)
        assert selector(read(query, job_id, selector=pin)) == pin
        assert read(query, job_id)['selection']['checkpoint'] == second['checkpoint']
        assert all(n == 0 for n in calls.values())
    assert reference.persisted_digest(worker.jobs) == before
    save('rollback', {'valid_signed_rollback_rejected_for_latest_and_old_selector': True,
        'old_selector_works_after_HEAD_restored': True, 'calls': calls, 'DB_unchanged': True})


def test_ready_has_no_stored_sample_or_invented_time(setup, monkeypatch):
    query, worker, job_id, raw, value = setup
    lease = reference.confirm(worker, job_id)
    def stop(*a, **kw):
        raise RuntimeError('owned fixture stop after signed initialization')
    with monkeypatch.context() as patch:
        patch.setattr(model.custody.continuation, 'advance_chunk', stop)
        with pytest.raises(model.custody.JointCustodyHold):
            worker.server.advance('tenant-1', raw, budget=1)
    accepted = worker.checkpoints.confirm('tenant-1', job_id, attempt=1, lease_token=lease['lease_token'])
    assert accepted['checkpoint']['status'] == 'ready'
    reference.readonly(value); before = reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch); result = read(query, job_id)
        assert result['summary'] == {'counts': {'samples': 0, 'events': 0}, 'last_sample_utc': None, 'last_event_utc': None}
        assert result['selection']['checkpoint']['computed_through_utc'] is None
        for kind in ('samples', 'events'):
            page = read(query, job_id, selector=selector(result), view=kind)['page']
            assert page['total'] == 0 and page['records'] == [] and page['next_offset'] is None
        assert all(n == 0 for n in calls.values())
    assert reference.persisted_digest(worker.jobs) == before
    save('ready', {'signed_initialization_interrupted_before_first_chunk': True,
        'computed_and_sample_UTC_null': True, 'sample_event_rows': 0, 'calls': calls, 'DB_unchanged': True})


@pytest.mark.parametrize('producer_setup', ['dense'], indirect=True)
def test_dense_64_row_page_terminal_checkpoint_before_publication(setup, monkeypatch):
    query, worker, job_id, raw, value = setup
    c = model.custody.continuation; ctx = value[2][2]._context
    expected = c.advance_chunk(ctx, c.start(ctx), 128)
    assert expected['status'] == 'completed' and len(expected['samples']) == 65
    lease = reference.confirm(worker, job_id)
    progress, first = advance(worker, job_id, raw, lease, 64)
    assert progress['status'] == 'yielded' and progress['counts']['samples'] == 64
    progress, final = advance(worker, job_id, raw, lease, 1)
    assert progress['status'] == 'completed' and progress['artifact_sha256'] is not None
    reference.readonly(value); before = reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch); summary = read(query, job_id); pin = selector(summary)
        assert summary['job']['state'] == 'simulating' and summary['prefix_status'] == 'accepted'
        pages = [read(query, job_id, selector=pin, view='samples', start=i)['page'] for i in (0, 64)]
        assert [len(p['records']) for p in pages] == [64, 1] and [p['next_offset'] for p in pages] == [64, None]
        rows = [r for p in pages for r in p['records']]
        assert model.execution._same([r['value'] for r in rows], expected['samples'])
        assert [r['time']['at'] for r in rows] == [model.custody.clock.at_index(value[2][2], r['step_index']) for r in expected['samples']]
        old_pin = {k: first['checkpoint'][k] for k in pin}
        assert read(query, job_id, selector=old_pin, view='samples')['page']['total'] == 64
        assert all(n == 0 for n in calls.values())
    assert reference.persisted_digest(worker.jobs) == before
    assert reference.reference.rows(worker, job_id, 'job_publications') == []
    save('dense', {'original_sample_count': 65, 'page_counts': [64, 1], 'same_original_values_UTC': True,
        'page_bytes': [len(model.storage._canonical(p)) for p in pages],
        'terminal_checkpoint_is_not_job_completion': True, 'no_result_publication': True, 'calls': calls, 'DB_unchanged': True})


def test_current_scopes_review_rights_and_late_revocation(setup, monkeypatch):
    query, worker, job_id, raw, value = setup
    lease = reference.confirm(worker, job_id); advance(worker, job_id, raw, lease, 2)
    reference.readonly(value); principal, rights = value[4:]; before = reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch)
        for scope in ('metadata', 'crop_result_read'):
            principal['scopes'].remove(scope)
            with pytest.raises(PermissionError): query.read('tenant-1', job_id)
            principal['scopes'].add(scope)
        rights.allowed = False
        with pytest.raises(model.JointPrefixHold): query.read('tenant-1', job_id)
        rights.allowed = True
        review = value[2][3]; original_status = review['status']; review['status'] = 'revoked'
        with pytest.raises(model.JointPrefixHold): query.read('tenant-1', job_id)
        review['status'] = original_status
        original = query._accepted
        def revoke(*a, **kw):
            result = original(*a, **kw); rights.allowed = False; return result
        patch.setattr(query, '_accepted', revoke)
        with pytest.raises(model.JointPrefixHold): query.read('tenant-1', job_id)
        rights.allowed = True
        assert all(n == 0 for n in calls.values())
    assert read(query, job_id)['prefix_status'] == 'accepted'
    assert reference.persisted_digest(worker.jobs) == before
    save('rights', {'scope_rejections': 2, 'review_revoked_rejected': True, 'source_rights_revoked_rejected': True,
        'late_revocation_rejected': True, 'read_without_write_or_execute_scope': True, 'calls': calls, 'DB_unchanged': True})


def test_cancel_request_and_ack_close_prefix_without_result(setup, monkeypatch):
    query, worker, job_id, raw, value = setup
    lease = reference.confirm(worker, job_id); _, first = advance(worker, job_id, raw, lease, 2)
    pin = {k: first['checkpoint'][k] for k in ('publication_sequence', 'head_sha256', 'proof_sha256')}
    assert worker.jobs.cancel('tenant-1', job_id)
    reference.readonly(value); before = reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch); pending = read(query, job_id)
        assert pending['prefix_status'] == 'closed' and pending['cancel_requested'] is True and pending['job']['state'] == 'simulating'
        assert all(pending[k] is None for k in ('selection', 'binding', 'manifest', 'time_binding', 'summary', 'page'))
        with pytest.raises(model.JointPrefixSelectionConflict): query.read('tenant-1', job_id, selector=pin, view='samples')
        assert all(n == 0 for n in calls.values())
    assert reference.persisted_digest(worker.jobs) == before
    writable(value)
    assert worker.jobs.ack_cancel('tenant-1', job_id, 1, lease['lease_token'], termination_reason='canceled_by_request')
    reference.readonly(value); before = reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch); canceled = read(query, job_id)
        assert canceled['prefix_status'] == 'closed' and canceled['job']['state'] == 'canceled' and canceled['page'] is None
        assert all(n == 0 for n in calls.values())
    assert reference.persisted_digest(worker.jobs) == before
    assert reference.reference.rows(worker, job_id, 'job_publications') == []
    save('cancel', {'request_and_ack_distinguished': True, 'no_partial_or_final_result': True, 'calls': calls, 'DB_unchanged': True})


def test_selector_bounds_missing_unaccepted_and_actual_lock(setup, monkeypatch):
    from uuid import uuid4
    query, worker, job_id, raw, value = setup
    reference.readonly(value)
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch); empty = read(query, job_id)
        assert empty['prefix_status'] == 'none' and empty['summary'] is empty['selection'] is None
        assert query.read('tenant-1', str(uuid4())) is None
    writable(value); lease = reference.confirm(worker, job_id); _, first = advance(worker, job_id, raw, lease, 2)
    pin = {k: first['checkpoint'][k] for k in ('publication_sequence', 'head_sha256', 'proof_sha256')}
    reference.readonly(value); before = reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch)
        for bad in (dict(pin, private=True), dict(pin, publication_sequence=True), dict(pin, publication_sequence=0),
                dict(pin, head_sha256='A'*64)):
            with pytest.raises(model.JointPrefixRequestRejected): query.read('tenant-1', job_id, selector=bad)
        for options in ({'view': 'unknown'}, {'view': 'samples'}, {'start': -1}, {'start': True},
                {'view': 'samples', 'selector': pin, 'limit': 65}, {'view': 'events', 'selector': pin, 'limit': 9},
                {'view': 'samples', 'selector': pin, 'start': 999}):
            with pytest.raises(model.JointPrefixRequestRejected): query.read('tenant-1', job_id, **options)
        with pytest.raises(model.JointPrefixSelectionConflict): query.read('tenant-1', job_id, selector=dict(pin, proof_sha256='a'*64))
        with worker.server._open('tenant-1', raw, False):
            with pytest.raises(model.JointPrefixPending): query.read('tenant-1', job_id)
        assert all(n == 0 for n in calls.values())
    assert reference.persisted_digest(worker.jobs) == before
    save('boundaries', {'missing_and_unstarted': True, 'invalid_shapes_ranges_limits_rejected': True,
        'unaccepted_selector_rejected': True, 'actual_file_lock_pending': True, 'calls': calls, 'DB_unchanged': True})


def test_original_signed_head_proof_commit_page_tampering_rejected(setup, monkeypatch):
    query, worker, job_id, raw, value = setup
    lease = reference.confirm(worker, job_id); _, accepted = advance(worker, job_id, raw, lease, 2)
    root, artifact, proofs = reference.reference.producer.locations(worker.server, raw)
    head = json.loads((artifact/'HEAD').read_bytes())
    commit = json.loads((artifact/(head['latest_commit_sha256']+'.json')).read_bytes())
    paths = {'intent': root/'intent.json', 'proof': proofs/(accepted['checkpoint']['head_sha256']+'.json'),
        'HEAD': artifact/'HEAD', 'commit': artifact/(head['latest_commit_sha256']+'.json'),
        'sample': artifact/(commit['pages']['samples'][0]['sha256']+'.json')}
    reference.readonly(value); before = reference.persisted_digest(worker.jobs); rejected = []
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch)
        for name, path in paths.items():
            original = path.read_bytes(); mode = path.stat().st_mode & 0o777
            try:
                changed = original+b' '
                if name == 'proof':
                    signed = json.loads(original); signed['hmac_sha256'] = '0'*64; changed = model.storage._canonical(signed)
                path.chmod(0o600); path.write_bytes(changed); path.chmod(mode)
                with pytest.raises(model.JointPrefixHold): query.read('tenant-1', job_id)
                rejected.append(name)
            finally:
                path.chmod(0o600); path.write_bytes(original); path.chmod(mode)
        assert read(query, job_id)['selection']['checkpoint'] == accepted['checkpoint']
        assert all(n == 0 for n in calls.values())
    assert reference.persisted_digest(worker.jobs) == before
    save('tampering', {'rejected': rejected, 'original_owned_files_restored': True, 'calls': calls, 'DB_unchanged': True})


def test_actual_independent_cancel_during_read_is_pending(setup, tmp_path, monkeypatch):
    query, worker, job_id, raw, value = setup
    lease = reference.confirm(worker, job_id); advance(worker, job_id, raw, lease, 2)
    reference.readonly(value)
    pack = reference.reference.producer.fresh_pack(tmp_path, value, worker.server.inspect('tenant-1', raw), worker.server)
    p = json.loads(pack.read_bytes()); p.update(job_id=job_id, phase='reader'); pack.write_text(json.dumps(p))
    script = reference.reference.FRESH_WORKER.split('with MonkeyPatch.context()')[0] + '''
assert jobs.cancel('tenant-1',p['job_id'])
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
print(json.dumps({'actual_scram':True,'external_cancel_accepted':True}))
'''
    original = query.query._bundle; observed = []; count = 0
    def changed(*args):
        nonlocal count
        count += 1
        if count == 2:
            child = subprocess.run([sys.executable, '-B', '-c', script, str(pack)], capture_output=True,
                stdin=subprocess.DEVNULL, timeout=120, env=dict(os.environ, PYTHONPATH=reference.reference.producer.FRESH_PYTHONPATH))
            assert child.returncode == 0, child.stderr.decode(); observed.append(json.loads(child.stdout))
        return original(*args)
    try:
        with monkeypatch.context() as patch:
            calls = reference.forbid(patch); patch.setattr(query.query, '_bundle', changed)
            with pytest.raises(model.JointPrefixPending): query.read('tenant-1', job_id)
            assert all(n == 0 for n in calls.values())
    finally:
        pack.unlink(); (tmp_path/'proof.private.json').unlink()
    assert len(observed) == 1 and read(query, job_id)['prefix_status'] == 'closed'
    save('concurrent-cancel', {'external_process': observed[0], 'mixed_snapshot_rejected': True,
        'reader_calls': calls, 'DB_delta_is_intentional_external_cancel': True})


@pytest.mark.parametrize('producer_setup', ['normal', 'hold'], indirect=True)
def test_terminal_uses_existing_result_and_prefix_is_closed(setup, monkeypatch):
    query, worker, job_id, raw, value = setup
    worker.server.advance('tenant-1', raw, budget=128)
    outcome = worker.run_once(job_id)
    assert outcome.state in ('succeeded', 'hold') and outcome.result_id
    reference.readonly(value); before = reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = reference.forbid(patch); result = read(query, job_id)
        assert result['prefix_status'] == 'closed' and result['job']['state'] == outcome.state
        assert all(result[k] is None for k in ('selection', 'binding', 'manifest', 'time_binding', 'summary', 'page'))
        terminal = json.loads(query.query.read('tenant-1', job_id))
        assert terminal['result']['result_id'] == outcome.result_id
        assert all(n == 0 for n in calls.values())
    assert reference.persisted_digest(worker.jobs) == before
    save('terminal-'+outcome.state, {'prefix_closed': True, 'same_existing_result': True, 'calls': calls, 'DB_unchanged': True})
