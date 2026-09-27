"""Versioned HTTP application assembled with trusted server-side dependencies."""

from uuid import UUID

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api_contracts import (ErrorEnvelope, JobStatus, MarketHoldStatus,
                            public_job_status, public_market_hold)


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status,
                        content={"error": {"code": code, "message": message}})


def create_app(job_store, market_hold_store, *, principal_provider) -> FastAPI:
    if (not callable(principal_provider) or
            not callable(getattr(job_store, "get_job", None)) or
            not callable(getattr(market_hold_store, "get_public_report", None))):
        raise ValueError("API trusted stores and principal provider are required")
    app = FastAPI(title="OpenSmartFarmSim", version="1", openapi_version="3.1.0")

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request, _error_detail):
        return _error(422, "invalid_request", "Invalid request")

    def authorized_tenant(scope: str):
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
        if scope not in principal["scopes"]:
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

    return app
