"""Closed ventilation execution HTTP contracts; operational dependencies load explicitly."""
from datetime import timezone
from hashlib import sha256
from pathlib import Path as FilePath
from typing import Annotated, Literal
import json

from fastapi import Path, Request, Response
from pydantic import Field, create_model, model_validator
from psycopg import sql
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect

from . import api_contracts as jobs_public
from . import api_crop_replay as public
from .api_json import read_json_request, JsonRequestRejected
from .api_market_source import _inline_schema
from .crop_result_store import READ_SCOPES, WRITE_SCOPES
from .job_store import JobIntentConflict
from .jobs import canonical_input_bytes
from .thermal_run_store import _canonical

VERSION = 'joint-ventilation-execution-query-v1'
CANCEL_VERSION = 'joint-ventilation-execution-cancel-v1'
INPUT_VERSION = 'joint-ventilation-execution-input-v1'
SOURCE_VERSION = 'joint-ventilation-input-source-v1'
RIGHTS_VERSION = 'joint-ventilation-input-rights-v1'
MAX_RESPONSE_BYTES = 16 * 1024
MAX_REQUEST_BYTES = 64 * 1024
MAX_CHECKPOINT_EVENTS = 4099
CODE_SHA256 = sha256(FilePath(__file__).read_bytes()).hexdigest()
SUBMIT_SCOPES = ('simulation_create',) + WRITE_SCOPES
PROGRESS_SCOPES = ('metadata',) + READ_SCOPES
CANCEL_SCOPES = ('cancel',)
JOB_ID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
Counter = Annotated[int, Field(strict=True, ge=0, le=2**63 - 1)]


def _need(value):
    if not value: raise ValueError('ventilation execution response unavailable')


class VentilationExecutionCounts(public._Public):
    samples: Counter
    events: Counter


class VentilationExecutionCheckpoint(public._Public):
    head_sha256: public.Digest
    proof_sha256: public.Digest
    artifact_sha256: public.Digest | None
    status: Literal['ready', 'yielded', 'completed', 'hold']
    steps: Counter
    planned_steps: Annotated[int, Field(strict=True, ge=1, le=2**63 - 1)]
    counts: VentilationExecutionCounts
    computed_through_utc: public.UtcStamp | None
    checkpoint_recorded_at: public.UtcStamp
    publication_sequence: Annotated[int, Field(strict=True, ge=1, le=MAX_CHECKPOINT_EVENTS)]


VentilationExecutionResultFarm = create_model('VentilationExecutionResultFarm', __base__=public._Public,
    **{k: (public.Digest if k == 'registration_sha256' else public.Name, ...)
       for k in ('scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id', 'batch_id', 'zone_id')})


class VentilationExecutionResult(public._Public):
    result_id: Annotated[str, Field(strict=True, pattern=r'^joint-ventilation-result-v1:[a-f0-9]{64}$')]
    farm: VentilationExecutionResultFarm
    status: Literal['completed', 'hold']


class VentilationExecutionRead(public._Public):
    version: Literal['joint-ventilation-execution-query-v1']
    scope: Literal['synthetic_joint_ventilation_math_only']
    G0_G4: Literal['not_assessed']
    job: jobs_public.JobStatus
    cancel_requested: Annotated[bool, Field(strict=True)]
    observed_at: public.UtcStamp
    checkpoint_status: Literal['none', 'current', 'unavailable']
    checkpoint: VentilationExecutionCheckpoint | None
    result: VentilationExecutionResult | None

    @model_validator(mode='after')
    def consistent_progress(self):
        _need((self.checkpoint_status == 'current') == (self.checkpoint is not None))
        if self.checkpoint is not None:
            c = self.checkpoint
            _need(c.steps <= c.planned_steps
                and (c.artifact_sha256 is not None) == (c.status in ('completed', 'hold'))
                and (c.computed_through_utc is None) == (c.status == 'ready'))
            if c.status == 'completed': _need(c.steps == c.planned_steps)
        if self.result is not None:
            _need(self.checkpoint is not None and self.checkpoint.status == self.result.status
                and self.job.state == ('succeeded' if self.result.status == 'completed' else 'hold'))
        return self


VentilationExecutionFarm = create_model('VentilationExecutionFarm', __base__=public._Public,
    **{k: (public.Digest if k == 'registration_sha256' else public.Name, ...)
       for k in ('scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id')})


class VentilationExecutionInput(public._Public):
    schema_version: Literal['joint-ventilation-input-source-v1']
    program_id: public.Name
    source_sha256: public.Digest
    context_sha256: public.Digest
    time_binding_sha256: public.Digest
    evidence_sha256: public.Digest


class VentilationExecutionRights(public._Public):
    schema_version: Literal['joint-ventilation-input-rights-v1']
    declaration_id: public.Name
    revision: public.Name
    input_source_sha256: public.Digest
    available_at: public.UtcStamp
    redistribute: Annotated[bool, Field(strict=True)]
    ownership_asserted: Annotated[bool, Field(strict=True)]
    access: Annotated[bool, Field(strict=True)]
    store: Annotated[bool, Field(strict=True)]
    transform: Annotated[bool, Field(strict=True)]
    use: Annotated[bool, Field(strict=True)]
    display: Annotated[bool, Field(strict=True)]


class VentilationExecutionRequest(public._Public):
    study_id: public.Name
    revision: public.Name
    farm: VentilationExecutionFarm
    input: VentilationExecutionInput
    rights: VentilationExecutionRights

    @model_validator(mode='after')
    def complete_declaration(self):
        r = self.rights
        _need(r.redistribute is False and all(getattr(r,k) is True for k in
            ('ownership_asserted', 'access', 'store', 'transform', 'use', 'display'))
            and r.input_source_sha256 == self.input.source_sha256)
        return self


class VentilationExecutionCancellation(public._Public):
    version: Literal['joint-ventilation-execution-cancel-v1']
    scope: Literal['synthetic_joint_ventilation_math_only']
    G0_G4: Literal['not_assessed']
    job: jobs_public.JobStatus
    cancel_requested: Annotated[bool, Field(strict=True)]
    cancel_accepted: Annotated[bool, Field(strict=True)]
    observed_at: public.UtcStamp


def install_ventilation_execution_routes(app, *, jobs, farms, store, admission, query,
                                   principal_provider, authorized_tenant, error, access):
    if not all(callable(v) for v in (principal_provider, authorized_tenant, error, access)):
        raise ValueError('trusted ventilation execution service required')
    holds = (); pending = (); headers = {'Cache-Control': 'no-store'}
    enabled = admission is not None or query is not None
    if enabled:
        from . import crop_greenhouse_ventilation_execution_query as current
        from .farm_authoring_storage import FarmAuthoringHold
        try:
            if (type(admission) is not current.checkpoints.execution.VentilationExecutionService
                    or type(query) is not current.VentilationExecutionQuery
                    or query.checkpoints.admission is not admission or query.results is not store
                    or admission.jobs is not jobs or query.jobs is not jobs
                    or query.server is not store.server or admission.binding is not store.server.binding
                    or admission.input_resolver is not store.server.input_resolver
                    or farms is None or admission.binding.farms is not farms
                    or jobs.principal_provider is not principal_provider):
                raise ValueError()
            admission._binding(); query._binding()
        except Exception: raise ValueError('trusted ventilation execution service required') from None
        holds = (current.VentilationExecutionQueryHold, current.checkpoints.execution.VentilationExecutionHold,
            current.custody.VentilationCustodyHold, current.custody.farms.VentilationFarmBindingHold, FarmAuthoringHold)
        pending = (current.VentilationExecutionQueryPending, current.custody.VentilationCustodyPending)
        headers.update({'X-OSSF-Ventilation-Execution-Query-Version': VERSION,
            'X-OSSF-Ventilation-Execution-Query-Code-SHA256': current.CODE_SHA256,
            'X-OSSF-Ventilation-Execution-HTTP-Code-SHA256': CODE_SHA256})

    def unavailable(): return error(503, 'ventilation_execution_unavailable', 'Ventilation execution unavailable')

    def after(tenant, scopes):
        observed, denied = authorized_tenant(*scopes)
        if denied is not None: return denied
        if observed != tenant: return error(403, 'forbidden', 'Resource access denied')
        return None

    async def empty(request):
        if request.query_params: return error(422, 'invalid_request', 'Invalid request')
        try:
            async for chunk in request.stream():
                if chunk: return error(422, 'invalid_request', 'Invalid request')
        except ClientDisconnect: return error(422, 'invalid_request', 'Invalid request')
        return None

    async def invoke(tenant, scopes, action, *, status=200):
        raw = None; failure = None
        try: raw = await run_in_threadpool(action)
        except PermissionError: failure = error(403, 'forbidden', 'Resource access denied')
        except JobIntentConflict: failure = error(409, 'intent_conflict', 'Intent already has a different request')
        except pending: failure = unavailable()
        except holds: failure = error(422, 'ventilation_execution_hold', 'Ventilation execution evidence unavailable')
        except Exception: failure = unavailable()
        denied = after(tenant, scopes)
        if denied is not None: return denied
        if failure is not None: return failure
        if raw is None: return error(404, 'not_found', 'Ventilation execution not found')
        if type(raw) is not bytes or not 1 <= len(raw) <= MAX_RESPONSE_BYTES: return unavailable()
        return Response(raw, status_code=status, media_type='application/json', headers=headers)

    errors = {s: {'model': jobs_public.ErrorEnvelope} for s in (401,403,404,409,413,415,422,503)}
    @app.post('/v1/crop-greenhouse-ventilation-executions', status_code=202, response_model=jobs_public.JobStatus,
        operation_id='submitGreenhouseVentilationExecution', responses=errors,
        openapi_extra={**access(SUBMIT_SCOPES), 'x-ossf-max-body-bytes': MAX_REQUEST_BYTES,
            'requestBody': {'required': True, 'content': {'application/json': {'schema': _inline_schema(VentilationExecutionRequest)}}}})
    async def submit(request: Request):
        tenant, denied = authorized_tenant(*SUBMIT_SCOPES)
        if denied is not None: return denied
        if request.query_params: return error(422, 'invalid_request', 'Invalid request')
        if not enabled: return unavailable()
        try:
            body = VentilationExecutionRequest.model_validate(await read_json_request(request, max_bytes=MAX_REQUEST_BYTES))
            raw = _canonical(body.model_dump(mode='json'))
        except JsonRequestRejected as exc: return error(exc.status, exc.code, exc.message)
        except (ClientDisconnect, ValueError, UnicodeError, RecursionError): return error(422, 'invalid_request', 'Invalid request')
        def action():
            row = admission.submit(tenant, raw)
            return _canonical(jobs_public.public_job_status(row).model_dump(mode='json'))
        return await invoke(tenant, SUBMIT_SCOPES, action, status=202)

    @app.get('/v1/jobs/{job_id}/crop-greenhouse-ventilation-execution', response_model=VentilationExecutionRead,
        operation_id='getGreenhouseVentilationExecution', openapi_extra=access(PROGRESS_SCOPES), responses=errors)
    async def progress(request: Request, job_id: Annotated[str, Path(pattern=JOB_ID_PATTERN)]):
        tenant, denied = authorized_tenant(*PROGRESS_SCOPES)
        if denied is not None: return denied
        denied = await empty(request)
        if denied is not None: return denied
        if not enabled: return unavailable()
        return await invoke(tenant, PROGRESS_SCOPES, lambda: query.read(tenant, job_id))

    @app.post('/v1/jobs/{job_id}/crop-greenhouse-ventilation-execution/cancel', response_model=VentilationExecutionCancellation,
        operation_id='cancelGreenhouseVentilationExecution', openapi_extra=access(CANCEL_SCOPES), responses=errors)
    async def cancel(request: Request, job_id: Annotated[str, Path(pattern=JOB_ID_PATTERN)]):
        tenant, denied = authorized_tenant(*CANCEL_SCOPES)
        if denied is not None: return denied
        denied = await empty(request)
        if denied is not None: return denied
        if not enabled: return unavailable()
        def target(conn):
            if jobs.principal_provider is not principal_provider: raise RuntimeError()
            row = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
                .format(jobs._table('jobs')), (tenant, job_id)).fetchone()
            if row is None or row['stage'] != 'simulation': return None
            raw = jobs._verified_input(row); body = json.loads(raw)
            if type(body) is not dict or body.get('input_version') != INPUT_VERSION: return None
            if canonical_input_bytes(body) != raw: raise RuntimeError()
            return row
        def action():
            with jobs.connect() as conn:
                if target(conn) is None: return None
            # Cancellation must remain available after scientific input rights are withdrawn.
            accepted = admission.cancel(tenant, job_id)
            denied = after(tenant, CANCEL_SCOPES)
            if denied is not None: raise PermissionError()
            with jobs.connect() as conn:
                row = target(conn)
                if row is None: return None
                observed = conn.execute('SELECT clock_timestamp() AS at').fetchone()['at']
            value = VentilationExecutionCancellation.model_validate({'version': CANCEL_VERSION,
                'scope': 'synthetic_joint_ventilation_math_only', 'G0_G4': 'not_assessed',
                'job': jobs_public.public_job_status(row), 'cancel_requested': row['cancel_requested'],
                'cancel_accepted': accepted, 'observed_at': observed.astimezone(timezone.utc).isoformat().replace('+00:00','Z')})
            return _canonical(value.model_dump(mode='json'))
        return await invoke(tenant, CANCEL_SCOPES, action)
    app.openapi_schema = None
