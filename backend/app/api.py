"""Versioned HTTP application assembled with trusted server-side dependencies."""

from uuid import UUID
from typing import Annotated
import json

from fastapi import FastAPI, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .api_contracts import (EconomicResultRead, ErrorEnvelope, JobStatus, MarketHoldStatus,
                            ThermalRunManifest, ThermalRunSeries, ThermalRunSummary,
                            public_job_status,
                            public_market_hold, LocationAccepted, JobHoldStatus, public_job_hold)
from .api_economics import RESULT_ID_PATTERN, project_economic_result
from .api_break_even import PLAN_ID_PATTERN, BreakEvenRead, project_break_even_result
from .api_thermal import RUN_ID_PATTERN, project_thermal_manifest, project_thermal_run
from .api_job_run import read_job_run
from .thermal_scenario_store import ThermalScenarioStore, ThermalScenarioHold
from .thermal_scenario_execution import SCENARIO_SCOPES
from .thermal_publisher import ThermalPublishHold
from .thermal_run_submission import ThermalRunRequest, ThermalRunSubmissionService, SUBMISSION_SCOPES
from .job_store import JobIntentConflict
from .orchestration import LocationRequest, LocationResearchService, ResearchRequestRejected


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status,
                        content={"error": {"code": code, "message": message}})


def _access(scopes):
    return {"security": [{"ServiceBearer": []}], "x-ossf-required-scopes": list(scopes)}


def create_app(job_store, market_hold_store, thermal_run_store, market_result_store,
               *, principal_provider, location_research_service=None, break_even_store=None,
               thermal_scenario_store=None, thermal_run_submission_service=None) -> FastAPI:
    if (not callable(principal_provider) or
            not callable(getattr(job_store, "get_job", None)) or
            not callable(getattr(market_hold_store, "get_public_report", None)) or
            not callable(getattr(thermal_run_store, "get_run", None)) or
            not callable(getattr(thermal_run_store, "get_snapshot", None)) or
            not callable(getattr(market_result_store, "get_economic_result", None))):
        raise ValueError("API trusted stores and principal provider are required")
    if location_research_service is not None and type(location_research_service) is not LocationResearchService:
        raise ValueError("trusted location research service required")
    if break_even_store is not None and not callable(getattr(break_even_store, "get_break_even_read", None)):
        raise ValueError("trusted break-even reader required")
    if thermal_scenario_store is not None and (type(thermal_scenario_store) is not ThermalScenarioStore or
                                              thermal_scenario_store.runs is not thermal_run_store):
        raise ValueError("trusted thermal scenario reader required")
    if thermal_run_submission_service is not None and (
            type(thermal_run_submission_service) is not ThermalRunSubmissionService or
            thermal_run_submission_service.jobs is not job_store or
            thermal_run_submission_service.scenarios is not thermal_scenario_store or
            thermal_run_submission_service.publisher.run_store is not thermal_run_store):
        raise ValueError("trusted thermal submission service required")
    app = FastAPI(title="OpenSmartFarmSim", version="1", openapi_version="3.1.0")
    location_scopes = ("location_create",)
    job_scopes = ("metadata",)
    job_hold_scopes = ("metadata", "artifact", "auditor")
    job_run_scopes = ("metadata", "artifact", "thermal_run_read")
    market_hold_scopes = ("market_hold_read",)
    run_scopes = ("thermal_run_read",)
    manifest_scopes = ("thermal_run_read", "thermal_snapshot_read")
    economic_scopes = ("market_result_read",)
    break_even_scopes = ("break_even_read",)

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

    @app.post("/v1/locations", status_code=202, response_model=LocationAccepted,
              operation_id="registerLocation",
              responses={status: {"model": ErrorEnvelope} for status in (401, 403, 409, 413, 415, 422, 503)},
              openapi_extra={**_access(location_scopes), "x-ossf-max-body-bytes": 4096,
                  "requestBody": {"required": True, "content": {
                  "application/json": {"schema": LocationRequest.model_json_schema()}}}})
    async def post_location(request: Request):
        tenant, denied = authorized_tenant(*location_scopes)
        if denied is not None:
            return denied
        if location_research_service is None:
            return _error(503, "research_unavailable", "Research submission unavailable")
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
            return _error(415, "unsupported_media_type", "JSON request required")
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw)+len(chunk) > 4096:
                return _error(413, "request_too_large", "Request too large")
            raw.extend(chunk)
        def unique_pairs(items):
            value = {}
            for key, item in items:
                if key in value:
                    raise ValueError("duplicate request key")
                value[key] = item
            return value
        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            body = LocationRequest.model_validate(value)
        except (ValueError, UnicodeError, RecursionError):
            return _error(422, "invalid_request", "Invalid request")
        try:
            location, point, row = await run_in_threadpool(location_research_service.submit, tenant, body)
            return LocationAccepted(location_id=location, point=point, spatial_support="pending_research",
                                    research_job=public_job_status(row))
        except PermissionError:
            return _error(403, "forbidden", "Resource access denied")
        except ResearchRequestRejected:
            return _error(422, "unsupported_request", "Research request unsupported")
        except JobIntentConflict:
            return _error(409, "intent_conflict", "Intent already has a different request")
        except Exception:
            return _error(503, "research_unavailable", "Research submission unavailable")

    @app.post("/v1/runs", status_code=202, response_model=JobStatus, operation_id="submitThermalRun",
              responses={status: {"model": ErrorEnvelope} for status in (401, 403, 409, 413, 415, 422, 503)},
              openapi_extra={**_access(SUBMISSION_SCOPES), "x-ossf-max-body-bytes": 4096,
                  "requestBody": {"required": True, "content": {
                  "application/json": {"schema": ThermalRunRequest.model_json_schema()}}}})
    async def post_run(request: Request):
        tenant, denied = authorized_tenant(*SUBMISSION_SCOPES)
        if denied is not None:
            return denied
        if thermal_run_submission_service is None:
            return _error(503, "simulation_unavailable", "Simulation submission unavailable")
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
            return _error(415, "unsupported_media_type", "JSON request required")
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw)+len(chunk) > 4096:
                return _error(413, "request_too_large", "Request too large")
            raw.extend(chunk)
        def unique_pairs(items):
            value = {}
            for key, item in items:
                if key in value:
                    raise ValueError("duplicate request key")
                value[key] = item
            return value
        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            body = ThermalRunRequest.model_validate(value)
        except (ValueError, UnicodeError, RecursionError):
            return _error(422, "invalid_request", "Invalid request")
        try:
            row = await run_in_threadpool(thermal_run_submission_service.submit, tenant, body)
            return public_job_status(row)
        except PermissionError:
            return _error(403, "forbidden", "Resource access denied")
        except (ThermalScenarioHold, ThermalPublishHold):
            return _error(422, "simulation_hold", "Simulation evidence unavailable")
        except JobIntentConflict:
            return _error(409, "intent_conflict", "Intent already has a different request")
        except Exception:
            return _error(503, "simulation_unavailable", "Simulation submission unavailable")

    @app.get("/v1/jobs/{job_id}", response_model=JobStatus, responses=errors,
             operation_id="getJob", openapi_extra=_access(job_scopes))
    def get_job(job_id: UUID):
        tenant, denied = authorized_tenant(*job_scopes)
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
             responses=errors, operation_id="getMarketHold", openapi_extra=_access(market_hold_scopes))
    def get_market_hold_report(report_id: UUID):
        tenant, denied = authorized_tenant(*market_hold_scopes)
        if denied is not None:
            return denied
        try:
            row = market_hold_store.get_public_report(tenant, str(report_id))
            if row is None:
                return _error(404, "not_found", "Market hold report not found")
            return public_market_hold(row)
        except Exception:
            return _error(503, "store_unavailable", "Market hold report unavailable")

    @app.get("/v1/jobs/{job_id}/hold-report", response_model=JobHoldStatus, responses=errors,
             operation_id="getJobHold", openapi_extra=_access(job_hold_scopes))
    def get_job_hold_report(job_id: UUID):
        tenant, denied = authorized_tenant(*job_hold_scopes)
        if denied is not None:
            return denied
        try:
            job = job_store.get_job(tenant, job_id)
            if (job is None or job["tenant_id"] != tenant or job["state"] != "hold" or
                    job.get("reason", {}).get("code") != "ai_validated_hold"):
                return _error(404, "not_found", "Job hold report not found")
            if job["job_id"] != job_id:
                raise ValueError("job identity mismatch")
            held = job_store.get_hold_report(tenant, job_id)
            raw = job_store.read_hold_report(tenant, job_id)
            if held is None or raw is None:
                return _error(404, "not_found", "Job hold report not found")
            return public_job_hold(job, held, raw)
        except Exception:
            return _error(503, "store_unavailable", "Job hold report unavailable")

    @app.get("/v1/jobs/{job_id}/run", response_model=ThermalRunSummary, responses=errors,
             operation_id="getJobRun", openapi_extra={**_access(job_run_scopes),
                 "x-ossf-conditional-scopes": {"thermal-simulation-result-v2": list(SCENARIO_SCOPES)}})
    def get_job_run(job_id: UUID):
        tenant, denied = authorized_tenant(*job_run_scopes)
        if denied is not None:
            return denied
        try:
            result = read_job_run(job_store, thermal_run_store, tenant, job_id, thermal_scenario_store)
            if result is None:
                return _error(404, "not_found", "Job Run not found")
            return result
        except PermissionError:
            return _error(403, "forbidden", "Resource access denied")
        except Exception:
            return _error(503, "store_unavailable", "Job Run unavailable")

    def displayed_run(run_id):
        tenant, denied = authorized_tenant(*run_scopes)
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

    @app.get("/v1/runs/{run_id}", response_model=ThermalRunSummary, responses=errors,
             operation_id="getRun", openapi_extra=_access(run_scopes))
    def get_run(run_id: RunId):
        result = displayed_run(run_id)
        return result if isinstance(result, JSONResponse) else result[0]

    @app.get("/v1/runs/{run_id}/series", response_model=ThermalRunSeries, responses=errors,
             operation_id="getRunSeries", openapi_extra=_access(run_scopes))
    def get_run_series(run_id: RunId):
        result = displayed_run(run_id)
        return result if isinstance(result, JSONResponse) else result[1]

    @app.get("/v1/runs/{run_id}/manifest", response_model=ThermalRunManifest,
             responses=errors, operation_id="getRunManifest", openapi_extra=_access(manifest_scopes))
    def get_run_manifest(run_id: RunId):
        tenant, denied = authorized_tenant(*manifest_scopes)
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
             responses=errors, operation_id="getEconomicResult", openapi_extra=_access(economic_scopes))
    def get_economic_result(result_id: Annotated[str, Path(pattern=RESULT_ID_PATTERN)]):
        tenant, denied = authorized_tenant(*economic_scopes)
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

    @app.get("/v1/break-even-results", response_model=BreakEvenRead, responses=errors,
             operation_id="getBreakEvenResult", openapi_extra=_access(break_even_scopes))
    def get_break_even_result(plan_id: Annotated[str, Query(pattern=PLAN_ID_PATTERN, max_length=200)]):
        tenant, denied = authorized_tenant(*break_even_scopes)
        if denied is not None:
            return denied
        try:
            if break_even_store is None:
                raise ValueError("break-even reader unavailable")
            held = break_even_store.get_break_even_read(tenant, plan_id)
            if held is None:
                return _error(404, "not_found", "Break-even result not found")
            request, result = held
            if request.plan_id != plan_id:
                raise ValueError("break-even request identity differs")
            return project_break_even_result(request, result)
        except Exception:
            return _error(503, "store_unavailable", "Break-even result unavailable")

    original_openapi = app.openapi
    def service_openapi():
        schema = original_openapi()
        schema["components"]["securitySchemes"] = {"ServiceBearer": {
            "type": "http", "scheme": "bearer",
            "description": "Opaque server-issued service credential over HTTPS. Tenant and scopes are server-owned."}}
        return schema
    app.openapi = service_openapi
    return app
