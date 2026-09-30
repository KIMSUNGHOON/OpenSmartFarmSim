"""Versioned HTTP application assembled with trusted server-side dependencies."""

from uuid import UUID
from typing import Annotated

from fastapi import FastAPI, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .api_contracts import (AuthoredThermalRunSummary, EconomicResultRead, ErrorEnvelope, JobStatus, MarketHoldStatus,
                            ThermalRunManifest, ThermalRunSeries, ThermalRunSummary,
                            public_job_status,
                            public_market_hold, LocationAccepted, JobHoldStatus, public_job_hold)
from .api_economics import RESULT_ID_PATTERN, project_economic_result
from .api_economic_cash_flow import EconomicCashPage, CashCursorRejected, MONTH_PATTERN
from .api_break_even import PLAN_ID_PATTERN, BreakEvenRead, project_break_even_result
from .api_thermal import RUN_ID_PATTERN, project_thermal_manifest, project_thermal_run
from .api_authored_thermal import (AUTHORED_READ_SCOPES, AUTHORED_RUN_ID_PATTERN,
    project_authored_run, read_authored_job_run)
from .farm_authored_run_store import AuthoredRunStore
from .api_job_run import read_job_run
from .api_job_break_even_result import BreakEvenJobResultService, BREAK_EVEN_JOB_READ_SCOPES
from .thermal_scenario_store import ThermalScenarioStore, ThermalScenarioHold, ThermalScenarioConflict, IDENTIFIER
from .thermal_scenario_execution import SCENARIO_SCOPES
from .thermal_publisher import ThermalPublishHold
from .thermal_run_submission import (RUN_REQUEST, run_request_schema, ThermalRunSubmissionService,
    FarmThermalRunRequest, SUBMISSION_SCOPES, FARM_SUBMISSION_SCOPES)
from .farm_thermal_execution import FarmThermalHold
from .api_json import read_json_request, JsonRequestRejected
from .api_scenario import ThermalScenarioRequest, ThermalScenarioSummary, project_scenario, scenario_request_schema
from .api_market_source import (MarketUserSourceRequest, MarketUserSourceSummary,
    MarketUserSourceService, SOURCE_SCOPES, SOURCE_READ_SCOPES, market_user_source_schema,
    SourceKind, MarketUserSourceRead, MarketUserSourcePage)
from .provenance import Name
from .market_source_store import MarketSourceDenied, MarketSourceConflict
from .api_economic_scenario import (EconomicScenarioService, EconomicScenarioRequest,
    EconomicScenarioSummary, ECONOMIC_SCENARIO_SCOPES)
from .api_market_source import _inline_schema
from .market_candidate_store import MarketCandidateDenied, MarketCandidateConflict
from .api_economic_calculation import (EconomicCalculationService, ECONOMIC_REQUEST,
    FarmEconomicCalculationRequest, economic_request_schema,
    EconomicCalculationHold, ECONOMIC_JOB_READ_SCOPES)
from .farm_economic_execution import FARM_ECONOMIC_SCOPES
from .economic_calculation_worker import CALCULATION_SCOPES
from .break_even_plan_submission import (BreakEvenPlanSubmissionService, BreakEvenPlanSubmission,
    BreakEvenPlanAccepted, PLAN_SUBMISSION_SCOPES, BreakEvenPlanReceipt, PLAN_RECEIPT_SCOPES, PlanReceiptConflict)
from .jobs import canonical_input_bytes
from .job_store import JobIntentConflict
from .orchestration import LocationRequest, LocationResearchService, ResearchRequestRejected
from .api_owned_collection import OwnedIngestionRequest, OwnedReviewRequest
from .owned_fixture_collection import CollectionService, CollectionHold, COLLECTION_SCOPES
from .owned_collection_review import OwnedCollectionReviewService, CollectionReviewHold, REVIEW_SCOPES
from .owned_research import OwnedResearchService, READ_SCOPES as OWNED_RESEARCH_READ_SCOPES, ADMISSION_SCOPES as OWNED_RESEARCH_SCOPES
from .api_assessment import CalculationAssessmentRequest
from .calculation_assessment import (CalculationAssessmentService, CalculationAssessmentHold,
    ADMISSION_SCOPES as ASSESSMENT_SCOPES)
from .farm_replay_scenario import (FarmReplayScenarioService, FarmReplayScenarioRequest,
    FarmReplayScenarioSummary, FarmReplayScenarioHold,
    READ_SCOPES as FARM_READ_SCOPES, WRITE_SCOPES as FARM_WRITE_SCOPES)
from .farm_authoring_storage import (FarmAuthoringService, FarmAuthoringRequest,
    FarmAuthoringSummary, FarmAuthoringHold,
    READ_SCOPES as FARM_AUTHORING_READ_SCOPES, WRITE_SCOPES as FARM_AUTHORING_WRITE_SCOPES)
from .farm_authored_review import (FarmAuthoredReviewService, FarmAuthoredReviewHold,
    REVIEW_SCOPES as AUTHORED_REVIEW_SCOPES)
from .api_farm_authored_review import FarmAuthoredReviewRequest


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status,
                        content={"error": {"code": code, "message": message}})


def _access(scopes):
    return {"security": [{"ServiceBearer": []}], "x-ossf-required-scopes": list(scopes)}


def create_app(job_store, market_hold_store, thermal_run_store, market_result_store,
               *, principal_provider, location_research_service=None, break_even_store=None,
               thermal_scenario_store=None, thermal_run_submission_service=None,
               market_user_source_service=None, economic_scenario_service=None,
               economic_calculation_service=None, break_even_plan_service=None,
               break_even_job_result_service=None, collection_service=None,
               owned_collection_review_service=None, assessment_service=None,
               farm_scenario_service=None, authored_run_store=None,
               farm_authoring_service=None, farm_authored_review_service=None) -> FastAPI:
    if (not callable(principal_provider) or
            not callable(getattr(job_store, "get_job", None)) or
            not callable(getattr(market_hold_store, "get_public_report", None)) or
            not callable(getattr(thermal_run_store, "get_run", None)) or
            not callable(getattr(thermal_run_store, "get_snapshot", None)) or
            not callable(getattr(market_result_store, "get_economic_result", None))):
        raise ValueError("API trusted stores and principal provider are required")
    if authored_run_store is not None and (
            type(authored_run_store) is not AuthoredRunStore or
            authored_run_store.jobs is not job_store or
            job_store.principal_provider is not principal_provider):
        raise ValueError('trusted authored Run reader required')
    if location_research_service is not None and type(location_research_service) not in (LocationResearchService, OwnedResearchService):
        raise ValueError("trusted location research service required")
    if type(location_research_service) is OwnedResearchService and (
            location_research_service.store is not job_store or location_research_service.runs is not thermal_run_store or
            job_store.principal_provider is not principal_provider):
        raise ValueError('trusted owned research service required')
    if break_even_store is not None and not callable(getattr(break_even_store, "get_break_even_read", None)):
        raise ValueError("trusted break-even reader required")
    if thermal_scenario_store is not None and (type(thermal_scenario_store) is not ThermalScenarioStore or
                                              thermal_scenario_store.runs is not thermal_run_store):
        raise ValueError("trusted thermal scenario reader required")
    if thermal_run_submission_service is not None and (
            type(thermal_run_submission_service) is not ThermalRunSubmissionService or
            thermal_run_submission_service.jobs is not job_store or
            thermal_run_submission_service.scenarios is not thermal_scenario_store or
            thermal_run_submission_service.publisher.run_store is not thermal_run_store or
            thermal_run_submission_service.farm_scenario_service is not farm_scenario_service):
        raise ValueError("trusted thermal submission service required")
    if market_user_source_service is not None and (
            type(market_user_source_service) is not MarketUserSourceService or
            market_user_source_service.jobs is not job_store):
        raise ValueError('trusted market user source service required')
    if economic_scenario_service is not None and (
            type(economic_scenario_service) is not EconomicScenarioService or
            economic_scenario_service.jobs is not job_store):
        raise ValueError('trusted economic scenario service required')
    if farm_scenario_service is not None and (
            type(farm_scenario_service) is not FarmReplayScenarioService or
            farm_scenario_service.jobs is not job_store or farm_scenario_service.thermal is not thermal_scenario_store or
            job_store.principal_provider is not principal_provider or
            farm_scenario_service.thermal.holds is not market_hold_store):
        raise ValueError('trusted farm scenario service required')
    if farm_authoring_service is not None and (
            type(farm_authoring_service) is not FarmAuthoringService or
            farm_authoring_service.replay is not farm_scenario_service or
            farm_scenario_service is None or
            farm_scenario_service.owned_research is None or
            farm_scenario_service.jobs is not job_store):
        raise ValueError('trusted farm authoring service required')
    if farm_authored_review_service is not None and (
            type(farm_authored_review_service) is not FarmAuthoredReviewService or
            farm_authored_review_service.authoring is not farm_authoring_service or
            farm_authoring_service is None):
        raise ValueError('trusted farm authored review service required')
    if economic_calculation_service is not None and (
            type(economic_calculation_service) is not EconomicCalculationService or
            economic_calculation_service.jobs is not job_store or
            economic_calculation_service.results is not market_result_store or
            economic_calculation_service.farm_scenario_service is not farm_scenario_service):
        raise ValueError('trusted economic calculation service required')
    if break_even_plan_service is not None and (
            type(break_even_plan_service) is not BreakEvenPlanSubmissionService or
            break_even_plan_service.jobs is not job_store or break_even_plan_service.store is not break_even_store):
        raise ValueError('trusted break-even plan service required')
    if break_even_job_result_service is not None and (
            type(break_even_job_result_service) is not BreakEvenJobResultService or
            break_even_job_result_service.jobs is not job_store or
            break_even_job_result_service.store is not break_even_store):
        raise ValueError('trusted break-even job result service required')
    if collection_service is not None and (type(collection_service) is not CollectionService or
            collection_service.jobs is not job_store or job_store.principal_provider is not principal_provider):
        raise ValueError('trusted collection service required')
    if owned_collection_review_service is not None and (
            type(owned_collection_review_service) is not OwnedCollectionReviewService or
            owned_collection_review_service.collection is not collection_service or
            owned_collection_review_service.runs is not thermal_run_store):
        raise ValueError('trusted collection review service required')
    if assessment_service is not None and (
            type(assessment_service) is not CalculationAssessmentService or
            assessment_service.jobs is not job_store or assessment_service.runs is not thermal_run_store or
            assessment_service.results is not market_result_store or
            assessment_service.scenario_store is not thermal_scenario_store or
            assessment_service.farm_scenario_service is not farm_scenario_service or
            job_store.principal_provider is not principal_provider):
        raise ValueError('trusted calculation assessment service required')
    app = FastAPI(title="OpenSmartFarmSim", version="1", openapi_version="3.1.0")
    location_scopes = ("location_create",)
    location_admission_scopes = OWNED_RESEARCH_SCOPES if type(location_research_service) is OwnedResearchService else location_scopes
    job_scopes = ("metadata",)
    job_hold_scopes = ("metadata", "artifact", "auditor")
    job_run_scopes = ("metadata", "artifact", "thermal_run_read")
    market_hold_scopes = ("market_hold_read",)
    run_scopes = ("thermal_run_read",)
    manifest_scopes = ("thermal_run_read", "thermal_snapshot_read")
    authored_scopes = AUTHORED_READ_SCOPES
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
                  'x-ossf-conditional-scopes':{'owned-research': list(OWNED_RESEARCH_READ_SCOPES)},
                  "requestBody": {"required": True, "content": {
                  "application/json": {"schema": LocationRequest.model_json_schema()}}}})
    async def post_location(request: Request):
        tenant, denied = authorized_tenant(*location_admission_scopes)
        if denied is not None:
            return denied
        if location_research_service is None:
            return _error(503, "research_unavailable", "Research submission unavailable")
        try:
            body = LocationRequest.model_validate(await read_json_request(request))
        except JsonRequestRejected as exc:
            return _error(exc.status, exc.code, exc.message)
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

    @app.post('/v1/ingestions', status_code=202, response_model=JobStatus, operation_id='submitOwnedIngestion',
              responses={status: {'model': ErrorEnvelope} for status in (401, 403, 409, 413, 415, 422, 503)},
              openapi_extra={**_access(COLLECTION_SCOPES), 'x-ossf-max-body-bytes':4096,
                  'requestBody': {'required':True, 'content': {'application/json': {
                  'schema':OwnedIngestionRequest.model_json_schema()}}}})
    async def post_owned_ingestion(request: Request):
        tenant, denied = authorized_tenant(*COLLECTION_SCOPES)
        if denied is not None:
            return denied
        if collection_service is None:
            return _error(503, 'collection_unavailable', 'Collection unavailable')
        try:
            body = OwnedIngestionRequest.model_validate_json(canonical_input_bytes(await read_json_request(request)))
        except JsonRequestRejected as exc:
            return _error(exc.status, exc.code, exc.message)
        except (ValueError, UnicodeError, RecursionError):
            return _error(422, 'invalid_request', 'Invalid request')
        try:
            row = await run_in_threadpool(collection_service.submit, tenant, body.research_job_id, body.idempotency_key)
            return public_job_status(row)
        except PermissionError:
            return _error(403, 'forbidden', 'Resource access denied')
        except CollectionHold:
            return _error(422, 'collection_hold', 'Collection input unavailable')
        except JobIntentConflict:
            return _error(409, 'intent_conflict', 'Intent already has a different request')
        except Exception:
            return _error(503, 'collection_unavailable', 'Collection unavailable')

    @app.post('/v1/collection-reviews', status_code=202, response_model=JobStatus, operation_id='submitOwnedCollectionReview',
              responses={status: {'model': ErrorEnvelope} for status in (401, 403, 409, 413, 415, 422, 503)},
              openapi_extra={**_access(REVIEW_SCOPES), 'x-ossf-max-body-bytes':4096,
                  'requestBody': {'required':True, 'content': {'application/json': {
                  'schema':OwnedReviewRequest.model_json_schema()}}}})
    async def post_owned_collection_review(request: Request):
        tenant, denied = authorized_tenant(*REVIEW_SCOPES)
        if denied is not None:
            return denied
        if owned_collection_review_service is None:
            return _error(503, 'collection_review_unavailable', 'Collection review unavailable')
        try:
            body = OwnedReviewRequest.model_validate_json(canonical_input_bytes(await read_json_request(request)))
        except JsonRequestRejected as exc:
            return _error(exc.status, exc.code, exc.message)
        except (ValueError, UnicodeError, RecursionError):
            return _error(422, 'invalid_request', 'Invalid request')
        try:
            row = await run_in_threadpool(owned_collection_review_service.submit,
                tenant, body.collection_job_id, body.idempotency_key)
            return public_job_status(row)
        except PermissionError:
            return _error(403, 'forbidden', 'Resource access denied')
        except CollectionReviewHold:
            return _error(422, 'collection_review_hold', 'Collection review input unavailable')
        except JobIntentConflict:
            return _error(409, 'intent_conflict', 'Intent already has a different request')
        except Exception:
            return _error(503, 'collection_review_unavailable', 'Collection review unavailable')

    @app.post("/v1/runs", status_code=202, response_model=JobStatus, operation_id="submitThermalRun",
              responses={status: {"model": ErrorEnvelope} for status in (401, 403, 409, 413, 415, 422, 503)},
              openapi_extra={**_access(SUBMISSION_SCOPES), "x-ossf-max-body-bytes": 4096,
                  'x-ossf-conditional-scopes':{'thermal-simulation-input-v3':list(FARM_SUBMISSION_SCOPES)},
                  "requestBody": {"required": True, "content": {
                  "application/json": {"schema": run_request_schema()}}}})
    async def post_run(request: Request):
        tenant, denied = authorized_tenant(*SUBMISSION_SCOPES)
        if denied is not None:
            return denied
        if thermal_run_submission_service is None:
            return _error(503, "simulation_unavailable", "Simulation submission unavailable")
        try:
            body = RUN_REQUEST.validate_python(await read_json_request(request))
        except JsonRequestRejected as exc:
            return _error(exc.status, exc.code, exc.message)
        except (ValueError, UnicodeError, RecursionError):
            return _error(422, "invalid_request", "Invalid request")
        try:
            if type(body) is FarmThermalRunRequest:
                _, denied = authorized_tenant(*FARM_SUBMISSION_SCOPES)
                if denied is not None:
                    return denied
            row = await run_in_threadpool(thermal_run_submission_service.submit, tenant, body)
            return public_job_status(row)
        except PermissionError:
            return _error(403, "forbidden", "Resource access denied")
        except (ThermalScenarioHold, ThermalPublishHold, FarmThermalHold):
            return _error(422, "simulation_hold", "Simulation evidence unavailable")
        except JobIntentConflict:
            return _error(409, "intent_conflict", "Intent already has a different request")
        except Exception:
            return _error(503, "simulation_unavailable", "Simulation submission unavailable")

    @app.post('/v1/farm-scenarios', response_model=FarmReplayScenarioSummary, operation_id='registerFarmReplayScenario',
              responses={status:{'model':ErrorEnvelope} for status in (401,403,409,413,415,422,503)},
              openapi_extra={**_access(FARM_WRITE_SCOPES),'x-ossf-max-body-bytes':4096,
                  'requestBody':{'required':True,'content':{'application/json':{
                      'schema':_inline_schema(FarmReplayScenarioRequest)}}}})
    async def post_farm_scenario(request: Request):
        tenant, denied = authorized_tenant(*FARM_WRITE_SCOPES)
        if denied is not None:
            return denied
        if farm_scenario_service is None:
            return _error(503,'farm_scenario_unavailable','Farm scenario registration unavailable')
        try:
            body = FarmReplayScenarioRequest.model_validate_json(canonical_input_bytes(await read_json_request(request)))
        except JsonRequestRejected as exc:
            return _error(exc.status,exc.code,exc.message)
        except (ValueError,UnicodeError,RecursionError):
            return _error(422,'invalid_request','Invalid request')
        try:
            return await run_in_threadpool(farm_scenario_service.submit,tenant,body)
        except PermissionError:
            return _error(403,'forbidden','Resource access denied')
        except JobIntentConflict:
            return _error(409,'scenario_conflict','Scenario version already has different input')
        except FarmReplayScenarioHold:
            return _error(422,'farm_scenario_hold','Farm scenario input unavailable')
        except Exception:
            return _error(503,'farm_scenario_unavailable','Farm scenario registration unavailable')

    @app.get('/v1/farm-scenarios', response_model=FarmReplayScenarioSummary, operation_id='getFarmReplayScenario',
             responses={status:{'model':ErrorEnvelope} for status in (401,403,404,422,503)},
             openapi_extra=_access(FARM_READ_SCOPES))
    async def get_farm_scenario(scenario_id: Annotated[str,Query(pattern=IDENTIFIER,max_length=200)],
                                scenario_revision: Annotated[str,Query(pattern=IDENTIFIER,max_length=200)]):
        tenant, denied = authorized_tenant(*FARM_READ_SCOPES)
        if denied is not None:
            return denied
        if farm_scenario_service is None:
            return _error(503,'farm_scenario_unavailable','Farm scenario read unavailable')
        try:
            row = await run_in_threadpool(farm_scenario_service.get,tenant,scenario_id,scenario_revision)
            if row is None:
                return _error(404,'not_found','Resource unavailable')
            return row
        except PermissionError:
            return _error(403,'forbidden','Resource access denied')
        except FarmReplayScenarioHold:
            return _error(422,'farm_scenario_hold','Farm scenario input unavailable')
        except Exception:
            return _error(503,'farm_scenario_unavailable','Farm scenario read unavailable')

    @app.post('/v1/farm-authored-inputs', response_model=FarmAuthoringSummary,
              operation_id='registerFarmAuthoredInputs',
              responses={status:{'model':ErrorEnvelope} for status in (401,403,409,413,415,422,503)},
              openapi_extra={**_access(FARM_AUTHORING_WRITE_SCOPES),'x-ossf-max-body-bytes':65536,
                  'requestBody':{'required':True,'content':{'application/json':{
                      'schema':_inline_schema(FarmAuthoringRequest)}}}})
    async def post_farm_authored_inputs(request: Request):
        tenant, denied = authorized_tenant(*FARM_AUTHORING_WRITE_SCOPES)
        if denied is not None:
            return denied
        if farm_authoring_service is None:
            return _error(503,'farm_authoring_unavailable','Farm authoring unavailable')
        try:
            body = FarmAuthoringRequest.model_validate_json(canonical_input_bytes(
                await read_json_request(request,max_bytes=65536)))
        except JsonRequestRejected as exc:
            return _error(exc.status,exc.code,exc.message)
        except (ValueError,UnicodeError,RecursionError):
            return _error(422,'invalid_request','Invalid request')
        try:
            return await run_in_threadpool(farm_authoring_service.submit,tenant,body)
        except PermissionError:
            return _error(403,'forbidden','Resource access denied')
        except JobIntentConflict:
            return _error(409,'scenario_conflict','Authored farm version already has different input')
        except FarmAuthoringHold:
            return _error(422,'farm_authoring_hold','Farm authoring evidence unavailable')
        except Exception:
            return _error(503,'farm_authoring_unavailable','Farm authoring unavailable')

    @app.get('/v1/farm-authored-inputs', response_model=FarmAuthoringSummary,
             operation_id='getFarmAuthoredInputs',
             responses={status:{'model':ErrorEnvelope} for status in (401,403,404,422,503)},
             openapi_extra=_access(FARM_AUTHORING_READ_SCOPES))
    async def get_farm_authored_inputs(scenario_id: Annotated[str,Query(pattern=IDENTIFIER,max_length=200)],
                                       scenario_revision: Annotated[str,Query(pattern=IDENTIFIER,max_length=200)]):
        tenant, denied = authorized_tenant(*FARM_AUTHORING_READ_SCOPES)
        if denied is not None:
            return denied
        if farm_authoring_service is None:
            return _error(503,'farm_authoring_unavailable','Farm authoring unavailable')
        try:
            row = await run_in_threadpool(farm_authoring_service.get,tenant,scenario_id,scenario_revision)
            if row is None:
                return _error(404,'not_found','Resource unavailable')
            return row
        except PermissionError:
            return _error(403,'forbidden','Resource access denied')
        except FarmAuthoringHold:
            return _error(422,'farm_authoring_hold','Farm authoring evidence unavailable')
        except Exception:
            return _error(503,'farm_authoring_unavailable','Farm authoring unavailable')

    @app.post('/v1/farm-authored-reviews', status_code=202, response_model=JobStatus,
              operation_id='submitFarmAuthoredReview',
              responses={status:{'model':ErrorEnvelope} for status in (401,403,409,413,415,422,503)},
              openapi_extra={**_access(AUTHORED_REVIEW_SCOPES),'x-ossf-max-body-bytes':4096,
                  'requestBody':{'required':True,'content':{'application/json':{
                      'schema':_inline_schema(FarmAuthoredReviewRequest)}}}})
    async def post_farm_authored_review(request: Request):
        tenant, denied = authorized_tenant(*AUTHORED_REVIEW_SCOPES)
        if denied is not None:
            return denied
        if farm_authored_review_service is None:
            return _error(503,'farm_review_unavailable','Farm review admission unavailable')
        try:
            body = FarmAuthoredReviewRequest.model_validate_json(canonical_input_bytes(
                await read_json_request(request,max_bytes=4096)))
        except JsonRequestRejected as exc:
            return _error(exc.status,exc.code,exc.message)
        except (ValueError,UnicodeError,RecursionError):
            return _error(422,'invalid_request','Invalid request')
        try:
            row = await run_in_threadpool(farm_authored_review_service.submit,tenant,
                body.scenario_id,body.scenario_revision,body.registration_sha256,body.idempotency_key)
            return public_job_status(row)
        except PermissionError:
            return _error(403,'forbidden','Resource access denied')
        except JobIntentConflict:
            return _error(409,'review_conflict','Review intent already has different input')
        except FarmAuthoredReviewHold:
            return _error(422,'farm_review_hold','Farm review evidence unavailable')
        except Exception:
            return _error(503,'farm_review_unavailable','Farm review admission unavailable')

    scenario_read_scopes = SCENARIO_SCOPES
    scenario_write_scopes = ('thermal_scenario_write',) + SCENARIO_SCOPES

    @app.post('/v1/scenarios', response_model=ThermalScenarioSummary, operation_id='registerThermalScenario',
              responses={status: {'model': ErrorEnvelope} for status in (401, 403, 409, 413, 415, 422, 503)},
              openapi_extra={**_access(scenario_write_scopes), 'x-ossf-max-body-bytes': 4096,
                  'requestBody': {'required': True, 'content': {
                  'application/json': {'schema': scenario_request_schema()}}}})
    async def post_scenario(request: Request):
        tenant, denied = authorized_tenant(*scenario_write_scopes)
        if denied is not None:
            return denied
        if thermal_scenario_store is None:
            return _error(503, 'scenario_unavailable', 'Scenario registration unavailable')
        try:
            body = ThermalScenarioRequest.model_validate(await read_json_request(request))
        except JsonRequestRejected as exc:
            return _error(exc.status, exc.code, exc.message)
        except (ValueError, UnicodeError, RecursionError):
            return _error(422, 'invalid_request', 'Invalid request')
        try:
            value = body.model_dump(mode='json') | {'tenant_id': tenant}
            record = await run_in_threadpool(thermal_scenario_store.put, tenant, value)
            return project_scenario(record)
        except ThermalScenarioConflict:
            return _error(409, 'scenario_conflict', 'Scenario version already has different input')
        except ThermalScenarioHold:
            _, denied = authorized_tenant(*scenario_write_scopes)
            if denied is not None:
                return denied
            return _error(422, 'scenario_hold', 'Scenario references unavailable')
        except Exception:
            return _error(503, 'scenario_unavailable', 'Scenario registration unavailable')

    @app.get('/v1/scenarios', response_model=ThermalScenarioSummary, responses=errors,
             operation_id='getThermalScenario', openapi_extra=_access(scenario_read_scopes))
    def get_scenario(scenario_id: Annotated[str, Query(pattern=IDENTIFIER, max_length=200)],
                     scenario_revision: Annotated[str, Query(pattern=IDENTIFIER, max_length=200)]):
        tenant, denied = authorized_tenant(*scenario_read_scopes)
        if denied is not None:
            return denied
        if thermal_scenario_store is None:
            return _error(503, 'scenario_unavailable', 'Scenario lookup unavailable')
        try:
            record = thermal_scenario_store.get(tenant, scenario_id, scenario_revision)
            if record is None:
                return _error(404, 'not_found', 'Scenario version not found')
            return project_scenario(record)
        except Exception:
            return _error(503, 'scenario_unavailable', 'Scenario lookup unavailable')

    @app.get('/v1/market-user-sources', response_model=MarketUserSourcePage,
             operation_id='listMarketUserSources', responses=errors,
             openapi_extra=_access(SOURCE_READ_SCOPES))
    def list_market_user_sources(kind: SourceKind,
            limit: Annotated[int, Query(ge=1, le=50)] = 20,
            after_record_id: Annotated[Name | None, Query(max_length=200)] = None,
            after_revision: Annotated[Name | None, Query(max_length=200)] = None):
        tenant, denied = authorized_tenant(*SOURCE_READ_SCOPES)
        if denied is not None:
            return denied
        if market_user_source_service is None:
            return _error(503, 'source_unavailable', 'User source lookup unavailable')
        if (after_record_id is None) != (after_revision is None):
            return _error(422, 'invalid_request', 'Invalid request')
        try:
            return market_user_source_service.list(tenant, kind, limit=limit,
                after_record_id=after_record_id, after_revision=after_revision)
        except (PermissionError, MarketSourceDenied):
            return _error(403, 'forbidden', 'Resource access denied')
        except Exception:
            return _error(503, 'source_unavailable', 'User source lookup unavailable')

    @app.get('/v1/market-user-sources/record', response_model=MarketUserSourceRead,
             operation_id='getMarketUserSource', responses=errors,
             openapi_extra=_access(SOURCE_READ_SCOPES))
    def get_market_user_source(kind: SourceKind,
            record_id: Annotated[Name, Query(max_length=200)],
            revision: Annotated[Name, Query(max_length=200)]):
        tenant, denied = authorized_tenant(*SOURCE_READ_SCOPES)
        if denied is not None:
            return denied
        if market_user_source_service is None:
            return _error(503, 'source_unavailable', 'User source lookup unavailable')
        try:
            result = market_user_source_service.get(tenant, kind, record_id, revision)
            if result is None:
                return _error(404, 'not_found', 'User source version not found')
            return result
        except (PermissionError, MarketSourceDenied):
            return _error(403, 'forbidden', 'Resource access denied')
        except Exception:
            return _error(503, 'source_unavailable', 'User source lookup unavailable')

    @app.post('/v1/market-user-sources', response_model=MarketUserSourceSummary,
              operation_id='registerMarketUserSource',
              responses={status: {'model': ErrorEnvelope} for status in (401, 403, 409, 413, 415, 422, 503)},
              openapi_extra={**_access(SOURCE_SCOPES), 'x-ossf-max-body-bytes': 65536,
                  'requestBody': {'required': True, 'content': {
                  'application/json': {'schema': market_user_source_schema()}}}})
    async def post_market_user_source(request: Request):
        tenant, denied = authorized_tenant(*SOURCE_SCOPES)
        if denied is not None:
            return denied
        if market_user_source_service is None:
            return _error(503, 'source_unavailable', 'User source registration unavailable')
        try:
            body = MarketUserSourceRequest.model_validate(await read_json_request(request, max_bytes=65536))
        except JsonRequestRejected as exc:
            return _error(exc.status, exc.code, exc.message)
        except (ValueError, UnicodeError, RecursionError):
            return _error(422, 'invalid_request', 'Invalid request')
        try:
            return await run_in_threadpool(market_user_source_service.submit, tenant, body)
        except (PermissionError, MarketSourceDenied):
            return _error(403, 'forbidden', 'Resource access denied')
        except (MarketSourceConflict, JobIntentConflict):
            return _error(409, 'source_conflict', 'User source intent or version has different input')
        except ValueError:
            return _error(422, 'invalid_request', 'Invalid request')
        except Exception:
            return _error(503, 'source_unavailable', 'User source registration unavailable')

    @app.post('/v1/economic-scenarios', response_model=EconomicScenarioSummary,
              operation_id='registerEconomicScenario',
              responses={status: {'model': ErrorEnvelope} for status in (401, 403, 409, 413, 415, 422, 503)},
              openapi_extra={**_access(ECONOMIC_SCENARIO_SCOPES), 'x-ossf-max-body-bytes': 4096,
                  'requestBody': {'required': True, 'content': {
                  'application/json': {'schema': _inline_schema(EconomicScenarioRequest)}}}})
    async def post_economic_scenario(request: Request):
        tenant, denied = authorized_tenant(*ECONOMIC_SCENARIO_SCOPES)
        if denied is not None:
            return denied
        if economic_scenario_service is None:
            return _error(503, 'economic_scenario_unavailable', 'Economic scenario registration unavailable')
        try:
            body = EconomicScenarioRequest.model_validate_json(
                canonical_input_bytes(await read_json_request(request)))
        except JsonRequestRejected as exc:
            return _error(exc.status, exc.code, exc.message)
        except (ValueError, UnicodeError, RecursionError):
            return _error(422, 'invalid_request', 'Invalid request')
        try:
            return await run_in_threadpool(economic_scenario_service.submit, tenant, body)
        except (PermissionError, MarketCandidateDenied):
            return _error(403, 'forbidden', 'Resource access denied')
        except (MarketCandidateConflict, JobIntentConflict):
            return _error(409, 'economic_scenario_conflict', 'Economic scenario intent or version has different input')
        except ValueError:
            return _error(422, 'invalid_request', 'Invalid request')
        except Exception:
            return _error(503, 'economic_scenario_unavailable', 'Economic scenario registration unavailable')

    @app.post('/v1/economic-results', status_code=202, response_model=JobStatus,
              operation_id='submitEconomicCalculation',
              responses={status: {'model': ErrorEnvelope} for status in (401, 403, 409, 413, 415, 422, 503)},
              openapi_extra={**_access(CALCULATION_SCOPES), 'x-ossf-max-body-bytes': 4096,
                  'x-ossf-conditional-scopes':{'economic-calculation-input-v2':list(FARM_ECONOMIC_SCOPES)},
                  'requestBody': {'required': True, 'content': {'application/json': {
                  'schema': economic_request_schema()}}}})
    async def post_economic_calculation(request: Request):
        tenant, denied = authorized_tenant(*CALCULATION_SCOPES)
        if denied is not None:
            return denied
        if economic_calculation_service is None:
            return _error(503, 'economic_calculation_unavailable', 'Economic calculation unavailable')
        try:
            body = ECONOMIC_REQUEST.validate_python(await read_json_request(request))
        except JsonRequestRejected as exc:
            return _error(exc.status, exc.code, exc.message)
        except (ValueError, UnicodeError, RecursionError):
            return _error(422, 'invalid_request', 'Invalid request')
        try:
            if type(body) is FarmEconomicCalculationRequest:
                _, denied = authorized_tenant(*FARM_ECONOMIC_SCOPES)
                if denied is not None:
                    return denied
            return public_job_status(await run_in_threadpool(economic_calculation_service.submit, tenant, body))
        except PermissionError:
            return _error(403, 'forbidden', 'Resource access denied')
        except EconomicCalculationHold:
            return _error(422, 'economic_calculation_hold', 'Economic calculation input unavailable')
        except JobIntentConflict:
            return _error(409, 'intent_conflict', 'Intent already has a different request')
        except Exception:
            return _error(503, 'economic_calculation_unavailable', 'Economic calculation unavailable')

    @app.get('/v1/jobs/{job_id}/economic-result', response_model=EconomicResultRead,
             responses=errors, operation_id='getJobEconomicResult', openapi_extra={**_access(ECONOMIC_JOB_READ_SCOPES),
                 'x-ossf-conditional-scopes':{'economic-calculation-input-v2':list(FARM_ECONOMIC_SCOPES)}})
    def get_job_economic_result(job_id: UUID):
        tenant, denied = authorized_tenant(*ECONOMIC_JOB_READ_SCOPES)
        if denied is not None:
            return denied
        try:
            if economic_calculation_service is None:
                raise RuntimeError('economic calculation service unavailable')
            result = economic_calculation_service.read_job_result(tenant, job_id)
            if result is None:
                return _error(404, 'not_found', 'Economic job result not found')
            return result
        except PermissionError:
            return _error(403, 'forbidden', 'Resource access denied')
        except Exception:
            return _error(503, 'store_unavailable', 'Economic job result unavailable')

    @app.get('/v1/jobs/{job_id}/economic-cash-flow', response_model=EconomicCashPage,
             responses=errors, operation_id='getJobEconomicCashFlow', openapi_extra={**_access(ECONOMIC_JOB_READ_SCOPES),
                 'x-ossf-conditional-scopes':{'economic-calculation-input-v2':list(FARM_ECONOMIC_SCOPES)}})
    def get_job_economic_cash_flow(job_id: UUID, limit: Annotated[int, Query(ge=1,le=24)]=12,
                                  after_month: Annotated[str|None, Query(pattern=MONTH_PATTERN)]=None):
        tenant, denied = authorized_tenant(*ECONOMIC_JOB_READ_SCOPES)
        if denied is not None:
            return denied
        try:
            if economic_calculation_service is None:
                raise RuntimeError('economic calculation service unavailable')
            result = economic_calculation_service.read_job_cash_flow(tenant,job_id,after_month=after_month,limit=limit)
            if result is None:
                return _error(404,'not_found','Economic job cash flow not found')
            return result
        except PermissionError:
            return _error(403,'forbidden','Resource access denied')
        except CashCursorRejected:
            return _error(422,'invalid_request','Invalid request')
        except Exception:
            return _error(503,'store_unavailable','Economic job cash flow unavailable')

    @app.get('/v1/jobs/{job_id}/break-even-result', response_model=BreakEvenRead,
             responses=errors, operation_id='getJobBreakEvenResult',
             openapi_extra=_access(BREAK_EVEN_JOB_READ_SCOPES))
    def get_job_break_even_result(job_id: UUID):
        tenant, denied = authorized_tenant(*BREAK_EVEN_JOB_READ_SCOPES)
        if denied is not None:
            return denied
        try:
            if break_even_job_result_service is None:
                raise RuntimeError('break-even job result service unavailable')
            result = break_even_job_result_service.read_job_result(tenant, job_id)
            if result is None:
                return _error(404, 'not_found', 'Break-even job result not found')
            return result
        except PermissionError:
            return _error(403, 'forbidden', 'Resource access denied')
        except Exception:
            return _error(503, 'store_unavailable', 'Break-even job result unavailable')

    @app.post('/v1/assessments', status_code=202, response_model=JobStatus,
              operation_id='submitCalculationAssessment',
              responses={status:{'model':ErrorEnvelope} for status in (401,403,409,413,415,422,503)},
              openapi_extra={**_access(ASSESSMENT_SCOPES), 'x-ossf-max-body-bytes':4096,
                  'x-ossf-conditional-scopes':{'thermal-simulation-result-v2':list(SCENARIO_SCOPES),
                      'thermal-simulation-result-v3':list(FARM_ECONOMIC_SCOPES),
                      'economic-calculation-result-v2':list(FARM_ECONOMIC_SCOPES)},
                  'requestBody':{'required':True, 'content':{'application/json':{
                      'schema':CalculationAssessmentRequest.model_json_schema()}}}})
    async def post_assessment(request: Request):
        tenant, denied = authorized_tenant(*ASSESSMENT_SCOPES)
        if denied is not None:
            return denied
        if assessment_service is None:
            return _error(503, 'assessment_unavailable', 'Assessment admission unavailable')
        try:
            body = CalculationAssessmentRequest.model_validate(await read_json_request(request))
        except JsonRequestRejected as exc:
            return _error(exc.status, exc.code, exc.message)
        except (ValueError, UnicodeError, RecursionError):
            return _error(422, 'invalid_request', 'Invalid request')
        try:
            row = await run_in_threadpool(assessment_service.submit, tenant,
                body.run_job_id, body.economic_job_id, body.idempotency_key)
            return public_job_status(row)
        except PermissionError:
            return _error(403, 'forbidden', 'Resource access denied')
        except JobIntentConflict:
            return _error(409, 'intent_conflict', 'Intent already has a different request')
        except CalculationAssessmentHold:
            return _error(422, 'assessment_hold', 'Completed calculation evidence unavailable')
        except Exception:
            return _error(503, 'assessment_unavailable', 'Assessment admission unavailable')

    @app.get('/v1/break-even-plans/receipt',response_model=BreakEvenPlanReceipt,responses={**errors,409:{'model':ErrorEnvelope}},
             operation_id='getBreakEvenPlanReceipt',openapi_extra=_access(PLAN_RECEIPT_SCOPES))
    def get_break_even_plan_receipt(plan_id:Annotated[str,Query(pattern=PLAN_ID_PATTERN,min_length=1,max_length=200)],
                                   submission_sha256:Annotated[str,Query(pattern=r'^[0-9a-f]{64}$')]):
        tenant,denied=authorized_tenant(*PLAN_RECEIPT_SCOPES)
        if denied is not None:return denied
        try:
            if break_even_plan_service is None:raise RuntimeError('break-even receipt service unavailable')
            value=break_even_plan_service.read_receipt(tenant,plan_id,submission_sha256)
            if value is None:return _error(404,'not_found','Break-even plan intent not found')
            return value
        except PermissionError:return _error(403,'forbidden','Resource access denied')
        except PlanReceiptConflict:return _error(409,'intent_conflict','Intent already has a different request')
        except Exception:return _error(503,'store_unavailable','Break-even plan receipt unavailable')

    @app.post('/v1/break-even-plans', status_code=202, response_model=BreakEvenPlanAccepted,
              operation_id='submitBreakEvenPlan',
              responses={status: {'model': ErrorEnvelope} for status in (401, 403, 409, 413, 415, 422, 503)},
              openapi_extra={**_access(PLAN_SUBMISSION_SCOPES), 'x-ossf-max-body-bytes': 65536,
                  'requestBody': {'required': True, 'content': {'application/json': {
                  'schema': _inline_schema(BreakEvenPlanSubmission)}}}})
    async def post_break_even_plan(request: Request):
        tenant, denied = authorized_tenant(*PLAN_SUBMISSION_SCOPES)
        if denied is not None:
            return denied
        if break_even_plan_service is None:
            return _error(503, 'break_even_plan_unavailable', 'Break-even plan admission unavailable')
        try:
            body = BreakEvenPlanSubmission.model_validate_json(
                canonical_input_bytes(await read_json_request(request, max_bytes=65536)))
        except JsonRequestRejected as exc:
            return _error(exc.status, exc.code, exc.message)
        except (ValueError, UnicodeError, RecursionError):
            return _error(422, 'invalid_request', 'Invalid request')
        try:
            return await run_in_threadpool(break_even_plan_service.submit, tenant, body)
        except PermissionError:
            return _error(403, 'forbidden', 'Resource access denied')
        except JobIntentConflict:
            return _error(409, 'intent_conflict', 'Intent already has a different request')
        except ValueError:
            return _error(422, 'invalid_request', 'Invalid request')
        except Exception:
            return _error(503, 'break_even_plan_unavailable', 'Break-even plan admission unavailable')

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
                 "x-ossf-conditional-scopes": {"thermal-simulation-result-v2": list(SCENARIO_SCOPES),
                     'thermal-simulation-result-v3':list(FARM_READ_SCOPES)}})
    def get_job_run(job_id: UUID):
        tenant, denied = authorized_tenant(*job_run_scopes)
        if denied is not None:
            return denied
        try:
            result = read_job_run(job_store, thermal_run_store, tenant, job_id, thermal_scenario_store,
                farm_scenario_service)
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

    AuthoredRunId = Annotated[str, Path(pattern=AUTHORED_RUN_ID_PATTERN)]

    def displayed_authored_run(run_id):
        tenant, denied = authorized_tenant(*authored_scopes)
        if denied is not None:
            return denied
        if authored_run_store is None:
            return _error(503, 'store_unavailable', 'Authored Run unavailable')
        try:
            stored = authored_run_store.get_run(tenant, run_id)
            if stored is None:
                return _error(404, 'not_found', 'Authored Run not found')
            return project_authored_run(stored)
        except Exception:
            return _error(503, 'store_unavailable', 'Authored Run unavailable')

    @app.get('/v1/jobs/{job_id}/authored-run', response_model=AuthoredThermalRunSummary,
             responses=errors, operation_id='getJobAuthoredRun',
             openapi_extra=_access(authored_scopes))
    def get_job_authored_run(job_id: UUID):
        tenant, denied = authorized_tenant(*authored_scopes)
        if denied is not None:
            return denied
        if authored_run_store is None:
            return _error(503, 'store_unavailable', 'Authored Run unavailable')
        try:
            result = read_authored_job_run(job_store, authored_run_store, tenant, job_id)
            return result if result is not None else _error(404, 'not_found', 'Authored Run not found')
        except Exception:
            return _error(503, 'store_unavailable', 'Authored Run unavailable')

    @app.get('/v1/authored-runs/{run_id}', response_model=AuthoredThermalRunSummary,
             responses=errors, operation_id='getAuthoredRun',
             openapi_extra=_access(authored_scopes))
    def get_authored_run(run_id: AuthoredRunId):
        result = displayed_authored_run(run_id)
        return result if isinstance(result, JSONResponse) else result[0]

    @app.get('/v1/authored-runs/{run_id}/series', response_model=ThermalRunSeries,
             responses=errors, operation_id='getAuthoredRunSeries',
             openapi_extra=_access(authored_scopes))
    def get_authored_run_series(run_id: AuthoredRunId):
        result = displayed_authored_run(run_id)
        return result if isinstance(result, JSONResponse) else result[1]

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
