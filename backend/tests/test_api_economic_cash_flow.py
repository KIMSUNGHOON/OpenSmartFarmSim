"""Projection contracts only; self-authored monthly values are not farm evidence."""
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.api_economic_cash_flow import project_economic_cash_flow, CashCursorRejected
from app.economics import MonthlyCash
from test_market_result_codec import result


def sample():
    value=result();context=value.market_context.model_copy(update={'hold_report_id':'11111111-1111-4111-8111-111111111111'})
    value=replace(value,market_context=context,economic_result=replace(value.economic_result,market_context=context,assessment_market_context=context))
    rows=tuple(MonthlyCash(f'2026-{month:02}',Decimal('-9007199254740993.0000000001'),Decimal('0'),
        Decimal('-9007199254740993.0000000001'),Decimal('-9007199254740993.0000000001'),
        datetime(2026,month,1,tzinfo=timezone.utc),Decimal('9007199254740993.0000000001')) for month in range(1,4))
    return replace(value,economic_result=replace(value.economic_result,monthly_cash=rows))


def test_exact_money_and_immutable_page_identity():
    value=sample();page=project_economic_cash_flow(value,limit=2)
    assert page.schema_version=='economic-cash-page-v1' and page.calendar_timezone=='Asia/Seoul'
    assert page.economic_result_id==value.economic_result.result_id
    assert page.monthly_cash[0].opening_balance_krw=='-9007199254740993.0000000001'
    assert page.monthly_cash[0].net_cash_krw=='0'
    assert page.total_months==3 and page.next_month_cursor=='2026-02'
    second=project_economic_cash_flow(value,after_month=page.next_month_cursor,limit=2)
    assert [row.month for row in second.monthly_cash]==['2026-03'] and second.next_month_cursor is None
    assert project_economic_cash_flow(value,after_month='2026-03').monthly_cash==[]
    with pytest.raises(CashCursorRejected):project_economic_cash_flow(value,after_month='2026-04')


def test_missing_series_remains_null_and_has_no_cursor():
    value=sample();held=replace(value,economic_result=replace(value.economic_result,monthly_cash=None))
    page=project_economic_cash_flow(held)
    assert page.series_status=='unavailable' and page.monthly_cash is None and page.total_months is None
    assert page.next_month_cursor is None and page.assessment_status=='hold'
    with pytest.raises(CashCursorRejected):project_economic_cash_flow(held,after_month='2026-01')


@pytest.mark.parametrize('fault',['duplicate','nonfinite','naive_time','wrong_result','empty'])
def test_bad_projection_is_rejected(fault):
    value=sample();rows=value.economic_result.monthly_cash
    if fault=='duplicate':rows=(rows[0],rows[0])
    if fault=='nonfinite':rows=(replace(rows[0],net=Decimal('NaN')),)
    if fault=='naive_time':rows=(replace(rows[0],minimum_at=datetime(2026,1,1)),)
    if fault=='empty':rows=()
    if fault=='wrong_result':value=replace(value,economic_result_ids=())
    value=replace(value,economic_result=replace(value.economic_result,monthly_cash=rows))
    with pytest.raises(ValueError):project_economic_cash_flow(value)


@pytest.mark.parametrize('limit',[0,25,True])
def test_invalid_page_bound_is_rejected(limit):
    with pytest.raises(CashCursorRejected):project_economic_cash_flow(sample(),limit=limit)
