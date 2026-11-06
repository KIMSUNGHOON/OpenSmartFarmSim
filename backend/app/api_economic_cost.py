"""Opt-in protected cost admission and original stored-result responses."""
from .api_economic_batch import _install_calculation_routes,CALCULATE_SCOPES
from .economic_batch_calculation import EconomicBatchAuthority
from .economic_cost_calculation import EconomicCostCalculationService,CostCalculationHold,_program
from .economic_cost_query import EconomicCostResultQuery,CostResultHold
from .economic_cost_wire import CostArtifactRead
from .job_store import JobIntentConflict


class _HTTPDenied(Exception):
    def __init__(self,response):self.response=response


class _CostHTTPService(EconomicCostCalculationService):
    def __init__(self,authority,check):
        super().__init__(authority);self._http_check,self._bound_http_check=check,check

    def _prepare(self,tenant,body):
        check=self._bound_http_check
        if self._http_check is not check:raise RuntimeError('economic cost HTTP callback changed')
        check(tenant,CALCULATE_SCOPES)
        try:return super()._prepare(tenant,body)
        finally:
            if self._http_check is not check:raise RuntimeError('economic cost HTTP callback changed')
            check(tenant,CALCULATE_SCOPES)


def install_economic_cost_routes(app,*,jobs,holds,contexts,authority,principal_provider,
        authorized_tenant,error,access):
    if(type(authority)is not EconomicBatchAuthority or authority.jobs is not jobs or
            authority._holds is not holds or holds._context_store is not contexts or
            jobs.principal_provider is not principal_provider or authority._binding()!=authority._bound):
        raise ValueError('economic cost HTTP binding rejected')
    program=_program();reader=EconomicCostResultQuery(authority)
    def pointers():
        return(jobs.principal_provider,authority.jobs,authority._source,authority._holds,
            holds._context_store,jobs.artifact_root,jobs.content_access,
            calculations.authority,calculations._http_check,calculations._bound_http_check,
            reader.authority,reader.jobs)
    def binding():
        if(pointers()!=bound or authority._binding()!=authority._bound or reader._pointers()!=reader._bound):
            raise RuntimeError('economic cost HTTP binding changed')
        if _program()!=program:raise CostCalculationHold('economic cost HTTP program changed')
        if pointers()!=bound or reader._pointers()!=reader._bound:
            raise RuntimeError('economic cost HTTP binding changed')
    def guard(tenant,scopes):
        for _ in range(2):
            current,denied=authorized_tenant(*scopes)
            if denied is not None:return denied
            if current!=tenant:return error(403,'forbidden','Resource access denied')
            binding()
        return None
    def check(tenant,scopes):
        denied=guard(tenant,scopes)
        if denied is not None:raise _HTTPDenied(denied)
    calculations=_CostHTTPService(authority,check);bound=pointers()
    def failure(exc):
        if isinstance(exc,_HTTPDenied):return exc.response
        if isinstance(exc,PermissionError):return error(403,'forbidden','Resource access denied')
        if isinstance(exc,JobIntentConflict):return error(409,'intent_conflict','Intent or version has different input')
        if isinstance(exc,(CostCalculationHold,CostResultHold)):return error(422,'economic_cost_hold','Economic cost evidence unavailable')
        if isinstance(exc,ValueError):return error(422,'invalid_request','Invalid request')
        return error(503,'economic_cost_unavailable','Economic cost unavailable')
    _install_calculation_routes(app,calculations=calculations,reader=reader,artifact_type=CostArtifactRead,
        family='economic-cost',operation_prefix='EconomicCost',authorized_tenant=authorized_tenant,
        error=error,access=access,guard=guard,failure=failure,reject_submission_query=True,
        route_names=('calculate_cost','get_cost_result'))
