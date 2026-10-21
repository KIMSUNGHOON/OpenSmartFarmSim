"""Closed read requests and lease changes before the original-page boundary."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app import crop_greenhouse_co2_prefix as model


def pin():
    return dict(publication_sequence=1, head_sha256='a'*64, proof_sha256='b'*64)


def job():
    now = datetime(2026, 10, 21, tzinfo=timezone.utc)
    return dict(tenant_id='tenant-1', job_id=str(uuid4()), state='simulating',
        stage='simulation', cancel_requested=False, attempt_count=1, lease_token='owned-token',
        lease_until=now+timedelta(seconds=600), updated_at=now, created_at=now,
        input_sha256='c'*64)


def test_closed_selector_positive_bounds_and_copy():
    for sequence in (1, model.checkpoints.MAX_EVENTS):
        original = dict(pin(), publication_sequence=sequence)
        selected = model._selector(original)
        assert selected == original and selected is not original
        selected['head_sha256'] = 'c'*64
        assert original['head_sha256'] == 'a'*64


def test_selector_rejects_open_shape_boolean_sequence_and_non_digest():
    rejected = [None, [], (), 'selector', {}, dict(pin(), private=True)]
    rejected += [{k: v for k, v in pin().items() if k != field} for field in pin()]
    rejected += [dict(pin(), publication_sequence=v) for v in
        (True, False, 0, -1, 1.0, '1', model.checkpoints.MAX_EVENTS+1)]
    rejected += [dict(pin(), **{field: value}) for field in ('head_sha256', 'proof_sha256')
        for value in (None, b'a'*64, 'A'*64, 'g'*64, 'a'*63, 'a'*65)]
    for value in rejected:
        with pytest.raises(model.Co2PrefixRequestRejected):
            model._selector(value)


def test_bad_requests_fail_before_authority_database_or_files(monkeypatch):
    query = object.__new__(model.Co2ExecutionPrefixQuery)
    def io(*args, **kwargs):
        pytest.fail('invalid request reached authority / DB / files')
    monkeypatch.setattr(query, '_guard', io)
    good_id = str(uuid4())
    for bad_id in (None, 1, True, '', 'not-a-uuid', good_id.upper(), '{'+good_id+'}'):
        with pytest.raises(model.Co2PrefixRequestRejected):
            query.read('tenant-1', bad_id)
    options = [dict(view=v) for v in (None, [], 'unknown')]
    options += [dict(start=v) for v in (-1, True, 0.0, '0')]
    options += [dict(limit=v) for v in (0, 1, True)]
    options += [dict(view=kind) for kind in ('samples', 'events')]
    options += [dict(selector=dict(pin(), private=True))]
    for kind, maximum in (('samples', 64), ('events', 8)):
        options += [dict(view=kind, selector=pin(), limit=v)
            for v in (0, -1, True, False, 1.0, '1', maximum+1)]
    for kw in options:
        with pytest.raises(model.Co2PrefixRequestRejected):
            query.read('tenant-1', good_id, **kw)


def test_exact_co2_query_authority_required():
    for value in (None, {}, object()):
        with pytest.raises(model.Co2PrefixHold):
            model.Co2ExecutionPrefixQuery(value)


def test_equivalent_aware_utc_and_forward_heartbeat_remain_readable():
    before = job()
    after = deepcopy(before)
    korea = timezone(timedelta(hours=9))
    for field in ('lease_until', 'updated_at', 'created_at'):
        after[field] = after[field].astimezone(korea)
    assert model._same_job_row(before, after)
    after['lease_until'] += timedelta(seconds=60)
    after['updated_at'] += timedelta(seconds=30)
    assert model._same_job_row(before, after)


def test_heartbeat_cannot_change_attempt_input_scope_cancel_or_time_history():
    before = job()
    changes = [dict(tenant_id='other'), dict(job_id=str(uuid4())), dict(state='canceled'),
        dict(stage='collection'), dict(cancel_requested=True), dict(cancel_requested=0),
        dict(attempt_count=2), dict(lease_token='replacement'), dict(input_sha256='d'*64),
        dict(created_at=before['created_at']+timedelta(microseconds=1))]
    for field in ('lease_until', 'updated_at'):
        changes += [{field: before[field]-timedelta(microseconds=1)},
            {field: before[field].replace(tzinfo=None)}, {field: None}]
    for fields in changes:
        assert not model._same_job_row(before, dict(before, **fields)), fields
    assert not model._same_job_row(before, {k: v for k, v in before.items() if k != 'lease_token'})
    assert not model._same_job_row(before, dict(before, extra=True))


def test_non_running_rows_do_not_gain_heartbeat_exception():
    for state, canceled in (('queued', False), ('simulating', True), ('canceled', True)):
        before = dict(job(), state=state, cancel_requested=canceled)
        assert model._same_job_row(before, deepcopy(before))
        after = dict(before, updated_at=before['updated_at']+timedelta(microseconds=1))
        assert not model._same_job_row(before, after)
