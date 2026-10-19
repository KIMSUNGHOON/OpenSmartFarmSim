"""Private advancement acknowledges writes; independent confirmation owns reads."""
import json
import inspect

import pytest

from app import crop_greenhouse_solar_server_custody as model
from test_crop_greenhouse_solar_execution_query import (
    worker_setup, producer_setup, authoring, profiles, login_database,
    original_login_scope, login_scope, query_cleanup, save)
import test_crop_greenhouse_solar_execution_query as reference

pytestmark = reference.reference.pytestmark


@pytest.mark.usefixtures('query_cleanup')
def test_private_ack_has_no_progress_and_confirmation_preserves_public_values(worker_setup, monkeypatch):
    worker, job_id, raw, _ = worker_setup
    lease = worker.jobs.claim(worker.lease_seconds, allowed_stages=('simulation',),
                              tenant_id='tenant-1', job_id=job_id)
    assert lease and worker._before(lease) == raw and worker._adopt(raw) is None

    def forbidden(*args, **kwargs):
        pytest.fail('private acknowledgement constructed a progress response')

    with monkeypatch.context() as patch:
        patch.setattr(model._Session, 'progress', forbidden)
        assert worker.server._advance_for_checkpoint('tenant-1', raw, budget=1) is None
    first = worker._confirm(lease)
    assert first['checkpoint']['steps'] == 0
    with monkeypatch.context() as patch:
        patch.setattr(model._Session, 'progress', forbidden)
        assert worker.server._advance_for_checkpoint('tenant-1', raw, budget=1) is None
    second = worker._confirm(lease)
    assert second['checkpoint']['steps'] == 1
    assert second['checkpoint']['computed_through_utc'] == '2026-10-01T00:00:02.123456Z'
    public = worker.server.advance('tenant-1', raw, budget=1)
    assert type(public) is bytes and public == worker.server.inspect('tenant-1', raw)
    latest = worker._confirm(lease)
    parsed = json.loads(public)
    assert latest['checkpoint']['steps'] == parsed['steps'] == 2
    assert latest['checkpoint']['counts'] == parsed['counts']
    assert latest['checkpoint']['head_sha256'] == parsed['head_sha256']
    assert latest['checkpoint']['rights_or_gate_approval'] is False
    save('worker-private-ack-public-confirmation', {'steps': [0, 1, 2],
        'private_return_None': True, 'private_progress_calls': 0,
        'public_response_preserved': True, 'original_UTC': second['checkpoint']['computed_through_utc']})


def checkpoint_events(worker, job_id):
    return [row for row in reference.reference.rows(worker, job_id, 'job_events')
            if row['kind'] == reference.reference.model.checkpoints.EVENT_KIND]


def artifact_paths(worker, raw):
    return reference.reference.producer.locations(worker.server, raw)


@pytest.mark.usefixtures('query_cleanup')
def test_private_options_and_budget_are_strict(worker_setup):
    worker, _, raw, _ = worker_setup
    for budget in (None, True, 0, -1, model.continuation.MAX_CHUNK_BOUNDARIES + 1):
        with pytest.raises(model.SolarCustodyHold):
            worker.server._advance_for_checkpoint('tenant-1', raw, budget=budget)
    with pytest.raises(TypeError):
        worker.server.advance('tenant-1', raw, budget=1, _return_progress=False)
    calls = []
    def prepare():
        calls.append(1)
        pytest.fail('invalid private option prepared a model')
    with worker.server._open('tenant-1', raw, True) as (session, _):
        for option in (None, 0, 1, 'false', [], {}):
            with pytest.raises(model.SolarCustodyHold):
                session.advance(1, prepare, _return_progress=option)
    with worker.server._open('tenant-1', raw, False) as (session, _):
        with pytest.raises(model.SolarCustodyHold):
            session.advance(1, prepare, _return_progress=False)
    assert not calls
    save('worker-private-ack-strict-options', {'invalid_options': 6, 'invalid_budgets': 5,
        'public_option_rejected': True, 'read_only_rejected': True, 'prepare_calls': 0})


@pytest.mark.usefixtures('query_cleanup')
def test_private_current_denial_precedes_history_and_continuation(worker_setup, monkeypatch):
    worker, _, raw, value = worker_setup
    worker.server.advance('tenant-1', raw, budget=1)
    _, artifact, _ = artifact_paths(worker, raw)
    original_head = (artifact / 'HEAD').read_bytes()
    source = worker.server.binding.farms.replay.candidates._source._source
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(1)
        pytest.fail('denied private advance consumed history or continued')
    for fault in ('physical', 'economic'):
        with monkeypatch.context() as patch:
            patch.setattr(model._Session, '_load', forbidden)
            for name in ('prepare_context', 'start', 'restore_checkpoint', 'advance_chunk'):
                patch.setattr(model.continuation, name, forbidden)
            if fault == 'physical': value[5].allowed = False
            else: patch.setattr(source, 'get_input_rights', lambda *_: None)
            try:
                with pytest.raises(model.SolarCustodyHold):
                    worker.server._advance_for_checkpoint('tenant-1', raw, budget=1)
            finally: value[5].allowed = True
        assert (artifact / 'HEAD').read_bytes() == original_head
    assert not calls
    save('worker-private-ack-current-denial', {'physical_and_economic_denied': True,
        'history_or_continuation_calls': 0, 'original_HEAD_preserved': True})


@pytest.mark.usefixtures('query_cleanup')
def test_ack_does_not_authorize_later_confirmation(worker_setup):
    worker, job_id, raw, value = worker_setup
    lease = worker.jobs.claim(worker.lease_seconds, allowed_stages=('simulation',),
                              tenant_id='tenant-1', job_id=job_id)
    assert lease and worker._before(lease) == raw
    assert worker.server._advance_for_checkpoint('tenant-1', raw, budget=1) is None
    assert not checkpoint_events(worker, job_id)
    value[5].allowed = False
    try:
        with pytest.raises(reference.reference.model.checkpoints.SolarCheckpointHold):
            worker._confirm(lease)
    finally: value[5].allowed = True
    assert not checkpoint_events(worker, job_id)
    _, artifact, _ = artifact_paths(worker, raw)
    path = artifact / 'HEAD'; original = path.read_bytes()
    try:
        path.chmod(0o600); path.write_bytes(original + b' '); path.chmod(0o400)
        with pytest.raises(reference.reference.model.checkpoints.SolarCheckpointHold):
            worker._confirm(lease)
        assert not checkpoint_events(worker, job_id)
    finally:
        path.chmod(0o600); path.write_bytes(original); path.chmod(0o400)
    confirmed = worker._confirm(lease)
    assert confirmed['checkpoint']['steps'] == 0 and len(checkpoint_events(worker, job_id)) == 1
    save('worker-private-ack-confirmation-fences', {'post_ack_rights_and_HEAD_rejected': True,
        'checkpoint_events_before_restoration': 0, 'fresh_confirm_after_restoration': True})


@pytest.mark.usefixtures('query_cleanup')
def test_private_late_proof_revocation_preserves_committed_head(worker_setup, monkeypatch):
    worker, job_id, raw, value = worker_setup
    worker.server.advance('tenant-1', raw, budget=1)
    _, artifact, _ = artifact_paths(worker, raw)
    original_head = (artifact / 'HEAD').read_bytes()
    immutable = model.files._immutable; reached = []
    def revoke(parent, name, raw, maximum, prefix):
        result = immutable(parent, name, raw, maximum, prefix)
        if prefix == '.proof-': reached.append(1); value[5].allowed = False
        return result
    with monkeypatch.context() as patch:
        patch.setattr(model.files, '_immutable', revoke)
        try:
            with pytest.raises(model.SolarCustodyHold):
                worker.server._advance_for_checkpoint('tenant-1', raw, budget=1)
        finally: value[5].allowed = True
    assert reached and (artifact / 'HEAD').read_bytes() == original_head
    assert not checkpoint_events(worker, job_id)
    assert json.loads(worker.server.inspect('tenant-1', raw))['steps'] == 0
    save('worker-private-ack-late-proof-denial', {'proof_reached': True,
        'original_HEAD_preserved': True, 'checkpoint_events': 0})


@pytest.mark.parametrize('producer_setup', [None, 'hold'], indirect=True)
@pytest.mark.usefixtures('query_cleanup')
def test_private_terminal_retry_is_nonnumerical(worker_setup, monkeypatch):
    worker, _, raw, _ = worker_setup
    expected = worker.server.advance('tenant-1', raw, budget=128)
    status = json.loads(expected)['status']; assert status in ('completed', 'hold')
    with monkeypatch.context() as patch:
        calls = reference.reference.producer.reference.forbid(patch)
        assert worker.server._advance_for_checkpoint('tenant-1', raw, budget=1) is None
        assert worker.server.inspect('tenant-1', raw) == expected
        assert all(count == 0 for count in calls.values())
    save('worker-private-ack-terminal-' + status, {'status': status, 'calls': calls,
        'public_original_response_equal': True, 'ack_None': True})


@pytest.mark.usefixtures('query_cleanup')
def test_worker_consumes_independent_confirmation_without_unused_response(worker_setup, monkeypatch):
    worker, job_id, _, _ = worker_setup
    progress = model._Session.progress; observations = []
    def public_advance(*args, **kwargs):
        pytest.fail('worker constructed an unused public advance response')
    def guarded_progress(session):
        frame = inspect.currentframe().f_back
        while frame is not None:
            assert frame.f_code is not model._Session.advance.__code__
            frame = frame.f_back
        observations.append(1)
        return progress(session)
    with monkeypatch.context() as patch:
        patch.setattr(model.SolarServerCustody, 'advance', public_advance)
        patch.setattr(model._Session, 'progress', guarded_progress)
        calls = reference.reference.producer.measured(patch)
        outcome = worker.run_once(job_id)
    assert outcome.state == 'succeeded' and outcome.result_id and observations
    assert calls['step'] == 16 and calls['start'] == 1
    save('worker-private-ack-actual-worker', {'state': outcome.state, 'calls': calls,
        'guarded_confirmation_and_result_reads': len(observations), 'public_advance_calls': 0})


@pytest.mark.usefixtures('query_cleanup')
def test_worker_rejects_noop_ack_without_fabricated_checkpoint(worker_setup, monkeypatch):
    worker, job_id, _, _ = worker_setup
    with monkeypatch.context() as patch:
        patch.setattr(model.SolarServerCustody, '_advance_for_checkpoint', lambda *a, **kw: None)
        calls = reference.reference.producer.measured(patch)
        outcome = worker.run_once(job_id)
    assert outcome.state == 'hold' and outcome.result_id is None
    assert all(count == 0 for count in calls.values())
    assert not checkpoint_events(worker, job_id)
    reference.reference.no_published_result(worker, job_id)
    save('worker-private-ack-noop-rejected', {'state': outcome.state, 'calls': calls,
        'checkpoint_events': 0, 'published_result': False})


@pytest.mark.usefixtures('query_cleanup')
def test_worker_post_ack_revocation_cannot_publish_checkpoint_or_result(worker_setup, monkeypatch):
    worker, job_id, _, value = worker_setup
    advance = model.SolarServerCustody._advance_for_checkpoint
    def revoke(server, *args, **kwargs):
        result = advance(server, *args, **kwargs); value[5].allowed = False
        return result
    with monkeypatch.context() as patch:
        patch.setattr(model.SolarServerCustody, '_advance_for_checkpoint', revoke)
        try: outcome = worker.run_once(job_id)
        finally: value[5].allowed = True
    assert outcome.state == 'hold' and outcome.result_id is None
    assert not checkpoint_events(worker, job_id)
    reference.reference.no_published_result(worker, job_id)
    save('worker-private-ack-worker-revocation', {'state': outcome.state,
        'checkpoint_events': 0, 'published_result': False})
