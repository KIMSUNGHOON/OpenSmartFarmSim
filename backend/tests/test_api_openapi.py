"""Versioned public schema and documented authority match real request behavior."""

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys

from fastapi.openapi.models import OpenAPI
from jsonschema import Draft202012Validator
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.api_contracts import LocationPoint
from app import api_openapi
from test_http_identity import request


OPERATIONS = {
    ('/v1/farm-scenarios','post'): ('registerFarmReplayScenario', ['farm_scenario_write',
        'farm_scenario_read','metadata','artifact','thermal_scenario_read','thermal_snapshot_read',
        'decision_context_read','market_hold_context_read','market_source_read','market_candidate_read']),
    ('/v1/farm-scenarios','get'): ('getFarmReplayScenario', ['farm_scenario_read','metadata','artifact',
        'thermal_scenario_read','thermal_snapshot_read','decision_context_read','market_hold_context_read',
        'market_source_read','market_candidate_read']),
    ('/v1/break-even-plans/receipt','get'): ('getBreakEvenPlanReceipt', ['metadata','artifact','break_even_read']),
    ('/v1/jobs/{job_id}/economic-cash-flow','get'): ('getJobEconomicCashFlow',
        ['metadata','artifact','market_source_read','market_candidate_read','market_result_read',
         'decision_context_read','market_hold_context_read']),
    ('/v1/assessments', 'post'): ('submitCalculationAssessment', ['assessment_create',
        'metadata', 'artifact', 'market_source_read', 'market_candidate_read', 'market_result_read',
        'decision_context_read', 'market_hold_context_read', 'thermal_run_read', 'thermal_snapshot_read']),
    ('/v1/ingestions', 'post'): ('submitOwnedIngestion', ['metadata', 'artifact', 'collection_execute']),
    ('/v1/collection-reviews', 'post'): ('submitOwnedCollectionReview',
        ['metadata', 'artifact', 'collection_read', 'collection_review_create',
         'thermal_snapshot_read', 'thermal_snapshot_write', 'decision_context_read']),
    ('/v1/jobs/{job_id}/break-even-result', 'get'): ('getJobBreakEvenResult',
        ['metadata', 'artifact', 'break_even_read', 'market_source_read', 'market_candidate_read',
         'decision_context_read', 'market_hold_context_read']),
    ('/v1/break-even-plans', 'post'): ('submitBreakEvenPlan',
        ['metadata', 'artifact', 'simulation_execute', 'break_even_read', 'break_even_write',
         'market_source_read', 'market_candidate_read', 'decision_context_read', 'market_hold_context_read']),
    ('/v1/economic-results', 'post'): ('submitEconomicCalculation',
        ['metadata', 'artifact', 'simulation_execute', 'market_source_read', 'market_candidate_read',
         'market_result_read', 'market_result_write', 'decision_context_read', 'market_hold_context_read']),
    ('/v1/jobs/{job_id}/economic-result', 'get'): ('getJobEconomicResult',
        ['metadata', 'artifact', 'market_source_read', 'market_candidate_read', 'market_result_read',
         'decision_context_read', 'market_hold_context_read']),
    ('/v1/economic-scenarios', 'post'): ('registerEconomicScenario',
        ['metadata', 'market_source_read', 'market_candidate_read', 'market_candidate_write',
         'decision_context_read', 'market_hold_context_read']),
    ('/v1/market-user-sources', 'post'): ('registerMarketUserSource',
        ['market_source_write', 'market_source_read', 'metadata']),
    ('/v1/market-user-sources', 'get'): ('listMarketUserSources', ['market_source_read', 'metadata']),
    ('/v1/market-user-sources/record', 'get'): ('getMarketUserSource', ['market_source_read', 'metadata']),
    ('/v1/scenarios', 'post'): ('registerThermalScenario', ['thermal_scenario_write',
        'thermal_scenario_read', 'thermal_snapshot_read', 'decision_context_read', 'market_hold_context_read']),
    ('/v1/scenarios', 'get'): ('getThermalScenario', ['thermal_scenario_read',
        'thermal_snapshot_read', 'decision_context_read', 'market_hold_context_read']),
    ("/v1/runs", "post"): ("submitThermalRun", ['thermal_run_submit', 'metadata', 'artifact',
        'thermal_scenario_read', 'thermal_snapshot_read', 'decision_context_read', 'market_hold_context_read']),
    ("/v1/locations", "post"): ("registerLocation", ["location_create"]),
    ("/v1/jobs/{job_id}", "get"): ("getJob", ["metadata"]),
    ("/v1/jobs/{job_id}/hold-report", "get"): ("getJobHold", ["metadata", "artifact", "auditor"]),
    ("/v1/jobs/{job_id}/run", "get"): ("getJobRun", ["metadata", "artifact", "thermal_run_read"]),
    ("/v1/market-hold-reports/{report_id}", "get"): ("getMarketHold", ["market_hold_read"]),
    ("/v1/runs/{run_id}", "get"): ("getRun", ["thermal_run_read"]),
    ("/v1/runs/{run_id}/series", "get"): ("getRunSeries", ["thermal_run_read"]),
    ("/v1/runs/{run_id}/manifest", "get"): ("getRunManifest", ["thermal_run_read", "thermal_snapshot_read"]),
    ("/v1/economic-results/{result_id}", "get"): ("getEconomicResult", ["market_result_read"]),
    ("/v1/break-even-results", "get"): ("getBreakEvenResult", ["break_even_read"]),
}


def test_snapshot_matches_actual_routes_and_public_protocol():
    document = api_openapi.contract_document()
    assert api_openapi.contract_bytes() == api_openapi.CONTRACT_PATH.read_bytes()
    assert OpenAPI.model_validate(document).openapi == "3.1.0"
    operations = {(path, method): operation for path, methods in document["paths"].items()
                  for method, operation in methods.items()}
    assert set(operations) == set(OPERATIONS)
    for key, (operation_id, scopes) in OPERATIONS.items():
        value = operations[key]
        assert value["operationId"] == operation_id
        assert value["security"] == [{"ServiceBearer": []}]
        assert value["x-ossf-required-scopes"] == scopes
        assert "401" in value["responses"] and "403" in value["responses"]
        for status, response in value["responses"].items():
            if int(status) >= 400:
                assert response["content"]["application/json"]["schema"] == {"$ref": "#/components/schemas/ErrorEnvelope"}
    bearer = document["components"]["securitySchemes"]["ServiceBearer"]
    assert operations[("/v1/jobs/{job_id}/run", "get")]["x-ossf-conditional-scopes"] == {
        "thermal-simulation-result-v2": ['thermal_scenario_read', 'thermal_snapshot_read',
            'decision_context_read', 'market_hold_context_read']}
    assert operations[('/v1/assessments','post')]['x-ossf-conditional-scopes'] == {
        'thermal-simulation-result-v2':['thermal_scenario_read','thermal_snapshot_read',
            'decision_context_read','market_hold_context_read']}
    assert bearer["type"] == "http" and bearer["scheme"] == "bearer" and "bearerFormat" not in bearer
    registration = operations[("/v1/locations", "post")]
    assert registration['x-ossf-conditional-scopes'] == {'owned-research':['metadata','decision_context_read']}
    assert registration["x-ossf-max-body-bytes"] == 4096
    assert "202" in registration["responses"] and "200" not in registration["responses"]
    submission = operations[("/v1/runs", "post")]
    assert submission['x-ossf-max-body-bytes'] == 4096
    assert '202' in submission['responses'] and '200' not in submission['responses']
    raw = api_openapi.contract_bytes()
    assert b"synthetic-service-a-" not in raw and b"tenant-a" not in raw
    assert b"token_sha256" not in raw and b"lease_token" not in raw


def test_references_resolve_locally_and_component_schemas_are_valid():
    document = api_openapi.contract_document()
    references = []
    def walk(value):
        if type(value) is dict:
            if "$ref" in value:
                pointer = value["$ref"]
                assert pointer.startswith("#/")
                target = document
                for piece in pointer[2:].split("/"):
                    target = target[piece.replace("~1", "/").replace("~0", "~")]
                assert type(target) is dict
                references.append(pointer)
            for item in value.values(): walk(item)
        elif type(value) is list:
            for item in value: walk(item)
    walk(document)
    assert references
    for value in document["components"]["schemas"].values():
        Draft202012Validator.check_schema(value)


@pytest.mark.parametrize("value", [{"latitude": 91, "longitude": 127}, {"latitude": 37.5, "longitude": -181},
    {"latitude": True, "longitude": 127}, {"latitude": "37.5", "longitude": 127},
    {"latitude": 37.5}, {"latitude": 37.5, "longitude": 127, "tenant_id": "private"}])
def test_point_runtime_and_schema_reject_the_same_invalid_shapes(value):
    schema = api_openapi.contract_document()["components"]["schemas"]["LocationPoint"]
    assert list(Draft202012Validator(schema).iter_errors(value))
    with pytest.raises(ValueError): LocationPoint.model_validate(value)


@pytest.mark.parametrize("key", OPERATIONS)
def test_each_documented_scope_is_required_before_any_store_read(key):
    path, method = key
    scopes = api_openapi.contract_document()["paths"][path][method]["x-ossf-required-scopes"]
    class Stores:
        calls = 0
        def read(self, *_):
            self.calls += 1
            raise AssertionError("denied request reached storage")
        get_job = get_public_report = get_run = get_snapshot = get_economic_result = get_break_even_read = read
    stores = Stores()
    principal = {"authenticated": True, "tenant_id": "tenant-a", "scopes": set()}
    app = create_app(stores, stores, stores, stores, principal_provider=lambda: principal, break_even_store=stores)
    path = (path.replace("{job_id}", "00000000-0000-4000-8000-000000000001")
        .replace("{report_id}", "00000000-0000-4000-8000-000000000002")
        .replace("{run_id}", "synthetic-thermal-v1:"+"a"*64).replace("{result_id}", "b"*64))
    for missing in scopes:
        principal["scopes"] = set(scopes)-{missing}
        status, body, _ = asyncio.run(request(app, path=path, method=method.upper(),
            query=(b'scenario_id=example&scenario_revision=r1' if path in ('/v1/scenarios','/v1/farm-scenarios')
                else b'plan_id=example&submission_sha256='+b'a'*64 if path == '/v1/break-even-plans/receipt'
                else b'kind=economic_input' if path == '/v1/market-user-sources'
                else b'kind=economic_input&record_id=example&revision=r1' if path == '/v1/market-user-sources/record'
                else b"plan_id=example" if path == "/v1/break-even-results" else b"token=spoofed")))
        assert status == 403 and body["error"]["code"] == "forbidden" and stores.calls == 0


def test_export_does_not_call_principal_or_operational_stores(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("schema export attempted operational access")
    monkeypatch.setattr(api_openapi, "current_principal", forbidden)
    for name in ("get_job", "get_public_report", "get_run", "get_snapshot", "get_economic_result", "get_break_even_read"):
        monkeypatch.setattr(api_openapi._SchemaOnlyStores, name, forbidden)
    assert api_openapi.contract_bytes() == api_openapi.CONTRACT_PATH.read_bytes()


def test_check_detects_missing_or_changed_bytes_and_write_is_exact(tmp_path, monkeypatch, capsys):
    path = tmp_path/"contract.json"
    monkeypatch.setattr(api_openapi, "CONTRACT_PATH", path)
    assert api_openapi.main(["--check"]) == 2
    assert str(path) not in capsys.readouterr().err
    assert api_openapi.main(["--write"]) == 0 and path.read_bytes() == api_openapi.contract_bytes()
    path.write_bytes(path.read_bytes()+b" ")
    assert api_openapi.main(["--check"]) == 2
    assert json.loads(capsys.readouterr().err)["code"] == "openapi_contract_unavailable_or_changed"
    assert api_openapi.main(["--write"]) == 0 and api_openapi.main(["--check"]) == 0


def test_actual_cli_check_runs_without_runtime_credentials():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-m", "app.api_openapi", "--check"], cwd=root,
        env={"PATH": os.defpath, "PYTHONPATH": str(root), "LANG": "C.UTF-8"},
        capture_output=True, timeout=10)
    assert result.returncode == 0 and result.stdout == result.stderr == b""
