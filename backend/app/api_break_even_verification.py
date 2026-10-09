"""Protected asynchronous replay admission and completed-result HTTP routes."""

from uuid import UUID

from fastapi import Request
from pydantic import Field
from starlette.concurrency import run_in_threadpool

from .api_break_even import BreakEvenRead
from .api_contracts import ErrorEnvelope, JobStatus
from .api_job_break_even_result import BREAK_EVEN_JOB_READ_SCOPES
from .api_json import JsonRequestRejected, read_json_request
from .api_market_source import _inline_schema
from .break_even_verification import BreakEvenVerificationService
from .break_even_verified_result import BreakEvenVerifiedResultService
from .job_store import JobIntentConflict
from .owned_fixture_collection import UUID_PATTERN
from .provenance import FrozenContract


VERIFICATION_SCOPES = BREAK_EVEN_JOB_READ_SCOPES + ('simulation_execute',)


class BreakEvenVerificationRequest(FrozenContract):
    calculation_job_id: str = Field(pattern=UUID_PATTERN)


def install_verification_routes(app, *, jobs, store, admission, results, authorized_tenant, error, access):
    for service, expected in ((admission, BreakEvenVerificationService), (results, BreakEvenVerifiedResultService)):
        if service is not None and (type(service) is not expected or service.jobs is not jobs or service.store is not store):
            raise ValueError('trusted break-even verification services required')

    @app.post('/v1/break-even-verifications', status_code=202, response_model=JobStatus,
        operation_id='submitBreakEvenVerification',
        responses={status: {'model': ErrorEnvelope} for status in (401, 403, 409, 413, 415, 422, 503)},
        openapi_extra={**access(VERIFICATION_SCOPES), 'x-ossf-max-body-bytes': 4096,
            'requestBody': {'required': True, 'content': {'application/json': {
                'schema': _inline_schema(BreakEvenVerificationRequest)}}}})
    async def submit_verification(request: Request):
        tenant, denied = authorized_tenant(*VERIFICATION_SCOPES)
        if denied is not None:
            return denied
        try:
            value = BreakEvenVerificationRequest.model_validate(await read_json_request(request))
        except JsonRequestRejected as exc:
            return error(exc.status, exc.code, exc.message)
        except ValueError:
            return error(422, 'invalid_request', 'Invalid request')
        try:
            if admission is None:
                raise RuntimeError('break-even verification service unavailable')
            return await run_in_threadpool(admission.submit, tenant, value.calculation_job_id)
        except PermissionError:
            return error(403, 'forbidden', 'Resource access denied')
        except JobIntentConflict:
            return error(409, 'idempotency_conflict', 'Request conflicts with stored intent')
        except ValueError:
            return error(422, 'break_even_verification_hold', 'Completed calculation unavailable')
        except Exception:
            return error(503, 'store_unavailable', 'Break-even verification unavailable')

    @app.get('/v1/jobs/{job_id}/break-even-verified-result', response_model=BreakEvenRead,
        operation_id='getJobBreakEvenVerifiedResult',
        responses={status: {'model': ErrorEnvelope} for status in (401, 403, 404, 422, 503)},
        openapi_extra=access(BREAK_EVEN_JOB_READ_SCOPES))
    def get_verified_result(job_id: UUID):
        tenant, denied = authorized_tenant(*BREAK_EVEN_JOB_READ_SCOPES)
        if denied is not None:
            return denied
        try:
            if results is None:
                raise RuntimeError('break-even verified result service unavailable')
            result = results.read_job_result(tenant, job_id)
            return result if result is not None else error(404, 'not_found', 'Break-even verified result not found')
        except PermissionError:
            return error(403, 'forbidden', 'Resource access denied')
        except Exception:
            return error(503, 'store_unavailable', 'Break-even verified result unavailable')
