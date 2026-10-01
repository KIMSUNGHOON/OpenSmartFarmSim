"""Actual SCRAM verification admission; all inputs and signing keys are synthetic."""

from pathlib import Path
import json
import sys
from uuid import UUID

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.break_even_verification import BreakEvenVerificationInput, BreakEvenVerificationService
from app.jobs import canonical_input_bytes
from test_api_job_break_even_result import (result_api, complete, calculation_setup,
    plan_api, login_database, login_scope, PROFILE)

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)


@pytest.fixture
def verification_setup(result_api):
    _, _, worker, calculation_id, principal = result_api
    complete(worker, calculation_id)
    service = BreakEvenVerificationService(worker.jobs, worker.store)
    return service, calculation_id, principal


def test_actual_parent_verification_intent_is_immutable_and_idempotent(verification_setup, monkeypatch):
    service, calculation_id, principal = verification_setup
    principal['scopes'].discard('break_even_write')
    def no_replay(*_): raise RuntimeError('admission must not replay the grid')
    monkeypatch.setattr(service.store, 'get_break_even_read', no_replay)
    accepted = service.submit('tenant-1', calculation_id)
    assert accepted.state == 'queued' and accepted.stage == 'simulation'
    assert service.submit('tenant-1', calculation_id) == accepted
    with service.jobs.connect() as conn:
        row = service.jobs._locked_job(conn, 'tenant-1', accepted.job_id)
        raw = service.jobs._verified_input(row)
    value = BreakEvenVerificationInput.model_validate_json(raw)
    assert raw == canonical_input_bytes(value.model_dump(mode='json'))
    assert value.calculation_job_id == calculation_id and value.trial_count == 2
    assert value.verification == 'completed_bytes_only_requires_replay'
    assert service.jobs.get_publication('tenant-1', accepted.job_id) is None
    principal['scopes'].remove('simulation_execute')
    with pytest.raises(PermissionError): service.submit('tenant-1', calculation_id)


def test_full_replay_publishes_private_evidence_and_a_bounded_receipt(verification_setup, monkeypatch):
    from app.break_even_replay import BreakEvenReplayEvidence
    from app.break_even_verification_worker import BreakEvenVerificationWorker
    service, calculation_id, principal = verification_setup
    principal['scopes'].discard('break_even_write')
    admitted = service.submit('tenant-1', calculation_id)
    worker = BreakEvenVerificationWorker(service.jobs, service.store, tenant_id='tenant-1')
    def unexpected_close(*_, **__): raise sys.exc_info()[1]
    monkeypatch.setattr(worker, '_close', unexpected_close)
    outcome = worker.run_once(str(admitted.job_id))
    assert outcome.state == 'succeeded' and outcome.calculation_job_id == calculation_id
    artifact = service.jobs.read_artifact('tenant-1', admitted.job_id)
    assert len(artifact) <= 4096
    receipt = json.loads(artifact)
    assert receipt['assessment_status'] == 'hold'
    assert receipt['verification_scope'] == 'historical_full_grid_replay_only'
    assert 'reads' not in receipt and 'tenant_id' not in receipt
    raw = service.jobs._read_private_evidence('tenant-1',
        {'sha256': receipt['evidence_sha256'], 'size': receipt['evidence_size']})
    evidence = BreakEvenReplayEvidence.model_validate_json(raw)
    assert evidence.trial_count == receipt['trial_count'] == 2
    assert evidence.result_sha256 == receipt['result_sha256']
    assert service.jobs.get_publication('tenant-1', admitted.job_id)['decision_id'] is None
    assert worker.run_once(str(admitted.job_id)) is None


def test_wrong_models_forged_parent_and_missing_scope_do_not_publish(verification_setup):
    from app.break_even_verification_worker import BreakEvenVerificationWorker
    service, calculation_id, principal = verification_setup
    admitted = service.submit('tenant-1', calculation_id)
    worker = BreakEvenVerificationWorker(service.jobs, service.store, tenant_id='tenant-1')
    assert worker.run_once(calculation_id) is None
    other = service.jobs.submit('tenant-1', 'simulation', {'input_version': 'other'}, 'other')
    assert worker.run_once(str(other['job_id'])) is None
    value = service.prepare('tenant-1', calculation_id).model_dump(mode='json')
    forged = service.jobs.submit('tenant-1', 'simulation', value | {'result_sha256': 'a' * 64}, 'forged')
    assert worker.run_once(str(forged['job_id'])).state == 'hold'
    assert service.jobs.get_publication('tenant-1', forged['job_id']) is None
    principal['scopes'].remove('simulation_execute')
    with pytest.raises(PermissionError): worker.run_once(str(admitted.job_id))
    assert service.jobs.get_job('tenant-1', admitted.job_id)['attempt_count'] == 0


def test_cancel_after_first_actual_trial_withholds_completion(verification_setup, monkeypatch):
    from app.break_even_verification_worker import BreakEvenVerificationWorker
    from app.market_scenario import MarketScenarioService
    service, calculation_id, _ = verification_setup
    admitted = service.submit('tenant-1', calculation_id)
    worker = BreakEvenVerificationWorker(service.jobs, service.store, tenant_id='tenant-1')
    original = MarketScenarioService.calculate_pinned
    calls = []
    def cancel(self, *args):
        result = original(self, *args)
        if not calls:
            calls.append(True)
            assert service.jobs.cancel('tenant-1', admitted.job_id)
        return result
    monkeypatch.setattr(MarketScenarioService, 'calculate_pinned', cancel)
    outcome = worker.run_once(str(admitted.job_id))
    assert calls and outcome.state == 'canceled'
    assert service.jobs.get_publication('tenant-1', admitted.job_id) is None


@pytest.mark.parametrize('fault,state', [('scope', 'hold'), ('publication', 'queued')])
def test_late_fault_rolls_back_verification_publication(verification_setup, monkeypatch, fault, state):
    from app.break_even_verification_worker import BreakEvenVerificationWorker
    service, calculation_id, principal = verification_setup
    admitted = service.submit('tenant-1', calculation_id)
    worker = BreakEvenVerificationWorker(service.jobs, service.store, tenant_id='tenant-1')
    with monkeypatch.context() as patch:
        if fault == 'scope':
            original = service.jobs._durable_artifact
            def revoke(*args):
                original(*args)
                principal['scopes'].remove('market_source_read')
            patch.setattr(service.jobs, '_durable_artifact', revoke)
        else:
            def fail(*_, **__): raise RuntimeError('private publication detail')
            patch.setattr(service.jobs, '_insert_publication', fail)
        outcome = worker.run_once(str(admitted.job_id))
    assert outcome.state == state and 'private' not in outcome.reason_code
    assert service.jobs.get_publication('tenant-1', admitted.job_id) is None
    if fault == 'publication':
        with service.jobs.connect() as conn:
            conn.execute(sql.SQL("UPDATE {} SET next_attempt_at=clock_timestamp()+interval '30 seconds' "
                "WHERE tenant_id=%s AND job_id=%s AND state='queued'")
                .format(service.jobs._table('jobs')), ('tenant-1', admitted.job_id))
        assert worker.run_once(str(admitted.job_id)) is None
        assert service.jobs.get_job('tenant-1', admitted.job_id)['attempt_count'] == 1
        with service.jobs.connect() as conn:
            conn.execute(sql.SQL("UPDATE {} SET next_attempt_at=clock_timestamp()-interval '1 second' "
                "WHERE tenant_id=%s AND job_id=%s AND state='queued'")
                .format(service.jobs._table('jobs')), ('tenant-1', admitted.job_id))
        replay = worker.run_once(str(admitted.job_id))
        assert replay.state == 'succeeded' and replay.attempt == 2


def test_expired_verification_attempt_recovers_with_new_fence(verification_setup, monkeypatch):
    from app.break_even_verification_worker import BreakEvenVerificationWorker
    service, calculation_id, _ = verification_setup
    admitted = service.submit('tenant-1', calculation_id)
    worker = BreakEvenVerificationWorker(service.jobs, service.store, tenant_id='tenant-1')
    original = service.jobs.read_input
    first = []
    def expire(*args):
        raw = original(*args)
        if not first:
            first.append(True)
            with service.jobs.connect() as conn:
                conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
                    .format(service.jobs._table('jobs')), (admitted.job_id,))
        return raw
    monkeypatch.setattr(service.jobs, 'read_input', expire)
    assert worker.run_once(str(admitted.job_id)).state == 'unclosed'
    assert service.jobs.get_publication('tenant-1', admitted.job_id) is None
    completed = worker.run_once(str(admitted.job_id))
    assert completed.state == 'succeeded' and completed.attempt == 2
