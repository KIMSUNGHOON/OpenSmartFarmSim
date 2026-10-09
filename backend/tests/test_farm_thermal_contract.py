"""Closed version discrimination preserves old shapes and rejects missing pins."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.thermal_simulation_worker import SIMULATION_INPUT, FarmSimulationInput
from app.jobs import canonical_input_bytes
from app.thermal_run_submission import RUN_REQUEST, FarmThermalRunRequest, run_request_schema


def value():
    return {'input_version':'thermal-simulation-input-v3','snapshot_id':'thermal-snapshot-v1:'+'a'*64,
        'review_job_id':'00000000-0000-4000-8000-000000000001','scenario_id':'thermal-one',
        'scenario_revision':'r1','scenario_sha256':'b'*64,'farm_scenario_id':'farm-one',
        'farm_scenario_revision':'r1','farm_scenario_sha256':'c'*64}


def test_complete_farm_input_is_closed_and_versioned():
    original=value()
    parsed=SIMULATION_INPUT.validate_json(canonical_input_bytes(original))
    assert type(parsed) is FarmSimulationInput and parsed.model_dump(mode='json')==original
    for field in ('farm_scenario_id','farm_scenario_revision','farm_scenario_sha256'):
        changed=dict(original);changed.pop(field)
        with pytest.raises(ValueError):SIMULATION_INPUT.validate_json(canonical_input_bytes(changed))
    with pytest.raises(ValueError):
        SIMULATION_INPUT.validate_json(canonical_input_bytes(original|{'input_version':'thermal-simulation-input-v2'}))
    with pytest.raises(ValueError):
        SIMULATION_INPUT.validate_json(canonical_input_bytes(original|{'approved':True}))
    with pytest.raises(ValueError):
        SIMULATION_INPUT.validate_json(canonical_input_bytes(original|{'farm_scenario_sha256':'unfixed'}))


def test_http_request_requires_all_farm_pins_and_preserves_v2():
    submitted=value()|{'model_version':'thermal-v1',
        'parameter_set_version':'synthetic-thermal-parameters-v1','idempotency_key':'farm-run'}
    assert type(RUN_REQUEST.validate_python(submitted)) is FarmThermalRunRequest
    for field in ('farm_scenario_id','farm_scenario_revision','farm_scenario_sha256'):
        incomplete=dict(submitted);incomplete.pop(field)
        with pytest.raises(ValueError):RUN_REQUEST.validate_python(incomplete)
    legacy={key:item for key,item in submitted.items() if not key.startswith('farm_')}
    legacy['input_version']='thermal-simulation-input-v2'
    assert RUN_REQUEST.validate_python(legacy).model_dump(mode='json')==legacy
    schema=run_request_schema()
    assert len(schema['oneOf'])==2
    assert all(branch['additionalProperties'] is False for branch in schema['oneOf'])
    assert schema['oneOf'][1]['properties']['input_version']['const']=='thermal-simulation-input-v3'
    assert {'farm_scenario_id','farm_scenario_revision','farm_scenario_sha256'}<=set(schema['oneOf'][1]['required'])
