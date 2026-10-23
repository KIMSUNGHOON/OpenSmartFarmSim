"""Authenticated leaf_population admission, current stored reads, and cancellation."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path as FilePath
from typing import Annotated, Literal

from fastapi import Path, Request, Response
from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator
from psycopg import sql
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect

from . import api_contracts as jobs_public
from .api_json import read_json_request, JsonRequestRejected
from .api_market_source import _inline_schema
from .crop_result_store import READ_SCOPES as FARM_READ_SCOPES, WRITE_SCOPES
from .job_store import JobIntentConflict


CODE_SHA256 = sha256(FilePath(__file__).read_bytes()).hexdigest()
SUBMIT_SCOPES = ('simulation_create',)+WRITE_SCOPES
READ_SCOPES = ('metadata', 'artifact')+FARM_READ_SCOPES
CANCEL_SCOPES = ('metadata', 'cancel')
MAX_REQUEST_BYTES = 65536
MAX_RESPONSE_BYTES = 2*1024**2
JOB_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
Name = Annotated[str, Field(strict=True, pattern=r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$')]
Digest = Annotated[str, Field(strict=True, pattern=r'^[0-9a-f]{64}$')]
Stamp = Annotated[str, Field(strict=True, pattern=r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z$')]
StrictBool = Annotated[bool, Field(strict=True)]


class LeafPopulationClosed(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, allow_inf_nan=False)


class LeafPopulationFarm(LeafPopulationClosed):
    scenario_id: Name
    scenario_revision: Name
    registration_sha256: Digest
    crop_id: Name


class LeafPopulationInput(LeafPopulationClosed):
    schema_version: Literal['leaf-population-input-source-v1']
    program_id: Name
    program_sha256: Digest
    source_sha256: Digest
    evidence_sha256: Digest


class LeafPopulationRights(LeafPopulationClosed):
    schema_version: Literal['leaf-population-input-rights-v1']
    declaration_id: Name
    revision: Name
    input_source_sha256: Digest
    available_at: Stamp
    redistribute: StrictBool
    ownership_asserted: StrictBool
    access: StrictBool
    store: StrictBool
    transform: StrictBool
    use: StrictBool
    display: StrictBool


class LeafPopulationParent(LeafPopulationClosed):
    job_id: Annotated[str, Field(strict=True, pattern=JOB_PATTERN)]
    result_sha256: Digest
    numerical_root_sha256: Digest


class LeafPopulationExecutionRequest(LeafPopulationClosed):
    study_id: Name
    revision: Name
    farm: LeafPopulationFarm
    parent: LeafPopulationParent
    input: LeafPopulationInput
    rights: LeafPopulationRights

    @model_validator(mode='after')
    def granted_software_use(self):
        r = self.rights
        if (r.redistribute is not False or not all(getattr(r, k) is True for k in
                ('ownership_asserted', 'access', 'store', 'transform', 'use', 'display'))
                or r.input_source_sha256 != self.input.source_sha256):
            raise ValueError('leaf_population input declaration unavailable')
        datetime.fromisoformat(r.available_at.replace('Z', '+00:00'))
        return self


class LeafPopulationResultSummary(LeafPopulationClosed):
    result_sha256: Digest
    numerical_root_sha256: Digest
    calculated_at: Stamp
    parent_job_id: Annotated[str, Field(strict=True, pattern=JOB_PATTERN)]
    parent_result_sha256: Digest
    parent_numerical_root_sha256: Digest
    parent_calculated_at: Stamp
    normalization: Literal['per_tracked_shoot']
    study_id: Name
    revision: Name
    farm: LeafPopulationFarm
    profile_applicability: Literal['unvalidated_for_registered_crop']
    binding_sha256: Digest
    program_sha256: Digest
    source_sha256: Digest
    input_evidence_sha256: Digest


class LeafPopulationFlags(LeafPopulationClosed):
    scope: Literal['software_research_only']
    claim_scope: Literal['synthetic_crop_math_only']
    gates: Literal['not_assessed']


class LeafPopulationExecutionRead(LeafPopulationFlags):
    schema_version: Literal['leaf-population-execution-read-v1']
    observed_at: Stamp
    job: jobs_public.JobStatus
    cancel_requested: StrictBool
    result: LeafPopulationResultSummary | None
    manifest: dict[str, JsonValue] | None
    frame: dict[str, JsonValue] | None
    replay: dict[str, JsonValue] | None

    @model_validator(mode='after')
    def completed_only(self):
        if (self.job.stage != 'simulation' or (self.result is not None) != (self.job.state == 'succeeded')
                or self.result is None and any(v is not None for v in (self.manifest, self.frame, self.replay))):
            raise ValueError('leaf_population execution response unavailable')
        return self


class LeafPopulationCancellation(LeafPopulationFlags):
    schema_version: Literal['leaf-population-execution-cancel-v1']
    observed_at: Stamp
    job: jobs_public.JobStatus
    cancel_requested: StrictBool
    cancel_accepted: StrictBool


def install_leaf_population_execution_routes(app, *, jobs, admission, query, principal_provider,
        authorized_tenant, error, access, farms=None):
    if not all(callable(v) for v in (principal_provider, authorized_tenant, error, access)):
        raise ValueError('trusted leaf_population execution service required')
    enabled = admission is not None or query is not None
    holds = (); pending = (); current = None
    headers = {'Cache-Control': 'no-store'}
    if enabled:
        from . import crop_leaf_population_execution_query as current
        holds = (current.LeafPopulationExecutionQueryHold, current.execution.LeafPopulationExecutionHold,
            current.execution.signed.LeafPopulationSignedArtifactHold)
        pending = (current.LeafPopulationExecutionQueryPending,)

    def binding():
        if not enabled: return
        try:
            if (type(admission) is not current.execution.LeafPopulationExecutionService
                    or type(query) is not current.LeafPopulationExecutionQuery or query.service is not admission
                    or admission.jobs is not jobs or query.jobs is not jobs or jobs.principal_provider is not principal_provider
                    or farms is not None and admission.authority.farm_binding.farms.farms is not farms):
                raise ValueError()
            admission._binding(); query._binding()
        except Exception:
            raise ValueError('trusted leaf_population execution service required') from None
    binding()
    if enabled:
        headers.update({'X-OSSF-LeafPopulation-Query-Code-SHA256': current.CODE_SHA256,
            'X-OSSF-LeafPopulation-HTTP-Code-SHA256': CODE_SHA256})

    def unavailable(): return error(503, 'leaf_population_execution_unavailable', 'Leaf population execution unavailable')

    def after(tenant, scopes):
        observed, denied = authorized_tenant(*scopes)
        return denied if denied is not None else None if observed == tenant else error(403, 'forbidden', 'Resource access denied')

    async def empty(request):
        if request.query_params: return error(422, 'invalid_request', 'Invalid request')
        try:
            async for chunk in request.stream():
                if chunk: return error(422, 'invalid_request', 'Invalid request')
        except ClientDisconnect: return error(422, 'invalid_request', 'Invalid request')
        return None

    async def invoke(tenant, scopes, action, model, status=200):
        raw = None; failure = None
        try:
            binding(); value = await run_in_threadpool(action); binding()
            raw = current.execution.signed.reader._canonical(model.model_validate(value).model_dump(mode='json'))
        except PermissionError: failure = error(403, 'forbidden', 'Resource access denied')
        except JobIntentConflict: failure = error(409, 'intent_conflict', 'Intent already has a different request')
        except pending: failure = unavailable()
        except holds: failure = error(422, 'leaf_population_execution_hold', 'LeafPopulation evidence unavailable')
        except Exception: failure = unavailable()
        denied = after(tenant, scopes)
        if denied is not None: return denied
        if failure is not None: return failure
        if not raw or len(raw) > MAX_RESPONSE_BYTES: return unavailable()
        return Response(raw, status_code=status, media_type='application/json', headers=headers)

    errors = {s: {'model': jobs_public.ErrorEnvelope} for s in (401, 403, 409, 413, 415, 422, 503)}
    @app.post('/v1/crop-leaf-population-executions', status_code=202, response_model=jobs_public.JobStatus,
        operation_id='submitLeafPopulationExecution', responses=errors, openapi_extra={**access(SUBMIT_SCOPES),
            'x-ossf-max-body-bytes': MAX_REQUEST_BYTES, 'requestBody': {'required': True,
                'content': {'application/json': {'schema': _inline_schema(LeafPopulationExecutionRequest)}}}})
    async def submit(request: Request):
        tenant, denied = authorized_tenant(*SUBMIT_SCOPES)
        if denied is not None: return denied
        if request.query_params: return error(422, 'invalid_request', 'Invalid request')
        if not enabled: return unavailable()
        try:
            body = LeafPopulationExecutionRequest.model_validate(await read_json_request(request, max_bytes=MAX_REQUEST_BYTES))
            raw = current.execution.signed.reader._canonical(body.model_dump(mode='json'))
        except JsonRequestRejected as exc: return error(exc.status, exc.code, exc.message)
        except (ClientDisconnect, ValueError, UnicodeError, RecursionError): return error(422, 'invalid_request', 'Invalid request')
        def action(): return jobs_public.public_job_status(admission.submit(tenant, raw)).model_dump(mode='json')
        return await invoke(tenant, SUBMIT_SCOPES, action, jobs_public.JobStatus, 202)

    async def read(request, job_id, view, index=None):
        tenant, denied = authorized_tenant(*READ_SCOPES)
        if denied is not None: return denied
        denied = await empty(request)
        if denied is not None: return denied
        if not enabled: return unavailable()
        return await invoke(tenant, READ_SCOPES, lambda: query.read(tenant, job_id, view=view, index=index), LeafPopulationExecutionRead)

    route_path = '/v1/jobs/{job_id}/crop-leaf-population-execution'
    @app.get(route_path, response_model=LeafPopulationExecutionRead, operation_id='getLeafPopulationExecution',
        responses=errors, openapi_extra=access(READ_SCOPES))
    async def status(request: Request, job_id: Annotated[str, Path(pattern=JOB_PATTERN)]):
        return await read(request, job_id, 'status')

    @app.get(route_path+'/manifest', response_model=LeafPopulationExecutionRead, operation_id='getLeafPopulationExecutionManifest',
        responses=errors, openapi_extra=access(READ_SCOPES))
    async def manifest(request: Request, job_id: Annotated[str, Path(pattern=JOB_PATTERN)]):
        return await read(request, job_id, 'manifest')

    @app.get(route_path+'/frames/{index}', response_model=LeafPopulationExecutionRead, operation_id='getLeafPopulationExecutionFrame',
        responses=errors, openapi_extra=access(READ_SCOPES))
    async def frame(request: Request, job_id: Annotated[str, Path(pattern=JOB_PATTERN)],
            index: Annotated[str, Path(pattern=r'^(0|[1-9][0-9]{0,8})$')]):
        return await read(request, job_id, 'frame', int(index))

    @app.get(route_path+'/replay', response_model=LeafPopulationExecutionRead, operation_id='getLeafPopulationExecutionReplay',
        responses=errors, openapi_extra=access(READ_SCOPES))
    async def replay(request: Request, job_id: Annotated[str, Path(pattern=JOB_PATTERN)]):
        return await read(request, job_id, 'replay')

    @app.post(route_path+'/cancel', response_model=LeafPopulationCancellation, operation_id='cancelLeafPopulationExecution',
        responses=errors, openapi_extra=access(CANCEL_SCOPES))
    async def cancel(request: Request, job_id: Annotated[str, Path(pattern=JOB_PATTERN)]):
        tenant, denied = authorized_tenant(*CANCEL_SCOPES)
        if denied is not None: return denied
        denied = await empty(request)
        if denied is not None: return denied
        if not enabled: return unavailable()
        def target():
            with jobs.connect() as conn:
                row = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
                    .format(jobs._table('jobs')), (tenant, job_id)).fetchone()
            if row is None or row['stage'] != 'simulation': raise current.LeafPopulationExecutionQueryHold()
            value = json.loads(jobs._verified_input(row))
            if value.get('input_version') != current.execution.INPUT_VERSION: raise current.LeafPopulationExecutionQueryHold()
            return row
        def action():
            target(); accepted = jobs.cancel(tenant, job_id); row = target()
            return {'schema_version': 'leaf-population-execution-cancel-v1', **current.execution.signed.FLAGS,
                'observed_at': current.execution.signed.parent_signed._stamp(datetime.now(timezone.utc)),
                'job': jobs_public.public_job_status(row).model_dump(mode='json'),
                'cancel_requested': row['cancel_requested'], 'cancel_accepted': accepted}
        return await invoke(tenant, CANCEL_SCOPES, action, LeafPopulationCancellation)
    app.openapi_schema = None
