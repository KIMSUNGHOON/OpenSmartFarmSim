"""Allowlisted public projection of a replayed conditional economic result."""

from decimal import Decimal
import re

from .api_contracts import EconomicResultRead


RESULT_ID_PATTERN = r"^[0-9a-f]{64}$"
_SAFE_REASON = re.compile(r"[A-Z][A-Z0-9_]{0,79}\Z")


def _decimal(value):
    if value is None:
        return None
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("economic total is not a finite decimal")
    return "0" if value.is_zero() else format(value, "f")


def _reason_codes(reasons):
    if type(reasons) is not tuple or len(reasons) > 100:
        raise ValueError("economic reason inventory invalid")
    safe = []
    for reason in reasons:
        if type(reason) is not str:
            raise ValueError("economic reason invalid")
        code = ("SALE_NET_REMITTANCE_HOLD" if reason.startswith("SALE_NET_REMITTANCE_")
                else reason if _SAFE_REASON.fullmatch(reason) else "DETAIL_WITHHELD")
        if code not in safe:
            safe.append(code)
    return safe


def project_economic_result(result):
    ledger = result.economic_result
    if (result.economic_result_ids != (ledger.result_id,) or
            result.market_context != ledger.market_context or
            result.market_context != ledger.assessment_market_context or
            result.assessment_status != "hold" or
            ledger.assessment_status != "hold" or
            ledger.forecast_run_id is not None or
            result.market_context.kind != "unavailable" or
            (result.calculation_status == "conditional_user_assumption" and
             (ledger.management_oi is None or ledger.operating_cash is None)) or
            not ledger.input_provenance or
            any(item.origin != "user" or item.evidence_level != "assumed"
                for item in ledger.input_provenance)):
        raise ValueError("conditional economic result is not displayable")
    return EconomicResultRead.model_validate({
        "economic_result_id": ledger.result_id,
        "market_scenario_result_id": result.result_id,
        "scenario_id": ledger.scenario_id,
        "scenario_revision": ledger.scenario_revision,
        "decision_at_utc": ledger.decision_at,
        "formula_version": ledger.formula_version,
        "market_context_kind": "unavailable",
        "market_hold_report_id": result.market_context.hold_report_id,
        "calculation_status": result.calculation_status,
        "assessment_status": result.assessment_status,
        "sales_totals_status": ledger.sales_totals_status,
        "input_origin": "user",
        "evidence_level": "assumed",
        "quantities": {
            "harvest_kg": _decimal(ledger.harvest_kg),
            "packout_kg": _decimal(ledger.packout_kg),
            "recognized_kg": _decimal(ledger.recognized_kg),
            "net_sold_kg": _decimal(ledger.net_sold_kg),
        },
        "amounts": {
            "gross_sales_krw": _decimal(ledger.gross_sales),
            "revenue_krw": _decimal(ledger.revenue),
            "variable_cost_krw": _decimal(ledger.variable_cost),
            "fixed_cost_krw": _decimal(ledger.fixed_cost),
            "depreciation_krw": _decimal(ledger.depreciation),
            "management_operating_income_krw": _decimal(ledger.management_oi),
            "operating_cash_krw": _decimal(ledger.operating_cash),
            "business_cash_krw": _decimal(ledger.business_cash),
            "equity_cash_krw": _decimal(ledger.equity_cash),
            "minimum_cash_balance_krw": _decimal(ledger.minimum_cash_balance),
            "cash_shortage_krw": _decimal(ledger.cash_shortage),
        },
        "hold_reason_codes": _reason_codes(result.hold_reasons),
    })
