"""Typed original cost traces with current read authority and no amount replay."""
from dataclasses import dataclass,replace
from datetime import datetime
from decimal import localcontext
from hashlib import sha256
import json
from uuid import UUID

from pydantic import TypeAdapter

from . import economic_cost_trace as trace
from .economic_batch_query import (EconomicBatchResultQuery,BatchResultHold,_Envelope,
    MAX_ARTIFACT_BYTES,_finite,_NAME,decode_stored_batch_result)
from .economic_contracts import untrusted_data
from .economic_cost_calculation import (EconomicCostCalculationInput,EconomicCostCalculationService,_program)
from .economic_production_batches import BatchEconomicScenario,_raw

ARTIFACT_VERSION='economic-cost-line-calculation-result-v1'
_TRACE=TypeAdapter(trace.CostTraceResult)


class CostResultHold(BatchResultHold):
    pass


class _CostEnvelope(_Envelope):
    input: EconomicCostCalculationInput


def _shape(result):
    _finite(result);_NAME.validate_python(result.tenant_id,strict=True)
    if result.period_start>result.period_end or tuple(v.category for v in result.groups)!=('variable','fixed'):
        raise ValueError()
    if len({v.cost.id for v in result.lines})!=len(result.lines):raise ValueError()
    for line in result.lines:
        if any(v is not None and v<0 for v in (line.incurred,line.bank_paid_in_period,
                line.bank_paid_after_period,line.setoff_in_period,line.remaining_payable_at_period_end)):
            raise ValueError()
    for group in result.groups:
        if any(v is not None and v<0 for v in (group.incurred,group.bank_paid_in_period,
                group.setoff_in_period,group.remaining_payable_at_period_end)):
            raise ValueError()
    year,number=result.period_start.year,result.period_start.month
    for month in result.months:
        if(month.month!=f'{year:04d}-{number:02d}'or month.known_bank_outflow<0 or
                month.bank_outflow is not None and month.bank_outflow<0):raise ValueError()
        year,number=(year+1,1)if number==12 else(year,number+1)
    if not result.months or result.months[-1].month!=f'{result.period_end.year:04d}-{result.period_end.month:02d}':
        raise ValueError()


def decode_stored_cost_result(raw):
    try:
        with localcontext(trace._CONTEXT):
            program=_program()
            if type(raw)is not bytes or not 1<=len(raw)<=MAX_ARTIFACT_BYTES:raise ValueError()
            value=json.loads(raw)
            if type(value)is not dict or _raw(value)!=raw:raise ValueError()
            base_value=value['base_result'];base=decode_stored_batch_result(_raw(base_value))
            parsed={**value,'base_result':{**base_value,'ledger':{**base_value['ledger'],'closing_inventory':None}}}
            result=replace(_TRACE.validate_json(_raw(parsed)),base_result=base)
            _shape(result)
            identity={key:item for key,item in value.items()if key!='trace_id'}
            if(trace.trace_bytes(result)!=raw or result.trace_id!=sha256(_raw(identity)).hexdigest()or
                    result.trace_version!=program['trace_version']or result.code_sha256!=program['code_sha256']or
                    result.component_sha256!=program['component_sha256']or _program()!=program):
                raise ValueError()
            return result
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,RecursionError):
        raise CostResultHold('stored economic cost result invalid')from None


@dataclass(frozen=True)
class StoredCostResult:
    raw: bytes
    publication_id: UUID
    published_at: datetime
    result: trace.CostTraceResult


def _declared(scenario,name):
    values=getattr(scenario,name)
    return values is not None and(bool(values)or any(v.group==name for v in scenario.zero_declarations))


class EconomicCostResultQuery(EconomicBatchResultQuery):
    _input_version='economic-cost-line-calculation-input-v1'
    _input_type=EconomicCostCalculationInput
    _envelope_type=_CostEnvelope
    _service_type=EconomicCostCalculationService
    _artifact_version=ARTIFACT_VERSION
    _stored_type=StoredCostResult
    _hold_type=CostResultHold

    def _reference(self,value):
        return value.base_input

    def _decode(self,raw):
        return decode_stored_cost_result(raw)

    def _fence(self):
        try:_program()
        except ValueError:raise CostResultHold('cost trace program unavailable')from None

    def _binding(self,tenant,value,result):
        reference=value.base_input
        super()._binding(tenant,reference,result.base_result)
        scenario=BatchEconomicScenario.model_validate(untrusted_data(self.authority.get_economic_scenario(
            reference.scenario_id,reference.scenario_revision)))
        if((result.tenant_id,result.period_start,result.period_end,result.setoffs_declared)!=
                (tenant,scenario.period_start,scenario.period_end,_declared(scenario,'setoffs'))or
                (result.trace_version,result.code_sha256,result.component_sha256)!=
                (value.trace_version,value.code_sha256,value.component_sha256)):
            raise CostResultHold('stored cost scope or program differs')
        expected=tuple((category,cost)for category,costs in
            [('variable',scenario.variable_costs),('fixed',scenario.fixed_costs)]for cost in costs or ())
        if tuple((line.category,line.cost)for line in result.lines)!=expected:
            raise CostResultHold('stored cost inputs differ')
        offsets={offset.cost_id:offset for offset in scenario.setoffs or ()}
        for line in result.lines:
            offset=offsets.get(line.cost.id)if line.category=='variable'else None
            status=('declared_bank_payment'if line.cost.payment is not None else
                'declared_setoff'if offset is not None else'undeclared_payment')
            if(line.setoff,line.payment_status)!=(offset,status):
                raise CostResultHold('stored cost payment declaration differs')
            if status=='undeclared_payment'and any(v is not None for v in
                    (line.bank_paid_in_period,line.bank_paid_after_period,line.remaining_payable_at_period_end)):
                raise CostResultHold('stored unknown cost payment differs')
        ledger=result.base_result.ledger
        for group,name,incurred in zip(result.groups,['variable_costs','fixed_costs'],[ledger.variable_cost,ledger.fixed_cost]):
            if group.declared!=_declared(scenario,name)or group.incurred!=incurred:
                raise CostResultHold('stored cost group declaration differs')
        original={month.month:month.net for month in ledger.monthly_cash or ()}
        complete=all(group.declared for group in result.groups)and all(line.bank_paid_in_period is not None for line in result.lines)
        if any(month.ledger_net!=original.get(month.month)or
                month.bank_outflow!=(month.known_bank_outflow if complete else None)for month in result.months):
            raise CostResultHold('stored cost month binding differs')
        expected_reconciliation='unavailable'if ledger.operating_payable_end is None else'matched'
        if result.ledger_payable_reconciliation!=expected_reconciliation:
            raise CostResultHold('stored cost reconciliation status differs')
