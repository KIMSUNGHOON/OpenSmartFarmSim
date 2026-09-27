"""The HTTP economic read is a tenant-scoped conditional projection."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import create_app
from app.api_economics import project_economic_result
from app.market_result_store import MarketResultStore
from app.market_scenario import MarketScenarioService
from test_api_job_status import get, UnusedThermalRunStore
from test_api_market_hold import UnusedJobStore
from test_api_thermal_run import UnusedMarketHoldStore
from test_market_signed_hold_integration import signed_market


def test_conditional_economic_result_http_projection_and_replay(signed_market):
    candidate_factory, _, request, principal, scope = signed_market
    candidate = MarketScenarioService(candidate_factory()).build_candidate(request, "tenant-1")

    def store():
        candidates = candidate_factory()
        return MarketResultStore(candidates.dsn, candidates.schema, candidates,
                                 principal_provider=lambda: principal)

    pinned = store().pin_market_result(candidate.scenario_id, candidate.revision)
    assert store().get_economic_result("tenant-1", pinned.economic_result.result_id) == pinned
    assert store().get_economic_result("tenant-2", pinned.economic_result.result_id) is None
    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(),
                     UnusedThermalRunStore(), store(),
                     principal_provider=lambda: principal)
    path = f"/v1/economic-results/{pinned.economic_result.result_id}"

    status, payload = get(app, path)
    assert status == 200
    assert payload["economic_result_id"] == pinned.economic_result.result_id
    assert payload["market_scenario_result_id"] == pinned.result_id
    assert payload["market_context_kind"] == "unavailable"
    assert payload["market_hold_report_id"] == request["market_context"]["hold_report_id"]
    assert payload["calculation_status"] == "conditional_user_assumption"
    assert payload["assessment_status"] == "hold"
    assert payload["input_origin"] == "user" and payload["evidence_level"] == "assumed"
    assert payload["quantities"]["harvest_kg"] == format(pinned.economic_result.harvest_kg, "f")
    assert payload["amounts"]["management_operating_income_krw"] == format(
        pinned.economic_result.management_oi, "f")
    assert payload["sales_totals_status"] == "inventory_reconciled"
    assert all(key not in payload for key in
               ("input_provenance", "closing_inventory", "rights_manifest_sha256",
                "binding_manifest_sha256", "tenant_id", "future_cash_schedule"))
    assert app.openapi()["paths"]["/v1/economic-results/{result_id}"]["get"]["responses"]["200"]

    principal["tenant_id"] = "tenant-2"
    assert get(app, path)[0] == 404
    principal["tenant_id"] = "tenant-1"
    principal["scopes"].remove("market_result_read")
    assert get(app, path)[0] == 403
    principal["scopes"].add("market_result_read")
    principal["authenticated"] = False
    assert get(app, path)[0] == 401
    principal["authenticated"] = True
    assert get(app, "/v1/economic-results/invalid")[0] == 422
    assert get(app, "/v1/economic-results/" + "0" * 64)[0] == 404

    scope["scope_version"] = "v2"
    assert get(app, path) == (503, {"error": {"code": "store_unavailable",
                                     "message": "Economic result unavailable"}})


def test_economic_result_http_fails_closed_on_bad_projection():
    from test_market_result_codec import result

    pinned = result()
    principal = {"authenticated": True, "tenant_id": "tenant-1",
                 "scopes": {"market_result_read"}}

    class BadStore:
        def get_economic_result(self, _tenant, _result_id):
            return replace(pinned, economic_result_ids=())

    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(),
                     UnusedThermalRunStore(), BadStore(),
                     principal_provider=lambda: principal)
    status, payload = get(app, "/v1/economic-results/" + "a" * 64)
    assert status == 503
    assert payload == {"error": {"code": "store_unavailable",
                                 "message": "Economic result unavailable"}}

    class WrongIdStore:
        def get_economic_result(self, _tenant, _result_id):
            return pinned

    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(),
                     UnusedThermalRunStore(), WrongIdStore(),
                     principal_provider=lambda: principal)
    assert get(app, "/v1/economic-results/" + "a" * 64)[0] == 503


def test_economic_projection_keeps_unknown_separate_from_zero():
    from test_market_result_codec import result

    pinned = result()
    context = pinned.market_context.model_copy(update={"hold_report_id": str(uuid4())})
    held_ledger = replace(pinned.economic_result, revenue=None,
                          management_oi=None, operating_cash=None,
                          gross_sales=Decimal("0"), market_context=context,
                          assessment_market_context=context)
    held = replace(pinned, economic_result=held_ledger, market_context=context,
                   calculation_status="hold")
    projected = project_economic_result(held)
    assert projected.amounts.revenue_krw is None
    assert projected.amounts.management_operating_income_krw is None
    assert projected.amounts.gross_sales_krw == "0"

    corrupt = replace(held, economic_result=replace(held_ledger,
                      gross_sales=Decimal("NaN")))
    with pytest.raises(ValueError, match="finite decimal"):
        project_economic_result(corrupt)
