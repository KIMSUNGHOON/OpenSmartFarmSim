"""Byte capacity of synthetic finite-grid outputs, not hosted throughput."""

from dataclasses import replace
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.break_even import BreakEvenService, BreakEvenRequest
from app.break_even_calculation_worker import _result_bytes
from app.break_even_store import BreakEvenStore, _RESULT, _canonical
from app.jobs import canonical_input_bytes
from test_break_even import trial_plan, saved_break_even


def test_actual_256_trial_output_fits_result_storage_without_input_limit():
    repo, request = trial_plan(list(range(20, 276)))
    result = BreakEvenService(repo).scan(request, 'tenant-1')
    assert len(result.trials) == 256 and result.assessment_status == 'hold'
    input_bytes = canonical_input_bytes({'input_version': 'break-even-calculation-input-v1',
        'request': BreakEvenRequest.model_validate(request).model_dump(mode='json'),
        'plan': repo.break_even_plan})
    expected = _canonical(_RESULT.dump_python(result, mode='json'))
    assert len(input_bytes) <= 65536 < len(expected) <= 1048576
    assert _result_bytes(result) == expected
    assert _RESULT.validate_json(expected) == result


def test_result_serializer_keeps_legacy_small_result_bytes():
    repo, request = trial_plan([20, 32])
    result = BreakEvenService(repo).scan(request, 'tenant-1')
    expected = canonical_input_bytes(_RESULT.dump_python(result, mode='json'))
    assert _result_bytes(result) == expected


def test_result_larger_than_its_storage_bound_is_refused():
    repo, request = trial_plan([20, 32])
    result = replace(BreakEvenService(repo).scan(request, 'tenant-1'),
        hold_reasons=('x' * 1048577,))
    with pytest.raises(ValueError, match='break-even result exceeds size limit'):
        _result_bytes(result)


def test_256_trial_result_round_trips_actual_postgresql_rows(saved_break_even):
    factory, _, _, principal = saved_break_even
    base = factory()
    repo, request = trial_plan(list(range(20, 276)))
    def store():
        return BreakEvenStore(base.dsn, base.schema, repo, principal_provider=lambda: principal)
    pinned = store().pin_break_even_plan(request, repo.break_even_plan)
    assert len(pinned.trials) == 256
    row = store()._row(request['plan_id'])
    assert len(row['result_raw']) == 80912 and row['result_raw'] == _result_bytes(pinned)
    assert store().get_break_even_result(request['plan_id']) == pinned
