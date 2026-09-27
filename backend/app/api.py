"""Versioned HTTP application assembled with trusted server-side dependencies."""

from uuid import UUID

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api_contracts import ErrorEnvelope, JobStatus, public_job_status


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status,
                        content={"error": {"code": code, "message": message}})


def create_app(job_store, *, principal_provider) -> FastAPI:
    if not callable(principal_provider):
        raise ValueError("API principal provider is required")
    app = FastAPI(title="OpenSmartFarmSim", version="1", openapi_version="3.1.0")

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request, _error_detail):
        return _error(422, "invalid_request", "Invalid request")

    @app.get("/v1/jobs/{job_id}", response_model=JobStatus,
             responses={status: {"model": ErrorEnvelope} for status in (401, 403, 404, 422, 503)})
    def get_job(job_id: UUID):
        try:
            principal = principal_provider()
        except Exception:
            return _error(401, "unauthenticated", "Authentication required")
        if (type(principal) is not dict or principal.get("authenticated") is not True or
                type(principal.get("tenant_id")) is not str or
                not principal["tenant_id"] or
                not isinstance(principal.get("scopes"), (set, frozenset, list, tuple)) or
                not all(type(scope) is str for scope in principal["scopes"])):
            return _error(401, "unauthenticated", "Authentication required")
        if "metadata" not in principal["scopes"]:
            return _error(403, "forbidden", "Job metadata access denied")
        try:
            row = job_store.get_job(principal["tenant_id"], job_id)
            if row is None:
                return _error(404, "not_found", "Job not found")
            if row["tenant_id"] != principal["tenant_id"]:
                return _error(404, "not_found", "Job not found")
            return public_job_status(row)
        except Exception:
            return _error(503, "store_unavailable", "Job status unavailable")

    return app
