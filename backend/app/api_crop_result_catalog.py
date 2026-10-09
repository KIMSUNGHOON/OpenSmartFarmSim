"""Authenticated, closed metadata pages; crop values use existing verified readers."""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import re
from typing import Annotated, Literal

from fastapi import Query, Request, Response
from pydantic import BeforeValidator, Field, TypeAdapter, model_validator
from starlette.concurrency import run_in_threadpool

from .api_contracts import ErrorEnvelope
from .api_crop_replay import _Public, Name, UtcStamp, NAME_PATTERN
from .api_crop_harvest_replay import Farm, FalseValue, ParentID, ResultID as HarvestID
from .crop_result_store import READ_SCOPES
from .provenance import Name as UserLabel
from .thermal_run_store import _canonical

PATH = '/v1/crop-research-result-catalog'
SELECTION_PATH = PATH+'/farm-crops'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_RESPONSE_BYTES = 64 * 1024
Kind = Literal['calculation_cycle_v1', 'harvest_v1']
STAMP_PATTERN = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$'
RecordedAt = Annotated[UtcStamp, Field(pattern=STAMP_PATTERN)]
AnyResultID = ParentID | HarvestID
Count = Annotated[int, Field(strict=True, ge=0, le=131072)]


def _true(value):
    if type(value) is not bool or value is not True:
        raise ValueError('explicit metadata selection policy required')
    return value


TrueValue = Annotated[Literal[True], BeforeValidator(_true)]


class Period(_Public):
    start: UtcStamp
    end: UtcStamp

    @model_validator(mode='after')
    def ordered(self):
        if datetime.fromisoformat(self.start) >= datetime.fromisoformat(self.end):
            raise ValueError('invalid metadata period')
        return self


class GrowthItem(_Public):
    result_id: ParentID
    recorded_at: RecordedAt
    calculation_status: Literal['completed', 'hold']
    claim_scope: Literal['synthetic_crop_math_only']
    study_id: Name
    revision: Name
    period: Period
    sample_count: Count
    event_count: Count


class HarvestItem(_Public):
    result_id: HarvestID
    recorded_at: RecordedAt
    calculation_status: Literal['completed', 'hold']
    claim_scope: Literal['synthetic_harvest_allocation_math_only']
    parent_result_id: ParentID
    row_count: Annotated[int, Field(strict=True, ge=0, le=262144)]


class GrowthCursor(_Public):
    recorded_at: RecordedAt
    result_id: ParentID


class HarvestCursor(_Public):
    recorded_at: RecordedAt
    result_id: HarvestID


class CatalogBase(_Public):
    version: Literal['crop-research-result-catalog-v1']
    scope: Literal['stored_research_metadata_only']
    farm: Farm
    selection_validation_required: TrueValue
    rights_or_gate_approval: FalseValue


class GrowthCatalog(CatalogBase):
    kind: Literal['calculation_cycle_v1']
    items: Annotated[list[GrowthItem], Field(max_length=20)]
    next_cursor: GrowthCursor | None


class HarvestCatalog(CatalogBase):
    kind: Literal['harvest_v1']
    items: Annotated[list[HarvestItem], Field(max_length=20)]
    next_cursor: HarvestCursor | None


CatalogPage = Annotated[GrowthCatalog | HarvestCatalog, Field(discriminator='kind')]
_PAGE = TypeAdapter(CatalogPage)
_STAMP = TypeAdapter(RecordedAt)


class FarmRegistration(_Public):
    scenario_id: Name
    scenario_revision: Name
    registration_sha256: Annotated[str, Field(strict=True, pattern=r'^[0-9a-f]{64}$')]


class RegisteredCrop(_Public):
    crop_id: Name
    batch_id: Name
    species: Annotated[UserLabel, Field(strict=True, min_length=1, max_length=200)]
    variety: Annotated[UserLabel, Field(strict=True, min_length=1, max_length=200)]
    occupancy: Period
    profile_status: Literal['unavailable']
    origin: Literal['user']
    evidence_level: Literal['assumed']


class FarmSelection(_Public):
    version: Literal['crop-research-farm-selection-v1']
    scope: Literal['registered_user_inputs_only']
    farm: FarmRegistration
    items: Annotated[list[RegisteredCrop], Field(max_length=32)]
    selection_validation_required: TrueValue
    rights_or_gate_approval: FalseValue


_FARM_SELECTION = TypeAdapter(FarmSelection)


class CatalogProjectionHold(ValueError):
    """Stored metadata does not support this public response."""


def _public_bytes(value, *, kind, farm, limit, before):
    try:
        projected = _PAGE.validate_python(value)
        if projected.kind != kind or projected.farm.model_dump(mode='json') != farm or len(projected.items) > limit:
            raise ValueError()
        keys = [(datetime.fromisoformat(row.recorded_at), row.result_id) for row in projected.items]
        if (keys != sorted(keys, reverse=True) or len(set(keys)) != len(keys) or
                before is not None and any(key >= (before['recorded_at'], before['result_id']) for key in keys)):
            raise ValueError()
        cursor = projected.next_cursor
        if cursor is not None and (len(keys) != limit or
                (datetime.fromisoformat(cursor.recorded_at), cursor.result_id) != keys[-1]):
            raise ValueError()
        raw = _canonical(projected.model_dump(mode='json'))
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError()
        return raw
    except Exception:
        raise CatalogProjectionHold('stored crop catalog display unavailable') from None


def _response(service, tenant, kind, farm, limit, before):
    with service.open(tenant, kind, farm, limit=limit, before=before) as value:
        return _public_bytes(value, kind=kind, farm=farm, limit=limit, before=before)


def _farm_selection_bytes(value, *, farm):
    try:
        projected = _FARM_SELECTION.validate_python(value)
        ids = [row.crop_id for row in projected.items]
        if projected.farm.model_dump(mode='json') != farm or ids != sorted(set(ids)):
            raise ValueError()
        raw = _canonical(projected.model_dump(mode='json'))
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError()
        return raw
    except Exception:
        raise CatalogProjectionHold('stored crop farm selection unavailable') from None


def _selection_response(service, tenant, farm):
    with service.open_farm_selection(tenant, farm) as value:
        return _farm_selection_bytes(value, farm=farm)


def install_catalog_routes(app, *, jobs, farms, calculation_query, harvest_query,
                           principal_provider, authorized_tenant, error, access):
    service = None
    if not all(callable(fn) for fn in (principal_provider, authorized_tenant, error, access)):
        raise ValueError('trusted crop catalog required')
    if calculation_query is not None:
        from . import crop_result_catalog as catalog
        try:
            if type(calculation_query) is not catalog.calculation.CalculationCurrentCycleQuery:
                raise ValueError()
            store = calculation_query.store
            if (type(store) is not catalog.calculation.storage.CalculationCycleCropResultStore or
                    store.jobs is not jobs or farms is None or store.server.binding.farms is not farms or
                    store.server.binding.jobs is not jobs or jobs.principal_provider is not principal_provider):
                raise ValueError()
            service = catalog.CropResultCatalog(calculation_query, harvest_query)
        except Exception:
            raise ValueError('trusted crop catalog required') from None
    headers = {} if service is None else {'Cache-Control': 'no-store', 'X-OSSF-Crop-Catalog-Version': catalog.VERSION,
        'X-OSSF-Crop-Catalog-Code-SHA256': catalog.CODE_SHA256,
        'X-OSSF-Crop-Catalog-Projection-SHA256': CODE_SHA256}
    selection_headers = {} if service is None else {**headers,
        'X-OSSF-Crop-Farm-Selection-Version': catalog.SELECTION_VERSION}

    @app.get(SELECTION_PATH, response_model=FarmSelection, operation_id='getCropResearchFarmSelection',
        openapi_extra=access(READ_SCOPES),
        responses={status: {'model': ErrorEnvelope} for status in (401, 403, 422, 503)})
    async def get_farm_selection(request: Request,
            scenario_id: Annotated[str, Query(pattern=NAME_PATTERN, max_length=200)],
            scenario_revision: Annotated[str, Query(pattern=NAME_PATTERN, max_length=200)],
            registration_sha256: Annotated[str, Query(pattern=r'^[0-9a-f]{64}$')]):
        tenant, denied = authorized_tenant(*READ_SCOPES)
        if denied is not None:
            return denied
        keys = [key for key, _ in request.query_params.multi_items()]
        if len(keys) != len(set(keys)) or set(keys) != {'scenario_id', 'scenario_revision', 'registration_sha256'}:
            return error(422, 'invalid_request', 'Invalid request')
        async for chunk in request.stream():
            if chunk:
                return error(422, 'invalid_request', 'Invalid request')
        if service is None:
            return error(503, 'crop_catalog_unavailable', 'Stored crop catalog unavailable')
        farm = {'scenario_id': scenario_id, 'scenario_revision': scenario_revision,
                'registration_sha256': registration_sha256}
        try:
            raw = await run_in_threadpool(_selection_response, service, tenant, farm)
            current, denied = authorized_tenant(*READ_SCOPES)
            if denied is not None:
                return denied
            if current != tenant:
                return error(403, 'forbidden', 'Resource access denied')
            return Response(raw, media_type='application/json', headers=selection_headers)
        except PermissionError:
            return error(403, 'forbidden', 'Resource access denied')
        except (catalog.CropResultCatalogHold, CatalogProjectionHold):
            return error(422, 'crop_catalog_hold', 'Stored crop catalog evidence unavailable')
        except Exception:
            return error(503, 'crop_catalog_unavailable', 'Stored crop catalog unavailable')

    @app.get(PATH, response_model=CatalogPage, operation_id='listCropResearchResults',
        openapi_extra=access(READ_SCOPES),
        responses={status: {'model': ErrorEnvelope} for status in (401, 403, 422, 503)})
    async def list_results(request: Request,
            kind: Annotated[Kind, Query()],
            scenario_id: Annotated[str, Query(pattern=NAME_PATTERN, max_length=200)],
            scenario_revision: Annotated[str, Query(pattern=NAME_PATTERN, max_length=200)],
            registration_sha256: Annotated[str, Query(pattern=r'^[0-9a-f]{64}$')],
            crop_id: Annotated[str, Query(pattern=NAME_PATTERN, max_length=200)],
            limit: Annotated[int, Query(ge=1, le=20)] = 10,
            before_recorded_at: Annotated[str | None, Query(pattern=STAMP_PATTERN, max_length=27)] = None,
            before_result_id: Annotated[str | None, Query(max_length=110)] = None):
        tenant, denied = authorized_tenant(*READ_SCOPES)
        if denied is not None:
            return denied
        pairs = list(request.query_params.multi_items()); keys = [key for key, _ in pairs]
        required = {'kind', 'scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id'}
        if (len(keys) != len(set(keys)) or not required <= set(keys) <= required | {
                'limit', 'before_recorded_at', 'before_result_id'} or
                any(not re.fullmatch(r'[1-9][0-9]*', value) for key, value in pairs if key == 'limit') or
                (before_recorded_at is None) != (before_result_id is None)):
            return error(422, 'invalid_request', 'Invalid request')
        farm = {'scenario_id': scenario_id, 'scenario_revision': scenario_revision,
                'registration_sha256': registration_sha256, 'crop_id': crop_id}
        before = None
        try:
            if before_recorded_at is not None:
                before = {'recorded_at': datetime.fromisoformat(_STAMP.validate_python(before_recorded_at)),
                          'result_id': TypeAdapter(ParentID if kind == 'calculation_cycle_v1' else HarvestID
                              ).validate_python(before_result_id)}
        except Exception:
            return error(422, 'invalid_request', 'Invalid request')
        async for chunk in request.stream():
            if chunk:
                return error(422, 'invalid_request', 'Invalid request')
        if service is None or kind == 'harvest_v1' and service.harvest is None:
            return error(503, 'crop_catalog_unavailable', 'Stored crop catalog unavailable')
        try:
            raw = await run_in_threadpool(_response, service, tenant, kind, farm, limit, before)
            current, denied = authorized_tenant(*READ_SCOPES)
            if denied is not None:
                return denied
            if current != tenant:
                return error(403, 'forbidden', 'Resource access denied')
            return Response(raw, media_type='application/json', headers=headers)
        except PermissionError:
            return error(403, 'forbidden', 'Resource access denied')
        except (catalog.CropResultCatalogHold, CatalogProjectionHold):
            return error(422, 'crop_catalog_hold', 'Stored crop catalog evidence unavailable')
        except Exception:
            return error(503, 'crop_catalog_unavailable', 'Stored crop catalog unavailable')

    app.openapi_schema = None
