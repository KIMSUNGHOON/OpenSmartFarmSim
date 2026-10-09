"""Actual SCRAM stores; synthetic inputs, holds and test signing keys only."""

from copy import copy
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.break_even_store import BreakEvenStore
from app.break_even_replay import BreakEvenReplayEvidence, ReplayReferences
from test_break_even_calculation_worker import calculation_setup
from test_api_break_even_plan import plan_api, login_database, login_scope, PROFILE

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)


def complete(calculation_setup):
    worker, job_id, principal = calculation_setup
    result = worker.run_once(job_id)
    assert result.state == 'succeeded'
    return worker, result.plan_id, principal


def test_actual_replay_records_current_plan_candidate_rights_and_context(calculation_setup):
    worker, plan_id, _ = complete(calculation_setup)
    request, result, evidence = worker.store.capture_break_even_replay('tenant-1', plan_id)
    assert evidence.trial_count == len(result.trials) == 2
    assert result.assessment_status == 'hold'
    methods = {item.method for item in evidence.reads}
    assert {'get_break_even_plan', 'get_market_candidate', 'get_economic_scenario',
        'get_economic_scenario_pin', 'get_economic_input', 'get_joint_shock',
        'get_joint_shock_pin', 'get_input_rights', 'get_settlement_applicability',
        'get_market_hold_report', 'get_decision_context'} <= methods
    raw = evidence.model_dump_json()
    assert BreakEvenReplayEvidence.model_validate_json(raw) == evidence
    assert 'raw_record' not in raw and 'scope_start' not in raw and 'synthetic-test-key' not in raw
    resumed = BreakEvenStore(worker.store.dsn, worker.store.schema, worker.store._source,
        principal_provider=worker.store._principal_provider, runtime_identity=worker.store.runtime_identity)
    assert resumed.capture_break_even_replay('tenant-1', plan_id) == (request, result, evidence)
    assert resumed.get_break_even_read('tenant-1', plan_id) == (request, result)


@pytest.mark.parametrize('fault', ['scope', 'source', 'code', 'cancel'])
def test_late_changes_or_interruptions_return_no_evidence(calculation_setup, monkeypatch, fault):
    worker, plan_id, principal = complete(calculation_setup)
    original = ReplayReferences.recheck
    expected = ValueError
    if fault == 'code':
        from app import thermal_publisher
        actual_digests = thermal_publisher.runtime_digests
        calls = []
        def changed_digests(root):
            calls.append(True)
            return actual_digests(root) if len(calls) == 1 else ('a' * 64, 'b' * 64)
        monkeypatch.setattr(thermal_publisher, 'runtime_digests', changed_digests)
    else:
        if fault == 'cancel': expected = RuntimeError
        def change(references, *, check=None):
            if fault == 'scope': principal['scopes'].remove('market_source_read')
            if fault == 'source': worker.store._source = copy(worker.store._source)
            if fault == 'cancel':
                def canceled(): raise RuntimeError('synthetic cancellation')
                return original(references, check=canceled)
            return original(references, check=check)
        monkeypatch.setattr(ReplayReferences, 'recheck', change)
    with pytest.raises(expected): worker.store.capture_break_even_replay('tenant-1', plan_id)
    with worker.jobs.connect() as conn:
        rows = conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(worker.jobs._table('job_publications'))).fetchone()['n']
    assert rows == 1
