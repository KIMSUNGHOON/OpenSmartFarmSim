"""Bounded monthly projection of an already verified conditional ledger."""
from datetime import date, datetime
import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .api_economics import _decimal, project_economic_result
from .economics import MonthlyCash
from .economic_contracts import utc

MONTH_PATTERN=r'^[0-9]{4}-(0[1-9]|1[0-2])$'


class CashCursorRejected(ValueError):
    pass


class MonthlyCashRead(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True)
    month:str=Field(pattern=MONTH_PATTERN)
    opening_balance_krw:str
    net_cash_krw:str
    closing_balance_krw:str
    minimum_balance_krw:str
    minimum_at_utc:datetime
    cash_shortage_krw:str
    _utc=field_validator('minimum_at_utc')(utc)


class EconomicCashPage(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True)
    schema_version:Literal['economic-cash-page-v1']
    economic_result_id:str
    market_scenario_result_id:str
    scenario_id:str
    scenario_revision:str
    decision_at_utc:datetime
    formula_version:str
    market_context_kind:Literal['unavailable']
    market_hold_report_id:UUID
    calculation_status:Literal['conditional_user_assumption','hold']
    assessment_status:Literal['hold']
    input_origin:Literal['user']
    evidence_level:Literal['assumed']
    calendar_timezone:Literal['Asia/Seoul']
    series_status:Literal['available','unavailable']
    total_months:int|None=Field(ge=1,le=119988)
    limit:int=Field(ge=1,le=24)
    after_month:str|None=Field(pattern=MONTH_PATTERN)
    next_month_cursor:str|None=Field(pattern=MONTH_PATTERN)
    monthly_cash:list[MonthlyCashRead]|None=Field(max_length=24)
    hold_reason_codes:list[str]=Field(max_length=100)


def project_economic_cash_flow(result,*,after_month=None,limit=12):
    if type(limit) is not int or not 1<=limit<=24:
        raise CashCursorRejected('invalid cash page size')
    summary=project_economic_result(result)
    rows=result.economic_result.monthly_cash
    keys=[]
    if rows is not None:
        if type(rows) is not tuple or not rows:
            raise ValueError('invalid cash series')
        for row in rows:
            if type(row) is not MonthlyCash or type(row.month) is not str or not re.fullmatch(MONTH_PATTERN,row.month):
                raise ValueError('invalid cash month')
            date.fromisoformat(row.month+'-01')
            keys.append(row.month)
        if keys!=sorted(set(keys)):
            raise ValueError('cash months are not ordered unique records')
    if after_month is not None and (type(after_month) is not str or after_month not in keys):
        raise CashCursorRejected('cash cursor does not belong to this result')
    start=keys.index(after_month)+1 if after_month is not None else 0
    selected=rows[start:start+limit] if rows is not None else None
    fields=('economic_result_id','market_scenario_result_id','scenario_id','scenario_revision','decision_at_utc',
        'formula_version','market_context_kind','market_hold_report_id','calculation_status','assessment_status',
        'input_origin','evidence_level','hold_reason_codes')
    values=summary.model_dump(include=set(fields))
    return EconomicCashPage.model_validate({**values,'schema_version':'economic-cash-page-v1',
        'calendar_timezone':'Asia/Seoul','series_status':'unavailable' if rows is None else 'available',
        'total_months':len(rows) if rows is not None else None,'limit':limit,'after_month':after_month,
        'next_month_cursor':selected[-1].month if selected and start+len(selected)<len(rows) else None,
        'monthly_cash':None if selected is None else [{'month':row.month,
            'opening_balance_krw':_decimal(row.opening),'net_cash_krw':_decimal(row.net),
            'closing_balance_krw':_decimal(row.closing),'minimum_balance_krw':_decimal(row.minimum_balance),
            'minimum_at_utc':row.minimum_at,'cash_shortage_krw':_decimal(row.shortage)} for row in selected]})
