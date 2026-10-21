"""Explicit authenticated routes for immutable accepted prefix records."""
from hashlib import sha256
from pathlib import Path as FilePath
import re
from typing import Annotated

from fastapi import Path, Request, Response
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect

from .api_contracts import ErrorEnvelope
from .api_crop_greenhouse_co2_execution_http import JOB_ID_PATTERN, PROGRESS_SCOPES

CODE_SHA256 = sha256(FilePath(__file__).read_bytes()).hexdigest()
PREFIX_PATH = '/v1/jobs/{job_id}/crop-greenhouse-co2-execution/prefix'


def _page_request(request, view):
    pairs = list(request.query_params.multi_items()); keys = [k for k, _ in pairs]
    if view == 'summary':
        if pairs: raise ValueError()
        return {}
    required = {'publication_sequence', 'head_sha256', 'proof_sha256'}
    if len(keys) != len(set(keys)) or not required <= set(keys) <= required | {'start', 'limit'}:
        raise ValueError()
    values = dict(pairs)
    for key in ('head_sha256', 'proof_sha256'):
        if re.fullmatch(r'[0-9a-f]{64}', values[key]) is None: raise ValueError()
    maximum = 64 if view == 'samples' else 8
    parsed = {}
    for key, default, low, high in (('publication_sequence', None, 1, 4099),
            ('start', '0', 0, 512 if view == 'samples' else 128), ('limit', str(maximum), 1, maximum)):
        text = values.get(key, default)
        if not 1 <= len(text) <= 4 or re.fullmatch(r'0|[1-9][0-9]*', text) is None:
            raise ValueError()
        number = int(text)
        if not low <= number <= high: raise ValueError()
        parsed[key] = number
    return {'selector': {'publication_sequence': parsed['publication_sequence'],
        **{k: values[k] for k in ('head_sha256', 'proof_sha256')}},
        'view': view, 'start': parsed['start'], 'limit': parsed['limit']}


def install_co2_prefix_routes(app, *, jobs, farms, store, query,
                                principal_provider, authorized_tenant, error, access):
    from . import crop_greenhouse_co2_prefix as current
    from . import api_crop_greenhouse_co2_prefix as public
    from .farm_authoring_storage import FarmAuthoringHold
    try:
        if (not all(callable(v) for v in (principal_provider, authorized_tenant, error, access))
                or type(query) is not current.Co2ExecutionPrefixQuery
                or type(query.query) is not current.execution.Co2ExecutionQuery
                or type(store) is not current.execution.storage.Co2ResultStore
                or query.jobs is not jobs or query.query.jobs is not jobs or store.jobs is not jobs
                or query.query.results is not store or query.server is not store.server
                or query.query.server is not query.server or farms is None
                or query.server.binding.farms is not farms or query.server.binding.jobs is not jobs
                or jobs.principal_provider is not principal_provider):
            raise ValueError()
        query._binding(); store._binding()
    except Exception:
        raise ValueError('trusted co2 prefix reader required') from None
    headers = {'Cache-Control': 'no-store', 'X-OSSF-Co2-Prefix-Version': public.VERSION,
        'X-OSSF-Co2-Prefix-Reader-Code-SHA256': current.CODE_SHA256,
        'X-OSSF-Co2-Prefix-Projection-Code-SHA256': public.CODE_SHA256,
        'X-OSSF-Co2-Prefix-HTTP-Code-SHA256': CODE_SHA256}
    errors = {status: {'model': ErrorEnvelope} for status in (401, 403, 404, 409, 422, 503)}
    holds = (current.Co2PrefixHold, public.ProjectionHold, current.execution.Co2ExecutionQueryHold,
        current.checkpoints.Co2CheckpointHold, current.checkpoints.execution.Co2ExecutionHold,
        current.custody.Co2CustodyHold, current.custody.farms.Co2FarmBindingHold, FarmAuthoringHold)

    def documentation(view):
        extra = {**access(PROGRESS_SCOPES), 'x-ossf-max-response-bytes': public.MAX_RESPONSE_BYTES}
        if view != 'summary':
            properties = public.Selector.model_json_schema()['properties']
            extra['parameters'] = [{'name': k, 'in': 'query', 'required': True, 'schema': properties[k]}
                for k in ('publication_sequence', 'head_sha256', 'proof_sha256')]
            extra['parameters'] += [{'name': k, 'in': 'query', 'required': False, 'schema':
                {'type': 'integer', 'minimum': low, 'maximum': high, 'default': default}}
                for k, low, high, default in (('start', 0, 512 if view == 'samples' else 128, 0),
                    ('limit', 1, 64 if view == 'samples' else 8, 64 if view == 'samples' else 8))]
        return extra

    def unavailable(): return error(503, 'co2_prefix_unavailable', 'Co2 prefix unavailable')

    def read(tenant, job_id, options):
        return public.read_prefix(query, tenant, job_id, **options)

    async def handle(request, job_id, view):
        tenant, denied = authorized_tenant(*PROGRESS_SCOPES)
        if denied is not None: return denied
        try:
            options = _page_request(request, view)
            async for chunk in request.stream():
                if chunk: raise ValueError()
        except (ValueError, ClientDisconnect):
            return error(422, 'invalid_request', 'Invalid request')
        raw = failure = None
        try:
            if sha256(FilePath(__file__).read_bytes()).hexdigest() != CODE_SHA256:
                raise RuntimeError()
            raw = await run_in_threadpool(read, tenant, job_id, options)
        except PermissionError: failure = error(403, 'forbidden', 'Resource access denied')
        except current.Co2PrefixSelectionConflict: failure = error(409, 'co2_prefix_selection_conflict', 'Co2 prefix selection unavailable')
        except current.Co2PrefixRequestRejected: failure = error(422, 'invalid_request', 'Invalid request')
        except current.Co2PrefixPending: failure = unavailable()
        except holds:
            failure = error(422, 'co2_prefix_hold', 'Co2 prefix evidence unavailable')
        except Exception: failure = unavailable()
        observed, denied = authorized_tenant(*PROGRESS_SCOPES)
        if denied is not None: return denied
        if observed != tenant: return error(403, 'forbidden', 'Resource access denied')
        if failure is not None: return failure
        if raw is None: return error(404, 'not_found', 'Co2 prefix not found')
        if type(raw) is not bytes or not 1 <= len(raw) <= public.MAX_RESPONSE_BYTES: return unavailable()
        return Response(raw, media_type='application/json', headers=headers)

    @app.get(PREFIX_PATH, response_model=public.PrefixReplay, operation_id='getCo2Prefix',
        openapi_extra=documentation('summary'), responses=errors)
    async def summary(request: Request, job_id: Annotated[str, Path(pattern=JOB_ID_PATTERN)]):
        return await handle(request, job_id, 'summary')

    @app.get(PREFIX_PATH+'/samples', response_model=public.PrefixReplay, operation_id='getCo2PrefixSamples',
        openapi_extra=documentation('samples'), responses=errors)
    async def samples(request: Request, job_id: Annotated[str, Path(pattern=JOB_ID_PATTERN)]):
        return await handle(request, job_id, 'samples')

    @app.get(PREFIX_PATH+'/events', response_model=public.PrefixReplay, operation_id='getCo2PrefixEvents',
        openapi_extra=documentation('events'), responses=errors)
    async def events(request: Request, job_id: Annotated[str, Path(pattern=JOB_ID_PATTERN)]):
        return await handle(request, job_id, 'events')

    app.openapi_schema = None
