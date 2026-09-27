"""Market hold HTTP reads use only the signed store's safe tenant projection."""

from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import create_app
from test_api_job_status import get, UnusedMarketResultStore
from test_api_job_status import UnusedThermalRunStore
from test_market_hold_store import SNAPSHOT_ID, setup


class UnusedJobStore:
    def get_job(self, _tenant, _job_id):
        raise AssertionError("market report must not read job metadata")


def test_market_hold_http_safe_projection_and_tenant_scope(setup):
    store, principal, scope, _, _ = setup
    report = store().issue_not_evaluated("tenant-a", SNAPSHOT_ID, "context-a")
    app = create_app(UnusedJobStore(), store(), UnusedThermalRunStore(),
                     UnusedMarketResultStore(),
                     principal_provider=lambda: principal)
    path = f"/v1/market-hold-reports/{report['hold_report_id']}"

    status, payload = get(app, path)
    assert status == 200
    assert set(payload) == {"hold_report_id", "status", "reasons", "missing_evidence"}
    assert payload["status"] == "hold"
    assert payload["reasons"] == ["market_g0_not_evaluated"]
    assert set(payload["missing_evidence"]) == {
        "market_source_rights", "market_source_vintage", "market_source_qc",
        "approved_market_snapshot"}
    assert all(key not in payload for key in
               ("tenant_id", "snapshot_id", "decision_at_utc", "scope", "rights"))

    scope["scope_version"] = "v2"
    assert get(app, path)[0] == 200  # Old report remains readable as historical hold.
    principal["tenant_id"] = "tenant-b"
    assert get(app, path)[0] == 404
    principal["tenant_id"] = "tenant-a"
    principal["scopes"].remove("market_hold_read")
    assert get(app, path)[0] == 403
    principal["authenticated"] = False
    assert get(app, path)[0] == 401
    assert get(app, "/v1/market-hold-reports/not-a-uuid")[0] == 422
    principal["authenticated"] = True
    principal["scopes"].add("market_hold_read")
    assert get(app, f"/v1/market-hold-reports/{uuid4()}")[0] == 404

    schema = app.openapi()
    assert schema["paths"]["/v1/market-hold-reports/{report_id}"]["get"]["responses"]["200"]


def test_market_hold_http_store_failure_does_not_expose_internal_details(setup):
    _, principal, _, _, _ = setup

    class BrokenMarketHoldStore:
        def get_public_report(self, _tenant, _report_id):
            raise RuntimeError("private signing key or database path")

    app = create_app(UnusedJobStore(), BrokenMarketHoldStore(), UnusedThermalRunStore(),
                     UnusedMarketResultStore(),
                     principal_provider=lambda: principal)
    status, payload = get(app, f"/v1/market-hold-reports/{uuid4()}")
    assert status == 503
    assert payload == {"error": {"code": "store_unavailable",
                                 "message": "Market hold report unavailable"}}
