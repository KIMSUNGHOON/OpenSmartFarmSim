"""Calculation-free immutable admission for the conditional cost trace."""
from hashlib import sha256
from typing import Literal

from pydantic import Field

from . import economic_cost_trace as trace
from .economic_batch_calculation import (BatchCalculationHold,EconomicBatchAuthority,
    EconomicBatchCalculationInput,EconomicBatchCalculationRequest,EconomicBatchCalculationService)
from .economic_contracts import untrusted_data
from .provenance import Digest,FrozenContract,Name

_PROGRAM=(trace.TRACE_VERSION,trace.CODE_SHA256,tuple(sorted(trace.COMPONENT_SHA256.items())))


class CostCalculationHold(BatchCalculationHold):
    pass


class EconomicCostCalculationInput(FrozenContract):
    input_version:Literal['economic-cost-line-calculation-input-v1']
    base_input:EconomicBatchCalculationInput
    trace_version:Literal['economic-cost-line-trace-v1']
    code_sha256:Digest
    component_sha256:dict[Name,Digest]=Field(min_length=1,max_length=16)


def _program():
    try:
        trace._fence()
        if(trace.TRACE_VERSION,trace.CODE_SHA256,tuple(sorted(trace.COMPONENT_SHA256.items())))!=_PROGRAM:
            raise ValueError('program binding changed')
    except ValueError:raise CostCalculationHold('cost trace program unavailable')from None
    return dict(trace_version=_PROGRAM[0],code_sha256=_PROGRAM[1],component_sha256=dict(_PROGRAM[2]))


class EconomicCostCalculationService:
    def __init__(self,authority):
        if type(authority)is not EconomicBatchAuthority:
            raise ValueError('economic cost server authority required')
        self.authority=authority

    def _prepare(self,tenant,body):
        authority=self.authority
        try:
            program=_program()
            base=EconomicBatchCalculationService(authority)._prepare(tenant,body)
            if _program()!=program:raise CostCalculationHold('cost trace program changed')
            return EconomicCostCalculationInput(input_version='economic-cost-line-calculation-input-v1',
                base_input=base,**program)
        except BatchCalculationHold:raise CostCalculationHold('economic cost input unavailable')from None
        finally:authority.require(tenant)

    def submit(self,tenant,body):
        authority=self.authority
        if type(authority)is not EconomicBatchAuthority:
            raise RuntimeError('economic cost authority changed')
        def guard():
            _program()
            if self.authority is not authority:
                raise RuntimeError('economic cost authority changed')
            authority.require(tenant,execute=True)
            _program()
            if self.authority is not authority:
                raise RuntimeError('economic cost authority changed')
        guard()
        body=EconomicBatchCalculationRequest.model_validate(untrusted_data(body))
        try:value=self._prepare(tenant,body)
        finally:guard()
        def final_guard():
            guard()
            try:
                if self._prepare(tenant,body)!=value:
                    raise RuntimeError('economic cost evidence changed')
            finally:guard()
        key='economic-cost-line-calculation-v1:'+sha256(body.idempotency_key.encode('ascii')).hexdigest()
        return authority.jobs.submit(tenant,'simulation',value.model_dump(mode='json'),key,
                                     commit_guard=final_guard)
