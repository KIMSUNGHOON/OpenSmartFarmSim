"""Economic V2 pins the exact farm plan and completed thermal job."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.economic_calculation_worker import ECONOMIC_INPUT, FarmEconomicCalculationInput
from app.api_economic_calculation import ECONOMIC_REQUEST, economic_request_schema
from app.jobs import canonical_input_bytes


def value():
    return {'input_version':'economic-calculation-input-v2','scenario_id':'economic-one',
        'scenario_revision':'r1','scenario_sha256':'a'*64,'candidate_id':'b'*64,
        'formula_version':'economic-ledger-v9-sales-settlement','farm_scenario_id':'farm-one',
        'farm_scenario_revision':'r1','farm_scenario_sha256':'c'*64,
        'thermal_job_id':'00000000-0000-4000-8000-000000000001'}


def test_closed_economic_input_requires_all_farm_and_thermal_pins():
    original=value()
    assert type(ECONOMIC_INPUT.validate_json(canonical_input_bytes(original))) is FarmEconomicCalculationInput
    for field in ('farm_scenario_id','farm_scenario_revision','farm_scenario_sha256','thermal_job_id'):
        changed=dict(original);changed.pop(field)
        with pytest.raises(ValueError):ECONOMIC_INPUT.validate_python(changed)
    for change in ({'input_version':'economic-calculation-input-v1'}, {'approved':True},
                   {'thermal_job_id':'not-a-job'}, {'farm_scenario_sha256':'bad'}):
        with pytest.raises(ValueError):ECONOMIC_INPUT.validate_python(original|change)


def test_http_request_is_closed_and_preserves_legacy_formula():
    submitted=value()|{'idempotency_key':'economic-farm-one'}
    assert ECONOMIC_REQUEST.validate_python(submitted).model_dump(mode='json')==submitted
    legacy={key:item for key,item in submitted.items() if not key.startswith('farm_') and key!='thermal_job_id'}
    legacy['input_version']='economic-calculation-input-v1'
    assert ECONOMIC_REQUEST.validate_python(legacy).model_dump(mode='json')==legacy
    with pytest.raises(ValueError):ECONOMIC_REQUEST.validate_python(submitted|{'formula_version':'generated-money'})
    branches=economic_request_schema()['oneOf']
    assert len(branches)==3 and all(branch['additionalProperties'] is False for branch in branches)
    assert {branch['properties']['input_version']['const'] for branch in branches}=={
        'economic-calculation-input-v1','economic-calculation-input-v2','economic-calculation-input-v3'}
    assert all(branch['properties']['formula_version']['const']==submitted['formula_version']
               for branch in branches)
