"""Opt-in protected batch sources, calculation intent and current stored result."""
from typing import Annotated,Literal,Union

from fastapi import Query,Path,Request,Response
from pydantic import Field,TypeAdapter
from starlette.concurrency import run_in_threadpool

from .api_contracts import ErrorEnvelope,JobStatus,public_job_status
from .api_json import read_json_request,JsonRequestRejected
from .api_market_source import (MarketUserSourceService,MarketUserSourceRequest,
    MarketUserSourceMetadata,MarketUserSourceSummary,MarketUserSourcePage,
    _source_read_variants,market_user_source_schema,_inline_schema)
from .economic_batch_source_store import EconomicBatchSourceStore,MODELS
from .economic_batch_calculation import (EconomicBatchAuthority,EconomicBatchCalculationService,
    EconomicBatchCalculationRequest,READ_SCOPES,BatchCalculationHold)
from .economic_batch_query import EconomicBatchResultQuery,BatchResultHold
from .economic_batch_wire import BatchArtifactRead
from .job_store import JobIntentConflict
from .market_source_store import MarketSourceConflict,MarketSourceDenied
from .owned_fixture_collection import UUID_PATTERN
from .provenance import Name

BatchSourceKind=Literal['economic_scenario','economic_input','joint_shock','input_rights',
    'settlement_applicability','settlement_evidence','prior_batch_cost','production_batch']
SOURCE_READ=('metadata','economic_batch_source_read')
SOURCE_WRITE=SOURCE_READ+('economic_batch_source_write',)
CALCULATE_SCOPES=READ_SCOPES+('simulation_execute',)
RESULT_SCOPES=READ_SCOPES+('artifact',)


class BatchSourceRequest(MarketUserSourceRequest):
    kind:BatchSourceKind
class BatchSourceMetadata(MarketUserSourceMetadata):
    kind:BatchSourceKind
class BatchSourceSummary(MarketUserSourceSummary):
    kind:BatchSourceKind
class BatchSourcePage(MarketUserSourcePage):
    kind:BatchSourceKind
    items:tuple[BatchSourceMetadata,...]=Field(max_length=50)


BatchSourceRead=Annotated[Union[_source_read_variants(MODELS,metadata=BatchSourceMetadata,prefix='Batch')],Field(discriminator='kind')]


class BatchSourceService(MarketUserSourceService):
    SOURCE_TYPE=EconomicBatchSourceStore
    REQUEST=BatchSourceRequest
    SUMMARY=BatchSourceSummary
    PAGE=BatchSourcePage
    READ_ADAPTER=TypeAdapter(BatchSourceRead)
    WRITE_SCOPES=SOURCE_WRITE
    READ_SCOPES=SOURCE_READ
    POLICY_FLAG='economic_batch_source_storage'
    INTENT_PREFIX='economic-batch-user-source-v1:'

    def __init__(self,jobs,authority):
        if type(authority)is not EconomicBatchAuthority:
            raise ValueError('economic batch source authority rejected')
        self._authority=authority
        super().__init__(jobs,authority._source)

    def _binding(self):
        super()._binding()
        if(self._authority.jobs is not self.jobs or self._authority._source is not self.sources or
                self._authority._binding()!=self._authority._bound):
            raise RuntimeError('economic batch source authority changed')


def install_economic_batch_routes(app,*,jobs,holds,contexts,authority,principal_provider,
        authorized_tenant,error,access):
    if(type(authority)is not EconomicBatchAuthority or authority.jobs is not jobs or
            authority._holds is not holds or holds._context_store is not contexts or
            jobs.principal_provider is not principal_provider or authority._binding()!=authority._bound):
        raise ValueError('economic batch HTTP binding rejected')
    sources=BatchSourceService(jobs,authority)
    calculations=EconomicBatchCalculationService(authority);reader=EconomicBatchResultQuery(authority)
    errors={s:{'model':ErrorEnvelope}for s in(401,403,404,409,413,415,422,503)}
    def guard(tenant,scopes):
        current,denied=authorized_tenant(*scopes)
        if denied is not None:return denied
        if current!=tenant:return error(403,'forbidden','Resource access denied')
        if(jobs.principal_provider is not principal_provider or authority.jobs is not jobs or
                authority._holds is not holds or holds._context_store is not contexts or
                authority._binding()!=authority._bound):
            raise RuntimeError('economic batch HTTP binding changed')
        return None
    def failure(exc):
        if isinstance(exc,(PermissionError,MarketSourceDenied)):return error(403,'forbidden','Resource access denied')
        if isinstance(exc,(JobIntentConflict,MarketSourceConflict)):return error(409,'intent_conflict','Intent or version has different input')
        if isinstance(exc,(BatchCalculationHold,BatchResultHold)):return error(422,'economic_batch_hold','Economic batch evidence unavailable')
        if isinstance(exc,ValueError):return error(422,'invalid_request','Invalid request')
        return error(503,'economic_batch_unavailable','Economic batch unavailable')
    async def payload(request,model,limit):
        return model.model_validate(await read_json_request(request,max_bytes=limit))
    def query_valid(request,allowed):
        keys=[key for key,_ in request.query_params.multi_items()]
        return len(keys)==len(set(keys))and set(keys)<=set(allowed)

    @app.post('/v1/economic-batch-sources',response_model=BatchSourceSummary,
        operation_id='registerEconomicBatchSource',responses=errors,
        openapi_extra={**access(SOURCE_WRITE),'x-ossf-max-body-bytes':65536,
            'requestBody':{'required':True,'content':{'application/json':{'schema':market_user_source_schema(MODELS,BatchSourceRequest)}}}})
    async def register_source(request:Request):
        tenant,denied=authorized_tenant(*SOURCE_WRITE)
        if denied is not None:return denied
        try:
            body=await payload(request,BatchSourceRequest,65536)
            result=await run_in_threadpool(sources.submit,tenant,body)
            return guard(tenant,SOURCE_WRITE)or result
        except JsonRequestRejected as exc:return error(exc.status,exc.code,exc.message)
        except Exception as exc:return failure(exc)

    @app.get('/v1/economic-batch-sources',response_model=BatchSourcePage,
        operation_id='listEconomicBatchSources',responses=errors,openapi_extra=access(SOURCE_READ))
    async def list_sources(request:Request,kind:BatchSourceKind,
            limit:Annotated[int,Query(ge=1,le=50)]=20,
            after_record_id:Annotated[Name|None,Query(max_length=200)]=None,
            after_revision:Annotated[Name|None,Query(max_length=200)]=None):
        tenant,denied=authorized_tenant(*SOURCE_READ)
        if denied is not None:return denied
        if not query_valid(request,{'kind','limit','after_record_id','after_revision'})or(after_record_id is None)!=(after_revision is None):
            return error(422,'invalid_request','Invalid request')
        try:
            result=await run_in_threadpool(sources.list,tenant,kind,limit=limit,
                after_record_id=after_record_id,after_revision=after_revision)
            return guard(tenant,SOURCE_READ)or result
        except Exception as exc:return failure(exc)

    @app.get('/v1/economic-batch-sources/record',response_model=BatchSourceRead,
        operation_id='getEconomicBatchSource',responses=errors,openapi_extra=access(SOURCE_READ))
    async def get_source(request:Request,kind:BatchSourceKind,
            record_id:Annotated[Name,Query(max_length=200)],revision:Annotated[Name,Query(max_length=200)]):
        tenant,denied=authorized_tenant(*SOURCE_READ)
        if denied is not None:return denied
        if not query_valid(request,{'kind','record_id','revision'}):return error(422,'invalid_request','Invalid request')
        try:
            result=await run_in_threadpool(sources.get,tenant,kind,record_id,revision)
            denied=guard(tenant,SOURCE_READ)
            return denied or(result if result is not None else error(404,'not_found','Resource unavailable'))
        except Exception as exc:return failure(exc)

    @app.post('/v1/economic-batch-calculations',status_code=202,response_model=JobStatus,
        operation_id='submitEconomicBatchCalculation',responses=errors,
        openapi_extra={**access(CALCULATE_SCOPES),'x-ossf-max-body-bytes':4096,
            'requestBody':{'required':True,'content':{'application/json':{'schema':_inline_schema(EconomicBatchCalculationRequest)}}}})
    async def calculate(request:Request):
        tenant,denied=authorized_tenant(*CALCULATE_SCOPES)
        if denied is not None:return denied
        try:
            body=await payload(request,EconomicBatchCalculationRequest,4096)
            result=await run_in_threadpool(calculations.submit,tenant,body)
            return guard(tenant,CALCULATE_SCOPES)or public_job_status(result)
        except JsonRequestRejected as exc:return error(exc.status,exc.code,exc.message)
        except Exception as exc:return failure(exc)

    @app.get('/v1/jobs/{job_id}/economic-batch-result',response_model=BatchArtifactRead,
        operation_id='getEconomicBatchResult',responses=errors,
        openapi_extra={**access(RESULT_SCOPES),'x-ossf-max-response-bytes':2097152})
    async def get_result(request:Request,job_id:Annotated[str,Path(pattern=UUID_PATTERN)]):
        tenant,denied=authorized_tenant(*RESULT_SCOPES)
        if denied is not None:return denied
        if not query_valid(request,set()):return error(422,'invalid_request','Invalid request')
        try:
            found=await run_in_threadpool(reader.read,tenant,job_id)
            denied=guard(tenant,RESULT_SCOPES)
            if denied is not None:return denied
            if found is None:return error(404,'not_found','Resource unavailable')
            return Response(found.raw,media_type='application/json',headers={'Cache-Control':'no-store',
                'X-OSSF-Publication-ID':str(found.publication_id),'X-OSSF-Published-At':found.published_at.isoformat()})
        except Exception as exc:return failure(exc)
