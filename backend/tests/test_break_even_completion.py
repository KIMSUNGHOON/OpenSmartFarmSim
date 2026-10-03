"""Completed bytes permit replay intent, never a projection without replay."""

from pathlib import Path
import sys
from uuid import UUID

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api_job_break_even_result import BreakEvenCompletion
from test_api_job_break_even_result import (result_api, complete, calculation_setup,
    plan_api, login_database, login_scope, PROFILE)

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)


def test_completion_metadata_does_not_claim_current_recalculation(result_api, monkeypatch):
    _, service, worker, job_id, _ = result_api
    identity = UUID(job_id)
    assert service.read_job_completion('tenant-1', identity) is None
    complete(worker, job_id)
    original = worker.store.get_break_even_read
    def no_replay(*_): raise RuntimeError('synthetic missing replay')
    monkeypatch.setattr(worker.store, 'get_break_even_read', no_replay)
    metadata = service.read_job_completion('tenant-1', identity)
    assert metadata.calculation_job_id == job_id and metadata.trial_count == 2
    assert metadata.verification == 'completed_bytes_only_requires_replay'
    assert BreakEvenCompletion.model_validate_json(metadata.model_dump_json()) == metadata
    assert not {'trials', 'target_value', 'minimum_cash_balance', 'zero_values'} & metadata.model_dump().keys()
    with pytest.raises(RuntimeError, match='synthetic missing replay'):
        service.read_job_result('tenant-1', identity)
    monkeypatch.setattr(worker.store, 'get_break_even_read', original)
    assert service.read_job_result('tenant-1', identity).assessment_status == 'hold'
