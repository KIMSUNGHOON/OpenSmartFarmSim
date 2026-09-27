"""Cash dates and adjustment paths use declared, test-only synthetic assumptions."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from test_economics import DECISION, T, base, n, run


def test_complete_two_month_cash_and_three_distinct_objectives():
    data = base(
        fixed_costs=({"id": "rent", "purpose": "period", "batch_id": None,
                      "sale_id": None, "incurred_at": T(15),
                      "quantity": n(1, "rent-q", "month"), "unit_cost": n(40, "rent-rate", "KRW/month"),
                      "paid_at": T(25), "payment": n(40, "rent-paid", "KRW")},),
        assets=({"id": "asset-1", "opening_basis": n(0, "asset-opening", "KRW"),
                 "acquisition_cost": n(200, "asset-cost", "KRW"),
                 "acquired_at": T(28), "installed_at": T(31),
                 "residual_value": n(0, "asset-residual", "KRW"),
                 "useful_life_days": n(620, "asset-life", "day"),
                 "opening_accumulated_depreciation": n(0, "asset-accum", "KRW")},),
        depreciation=({"id": "asset-dep", "at": datetime(2026, 11, 30, 12, tzinfo=timezone.utc), "asset_id": "asset-1",
                       "amount": n(10, "depreciation", "KRW")},),
        grants=({"id": "grant", "at": T(26), "amount": n(30, "grant", "KRW")},),
        asset_disposals=(), taxes=({"id": "tax", "at": T(27), "amount": n(5, "tax", "KRW")},),
        capex=({"id": "asset-purchase", "at": T(28), "asset_id": "asset-1",
                "amount": n(200, "capex", "KRW")},),
        debt_accounts=({"id": "loan-1", "opening_principal": n(0, "loan-opening", "KRW")},),
        loan_draws=({"id": "draw", "at": T(29), "loan_id": "loan-1",
                     "amount": n(100, "draw", "KRW")},),
        principal_payments=({"id": "principal", "at": T(30), "loan_id": "loan-1",
                             "amount": n(20, "principal", "KRW")},),
        interest_payments=({"id": "interest", "at": T(30), "loan_id": "loan-1",
                            "amount": n(3, "interest", "KRW")},),
    )
    result = run(data)
    assert result.revenue == Decimal("500")
    assert result.variable_cost == Decimal("25")
    assert result.fixed_cost == Decimal("40")
    assert result.depreciation == Decimal("10")
    assert result.management_oi == Decimal("425")
    assert result.operating_cash == Decimal("435")
    assert result.business_cash == Decimal("260")
    assert result.equity_cash == Decimal("337")
    assert result.target_values == {"oi": Decimal("425"), "operating_cash": Decimal("435"),
                                    "cumulative_equity_cash": Decimal("337")}
    assert [(m.month, m.opening, m.net, m.closing) for m in result.monthly_cash] == [
        ("2026-10", Decimal("100"), Decimal("337"), Decimal("437")),
        ("2026-11", Decimal("437"), Decimal("0"), Decimal("437")),
    ]


def test_kst_month_boundary_governs_cash_period():
    data = base(period_end=date(2026, 11, 30))
    data["collections"][0]["at"] = T(31, 15)  # 1 November KST
    result = run(data)
    assert result.monthly_cash[0].net == Decimal("-25")
    assert result.monthly_cash[1].net == Decimal("500")
    assert result.monthly_cash[1].closing == Decimal("575")


def test_cash_shortage_tracks_within_month_payment_instant():
    data = base(period_end=date(2026, 10, 31), opening_cash=n(0, "opening-cash", "KRW"))
    data["variable_costs"][0]["paid_at"] = T(16)
    data["variable_costs"][1]["paid_at"] = T(16)
    result = run(data)
    october = result.monthly_cash[0]
    assert october.closing == Decimal("475")
    assert (october.minimum_balance, october.minimum_at, october.shortage) == (
        Decimal("-25"), T(16), Decimal("25"))
    assert (result.minimum_cash_balance, result.minimum_cash_at, result.cash_shortage) == (
        Decimal("-25"), T(16), Decimal("25"))


def test_same_instant_cash_events_are_net_before_minimum_sample():
    data = base(period_end=date(2026, 10, 31), opening_cash=n(0, "opening-cash", "KRW"))
    for cost in data["variable_costs"]:
        cost["paid_at"] = T(20)
    result = run(data)
    october = result.monthly_cash[0]
    assert october.closing == Decimal("475")
    assert (october.minimum_balance, october.minimum_at, october.shortage) == (
        Decimal("0"), datetime(2026, 9, 30, 15, tzinfo=timezone.utc), Decimal("0"))


def test_negative_cash_carried_into_november_is_dated_at_kst_opening():
    data = base(opening_cash=n(0, "opening-cash", "KRW"))
    data["variable_costs"][0]["paid_at"] = T(16)
    data["variable_costs"][1]["paid_at"] = T(16)
    data["collections"][0]["at"] = datetime(2026, 11, 20, tzinfo=timezone.utc)
    result = run(data)
    november = result.monthly_cash[1]
    assert november.opening == Decimal("-25")
    assert (november.minimum_balance, november.minimum_at, november.shortage) == (
        Decimal("-25"), datetime(2026, 10, 31, 15, tzinfo=timezone.utc), Decimal("25"))


def test_cash_minima_are_held_when_cash_is_incomplete():
    result = run(base(taxes=None))
    assert result.monthly_cash is None
    assert result.minimum_cash_balance is None
    assert result.minimum_cash_at is None
    assert result.cash_shortage is None


@pytest.mark.parametrize("group,account", [
    ("depreciation", "asset"), ("capex", "asset"), ("asset_disposals", "asset"),
    ("grants", None), ("taxes", None), ("loan_draws", "loan"),
    ("principal_payments", "loan"), ("interest_payments", "loan"),
])
@pytest.mark.parametrize("outside", [datetime(2026, 9, 30, 14, tzinfo=timezone.utc), T(31, 15)])
def test_parent_amount_events_reject_dates_outside_kst_evaluation(group, account, outside):
    data = base(period_end=date(2026, 10, 31))
    event = {"id": f"{group}-1", "at": outside, "amount": n(1, f"{group}-amount", "KRW")}
    if account == "asset":
        data["assets"] = ({"id": "asset-1", "opening_basis": n(1, "asset-opening", "KRW")},)
        event["asset_id"] = "asset-1"
    if account == "loan":
        data["debt_accounts"] = ({"id": "loan-1", "opening_principal": n(1, "loan-opening", "KRW")},)
        event["loan_id"] = "loan-1"
    data[group] = (event,)
    data["zero_declarations"] = tuple(
        declaration for declaration in data["zero_declarations"]
        if declaration["group"] not in {group, "assets" if account == "asset" else "debt_accounts"}
    )
    with pytest.raises(ValueError, match="outside evaluation period"):
        run(data)


def test_parent_event_at_utc_to_kst_end_boundary_is_inside():
    data = base(period_end=date(2026, 10, 31), grants=(
        {"id": "grant-1", "at": T(31, 14), "amount": n(1, "grant-amount", "KRW")},))
    assert run(data).business_cash == Decimal("476")


def test_later_cash_is_scheduled_without_losing_accruals():
    outside = T(31, 15)  # 1 November 00:00 KST
    data = base(period_end=date(2026, 10, 31))
    data["collections"][0]["at"] = outside
    result = run(data)
    assert result.revenue == Decimal("500") and result.management_oi == Decimal("475")
    assert result.operating_cash == Decimal("-25")
    assert result.business_cash == result.equity_cash == Decimal("-25")
    assert result.monthly_cash[0].closing == Decimal("75")
    assert result.future_cash_schedule[0].event_id == "collection-1"
    assert result.receivable_end == Decimal("500")
    assert result.operating_cash_bridge == Decimal("-25")

    data = base(period_end=date(2026, 10, 31))
    data["variable_costs"][0]["paid_at"] = outside
    result = run(data)
    assert result.variable_cost == Decimal("25") and result.management_oi == Decimal("475")
    assert result.operating_cash == Decimal("495")
    assert result.operating_payable_end == Decimal("20")
    assert result.future_cash_schedule[0].event_id == "production"

    data = base(period_end=date(2026, 10, 31), returns=(
        {"id": "return-1", "sale_id": "sale-1", "at": T(24),
         "quantity": n(1, "return-q"), "disposition": "resaleable",
         "refund": n(100, "refund", "KRW"), "refund_paid_at": outside},))
    result = run(data)
    assert result.revenue == Decimal("400") and result.management_oi == Decimal("375")
    assert result.operating_cash == Decimal("475")
    assert result.refund_payable_end == Decimal("100")
    assert result.future_cash_schedule[0].event_id == "return-1"


def test_resaleable_return_reenters_inventory_and_refund_only_once():
    data = base(returns=({"id": "return-1", "sale_id": "sale-1", "at": T(24),
                          "quantity": n(1, "return-q"), "disposition": "resaleable",
                          "refund": n(100, "refund", "KRW"), "refund_paid_at": T(25)},),)
    result = run(data)
    assert result.recognized_kg == Decimal("5")
    assert result.net_sold_kg == Decimal("4")
    assert result.closing_inventory == {("batch-1", "grade-1", "direct"): Decimal("4")}
    assert result.revenue == Decimal("400")
    assert result.operating_cash == Decimal("375")


def test_disposed_return_and_pre_sale_disposal_do_not_reenter_inventory():
    data = base(returns=({"id": "return-1", "sale_id": "sale-1", "at": T(24),
                          "quantity": n(1, "return-q"), "disposition": "disposed",
                          "refund": n(100, "refund", "KRW"), "refund_paid_at": T(25)},),
                disposals=({"id": "disposal-1", "batch_id": "batch-1", "grade": "grade-1",
                            "channel": "direct", "at": T(16), "quantity": n(1, "disposed-q")},))
    result = run(data)
    assert result.closing_inventory == {("batch-1", "grade-1", "direct"): Decimal("2")}
    assert result.revenue == Decimal("400")


def test_returns_cannot_exceed_original_sale_or_double_adjustment():
    data = base(returns=({"id": "r1", "sale_id": "sale-1", "at": T(24),
                          "quantity": n(3, "r1q"), "disposition": "resaleable",
                          "refund": n(300, "r1refund", "KRW"), "refund_paid_at": T(25)},
                         {"id": "r2", "sale_id": "sale-1", "at": T(24),
                          "quantity": n(3, "r2q"), "disposition": "disposed",
                          "refund": n(300, "r2refund", "KRW"), "refund_paid_at": T(25)}))
    with pytest.raises(ValueError):
        run(data)
    data = base(returns=({"id": "r1", "sale_id": "sale-1", "at": T(24),
                          "quantity": n(1, "r1q"), "disposition": "resaleable",
                          "refund": n(100, "r1refund", "KRW"), "refund_paid_at": T(25)},),
                discounts=({"id": "discount-1", "sale_id": "sale-1", "at": T(24),
                            "amount": n(450, "discount", "KRW")},))
    with pytest.raises(ValueError):
        run(data)


def test_absence_declarations_are_required_for_each_relevant_result():
    result = run(base(taxes=None))
    assert result.management_oi == Decimal("475")
    assert result.operating_cash == Decimal("475")
    assert result.business_cash is None and result.equity_cash is None
    assert result.monthly_cash is None
    assert "TAXES_UNDECLARED" in result.hold_reasons
    assert result.target_values["cumulative_equity_cash"] is None


def test_thermal_demand_cannot_be_submitted_as_an_electricity_bill():
    data = base()
    data["thermal_demand"] = n(100, "thermal", "kWh_th")
    with pytest.raises(ValueError):
        run(data)


def test_depreciation_requires_basis_available_by_each_event_date():
    asset = ({"id": "asset-1", "opening_basis": n(0, "asset-opening", "KRW")},)
    depreciation = ({"id": "dep", "at": T(20), "asset_id": "asset-1",
                     "amount": n(100, "dep-amount", "KRW")},)
    with pytest.raises(ValueError, match="depreciation exceeds available asset basis"):
        run(base(assets=asset, depreciation=depreciation))
    later_capex = ({"id": "capex-1", "at": T(21), "asset_id": "asset-1",
                    "amount": n(100, "capex-amount", "KRW")},)
    with pytest.raises(ValueError, match="depreciation exceeds available asset basis"):
        run(base(assets=asset, depreciation=depreciation, capex=later_capex))
    earlier_capex = ({**later_capex[0], "at": T(19)},)
    incomplete = run(base(assets=asset, depreciation=depreciation, capex=earlier_capex))
    assert incomplete.depreciation is None and incomplete.management_oi is None
    assert "DEPRECIATION_SCHEDULE_INCOMPLETE" in incomplete.hold_reasons
    second_depreciation = depreciation + ({"id": "dep-2", "at": T(22), "asset_id": "asset-1",
                                          "amount": n(1, "dep-2-amount", "KRW")},)
    with pytest.raises(ValueError, match="depreciation exceeds available asset basis"):
        run(base(assets=asset, depreciation=second_depreciation, capex=earlier_capex))


@pytest.mark.parametrize("group,at", [
    ("depreciation", T(20)), ("depreciation", T(10)),
    ("capex", T(20)), ("capex", T(10)),
])
def test_asset_disposal_retires_basis_and_rejects_later_or_same_instant_events(group, at):
    asset = ({"id": "asset-1", "opening_basis": n(100, "asset-opening", "KRW")},)
    disposal = ({"id": "asset-sale", "at": T(10), "asset_id": "asset-1",
                 "amount": n(250, "asset-proceeds", "KRW")},)
    event = {"id": f"{group}-after-sale", "at": at, "asset_id": "asset-1",
             "amount": n(100, f"{group}-after-sale-amount", "KRW")}
    with pytest.raises(ValueError, match="asset event at or after disposal"):
        run(base(assets=asset, asset_disposals=disposal, **{group: (event,)}))


def test_asset_disposal_allows_prior_depreciation_but_rejects_second_disposal():
    asset = ({"id": "asset-1", "opening_basis": n(100, "asset-opening", "KRW"),
              "acquisition_cost": n(100, "asset-cost", "KRW"),
              "acquired_at": DECISION, "installed_at": T(1),
              "residual_value": n(0, "asset-residual", "KRW"),
              "useful_life_days": n(9, "asset-life", "day"),
              "opening_accumulated_depreciation": n(0, "asset-accum", "KRW")},)
    disposal = {"id": "asset-sale", "at": T(10), "asset_id": "asset-1",
                "amount": n(250, "asset-proceeds", "KRW")}
    prior_depreciation = ({"id": "dep", "at": T(9), "asset_id": "asset-1",
                           "amount": n(100, "dep-amount", "KRW")},)
    result = run(base(assets=asset, asset_disposals=(disposal,),
                      depreciation=prior_depreciation))
    assert result.depreciation == Decimal("100")
    assert result.business_cash == Decimal("725")
    too_much = ({**prior_depreciation[0], "amount": n(101, "dep-amount", "KRW")},)
    with pytest.raises(ValueError, match="depreciation exceeds available asset basis"):
        run(base(assets=asset, asset_disposals=(disposal,), depreciation=too_much))
    second = {"id": "asset-sale-again", "at": T(11), "asset_id": "asset-1",
              "amount": n(1, "second-asset-proceeds", "KRW")}
    with pytest.raises(ValueError, match="duplicate asset disposal"):
        run(base(assets=asset, asset_disposals=(disposal, second)))


def test_discount_after_full_collection_rejects_unsupported_cash_correction():
    data = base(discounts=({"id": "discount-1", "sale_id": "sale-1", "at": T(24),
                           "amount": n(100, "discount-amount", "KRW")},))
    with pytest.raises(ValueError, match="DISCOUNT_AFTER_COLLECTION_CASH_CORRECTION_UNSUPPORTED"):
        run(data)


def test_later_receipt_payment_refund_keep_period_cash_and_future_schedule():
    later = T(31, 15)
    data = base(period_end=date(2026, 10, 31), returns=({
        "id": "return-1", "sale_id": "sale-1", "at": T(24),
        "quantity": n(1, "return-q"), "disposition": "resaleable",
        "refund": n(100, "refund", "KRW"), "refund_paid_at": later},))
    data["collections"][0]["at"] = later
    data["variable_costs"][0]["paid_at"] = later
    result = run(data)
    assert result.management_oi == Decimal("375")
    assert result.operating_cash == Decimal("-5")
    assert result.monthly_cash[0].closing == Decimal("95")
    assert [(e.event_id, e.at, e.amount, e.category) for e in result.future_cash_schedule] == [
        ("collection-1", later, Decimal("500"), "collection"),
        ("return-1", later, Decimal("-100"), "refund"),
        ("production", later, Decimal("-20"), "variable_cost_payment"),
    ]
    assert result.receivable_end == Decimal("500")
    assert result.refund_payable_end == Decimal("100")
    assert result.operating_payable_end == Decimal("20")


def test_opening_bridge_balances_must_be_explicit_zero():
    data = base(opening_receivable=None)
    result = run(data)
    assert result.operating_cash is None and result.monthly_cash is None
    assert result.operating_cash_bridge is None
    assert "OPENING_RECEIVABLE_UNDECLARED" in result.hold_reasons
    with pytest.raises(ValueError, match="unsupported nonzero opening"):
        run(base(opening_receivable=n(1, "opening-receivable", "KRW")))


def test_partial_collections_payments_and_discount_reconcile_bridge():
    data = base(collections=({"id": "collection-1", "sale_id": "sale-1", "at": T(20),
                               "amount": n(300, "collection", "KRW")},),
                discounts=({"id": "discount-1", "sale_id": "sale-1", "at": T(19),
                            "amount": n(50, "discount", "KRW")},))
    data["variable_costs"][0]["payment"]["value"] = "10"
    result = run(data)
    assert result.management_oi == Decimal("425")
    assert result.receivable_end == Decimal("150")
    assert result.operating_payable_end == Decimal("10")
    assert result.operating_cash_bridge == Decimal("285")
    assert result.operating_cash == Decimal("285")


def test_unjustified_depreciation_is_rejected_even_with_sufficient_basis():
    asset = ({"id": "asset-1", "opening_basis": n(100, "asset-opening", "KRW"),
              "acquisition_cost": n(100, "asset-cost", "KRW"),
              "acquired_at": DECISION, "installed_at": T(1),
              "residual_value": n(0, "asset-residual", "KRW"),
              "useful_life_days": n(100, "asset-life", "day"),
              "opening_accumulated_depreciation": n(0, "asset-accum", "KRW")},)
    event = ({"id": "dep", "at": T(2), "asset_id": "asset-1",
              "amount": n(100, "dep-amount", "KRW")},)
    with pytest.raises(ValueError, match="depreciation schedule"):
        run(base(assets=asset, depreciation=event))


def test_depreciation_event_must_follow_exact_installation_instant():
    installed = T(1, 12)
    asset = ({"id": "asset-1", "opening_basis": n(100, "asset-opening", "KRW"),
              "acquisition_cost": n(100, "asset-cost", "KRW"),
              "acquired_at": DECISION, "installed_at": installed,
              "residual_value": n(0, "asset-residual", "KRW"),
              "useful_life_days": n(100, "asset-life", "day"),
              "opening_accumulated_depreciation": n(0, "asset-accum", "KRW")},)
    empty = dict(period_end=date(2026, 10, 1), assets=asset,
                 harvests=(), packouts=(), culls=(), cull_disposals=(), sales=(),
                 collections=(), variable_costs=(), fixed_costs=())
    before = ({"id": "dep", "at": T(1, 1), "asset_id": "asset-1",
               "amount": n(1, "dep-amount", "KRW")},)
    with pytest.raises(ValueError, match="before installation"):
        run(base(depreciation=before, **empty))
    after = ({**before[0], "at": T(1, 13)},)
    assert run(base(depreciation=after, **empty)).depreciation == Decimal("1")


def test_straight_line_rounds_cumulative_pro_rated_days_to_cents():
    asset = ({"id": "asset-1", "opening_basis": n(100, "asset-opening", "KRW"),
              "acquisition_cost": n(100, "asset-cost", "KRW"),
              "acquired_at": DECISION, "installed_at": T(1),
              "residual_value": n(0, "asset-residual", "KRW"),
              "useful_life_days": n(3, "asset-life", "day"),
              "opening_accumulated_depreciation": n(0, "asset-accum", "KRW")},)
    events = ({"id": "dep-1", "at": T(1), "asset_id": "asset-1",
               "amount": n("33.33", "dep-1-amount", "KRW")},
              {"id": "dep-2", "at": T(3), "asset_id": "asset-1",
               "amount": n("66.67", "dep-2-amount", "KRW")})
    result = run(base(period_end=date(2026, 10, 3), assets=asset, depreciation=events,
                      harvests=(), packouts=(), culls=(), cull_disposals=(), sales=(),
                      collections=(), variable_costs=(), fixed_costs=()))
    assert result.depreciation == Decimal("100.00")
    assert result.management_oi == Decimal("-100.00")
    bad = ({**events[0], "amount": n("33.34", "dep-1-amount", "KRW")},
           {**events[1], "amount": n("66.66", "dep-2-amount", "KRW")})
    with pytest.raises(ValueError, match="depreciation schedule"):
        run(base(period_end=date(2026, 10, 3), assets=asset, depreciation=bad,
                 harvests=(), packouts=(), culls=(), cull_disposals=(), sales=(),
                 collections=(), variable_costs=(), fixed_costs=()))


@pytest.mark.parametrize("field", ["opening_receivable", "opening_refund_payable",
                                   "opening_operating_payable"])
def test_each_opening_bridge_balance_must_be_pinned(field):
    result = run(base(**{field: None}))
    assert result.operating_cash is None and result.operating_cash_bridge is None
    assert f"{field.upper()}_UNDECLARED" in result.hold_reasons


def test_before_period_cash_is_rejected():
    data = base(period_start=date(2026, 10, 2))
    data["variable_costs"][0]["paid_at"] = T(1)
    with pytest.raises(ValueError, match="before-period cash"):
        run(data)
    data = base(period_start=date(2026, 10, 2))
    data["collections"][0]["at"] = T(1)
    with pytest.raises(ValueError, match="before-period cash"):
        run(data)


def test_opening_accumulated_depreciation_must_match_schedule():
    asset = {"id": "asset-1", "opening_basis": n(99, "asset-opening", "KRW"),
             "acquisition_cost": n(100, "asset-cost", "KRW"),
             "acquired_at": DECISION,
             "installed_at": datetime(2026, 9, 30, 0, tzinfo=timezone.utc),
             "residual_value": n(0, "asset-residual", "KRW"),
             "useful_life_days": n(100, "asset-life", "day"),
             "opening_accumulated_depreciation": n(1, "asset-accum", "KRW")}
    event = ({"id": "dep", "at": T(2), "asset_id": "asset-1",
              "amount": n(2, "dep-amount", "KRW")},)
    data = base(period_end=date(2026, 10, 2), assets=(asset,), depreciation=event,
                harvests=(), packouts=(), culls=(), cull_disposals=(), sales=(),
                collections=(), variable_costs=(), fixed_costs=())
    assert run(data).depreciation == Decimal("2")
    bad = {**asset, "opening_accumulated_depreciation": n(0, "asset-accum", "KRW")}
    with pytest.raises(ValueError, match="depreciation schedule opening book basis"):
        run(base(**{**data, "assets": (bad,)}))
