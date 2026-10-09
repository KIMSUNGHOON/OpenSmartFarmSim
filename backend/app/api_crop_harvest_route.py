"""Authenticated bounded reads of registered synthetic harvest arithmetic."""
import re
from typing import Annotated, Literal

from fastapi import Path, Query, Request, Response
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect

from . import api_crop_harvest_replay as public
from .api_contracts import ErrorEnvelope
from .api_crop_replay import NAME_PATTERN
from .crop_result_store import READ_SCOPES


def _read_response(query, tenant, result_id, farm_ref, view, offset, limit):
    with query.open(tenant,result_id,farm_ref,start=offset,limit=limit) as value:
        if value is None:return None
        projected=public.project_harvest_result(value,view=view,limit=limit)
        return public._public_bytes(projected)


def install_harvest_routes(app, *, jobs, farms, query, principal_provider, authorized_tenant, error, access):
    if not all(callable(v) for v in (principal_provider,authorized_tenant,error,access)):
        raise ValueError('trusted harvest reader required')
    headers={'Cache-Control':'no-store'};holds=(public.HarvestProjectionHold,)
    if query is not None:
        from . import crop_harvest_current_query as current
        registry=current.registry;original=current.current
        try:
            if type(query) is not current.HarvestCurrentQuery:raise ValueError()
            store=query.store
            if type(store) is not registry.HarvestRegistry or store.role!=store.policy.reader:raise ValueError()
            parent=store.query.store
            if (type(store.query) is not original.CalculationCurrentCycleQuery
                    or type(parent) is not original.storage.CalculationCycleCropResultStore
                    or parent.jobs is not jobs or farms is None or parent.server.binding.farms is not farms
                    or parent.server.binding.jobs is not jobs or jobs.principal_provider is not principal_provider):raise ValueError()
            query._binding()
        except Exception:raise ValueError('trusted harvest reader required') from None
        holds+=(current.HarvestCurrentQueryHold,registry.HarvestRegistrationHold,registry.replay.HarvestArtifactHold)
        headers.update({'X-OSSF-Harvest-Query-Version':current.VERSION,
            'X-OSSF-Harvest-Query-Code-SHA256':current.CODE_SHA256,
            'X-OSSF-Harvest-Projection-Code-SHA256':public.CODE_SHA256})

    @app.get('/v1/crop-harvest-research-results/{result_id}',response_model=public.HarvestReplay,
        operation_id='getHarvestResearchResult',openapi_extra=access(READ_SCOPES),
        responses={status:{'model':ErrorEnvelope} for status in (401,403,404,422,503)})
    async def get_harvest(request: Request,
            result_id: Annotated[str,Path(pattern=public.RESULT_ID_PATTERN)],
            scenario_id: Annotated[str,Query(pattern=NAME_PATTERN,max_length=200)],
            scenario_revision: Annotated[str,Query(pattern=NAME_PATTERN,max_length=200)],
            registration_sha256: Annotated[str,Query(pattern=r'^[0-9a-f]{64}$')],
            crop_id: Annotated[str,Query(pattern=NAME_PATTERN,max_length=200)],
            view: Literal['summary','records']='summary',
            offset: Annotated[int,Query(ge=0,le=public.MAX_ROWS)]=0,
            limit: Annotated[int|None,Query(ge=1,le=64)]=None):
        tenant,denied=authorized_tenant(*READ_SCOPES)
        if denied is not None:return denied
        pairs=list(request.query_params.multi_items());keys=[key for key,_ in pairs]
        required={'scenario_id','scenario_revision','registration_sha256','crop_id'}
        if (len(keys)!=len(set(keys)) or not required<=set(keys)<=required|{'view','offset','limit'}
                or any(not re.fullmatch(r'0|[1-9][0-9]*',value) for key,value in pairs if key in ('offset','limit'))
                or view=='summary' and bool({'offset','limit'}&set(keys))):
            return error(422,'invalid_request','Invalid request')
        try:
            async for chunk in request.stream():
                if chunk:return error(422,'invalid_request','Invalid request')
        except ClientDisconnect:
            return error(422,'invalid_request','Invalid request')
        if query is None:return error(503,'harvest_research_unavailable','Harvest research result unavailable')
        if view=='records' and limit is None:limit=64
        try:
            raw=await run_in_threadpool(_read_response,query,tenant,result_id,
                {'scenario_id':scenario_id,'scenario_revision':scenario_revision,'registration_sha256':registration_sha256,
                    'crop_id':crop_id},view,offset,limit)
            current_tenant,denied=authorized_tenant(*READ_SCOPES)
            if denied is not None:return denied
            if current_tenant!=tenant:return error(403,'forbidden','Resource access denied')
            if raw is None:return error(404,'not_found','Harvest research result not found')
            return Response(raw,media_type='application/json',headers=headers)
        except PermissionError:return error(403,'forbidden','Resource access denied')
        except holds:return error(422,'harvest_research_hold','Harvest research evidence unavailable')
        except Exception:return error(503,'harvest_research_unavailable','Harvest research result unavailable')

    app.openapi_schema=None
