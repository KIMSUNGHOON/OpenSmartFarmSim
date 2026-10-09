"""Authenticated bounded reads of original verified calculation results."""
import re
from typing import Annotated, Literal

from fastapi import Path, Query, Request, Response
from starlette.concurrency import run_in_threadpool

from . import api_crop_cycle_calculation_replay as public
from .api_contracts import ErrorEnvelope
from .api_crop_replay import NAME_PATTERN
from .crop_result_store import READ_SCOPES


def _read_response(query, tenant, result_id, farm_ref, view, offset, limit):
    with query.open(tenant, result_id, farm_ref, kind=None if view == 'summary' else view,
                    start=offset, limit=limit) as value:
        if value is None:
            return None
        projected = public.project_calculation_cycle_result(value['record'], value['terminal'],
            view=view, page=value['page'], limit=limit)
        return public._public_bytes(projected)


def install_calculation_cycle_routes(app, *, jobs, farms, store, query,
                                    principal_provider, authorized_tenant, error, access):
    headers = {'Cache-Control': 'no-store'}
    holds = ()
    if store is not None or query is not None:
        from .crop_cycle_calculation_result_store import CalculationCycleCropResultStore
        from . import crop_cycle_calculation_current_query as current
        from .crop_cycle_calculation_server_custody import CalculationCustodyHold
        from .crop_cycle_calculation_farm_binding import CalculationFarmBindingHold
        from .farm_authoring_storage import FarmAuthoringHold
        if (type(store) is not CalculationCycleCropResultStore or
                type(query) is not current.CalculationCurrentCycleQuery or query.store is not store or
                store.jobs is not jobs or farms is None or store.server.binding.farms is not farms or
                store.server.binding.jobs is not jobs or jobs.principal_provider is not principal_provider):
            raise ValueError('trusted calculation cycle reader required')
        store._binding()
        query._binding()
        holds = (CalculationCustodyHold, CalculationFarmBindingHold,
                 FarmAuthoringHold, current.CalculationCurrentCycleQueryHold)
        headers.update({'X-OSSF-Crop-Query-Version': current.VERSION,
                        'X-OSSF-Crop-Query-Code-SHA256': current.CODE_SHA256})

    @app.get('/v1/crop-cycle-calculation-research-results/{result_id}',
        response_model=public.CalculationCycleCropReplay, operation_id='getCalculationCycleCropResearchResult',
        openapi_extra=access(READ_SCOPES),
        responses={status: {'model': ErrorEnvelope} for status in (401, 403, 404, 422, 503)})
    async def get_calculation_cycle(request: Request,
            result_id: Annotated[str, Path(pattern=public.RESULT_ID_PATTERN)],
            scenario_id: Annotated[str, Query(pattern=NAME_PATTERN, max_length=200)],
            scenario_revision: Annotated[str, Query(pattern=NAME_PATTERN, max_length=200)],
            registration_sha256: Annotated[str, Query(pattern=r'^[0-9a-f]{64}$')],
            crop_id: Annotated[str, Query(pattern=NAME_PATTERN, max_length=200)],
            view: Literal['summary', 'samples', 'events'] = 'summary',
            offset: Annotated[int, Query(ge=0, le=131072)] = 0,
            limit: Annotated[int | None, Query(ge=1, le=64)] = None):
        tenant, denied = authorized_tenant(*READ_SCOPES)
        if denied is not None:
            return denied
        pairs = list(request.query_params.multi_items())
        keys = [key for key, _ in pairs]
        required = {'scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id'}
        if (len(keys) != len(set(keys)) or not required <= set(keys) <= required | {'view', 'offset', 'limit'} or
                any(not re.fullmatch(r'0|[1-9][0-9]*', value)
                    for key, value in pairs if key in ('offset', 'limit')) or
                (view == 'summary' and bool({'offset', 'limit'} & set(keys))) or
                (view == 'events' and limit is not None and limit > 8)):
            return error(422, 'invalid_request', 'Invalid request')
        async for chunk in request.stream():
            if chunk:
                return error(422, 'invalid_request', 'Invalid request')
        if store is None:
            return error(503, 'crop_research_unavailable', 'Crop research result unavailable')
        if view != 'summary' and limit is None:
            limit = 64 if view == 'samples' else 8
        try:
            raw = await run_in_threadpool(_read_response, query, tenant, result_id,
                {'scenario_id': scenario_id, 'scenario_revision': scenario_revision,
                 'registration_sha256': registration_sha256, 'crop_id': crop_id}, view, offset, limit)
            current_tenant, denied = authorized_tenant(*READ_SCOPES)
            if denied is not None:
                return denied
            if current_tenant != tenant:
                return error(403, 'forbidden', 'Resource access denied')
            if raw is None:
                return error(404, 'not_found', 'Crop research result not found')
            return Response(raw, media_type='application/json', headers=headers)
        except PermissionError:
            return error(403, 'forbidden', 'Resource access denied')
        except holds:
            return error(422, 'crop_research_hold', 'Crop research evidence unavailable')
        except Exception:
            return error(503, 'crop_research_unavailable', 'Crop research result unavailable')
