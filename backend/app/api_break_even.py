"""Public conditional grid projection after immutable full-path replay."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from .api_economics import _decimal, _reason_codes
from .break_even import BreakEvenRequest, BreakEvenResult


PLAN_ID_PATTERN = r'^[^\s\x00-\x1f](?:[^\x00-\x1f]*[^\s\x00-\x1f])?$'


class BreakEvenTrialRead(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    value: str
    target_value_krw: str
    minimum_cash_balance_krw: str | None
    cash_shortage_krw: str | None


class BreakEvenRead(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    plan_id: str = Field(pattern=PLAN_ID_PATTERN, min_length=1, max_length=200)
    status: Literal['zero_on_grid', 'no_zero_on_grid', 'bracket_only', 'nonmonotone_on_grid', 'hold']
    scope: Literal['conditional_user_grid_only']
    assessment_status: Literal['hold']
    input_origin: Literal['user']
    evidence_level: Literal['assumed']
    market_context_kind: Literal['unavailable']
    market_hold_report_id: str
    decision_at_utc: datetime
    period_start: date
    period_end: date
    target: Literal['oi', 'operating_cash', 'cumulative_equity_cash']
    variable_unit: Literal['kg', 'KRW/kg']
    minimum: str
    maximum: str
    step: str
    zero_values: list[str] = Field(max_length=256)
    brackets: list[Annotated[list[str], Field(min_length=2, max_length=2)]] = Field(max_length=255)
    trials: list[BreakEvenTrialRead] = Field(max_length=256)
    hold_reason_codes: list[str] = Field(max_length=100)


def project_break_even_result(request, result):
    if type(request) is not BreakEvenRequest or type(result) is not BreakEvenResult:
        raise ValueError('break-even display requires verified request/result')
    request = BreakEvenRequest.model_validate_json(request.model_dump_json())
    if (result.scope != 'conditional_user_grid_only' or result.assessment_status != 'hold' or
            (result.target, result.variable) != (request.target, request.variable) or
            (result.minimum, result.maximum, result.step) !=
            (Decimal(request.minimum), Decimal(request.maximum), Decimal(request.step)) or
            (result.status == 'hold' and (result.trials or result.zero_values or result.brackets))):
        raise ValueError('break-even conditional scope differs')
    return BreakEvenRead.model_validate({
        'plan_id': request.plan_id, 'status': result.status, 'scope': result.scope,
        'assessment_status': result.assessment_status, 'input_origin': 'user', 'evidence_level': 'assumed',
        'market_context_kind': 'unavailable', 'market_hold_report_id': request.market_context.hold_report_id,
        'decision_at_utc': request.decision_at, 'period_start': request.period_start, 'period_end': request.period_end,
        'target': result.target, 'variable_unit': result.variable,
        'minimum': _decimal(result.minimum), 'maximum': _decimal(result.maximum), 'step': _decimal(result.step),
        'zero_values': [_decimal(value) for value in result.zero_values],
        'brackets': [[_decimal(value) for value in pair] for pair in result.brackets],
        'trials': [{'value': _decimal(trial.value), 'target_value_krw': _decimal(trial.target_value),
            'minimum_cash_balance_krw': _decimal(trial.minimum_cash_balance),
            'cash_shortage_krw': _decimal(trial.cash_shortage)} for trial in result.trials],
        'hold_reason_codes': _reason_codes(result.hold_reasons),
    })
