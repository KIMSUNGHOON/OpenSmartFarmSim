"""The external scenario schema agrees with the runtime without a database."""

import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.thermal_scenario_store import ThermalScenario


def test_schema_matches_closed_runtime_contract():
    path = Path(__file__).resolve().parents[2]/'contracts/thermal-scenario-v1.schema.json'
    document = json.loads(path.read_bytes())
    assert document == ThermalScenario.model_json_schema()
    Draft202012Validator.check_schema(document)
    assert document['additionalProperties'] is False
