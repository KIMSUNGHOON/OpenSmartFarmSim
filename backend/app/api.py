"""Versioned HTTP application assembled with trusted server-side dependencies."""

from uuid import UUID
from typing import Annotated

from fastapi import FastAPI, Path
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api_contracts import (EconomicResultRead, ErrorEnvelope, JobStatus, MarketHoldStatus,
                            ThermalRunManifest, ThermalRunSeries, ThermalRunSummary,
                            public_job_status,
                            public_market_hold)
from .api_economics import RESULT_ID_PATTERN, project_economic_result
from .api_thermal import RUN_ID_PATTERN, project_thermal_manifest, project_thermal_run


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status,
                        content={"error": {"code": code, "message": message}})


def create_app(job_store, market_hold_store, thermal_run_store, market_result_store,
               *, principal_provider) -> FastAPI:
    if (not callable(principal_provider) or
            not callable(getattr(job_store, "get_job", None)) or
            not callable(getattr(market_hold_store, "get_public_report", None)) or
            not callable(getattr(thermal_run_store, "get_run", None)) or
            not callable(getattr(thermal_run_store, "get_snapshot", None)) or
            not callable(getattr(market_result_store, "get_economic_result", None))):
        raise ValueError("API trusted stores and principal provider are required")
    app = FastAPI(title="OpenSmartFarmSim", version="1", openapi_version="3.1.0")

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request, _error_detail):
        return _error(422, "invalid_request", "Invalid request")

    def authorized_tenant(*required_scopes: str):
        try:
            principal = principal_provider()
        except Exception:
            return None, _error(401, "unauthenticated", "Authentication required")
        if (type(principal) is not dict or principal.get("authenticated") is not True or
                type(principal.get("tenant_id")) is not str or
                not principal["tenant_id"] or
                not isinstance(principal.get("scopes"), (set, frozenset, list, tuple)) or
                not all(type(item) is str for item in principal["scopes"])):
            return None, _error(401, "unauthenticated", "Authentication required")
        if any(scope not in principal["scopes"] for scope in required_scopes):
            return None, _error(403, "forbidden", "Resource access denied")
        return principal["tenant_id"], None

    errors = {status: {"model": ErrorEnvelope} for status in (401, 403, 404, 422, 503)}

    @app.get("/v1/jobs/{job_id}", response_model=JobStatus, responses=errors)
    def get_job(job_id: UUID):
        tenant, denied = authorized_tenant("metadata")
        if denied is not None:
            return denied
        try:
            row = job_store.get_job(tenant, job_id)
            if row is None:
                return _error(404, "not_found", "Job not found")
            if row["tenant_id"] != tenant:
                return _error(404, "not_found", "Job not found")
            return public_job_status(row)
        except Exception:
            return _error(503, "store_unavailable", "Job status unavailable")

    @app.get("/v1/market-hold-reports/{report_id}", response_model=MarketHoldStatus,
             responses=errors)
    def get_market_hold_report(report_id: UUID):
        tenant, denied = authorized_tenant("market_hold_read")
        if denied is not None:
            return denied
        try:
            row = market_hold_store.get_public_report(tenant, str(report_id))
            if row is None:
                return _error(404, "not_found", "Market hold report not found")
            return public_market_hold(row)
        except Exception:
            return _error(503, "store_unavailable", "Market hold report unavailable")

    def displayed_run(run_id):
        tenant, denied = authorized_tenant("thermal_run_read")
        if denied is not None:
            return denied
        try:
            stored = thermal_run_store.get_run(tenant, run_id)
            if stored is None:
                return _error(404, "not_found", "Run not found")
            return project_thermal_run(stored)
        except Exception:
            return _error(503, "store_unavailable", "Run unavailable")

    RunId = Annotated[str, Path(pattern=RUN_ID_PATTERN)]

    @app.get("/v1/runs/{run_id}", response_model=ThermalRunSummary, responses=errors)
    def get_run(run_id: RunId):
        result = displayed_run(run_id)
        return result if isinstance(result, JSONResponse) else result[0]

    @app.get("/v1/runs/{run_id}/series", response_model=ThermalRunSeries, responses=errors)
    def get_run_series(run_id: RunId):
        result = displayed_run(run_id)
        return result if isinstance(result, JSONResponse) else result[1]

    @app.get("/v1/runs/{run_id}/manifest", response_model=ThermalRunManifest,
             responses=errors)
    def get_run_manifest(run_id: RunId):
        tenant, denied = authorized_tenant("thermal_run_read", "thermal_snapshot_read")
        if denied is not None:
            return denied
        try:
            stored = thermal_run_store.get_run(tenant, run_id)
            if stored is None:
                return _error(404, "not_found", "Run not found")
            snapshot = thermal_run_store.get_snapshot(tenant, stored["report"]["snapshot_id"])
            if snapshot is None:
                return _error(503, "store_unavailable", "Run manifest unavailable")
            return project_thermal_manifest(stored, snapshot)
        except Exception:
            return _error(503, "store_unavailable", "Run manifest unavailable")

    @app.get("/v1/economic-results/{result_id}", response_model=EconomicResultRead,
             responses=errors)
    def get_economic_result(result_id: Annotated[str, Path(pattern=RESULT_ID_PATTERN)]):
        tenant, denied = authorized_tenant("market_result_read")
        if denied is not None:
            return denied
        try:
            result = market_result_store.get_economic_result(tenant, result_id)
            if result is None:
                return _error(404, "not_found", "Economic result not found")
            if result.economic_result.result_id != result_id:
                raise ValueError("economic result ID differs from request")
            return project_economic_result(result)
        except Exception:
            return _error(503, "store_unavailable", "Economic result unavailable")

    return app
