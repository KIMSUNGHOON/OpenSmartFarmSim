"""Distinct authored pins cannot degrade to either prior economic input."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.authored_economic_execution import authored_economic_pointers, AuthoredEconomicHold
from app.economic_calculation_worker import ECONOMIC_INPUT, AuthoredEconomicCalculationInput
from app.api_economic_calculation import (ECONOMIC_REQUEST, economic_request_schema,
    additional_economic_scopes)
from app.authored_economic_execution import AUTHORED_ECONOMIC_SCOPES


def body():
    return {'input_version': 'economic-calculation-input-v3', 'scenario_id': 'money-one',
        'scenario_revision': 'r1', 'scenario_sha256': 'a' * 64, 'candidate_id': 'b' * 64,
        'formula_version': 'economic-ledger-v9-sales-settlement',
        'authored_scenario_id': 'farm-one', 'authored_scenario_revision': 'r1',
        'registration_sha256': 'c' * 64,
        'thermal_job_id': '11111111-1111-4111-8111-111111111111'}


def test_authored_economic_input_keeps_distinct_identity():
    value = ECONOMIC_INPUT.validate_python(body())
    assert type(value) is AuthoredEconomicCalculationInput
    assert value.model_dump(mode='json') == body()
    for field in ('authored_scenario_id', 'authored_scenario_revision', 'registration_sha256', 'thermal_job_id'):
        incomplete = body()
        del incomplete[field]
        with pytest.raises(ValueError):
            ECONOMIC_INPUT.validate_python(incomplete)


def test_authored_economic_request_schema_declares_closed_third_version():
    request = ECONOMIC_REQUEST.validate_python(body() | {'idempotency_key': 'intent-one'})
    assert additional_economic_scopes(request) == AUTHORED_ECONOMIC_SCOPES
    schemas = economic_request_schema()['oneOf']
    assert len(schemas) == 3
    third = schemas[2]
    assert third['properties']['input_version']['const'] == 'economic-calculation-input-v3'
    assert third['additionalProperties'] is False
    assert {'registration_sha256', 'thermal_job_id', 'idempotency_key'} <= set(third['required'])


@pytest.mark.parametrize('change', [
    {'input_version': 'economic-calculation-input-v1'},
    {'input_version': 'economic-calculation-input-v2'},
    {'thermal_job_id': '11111111-1111-4111-8111-11111111111A'},
    {'registration_sha256': 'f' * 63},
    {'farm_scenario_id': 'farm-replay'},
    {'thermal_receipt_sha256': 'a' * 64},
])
def test_invalid_authored_input_cannot_replace_completion_evidence(change):
    with pytest.raises(ValueError):
        ECONOMIC_INPUT.validate_python(body() | change)


@pytest.mark.parametrize('runs', [None, object()])
def test_missing_or_untrusted_authored_store_holds(runs):
    with pytest.raises(AuthoredEconomicHold, match='^authored economic authority unavailable$'):
        authored_economic_pointers(runs, object(), object(), object())
