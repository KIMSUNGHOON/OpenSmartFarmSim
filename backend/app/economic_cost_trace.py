"""Versioned per-Cost evidence over the unchanged conditional v10 ledger."""
from dataclasses import asdict,dataclass,replace
from datetime import date
from decimal import Decimal,Context,Inexact,InvalidOperation,DivisionByZero,Overflow,localcontext
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from . import economic_production_batches as batch
from . import economics as money
from .economic_contracts import Cost,SettlementSetoff,untrusted_data

TRACE_VERSION='economic-cost-line-trace-v1'
MAX_BYTES=2*1024**2
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENTS=(batch,*batch.COMPONENTS)
COMPONENT_SHA256={m.__name__:sha256(Path(m.__file__).read_bytes()).hexdigest()for m in COMPONENTS}
_CONTEXT=Context(prec=128,rounding=money.ROUND_HALF_UP,Emin=-999999,Emax=999999,
    capitals=1,clamp=0,flags=[],traps=[InvalidOperation,DivisionByZero,Overflow,Inexact])


@dataclass(frozen=True)
class CostLine:
    category:Literal['variable','fixed']
    cost:Cost
    incurred:Decimal
    bank_paid_in_period:Decimal|None
    bank_paid_after_period:Decimal|None
    setoff:SettlementSetoff|None
    setoff_in_period:Decimal|None
    remaining_payable_at_period_end:Decimal|None
    payment_status:Literal['declared_bank_payment','declared_setoff','undeclared_payment']


@dataclass(frozen=True)
class CostGroup:
    category:Literal['variable','fixed']
    declared:bool
    incurred:Decimal|None
    bank_paid_in_period:Decimal|None
    setoff_in_period:Decimal|None
    remaining_payable_at_period_end:Decimal|None


@dataclass(frozen=True)
class CostMonth:
    month:str
    known_bank_outflow:Decimal
    bank_outflow:Decimal|None
    ledger_net:Decimal|None
    scope:Literal['cost_bank_outflow_component_only']='cost_bank_outflow_component_only'


@dataclass(frozen=True)
class CostTraceResult:
    trace_version:str
    trace_id:str
    tenant_id:str
    period_start:date
    period_end:date
    setoffs_declared:bool
    base_result:batch.ProductionBatchResult
    lines:tuple[CostLine,...]
    groups:tuple[CostGroup,...]
    months:tuple[CostMonth,...]
    ledger_payable_reconciliation:Literal['matched','unavailable']
    code_sha256:str
    component_sha256:dict[str,str]
    scope:Literal['conditional_user_assumptions_only']='conditional_user_assumptions_only'
    G0_G4:Literal['not_assessed']='not_assessed'
    R2:Literal['not_approved']='not_approved'
    currency:Literal['KRW']='KRW'


def _fence():
    batch._code_fence()
    if(sha256(Path(__file__).read_bytes()).hexdigest()!=CODE_SHA256 or
            any(sha256(Path(m.__file__).read_bytes()).hexdigest()!=COMPONENT_SHA256[m.__name__]for m in COMPONENTS)):
        raise ValueError('CODE_HOLD: unchanged cost trace and v10 components required')


def _payload(result):
    value=asdict(result)
    value['base_result']=json.loads(batch.result_bytes(result.base_result))
    return value


def _encoded(result,*,identity=False):
    with localcontext(_CONTEXT):
        value=_payload(result)
        if identity:value.pop('trace_id')
        return batch._raw(value)


def trace_bytes(result):
    if type(result)is not CostTraceResult:raise ValueError('cost trace result required')
    raw=_encoded(result)
    if not 1<=len(raw)<=MAX_BYTES:raise ValueError('CAPACITY_HOLD: bounded complete cost trace required')
    return raw


def _sum_known(values,declared=True):
    values=tuple(values)
    return money.total(values)if declared and all(v is not None for v in values)else None


def _declared(s,name):
    values=getattr(s,name)
    return values is not None and(bool(values)or any(v.group==name for v in s.zero_declarations))


def _line(ledger,s,category,cost,setoffs):
    amount=ledger._costs((cost,),s,set(),{sale.id:sale for sale in s.sales})
    setoff=setoffs.get(cost.id)if category=='variable'else None
    if cost.payment is not None:
        paid=money.money(cost.payment);inside=money.in_period(cost.paid_at,s)
        bank,after=(paid,money.ZERO)if inside else(money.ZERO,paid)
        offset=money.ZERO;status='declared_bank_payment'
    elif setoff is not None:
        bank=after=money.ZERO
        offset=money.money(setoff.amount)if money.in_period(setoff.at,s)else money.ZERO
        status='declared_setoff'
    else:
        bank=after=None;status='undeclared_payment'
        offset=None if category=='variable'and cost.purpose=='sale'and not _declared(s,'setoffs')else money.ZERO
    remaining=amount-bank-offset if bank is not None and offset is not None else None
    if remaining is not None and remaining<0:raise ValueError('TRACE_HOLD: negative cost payable')
    return CostLine(category,cost,amount,bank,after,setoff,offset,remaining,status)


def _groups(s,lines):
    out=[]
    for category,events in [('variable',s.variable_costs),('fixed',s.fixed_costs)]:
        selected=[line for line in lines if line.category==category];declared=_declared(s,category+'_costs')
        values=[_sum_known((getattr(v,name)for v in selected),declared)for name in
            ['incurred','bank_paid_in_period','setoff_in_period','remaining_payable_at_period_end']]
        out.append(CostGroup(category,declared,*values))
    return tuple(out)


def _months(s,result,lines,groups):
    complete=all(v.declared for v in groups)and all(v.bank_paid_in_period is not None for v in lines)
    original={v.month:v.net for v in result.ledger.monthly_cash or ()}
    out=[];year,number=s.period_start.year,s.period_start.month
    while(year,number)<=(s.period_end.year,s.period_end.month):
        key=f'{year:04d}-{number:02d}'
        known=money.total(v.bank_paid_in_period for v in lines if v.cost.paid_at is not None and
            money.in_period(v.cost.paid_at,s)and money.month(v.cost.paid_at)==key)
        out.append(CostMonth(key,known,known if complete else None,original.get(key)))
        year,number=(year+1,1)if number==12 else(year,number+1)
    return tuple(out)


def _reconcile(s,result,lines,groups,months):
    ledger=result.ledger
    if(groups[0].incurred,groups[1].incurred)!=(ledger.variable_cost,ledger.fixed_cost):
        raise ValueError('TRACE_HOLD: cost group differs from original ledger')
    for original in result.batch_costs:
        selected=[v for v in lines if v.cost.purpose=='production'and v.cost.batch_id==original.batch_id]
        amounts=[_sum_known((v.incurred for v in selected if v.category==g.category),g.declared)for g in groups]
        declared=all(g.declared for g in groups)
        paid=_sum_known((v.bank_paid_in_period for v in selected),declared)
        remaining=_sum_known((v.remaining_payable_at_period_end for v in selected),declared)
        if tuple([*amounts,paid,remaining])!=(original.variable_incurred,original.fixed_incurred,
                original.cash_paid_in_period,original.remaining_payable_at_period_end):
            raise ValueError('TRACE_HOLD: cost lines differ from original batch')
    if money.total(v.known_bank_outflow for v in months)!=money.total(
            v.bank_paid_in_period for v in lines if v.bank_paid_in_period is not None):
        raise ValueError('TRACE_HOLD: cost month known component differs')
    if _sum_known(v.bank_outflow for v in months)!=_sum_known(v.bank_paid_in_period for v in groups):
        raise ValueError('TRACE_HOLD: cost month total differs')
    actual={(v.category,v.event_id):(v.at,v.amount)for v in ledger.future_cash_schedule
        if v.category in {'variable_cost_payment','fixed_cost_payment'}}
    expected={(v.category+'_cost_payment',v.cost.id):(v.cost.paid_at,-money.money(v.cost.payment))for v in lines
        if v.cost.paid_at is not None and money.day(v.cost.paid_at)>s.period_end}
    if actual!=expected:raise ValueError('TRACE_HOLD: future cost payment differs')
    actual={v.event_id:(v.sale_id,v.cost_id,v.at,v.amount)for v in ledger.future_setoff_schedule}
    expected={v.setoff.id:(v.setoff.sale_id,v.cost.id,v.setoff.at,money.money(v.setoff.amount))for v in lines
        if v.setoff is not None and money.day(v.setoff.at)>s.period_end}
    if actual!=expected:raise ValueError('TRACE_HOLD: future cost setoff differs')
    if ledger.operating_payable_end is None:return 'unavailable'
    if _sum_known(v.remaining_payable_at_period_end for v in groups)!=ledger.operating_payable_end:
        raise ValueError('TRACE_HOLD: cost payable differs from original ledger')
    return 'matched'


class CostLineLedger:
    def __init__(self,repository):self._repository=repository

    def _current(self,ledger,repository,s):
        if self._repository is not repository or ledger._repository is not repository:
            raise ValueError('TRACE_HOLD: repository binding changed')
        try:allowed=repository.tenant_is_authenticated(s.tenant_id)is True
        except Exception:allowed=False
        if not allowed:raise ValueError('TRACE_HOLD: current tenant access required')
        if self._repository is not repository or ledger._repository is not repository:
            raise ValueError('TRACE_HOLD: repository binding changed')

    def calculate(self,scenario):
        _fence()
        try:
            s=batch.BatchEconomicScenario.model_validate(untrusted_data(scenario))
            if len(batch._raw(s))>MAX_BYTES:raise ValueError('CAPACITY_HOLD: bounded cost scenario required')
            repository=self._repository;ledger=batch.ProductionBatchLedger(repository)
            self._current(ledger,repository,s);before=ledger._context(s)
            try:
                with localcontext(_CONTEXT):
                    original=ledger.calculate(s)
                    offsets={v.cost_id:v for v in s.setoffs or ()}
                    lines=tuple(_line(ledger,s,category,cost,offsets)for category,events in
                        [('variable',s.variable_costs),('fixed',s.fixed_costs)]for cost in events or ())
                    groups=_groups(s,lines);months=_months(s,original,lines,groups)
                    reconciled=_reconcile(s,original,lines,groups,months)
            except Inexact:raise ValueError('cost trace exceeds exact 128-digit domain')from None
            output=CostTraceResult(TRACE_VERSION,'',s.tenant_id,s.period_start,s.period_end,_declared(s,'setoffs'),
                original,lines,groups,months,reconciled,CODE_SHA256,dict(COMPONENT_SHA256))
            output=replace(output,trace_id=sha256(_encoded(output,identity=True)).hexdigest())
            trace_bytes(output)
            if ledger._context(s)!=before:raise ValueError('TRACE_HOLD: current source changed')
            self._current(ledger,repository,s)
            return output
        finally:_fence()
