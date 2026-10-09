"""Authenticated bounded reads of original joint crop and climate results."""
import re
from typing import Annotated, Literal

from fastapi import Path, Query, Request, Response
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect

from .api_contracts import ErrorEnvelope
from .api_crop_replay import NAME_PATTERN
from .crop_result_store import READ_SCOPES


def install_joint_crop_climate_routes(app, *, jobs, farms, store, query,
                                     principal_provider, authorized_tenant, error, access):
    from . import api_crop_climate_joint_replay as public
    if not all(callable(v) for v in (principal_provider, authorized_tenant, error, access)):
        raise ValueError('trusted joint crop climate reader required')
    headers = {'Cache-Control': 'no-store'}
    holds = (public.ProjectionHold,)
    if store is not None or query is not None:
        from . import crop_climate_joint_current_query as current
        from .farm_authoring_storage import FarmAuthoringHold
        try:
            if (type(store) is not current.storage.JointCropClimateResultStore
                    or type(query) is not current.JointCropClimateCurrentQuery or query.store is not store
                    or store.jobs is not jobs or farms is None or store.server.binding.farms is not farms
                    or store.server.binding.jobs is not jobs or jobs.principal_provider is not principal_provider):
                raise ValueError()
            store._binding(); query._binding()
        except Exception:
            raise ValueError('trusted joint crop climate reader required') from None
        holds += (current.JointCurrentQueryHold, current.server.JointCustodyHold,
                  current.server.farms.JointFarmBindingHold, FarmAuthoringHold)
        headers.update({'X-OSSF-Joint-Query-Version': current.VERSION,
            'X-OSSF-Joint-Query-Code-SHA256': current.CODE_SHA256,
            'X-OSSF-Joint-Projection-Code-SHA256': public.CODE_SHA256})

    @app.get('/v1/crop-climate-joint-research-results/{result_id}', response_model=public.JointReplay,
        operation_id='getJointCropClimateResearchResult', openapi_extra=access(READ_SCOPES),
        responses={status: {'model': ErrorEnvelope} for status in (401, 403, 404, 422, 503)})
    async def get_joint_result(request: Request,
            result_id: Annotated[str, Path(pattern=public.RESULT_ID_PATTERN)],
            scenario_id: Annotated[str, Query(pattern=NAME_PATTERN, max_length=200)],
            scenario_revision: Annotated[str, Query(pattern=NAME_PATTERN, max_length=200)],
            registration_sha256: Annotated[str, Query(pattern=r'^[0-9a-f]{64}$')],
            crop_id: Annotated[str, Query(pattern=NAME_PATTERN, max_length=200)],
            view: Literal['summary', 'samples', 'events'] = 'summary',
            offset: Annotated[int, Query(ge=0, le=512)] = 0,
            limit: Annotated[int | None, Query(ge=1, le=64)] = None):
        tenant, denied = authorized_tenant(*READ_SCOPES)
        if denied is not None: return denied
        pairs = list(request.query_params.multi_items()); keys = [key for key, _ in pairs]
        required = {'scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id'}
        if (len(keys) != len(set(keys)) or not required <= set(keys) <= required | {'view', 'offset', 'limit'}
                or any(not re.fullmatch(r'0|[1-9][0-9]*', value) for key, value in pairs if key in ('offset', 'limit'))
                or view == 'summary' and bool({'offset', 'limit'} & set(keys))
                or view == 'events' and (offset > 128 or limit is not None and limit > 8)):
            return error(422, 'invalid_request', 'Invalid request')
        try:
            async for chunk in request.stream():
                if chunk: return error(422, 'invalid_request', 'Invalid request')
        except ClientDisconnect:
            return error(422, 'invalid_request', 'Invalid request')
        if query is None:
            return error(503, 'joint_research_unavailable', 'Joint research result unavailable')
        failure = None
        try:
            raw = await run_in_threadpool(query.read, tenant, result_id,
                {'scenario_id': scenario_id, 'scenario_revision': scenario_revision,
                 'registration_sha256': registration_sha256, 'crop_id': crop_id},
                view=view, offset=offset, limit=limit)
        except PermissionError: failure = error(403, 'forbidden', 'Resource access denied')
        except holds: failure = error(422, 'joint_research_hold', 'Joint research evidence unavailable')
        except Exception: failure = error(503, 'joint_research_unavailable', 'Joint research result unavailable')
        current_tenant, denied = authorized_tenant(*READ_SCOPES)
        if denied is not None: return denied
        if current_tenant != tenant: return error(403, 'forbidden', 'Resource access denied')
        if failure is not None: return failure
        if raw is None: return error(404, 'not_found', 'Joint research result not found')
        if type(raw) is not bytes or not 1 <= len(raw) <= public.MAX_RESPONSE_BYTES:
            return error(503, 'joint_research_unavailable', 'Joint research result unavailable')
        return Response(raw, media_type='application/json', headers=headers)

    app.openapi_schema = None
