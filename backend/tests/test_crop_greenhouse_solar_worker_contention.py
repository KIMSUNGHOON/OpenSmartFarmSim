"""Pending custody calls must retain authority and bounded failure semantics."""
from types import SimpleNamespace

import pytest

from app import crop_greenhouse_solar_execution_worker as model


@pytest.fixture
def worker(monkeypatch):
    value = object.__new__(model.SolarExecutionWorker)
    clock, waits, renewals = [0.0], [], []
    def wait(seconds):
        waits.append(seconds)
        clock[0] += seconds
    monkeypatch.setattr(model, 'time', SimpleNamespace(monotonic=lambda:clock[0], sleep=wait))
    value._before = lambda lease:renewals.append(lease)
    return value, clock, waits, renewals


def test_temporary_contention_rechecks_lease_then_returns_original_value(worker):
    value, _, waits, renewals = worker
    calls, expected, lease = [], object(), object()
    def call():
        calls.append(True)
        if len(calls) == 1:
            raise model.checkpoints.custody.SolarCustodyPending('busy')
        return expected
    assert value._custody_call(lease, call) is expected
    assert len(calls) == 2 and renewals == [lease] and waits == [.05]


def test_permanent_contention_exhausts_budget_and_preserves_original_exception(worker):
    value, clock, waits, renewals = worker
    failure = model.checkpoints.custody.SolarCustodyPending('busy')
    def call():
        raise failure
    with pytest.raises(model.checkpoints.custody.SolarCustodyPending) as caught:
        value._custody_call(object(), call)
    assert caught.value is failure and 5 <= clock[0] < 5.051
    assert waits and len(waits) == len(renewals) and max(waits) <= .05


@pytest.mark.parametrize('failure', [PermissionError('revoked'),
    model.checkpoints.SolarCheckpointLeaseLost('canceled')])
def test_cancel_or_revocation_while_waiting_stops_before_retry(worker, failure):
    value, _, waits, _ = worker
    calls = []
    def call():
        calls.append(True)
        raise model.checkpoints.custody.SolarCustodyPending('busy')
    def rejected(_):
        raise failure
    value._before = rejected
    with pytest.raises(type(failure)) as caught:
        value._custody_call(object(), call)
    assert caught.value is failure and len(calls) == 1 and waits == []


def test_other_operation_errors_are_not_retried(worker):
    value, _, waits, renewals = worker
    failure = ValueError('invalid signed input')
    def call():
        raise failure
    with pytest.raises(ValueError) as caught:
        value._custody_call(object(), call)
    assert caught.value is failure and not waits and not renewals


def test_authority_check_that_exhausts_budget_prevents_another_operation(worker):
    value, clock, waits, _ = worker
    calls = []
    failure = model.checkpoints.custody.SolarCustodyPending('busy')
    def call():
        calls.append(True)
        raise failure
    def slow_check(_):
        clock[0] += 6
    value._before = slow_check
    with pytest.raises(model.checkpoints.custody.SolarCustodyPending) as caught:
        value._custody_call(object(), call)
    assert caught.value is failure and len(calls) == 1 and waits == []
