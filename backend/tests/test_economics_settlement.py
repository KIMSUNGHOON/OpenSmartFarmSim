"""Self-authored settlement assumptions exercise software contracts, not farm evidence."""

from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_DOWN, ROUND_UP, localcontext

import pytest
from pydantic import ValidationError

from test_economics import (
    DECISION, T, TrustedTestRepository, base, n, run, settlement_record,
)
from app.economic_contracts import EconomicScenario
from app.economics import EconomicLedger, canonical_scenario_sha256


def example():
    data = base(
        period_end=date(2026, 10, 31),
        packouts=({"id": "pack-1", "harvest_id": "harvest-1", "batch_id": "batch-1",
                   "grade": "grade-1", "channel": "direct", "at": T(15, 1),
                   "quantity": n(10, "p")},),
        culls=(), cull_disposals=(),
        sales=({"id": "sale-1", "batch_id": "batch-1", "grade": "grade-1",
                "channel": "direct", "dispatch_at": T(15, 2), "delivery_at": T(15, 3),
                "inspection_at": T(15, 4), "recognized_at": T(15, 5),
                "quantity": n(10, "s"), "price": n(100, "price", "KRW/kg"),
                "price_basis": "gross_before_deductions"},),
        collections=({"id": "collection-1", "sale_id": "sale-1", "at": T(22),
                      "amount": n(840, "collection", "KRW")},),
        discounts=({"id": "discount-1", "sale_id": "sale-1", "at": T(18),
                    "amount": n(100, "discount", "KRW")},),
        variable_costs=(
            {"id": "production", "purpose": "production", "batch_id": "batch-1",
             "sale_id": None, "incurred_at": T(15), "quantity": n(10, "production-q"),
             "unit_cost": n(4, "production-rate", "KRW/kg"), "paid_at": T(21),
             "payment": n(40, "production-paid", "KRW")},
            {"id": "separate-sale-cost", "purpose": "sale", "batch_id": None,
             "sale_id": "sale-1", "incurred_at": T(15, 2), "quantity": n(1, "separate-q"),
             "unit_cost": n(30, "separate-rate", "KRW/kg"), "paid_at": T(21),
             "payment": n(30, "separate-paid", "KRW")},
            {"id": "fee", "purpose": "sale", "batch_id": None,
             "sale_id": "sale-1", "incurred_at": T(15, 5), "quantity": n(1, "fee-q"),
             "unit_cost": n(60, "fee-amount", "KRW/kg"), "paid_at": None,
             "payment": None},
        ),
        setoffs=({"id": "setoff-1", "sale_id": "sale-1", "cost_id": "fee",
                  "at": T(20), "amount": n(60, "setoff-amount", "KRW"),
                  "settlement_ref": "self-authored-settlement-1",
                  "evidence_revision": "r1", "evidence_sha256": "0" * 64},),
    )
    entry = data["setoffs"][0]
    entry["evidence_sha256"] = settlement_record(data, entry)["raw_sha256"]
    return data


def net(result):
    return result.sale_net_remittances[0]


def test_full_setoff_reconciles_without_bank_event_and_replays():
    data = example()
    first = run(data)
    second = run(data)
    assert first == second
    assert first.formula_version == "economic-ledger-v9-sales-settlement"
    assert first.scenario_sha256 == canonical_scenario_sha256(EconomicScenario.model_validate(data))
    assert (first.gross_sales, first.revenue, first.variable_cost, first.management_oi) == (
        Decimal(1000), Decimal(900), Decimal(130), Decimal(770))
    assert (first.operating_cash, first.operating_cash_bridge, first.receivable_end,
            first.operating_payable_end) == (Decimal(770), Decimal(770), Decimal(0), Decimal(0))
    assert (net(first).amount, net(first).per_kg, net(first).status) == (
        Decimal(840), Decimal(84), "conditional_user_assumption")
    assert len(first.monthly_cash) == 1 and first.monthly_cash[0].net == Decimal(770)
    assert first.assessment_status == "hold" and first.forecast_run_id is None
    assert first.market_context.hold_report_id == "hold-1"


def test_partial_collection_holds_per_sale_price_and_keeps_receivable():
    data = example()
    data["collections"][0]["amount"]["value"] = "500"
    result = run(data)
    assert result.receivable_end == Decimal(340)
    assert result.operating_cash == result.operating_cash_bridge == Decimal(430)
    assert net(result).per_kg is None and net(result).hold_reason == "COLLECTION_INCOMPLETE"


def test_collection_after_period_stays_out_of_current_cash_and_price():
    data = example()
    data["collections"][0]["at"] = datetime(2026, 11, 1, tzinfo=timezone.utc)
    result = run(data)
    assert result.operating_cash == result.operating_cash_bridge == Decimal(-70)
    assert result.receivable_end == Decimal(840)
    assert result.operating_payable_end == Decimal(0)
    assert result.future_cash_schedule[0].event_id == "collection-1"
    assert net(result).per_kg is None and net(result).hold_reason == "COLLECTION_AFTER_PERIOD"


def test_future_setoff_stays_in_schedule_and_current_balances():
    data = example()
    data["setoffs"][0]["at"] = datetime(2026, 11, 1, tzinfo=timezone.utc)
    data["setoffs"][0]["evidence_sha256"] = settlement_record(data, data["setoffs"][0])["raw_sha256"]
    result = run(data)
    assert (result.receivable_end, result.operating_payable_end) == (Decimal(60), Decimal(60))
    assert result.operating_cash == result.operating_cash_bridge == Decimal(770)
    assert [(e.event_id, e.sale_id, e.amount) for e in result.future_setoff_schedule] == [
        ("setoff-1", "sale-1", Decimal(60))]
    assert result.future_cash_schedule == ()
    assert net(result).per_kg is None and net(result).hold_reason == "SETTLEMENT_AFTER_PERIOD"


def test_return_refund_is_separate_and_per_sale_price_held():
    data = example()
    data["returns"] = ({"id": "return-1", "sale_id": "sale-1", "at": T(23),
                        "quantity": n(1, "return-q"), "disposition": "disposed",
                        "refund": n(100, "refund", "KRW"), "refund_paid_at": T(24)},)
    data["zero_declarations"] = tuple(z for z in data["zero_declarations"] if z["group"] != "returns")
    result = run(data)
    assert result.revenue == Decimal(800)
    assert result.management_oi == result.operating_cash == result.operating_cash_bridge == Decimal(670)
    assert net(result).per_kg is None and net(result).hold_reason == "RETURN_PRESENT"


def test_explicit_zero_and_unknown_setoff_are_distinct():
    data = base()
    zero = run(data)
    assert net(zero).per_kg == Decimal(100)
    data["setoffs"] = None
    data["zero_declarations"] = tuple(z for z in data["zero_declarations"] if z["group"] != "setoffs")
    unknown = run(data)
    assert net(unknown).per_kg is None and net(unknown).hold_reason == "SETTLEMENT_UNDECLARED"
    assert "SETOFFS_UNDECLARED" in unknown.hold_reasons
    assert unknown.receivable_end is None and unknown.operating_payable_end is None


def test_unpaid_cost_without_full_setoff_keeps_unknown_payment_hold():
    data = example()
    data["setoffs"] = ()
    data["zero_declarations"] += ({"group": "setoffs", "zero": n(0, "zero-setoffs", "KRW")},)
    result = run(data)
    assert result.variable_cost == Decimal(130) and result.management_oi == Decimal(770)
    assert result.operating_cash is None and "OPERATING_PAYMENT_UNDECLARED" in result.hold_reasons


def test_multiple_sales_cannot_cross_link_fee():
    data = example()
    data["sales"][0]["quantity"]["value"] = "5"
    second = {**data["sales"][0], "id": "sale-2",
              "quantity": n(5, "s-2"), "price": n(100, "price-2", "KRW/kg")}
    data["sales"] += (second,)
    data["collections"][0]["amount"]["value"] = "400"
    data["collections"] += ({"id": "collection-2", "sale_id": "sale-2", "at": T(22),
                             "amount": n(440, "collection-2", "KRW")},)
    data["setoffs"][0]["sale_id"] = "sale-2"
    data["setoffs"][0]["evidence_sha256"] = settlement_record(data, data["setoffs"][0])["raw_sha256"]
    with pytest.raises(ValueError, match="same sale"):
        run(data)


def test_unreconciled_inventory_holds_conditional_sale_price():
    data = example()
    data["opening_inventory"] = None
    data["zero_declarations"] = tuple(z for z in data["zero_declarations"]
                                       if z["group"] != "opening_inventory")
    result = run(data)
    assert result.revenue is None and result.sales_totals_status == "unverified_input_arithmetic"
    assert net(result).per_kg is None and net(result).hold_reason == "INVENTORY_UNRECONCILED"


def test_nonterminating_conditional_unit_price_is_decimal():
    data = base()
    data["sales"][0]["quantity"]["value"] = "3"
    data["collections"][0]["amount"]["value"] = "299"
    data["discounts"] = ({"id": "discount-1", "sale_id": "sale-1", "at": T(19),
                          "amount": n(1, "discount", "KRW")},)
    data["zero_declarations"] = tuple(z for z in data["zero_declarations"] if z["group"] != "discounts")
    result = run(data)
    assert net(result).status == "conditional_user_assumption"
    assert Decimal(99) < net(result).per_kg < Decimal(100)


def test_nonterminating_remittance_replays_identically_across_decimal_rounding_modes():
    data = base()
    data["sales"][0]["quantity"]["value"] = "3"
    data["collections"][0]["amount"]["value"] = "299"
    data["discounts"] = ({"id": "discount-1", "sale_id": "sale-1", "at": T(19),
                          "amount": n(1, "discount", "KRW")},)
    data["zero_declarations"] = tuple(z for z in data["zero_declarations"] if z["group"] != "discounts")

    with localcontext() as context:
        context.rounding = ROUND_DOWN
        rounded_down = run(data)
    with localcontext() as context:
        context.rounding = ROUND_UP
        rounded_up = run(data)

    assert rounded_down.result_id == rounded_up.result_id
    assert rounded_down == rounded_up


@pytest.mark.parametrize("change", ["wrong_sale", "wrong_purpose", "wrong_amount", "cash_payment", "duplicate_cost"])
def test_invalid_fee_link_or_double_payment_is_rejected(change):
    data = example()
    if change == "wrong_sale":
        data["setoffs"][0]["sale_id"] = "other-sale"
    elif change == "wrong_purpose":
        data["variable_costs"][2]["purpose"] = "period"
        data["variable_costs"][2]["sale_id"] = None
    elif change == "wrong_amount":
        data["setoffs"][0]["amount"]["value"] = "61"
    elif change == "cash_payment":
        data["variable_costs"][2]["paid_at"] = T(21)
        data["variable_costs"][2]["payment"] = n(60, "fee-paid", "KRW")
    else:
        data["setoffs"] += ({**data["setoffs"][0], "id": "setoff-2",
                             "amount": n(60, "setoff-amount-2", "KRW")},)
    if change in {"wrong_sale", "wrong_amount"}:
        data["setoffs"][0]["evidence_sha256"] = settlement_record(data, data["setoffs"][0])["raw_sha256"]
    with pytest.raises(ValueError):
        run(data)


@pytest.mark.parametrize("mutation", ["missing", "foreign", "late", "scope", "rights", "hash", "revision", "sale", "amount", "immutable"])
def test_server_owned_evidence_rejects_tamper(mutation):
    scenario = EconomicScenario.model_validate(example())
    repo = TrustedTestRepository(scenario)
    key = ("self-authored-settlement-1", "r1")
    if mutation == "missing":
        repo.settlements.pop(key)
    elif mutation == "foreign":
        repo.settlements[key]["tenant_id"] = "tenant-2"
    elif mutation == "late":
        repo.settlements[key]["available_at"] = T(1)
    elif mutation == "scope":
        repo.settlements[key]["scope_end"] = date(2026, 10, 1)
    elif mutation == "rights":
        repo.settlements[key]["rights"] = "display_only"
    elif mutation == "hash":
        repo.settlements[key]["raw_sha256"] = "f" * 64
    elif mutation == "revision":
        repo.settlements[key]["revision"] = "r2"
    elif mutation == "sale":
        repo.settlements[key]["sale_id"] = "other-sale"
    elif mutation == "amount":
        repo.settlements[key]["amount"]["value"] = "59"
    else:
        repo.settlements[key]["immutable"] = False
    with pytest.raises(ValueError):
        EconomicLedger(repo).calculate(scenario)


def test_raw_amount_revision_and_scenario_pin_tamper_are_rejected():
    scenario = EconomicScenario.model_validate(example())
    repo = TrustedTestRepository(scenario)
    repo.records[("setoff-amount", "r1")]["value"] = "59"
    with pytest.raises(ValueError, match="owned revision"):
        EconomicLedger(repo).calculate(scenario)
    repo = TrustedTestRepository(scenario)
    repo.scenario_pin["payload_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="scenario pin"):
        EconomicLedger(repo).calculate(scenario)


def test_settlement_revision_and_hash_change_canonical_result_identity():
    first = run(example())
    data = example()
    data["setoffs"][0]["evidence_revision"] = "r2"
    data["setoffs"][0]["evidence_sha256"] = settlement_record(data, data["setoffs"][0])["raw_sha256"]
    second = run(data)
    assert first.scenario_sha256 != second.scenario_sha256
    assert first.result_id != second.result_id
    assert second.management_oi == first.management_oi


def test_request_hash_or_reference_cannot_self_certify_settlement():
    data = example()
    data["setoffs"][0]["evidence_sha256"] = "f" * 64
    scenario = EconomicScenario.model_validate(data)
    with pytest.raises(ValueError, match="settlement evidence"):
        EconomicLedger(TrustedTestRepository(scenario)).calculate(scenario)

    original = EconomicScenario.model_validate(example())
    repo = TrustedTestRepository(original)
    data = example()
    data["setoffs"][0]["settlement_ref"] = "missing-evidence"
    scenario = EconomicScenario.model_validate(data)
    digest = canonical_scenario_sha256(scenario)
    repo.scenario_pin["payload_sha256"] = digest
    repo.scenario_pin["immutable_job_input_sha256"] = digest
    with pytest.raises(ValueError, match="settlement evidence lookup"):
        EconomicLedger(repo).calculate(scenario)


def test_discount_collection_setoff_over_gross_and_late_discount_rejected():
    data = example()
    data["collections"][0]["amount"]["value"] = "850"
    with pytest.raises(ValueError, match="exceed"):
        run(data)
    data = example()
    data["discounts"][0]["at"] = T(23)
    with pytest.raises(ValueError, match="DISCOUNT_AFTER_COLLECTION"):
        run(data)


def test_aggregate_remittance_without_sale_allocation_is_rejected():
    data = example()
    data["collections"][0]["sale_id"] = "aggregate"
    with pytest.raises(ValueError, match="sale"):
        run(data)


def test_old_scenario_version_rejected_and_setoff_contract_is_frozen():
    data = example()
    data["schema_version"] = "2"
    with pytest.raises(ValidationError, match="schema_version"):
        EconomicScenario.model_validate(data)
    scenario = EconomicScenario.model_validate(example())
    with pytest.raises(ValidationError):
        scenario.setoffs[0].amount.value = "9"
