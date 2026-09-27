"""Synthetic G1 ledger contracts; the repository below is a trusted-server test fake only."""

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import json
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.economic_contracts import EconomicScenario, iter_economic_numbers
from app.economics import EconomicLedger, canonical_scenario_sha256
import app.economics as economics

ROOT = Path(__file__).resolve().parents[2]
DECISION = datetime(2026, 9, 28, tzinfo=timezone.utc)
T = lambda day, hour=0: datetime(2026, 10, day, hour, tzinfo=timezone.utc)
MARKET = {"kind": "unavailable", "hold_report_id": "hold-1"}
ZERO_GROUP_UNITS = {
    "cull_disposals": "kg", "opening_inventory": "kg", "collections": "KRW",
    "returns": "kg", "discounts": "KRW", "disposals": "kg",
    "variable_costs": "KRW", "fixed_costs": "KRW", "depreciation": "KRW",
    "assets": "KRW", "grants": "KRW", "asset_disposals": "KRW",
    "taxes": "KRW", "capex": "KRW", "loan_draws": "KRW",
    "principal_payments": "KRW", "interest_payments": "KRW", "debt_accounts": "KRW",
}


def n(value, input_id, unit="kg"):
    return {"value": str(value), "unit": unit, "input_id": input_id, "revision": "r1",
            "origin": "user", "evidence_level": "assumed", "assumption_scope": f"scenario-1:{input_id}",
            "source_ref": "self-authored-test", "available_at": DECISION}


def opening_lot(quantity=5, cost=200, basis=5):
    return {"grade": "grade-1", "batch_id": "batch-1", "channel": "direct",
            "prior_cost_ref": "prior-batch-cost", "quantity": n(quantity, "opening-stock"),
            "prior_cost_amount": n(cost, "prior-cost", "KRW"),
            "allocation_basis": n(basis, "prior-basis"),
            "allocation_policy": "proportional_saleable_kg_v1"}


def base(**overrides):
    data = dict(schema_version="2", scenario_id="scenario-1", scenario_revision="r1",
                tenant_id="tenant-1",
                decision_at=DECISION, period_start=date(2026, 10, 1), period_end=date(2026, 11, 30),
                scenario_market_context=MARKET, market_context=MARKET,
                harvests=({"id": "harvest-1", "batch_id": "batch-1", "at": T(15), "quantity": n(10, "h")},),
                packouts=({"id": "pack-1", "harvest_id": "harvest-1", "batch_id": "batch-1",
                           "grade": "grade-1", "channel": "direct", "at": T(15, 1), "quantity": n(8, "p")},),
                culls=({"id": "cull-1", "harvest_id": "harvest-1", "at": T(15, 1),
                        "quantity": n(2, "cull")},),
                cull_disposals=({"id": "cull-disposal-1", "cull_id": "cull-1", "at": T(15, 1),
                                 "quantity": n(2, "cull-disposal")},),
                opening_inventory=(),
                sales=({"id": "sale-1", "batch_id": "batch-1", "grade": "grade-1", "channel": "direct",
                        "dispatch_at": T(15, 2), "delivery_at": T(15, 3), "inspection_at": T(15, 4),
                        "recognized_at": T(15, 5), "quantity": n(5, "s"),
                        "price": n(100, "price", "KRW/kg"),
                        "price_basis": "gross_before_deductions"},),
                collections=({"id": "collection-1", "sale_id": "sale-1", "at": T(20),
                              "amount": n(500, "collection", "KRW")},),
                returns=(), discounts=(), disposals=(),
                variable_costs=({"id": "production", "purpose": "production", "batch_id": "batch-1",
                                 "sale_id": None, "incurred_at": T(15),
                                 "quantity": n(10, "production-q"), "unit_cost": n(2, "production-rate", "KRW/kg"),
                                 "paid_at": T(21), "payment": n(20, "production-paid", "KRW")},
                                {"id": "dispatch", "purpose": "sale", "batch_id": None,
                                 "sale_id": "sale-1", "incurred_at": T(15, 2),
                                 "quantity": n(5, "dispatch-q"), "unit_cost": n(1, "dispatch-rate", "KRW/kg"),
                                 "paid_at": T(23), "payment": n(5, "dispatch-paid", "KRW")}),
                fixed_costs=(), depreciation=(), assets=(), grants=(), asset_disposals=(), taxes=(),
                capex=(), loan_draws=(), principal_payments=(), interest_payments=(),
                debt_accounts=(),
                opening_cash=n(100, "opening-cash", "KRW"),
                opening_receivable=n(0, "opening-receivable", "KRW"),
                opening_refund_payable=n(0, "opening-refund-payable", "KRW"),
                opening_operating_payable=n(0, "opening-operating-payable", "KRW"))
    data.update(overrides)
    data.setdefault("zero_declarations", tuple(
        {"group": group, "zero": n(0, f"zero-{group}", unit)}
        for group, unit in ZERO_GROUP_UNITS.items() if data[group] == ()
    ))
    return data


class TrustedTestRepository:
    """Injected by server test setup, never supplied in a client scenario; no production DB claim."""

    def __init__(self, scenario):
        self.records = {}
        self.authenticated = True
        digest = canonical_scenario_sha256(scenario)
        self.scenario_pin = {
            "tenant_id": scenario.tenant_id, "scenario_id": scenario.scenario_id,
            "scenario_revision": scenario.scenario_revision, "decision_at": scenario.decision_at,
            "payload_sha256": digest, "immutable_job_input_ref": "test-job-input-1",
            "immutable_job_input_sha256": digest, "immutable": True,
        }
        for value in iter_economic_numbers(scenario):
            self.records[(value.input_id, value.revision)] = {
                **value.model_dump(), "tenant_id": scenario.tenant_id,
                "scope_start": scenario.period_start, "scope_end": scenario.period_end,
            }
        self.hold = {"hold_report_id": "hold-1", "tenant_id": "tenant-1",
                     "decision_at": DECISION, "reasons": ("NO_APPROVED_MARKET_SNAPSHOT",),
                     "missing_evidence": ("G0_APPROVED_MARKET_SOURCE",)}
        self.prior_costs = {
            lot.prior_cost_ref: {
                "cost_ref": lot.prior_cost_ref, "tenant_id": scenario.tenant_id,
                "batch_id": lot.batch_id, "grade": lot.grade, "channel": lot.channel,
                "cost_amount": lot.prior_cost_amount.model_dump() if lot.prior_cost_amount else None,
                "allocation_basis_kg": lot.allocation_basis.model_dump() if lot.allocation_basis else None,
                "opening_quantity_kg": lot.quantity.model_dump(),
                "allocation_policy": lot.allocation_policy,
                "rights": "conditional_g1_use",
                "available_at": DECISION, "scope_start": scenario.period_start,
                "scope_end": scenario.period_end,
            }
            for lot in scenario.opening_inventory or () if lot.prior_cost_ref is not None
        }

    def tenant_is_authenticated(self, tenant_id):
        return self.authenticated and tenant_id == "tenant-1"

    def get_market_hold_report(self, hold_report_id):
        return self.hold if hold_report_id == "hold-1" else None

    def get_economic_input(self, input_id, revision):
        return self.records.get((input_id, revision))

    def get_economic_scenario_pin(self, scenario_id, revision):
        if (scenario_id, revision) == (self.scenario_pin["scenario_id"],
                                       self.scenario_pin["scenario_revision"]):
            return self.scenario_pin
        return None

    def get_prior_batch_cost(self, cost_ref):
        return self.prior_costs.get(cost_ref)


def run(data=None, repo=None):
    scenario = EconomicScenario.model_validate(data or base())
    return EconomicLedger(repo or TrustedTestRepository(scenario)).calculate(scenario)


def test_complete_synthetic_ledger_tracks_inventory_and_distinct_targets():
    result = run()
    assert result.market_context.hold_report_id == "hold-1"
    assert result.scenario_revision == "r1"
    assert result.formula_version == "economic-ledger-v7-pre-dispatch-sale-cost"
    assert result.scenario_sha256 == canonical_scenario_sha256(EconomicScenario.model_validate(base()))
    assert result.assessment_market_context == result.market_context
    assert result.assessment_status == "hold" and result.forecast_run_id is None
    assert result.harvest_kg == Decimal("10")
    assert result.packout_kg == Decimal("8")
    assert result.cull_disposed_kg == Decimal("2")
    assert result.recognized_kg == Decimal("5")
    assert result.closing_inventory == {("batch-1", "grade-1", "direct"): Decimal("3")}
    assert result.gross_sales == Decimal("500")
    assert result.sales_totals_status == "inventory_reconciled"
    assert result.revenue == Decimal("500")
    assert result.variable_cost == Decimal("25")
    assert result.management_oi == Decimal("475")
    assert result.operating_cash == Decimal("475")
    assert result.business_cash == Decimal("475")
    assert result.equity_cash == Decimal("475")
    assert result.target_values == {"oi": Decimal("475"), "operating_cash": Decimal("475"),
                                    "cumulative_equity_cash": Decimal("475")}
    assert tuple((item.input_id, item.revision) for item in result.input_provenance) == result.input_versions
    zero = next(item for item in result.input_provenance if item.input_id == "zero-opening_inventory")
    assert (zero.value, zero.unit, zero.revision, zero.origin, zero.evidence_level,
            zero.assumption_scope, zero.source_ref, zero.available_at) == (
                "0", "kg", "r1", "user", "assumed", "scenario-1:zero-opening_inventory",
                "self-authored-test", DECISION)
    assert not hasattr(zero, "tenant_id")
    with pytest.raises(ValidationError):
        zero.value = "9"


def test_declared_zero_opening_cash_is_a_verified_numeric_input():
    result = run(base(opening_cash=n(0, "opening-cash", "KRW")))
    assert result.monthly_cash[0].opening == Decimal("0")
    assert next(item for item in result.input_provenance if item.input_id == "opening-cash").value == "0"


@pytest.mark.parametrize("group,result_field", [
    ("cull_disposals", "cull_disposed_kg"), ("opening_inventory", "closing_inventory"),
    ("collections", "operating_cash"), ("returns", "revenue"),
    ("discounts", "revenue"), ("disposals", "closing_inventory"),
    ("variable_costs", "variable_cost"), ("fixed_costs", "fixed_cost"),
    ("depreciation", "depreciation"), ("assets", "management_oi"),
    ("grants", "business_cash"), ("asset_disposals", "business_cash"),
    ("taxes", "business_cash"), ("capex", "business_cash"),
    ("loan_draws", "equity_cash"), ("principal_payments", "equity_cash"),
    ("interest_payments", "equity_cash"), ("debt_accounts", "equity_cash"),
])
def test_each_empty_group_needs_its_own_scoped_zero(group, result_field):
    data = base(**{group: ()})
    data["zero_declarations"] = tuple(
        declaration for declaration in data["zero_declarations"] if declaration["group"] != group)
    result = run(data)
    assert f"{group.upper()}_UNDECLARED" in result.hold_reasons
    assert getattr(result, result_field) is None


def test_zero_declaration_rejects_nonempty_or_missing_group_and_wrong_unit():
    data = base()
    data["returns"] = ({"id": "return-1", "sale_id": "sale-1", "at": T(24),
                        "quantity": n(1, "return-q"), "disposition": "resaleable",
                        "refund": n(100, "refund", "KRW"), "refund_paid_at": T(25)},)
    with pytest.raises(ValidationError):
        EconomicScenario.model_validate(data)
    data = base()
    data["returns"] = None
    with pytest.raises(ValidationError):
        EconomicScenario.model_validate(data)
    data = base()
    data["zero_declarations"][0]["zero"]["unit"] = "KRW"
    with pytest.raises(ValidationError):
        EconomicScenario.model_validate(data)


@pytest.mark.parametrize("mutation", ["forged", "missing", "foreign", "late", "scope"])
def test_zero_declaration_is_verified_against_owned_repository(mutation):
    scenario = EconomicScenario.model_validate(base())
    repo = TrustedTestRepository(scenario)
    key = ("zero-opening_inventory", "r1")
    if mutation == "forged":
        repo.records[key]["value"] = "1"
    elif mutation == "missing":
        repo.records.pop(key)
    elif mutation == "foreign":
        repo.records[key]["tenant_id"] = "tenant-2"
    elif mutation == "late":
        repo.records[key]["available_at"] = T(1)
    else:
        repo.records[key]["scope_end"] = date(2026, 10, 1)
    with pytest.raises(ValueError):
        EconomicLedger(repo).calculate(scenario)


def test_large_decimal_cost_product_and_aggregate_stay_exact():
    driver = "123456789012345678901234567890123456789"
    rate = "987654321098765432109876543210987654321"
    data = base()
    data["variable_costs"] += ({"id": "energy", "purpose": "period", "batch_id": None,
                                "sale_id": None, "incurred_at": T(15),
                                "quantity": n(driver, "energy-q", "kWh_e"),
                                "unit_cost": n(rate, "energy-rate", "KRW/kWh_e"),
                                "paid_at": None, "payment": None},)
    result = run(data)
    assert result.variable_cost == Decimal(str(int(driver) * int(rate) + 25))


def test_arithmetic_rejects_an_aggregate_beyond_exact_domain():
    maximum = "9" * 64
    data = base(variable_costs=tuple(
        {"id": f"energy-{index}", "purpose": "period", "batch_id": None,
         "sale_id": None, "incurred_at": T(15),
         "quantity": n(maximum, f"energy-q-{index}", "kWh_e"),
         "unit_cost": n(maximum, f"energy-rate-{index}", "KRW/kWh_e"),
         "paid_at": None, "payment": None}
        for index in (1, 2)
    ))
    with pytest.raises(ValueError, match="exact 128-digit domain"):
        run(data)


def test_fixture_is_only_a_partial_algebraic_example():
    fixture = json.loads((ROOT / "fixtures/synthetic-economics-v1.json").read_text())
    baseline = fixture["baseline"]
    assert baseline["harvest"]["value"] == "10"
    assert baseline["saleable_packout"]["value"] == "8"
    assert baseline["sale"]["recognized_quantity"]["value"] == "5"
    assert baseline["collection"]["amount"]["value"] == "500"
    assert [cost["payment_amount"]["value"] for cost in baseline["costs"]] == ["20", "5"]
    assert baseline["opening_saleable_inventory"]["value"] == "1"
    assert baseline["closing_saleable_inventory"]["value"] == "4"
    partial = base(opening_inventory=({"grade": None, "batch_id": None, "channel": None,
                                      "prior_cost_ref": None,
                                      "quantity": n(baseline["opening_saleable_inventory"]["value"], "unknown-opening")},),
                   fixed_costs=None, depreciation=None, assets=None, grants=None, asset_disposals=None,
                   taxes=None, capex=None, loan_draws=None, principal_payments=None,
                   interest_payments=None, debt_accounts=None, returns=None, discounts=None,
                   opening_cash=None, opening_receivable=None, opening_refund_payable=None,
                   opening_operating_payable=None)
    partial["harvests"][0]["quantity"]["value"] = baseline["harvest"]["value"]
    partial["packouts"][0]["quantity"]["value"] = baseline["saleable_packout"]["value"]
    partial["culls"][0]["quantity"]["value"] = baseline["unsaleable_cull"]["value"]
    partial["cull_disposals"][0]["quantity"]["value"] = baseline["cull_disposal"]["value"]
    partial["sales"][0]["quantity"]["value"] = baseline["sale"]["recognized_quantity"]["value"]
    partial["sales"][0]["price"]["value"] = baseline["sale"]["farm_contract_price_before_deductions"]["value"]
    partial["collections"][0]["amount"]["value"] = baseline["collection"]["amount"]["value"]
    assert [cost["id"] for cost in baseline["costs"]] == [
        "sentinel_production_input", "sentinel_dispatch_service"]
    partial["variable_costs"][0].update(purpose="production", batch_id="batch-1", sale_id=None)
    partial["variable_costs"][1].update(purpose="sale", batch_id=None, sale_id="sale-1")
    for cost, fixture_cost in zip(partial["variable_costs"], baseline["costs"], strict=True):
        cost["quantity"]["value"] = fixture_cost["quantity"]["value"]
        cost["unit_cost"]["value"] = fixture_cost["unit_cost"]["value"]
        cost["payment"]["value"] = fixture_cost["payment_amount"]["value"]
    result = run(partial)
    assert result.gross_sales == Decimal("500")
    assert result.recognized_kg == Decimal("5")
    assert result.sales_totals_status == "unverified_input_arithmetic"
    assert result.variable_cost == Decimal("25")
    assert result.closing_inventory is None
    assert result.revenue is None and result.management_oi is None
    assert result.operating_cash is None and result.business_cash is None and result.equity_cash is None
    assert result.monthly_cash is None
    assert {"OPENING_INVENTORY_LINKAGE_UNKNOWN", "RETURNS_UNDECLARED", "FIXED_COSTS_UNDECLARED",
            "OPENING_CASH_UNDECLARED", "OPENING_RECEIVABLE_UNDECLARED",
            "OPENING_REFUND_PAYABLE_UNDECLARED",
            "OPENING_OPERATING_PAYABLE_UNDECLARED"} <= set(result.hold_reasons)


@pytest.mark.parametrize("bad", [1, 1.0, True, None, "NaN", "Infinity", "-Infinity", "1e9999"])
def test_numeric_contract_rejects_non_json_finite_decimal_strings(bad):
    data = base()
    data["sales"][0]["price"]["value"] = bad
    with pytest.raises(ValidationError):
        EconomicScenario.model_validate(data)


@pytest.mark.parametrize("field,value", [("unit", "kWh_th"), ("origin", "source"),
                                         ("evidence_level", "measured"), ("assumption_scope", ""),
                                         ("input_id", None), ("revision", None), ("source_ref", None)])
def test_numeric_metadata_is_strict(field, value):
    data = base()
    data["sales"][0]["price"][field] = value
    with pytest.raises(ValidationError):
        EconomicScenario.model_validate(data)


def test_extra_and_client_repository_are_rejected():
    data = base(repository={"get_economic_input": "forged"})
    with pytest.raises(ValidationError):
        EconomicScenario.model_validate(data)
    data = base()
    data["sales"][0]["price"]["g0_pass"] = True
    with pytest.raises(ValidationError):
        EconomicScenario.model_validate(data)


def test_gross_price_basis_must_be_explicit():
    data = base()
    data["sales"][0]["price_basis"] = "net_after_deductions"
    with pytest.raises(ValidationError):
        EconomicScenario.model_validate(data)


def test_server_owned_input_revision_value_scope_and_authentication_are_checked():
    scenario = EconomicScenario.model_validate(base())
    for mutation in ("value", "revision", "tenant", "scope", "late", "assumption_scope", "auth", "market"):
        repo = TrustedTestRepository(scenario)
        if mutation == "value":
            repo.records[("price", "r1")]["value"] = "999"
        elif mutation == "revision":
            repo.records.pop(("price", "r1"))
        elif mutation == "tenant":
            repo.records[("price", "r1")]["tenant_id"] = "tenant-2"
        elif mutation == "scope":
            repo.records[("price", "r1")]["scope_end"] = date(2026, 10, 1)
        elif mutation == "late":
            repo.records[("price", "r1")]["available_at"] = T(1)
        elif mutation == "assumption_scope":
            repo.records[("price", "r1")]["assumption_scope"] = "different scenario"
        elif mutation == "auth":
            repo.authenticated = False
        else:
            repo.hold["hold_report_id"] = "forged"
        with pytest.raises(ValueError):
            EconomicLedger(repo).calculate(scenario)


def test_existing_model_instances_are_revalidated_at_calculation_boundary():
    scenario = EconomicScenario.model_validate(base())
    repo = TrustedTestRepository(scenario)
    forged = scenario.opening_cash.model_copy(update={"value": "NaN"})
    with pytest.raises(ValidationError):
        EconomicLedger(repo).calculate(scenario.model_copy(update={"opening_cash": forged}))


def test_scenario_and_economic_context_ids_must_match():
    data = base(scenario_market_context={"kind": "unavailable", "hold_report_id": "another-hold"})
    with pytest.raises(ValueError):
        run(data)


def test_sales_require_same_kst_day_and_ordered_transfer_events():
    for changes in ({"inspection_at": T(16)}, {"delivery_at": T(15, 1)},
                    {"recognized_at": T(15, 3)}):
        data = base()
        data["sales"][0].update(changes)
        with pytest.raises(ValueError):
            run(data)


def test_cull_disposal_is_linked_and_cannot_create_saleable_stock():
    data = base()
    data["cull_disposals"][0]["quantity"]["value"] = "3"
    with pytest.raises(ValueError):
        run(data)
    data = base()
    data["cull_disposals"][0]["cull_id"] = "other-cull"
    with pytest.raises(ValueError):
        run(data)
    assert run().closing_inventory == {("batch-1", "grade-1", "direct"): Decimal("3")}


def test_production_cost_is_not_charged_again_when_old_inventory_sells():
    data = base(harvests=(), packouts=(), culls=(), cull_disposals=(), variable_costs=(),
                opening_inventory=(opening_lot(),))
    result = run(data)
    assert result.variable_cost == Decimal("0")
    assert result.revenue == Decimal("500")
    assert result.management_oi == Decimal("500")
    assert result.closing_inventory == {("batch-1", "grade-1", "direct"): Decimal("0")}
    assert result.closing_inventory_cost_by_batch == {"batch-1": Decimal("0.00")}


def test_opening_batch_cost_link_is_verified_in_trusted_repository():
    data = base(harvests=(), packouts=(), culls=(), cull_disposals=(), variable_costs=(),
                opening_inventory=(opening_lot(),))
    scenario = EconomicScenario.model_validate(data)
    for mutation in ("missing", "foreign", "grade", "late"):
        repo = TrustedTestRepository(scenario)
        record = repo.prior_costs["prior-batch-cost"]
        if mutation == "missing":
            repo.prior_costs.clear()
        elif mutation == "foreign":
            record["tenant_id"] = "tenant-2"
        elif mutation == "grade":
            record["grade"] = "other"
        else:
            record["available_at"] = T(1)
        with pytest.raises(ValueError):
            EconomicLedger(repo).calculate(scenario)


def test_over_sale_or_unlinked_opening_batch_fails_closed():
    data = base()
    data["sales"][0]["quantity"]["value"] = "9"
    with pytest.raises(ValueError):
        run(data)
    data = base(opening_inventory=({"grade": "grade-1", "batch_id": "other-batch", "channel": "direct",
                                   "prior_cost_ref": None, "quantity": n(1, "opening")},))
    assert run(data).closing_inventory is None


def test_asset_and_debt_events_need_declared_matching_accounts():
    data = base(capex=({"id": "purchase", "at": T(28), "asset_id": "asset-1",
                        "amount": n(200, "purchase", "KRW")},))
    with pytest.raises(ValueError):
        run(data)
    data = base(loan_draws=({"id": "draw", "at": T(29), "loan_id": "loan-1",
                             "amount": n(100, "loan-draw", "KRW")},))
    with pytest.raises(ValueError):
        run(data)


def test_principal_cannot_exceed_declared_opening_debt_plus_draws():
    data = base(debt_accounts=({"id": "loan-1", "opening_principal": n(0, "loan-opening", "KRW")},),
                principal_payments=({"id": "principal", "at": T(29), "loan_id": "loan-1",
                                     "amount": n(1, "principal", "KRW")},))
    with pytest.raises(ValueError):
        run(data)


@pytest.mark.parametrize("change", ["collection_date", "recognition_date", "cost_batch_link",
                                    "cost_incurred_date"])
def test_owned_scenario_pin_rejects_changed_dates_and_event_links(change):
    scenario = EconomicScenario.model_validate(base())
    repo = TrustedTestRepository(scenario)
    data = base()
    if change == "collection_date":
        data["collections"][0]["at"] = T(22)
    elif change == "recognition_date":
        data["sales"][0]["recognized_at"] = T(15, 6)
    elif change == "cost_incurred_date":
        data["variable_costs"][1]["incurred_at"] = T(15, 1)
    else:
        data["variable_costs"][1]["batch_id"] = "batch-1"
    with pytest.raises(ValueError, match="scenario pin"):
        EconomicLedger(repo).calculate(EconomicScenario.model_validate(data))


@pytest.mark.parametrize("mutation", ["method", "missing", "foreign", "decision", "revision",
                                          "payload", "job_hash", "job_ref", "mutable"])
def test_scenario_pin_fails_closed_for_missing_foreign_or_unbound_job_input(mutation):
    scenario = EconomicScenario.model_validate(base())
    repo = TrustedTestRepository(scenario)
    if mutation == "method":
        repo.get_economic_scenario_pin = None
    elif mutation == "missing":
        repo.get_economic_scenario_pin = lambda *_: None
    elif mutation == "foreign":
        repo.scenario_pin["tenant_id"] = "tenant-2"
    elif mutation == "decision":
        repo.scenario_pin["decision_at"] = T(1)
    elif mutation == "revision":
        repo.scenario_pin["scenario_revision"] = "r2"
    elif mutation == "payload":
        repo.scenario_pin["payload_sha256"] = "0" * 64
    elif mutation == "job_hash":
        repo.scenario_pin["immutable_job_input_sha256"] = "0" * 64
    elif mutation == "job_ref":
        repo.scenario_pin["immutable_job_input_ref"] = ""
    else:
        repo.scenario_pin["immutable"] = False
    with pytest.raises(ValueError, match="scenario pin"):
        EconomicLedger(repo).calculate(scenario)


def test_unlinked_zero_opening_stock_holds_all_sale_dependent_results():
    data = base(harvests=(), packouts=(), culls=(), cull_disposals=(), variable_costs=(),
                opening_inventory=({"grade": None, "batch_id": None, "channel": None,
                                    "prior_cost_ref": None, "quantity": n(0, "unknown-opening")},))
    result = run(data)
    assert result.gross_sales == Decimal("500")
    assert result.recognized_kg == Decimal("5")
    assert result.sales_totals_status == "unverified_input_arithmetic"
    assert result.variable_cost == Decimal("0")
    assert result.closing_inventory is None
    assert result.revenue is None and result.management_oi is None
    assert result.operating_cash is None and result.business_cash is None and result.equity_cash is None
    assert result.monthly_cash is None
    assert all(value is None for value in result.target_values.values())
    assert "OPENING_INVENTORY_LINKAGE_UNKNOWN" in result.hold_reasons


def test_result_identity_changes_with_formula_version(monkeypatch):
    original = run()
    monkeypatch.setattr(economics, "FORMULA_VERSION", "economic-ledger-v7-test")
    changed = run()
    assert original.result_id != changed.result_id


def test_opening_lot_cost_is_pinned_and_allocated_without_recharging_production():
    data = base(harvests=(), packouts=(), culls=(), cull_disposals=(),
                variable_costs=(), opening_inventory=({
                    "grade": "grade-1", "batch_id": "batch-1", "channel": "direct",
                    "prior_cost_ref": "prior-batch-cost", "quantity": n(10, "opening-stock"),
                    "prior_cost_amount": n(200, "prior-cost", "KRW"),
                    "allocation_basis": n(10, "prior-basis"),
                    "allocation_policy": "proportional_saleable_kg_v1",
                },))
    result = run(data)
    assert result.closing_inventory_cost_by_batch == {"batch-1": Decimal("100")}
    assert result.variable_cost == Decimal("0")
    assert result.management_oi == Decimal("500")
    changed = base(**{**data, "opening_inventory": ({**data["opening_inventory"][0],
        "prior_cost_amount": n(20, "prior-cost", "KRW")},)})
    assert run(changed).scenario_sha256 != result.scenario_sha256
    assert run(changed).closing_inventory_cost_by_batch == {"batch-1": Decimal("10")}


def test_opening_cost_owned_record_rejects_mismatched_amount_and_basis():
    data = base(harvests=(), packouts=(), culls=(), cull_disposals=(),
                variable_costs=(), opening_inventory=({
                    "grade": "grade-1", "batch_id": "batch-1", "channel": "direct",
                    "prior_cost_ref": "prior-batch-cost", "quantity": n(5, "opening-stock"),
                    "prior_cost_amount": n(200, "prior-cost", "KRW"),
                    "allocation_basis": n(5, "prior-basis"),
                    "allocation_policy": "proportional_saleable_kg_v1",
                },))
    scenario = EconomicScenario.model_validate(data)
    for field, value in (("cost_amount", "999"), ("allocation_basis_kg", "9"),
                         ("rights", "no_use")):
        repo = TrustedTestRepository(scenario)
        repo.prior_costs["prior-batch-cost"][field] = value
        with pytest.raises(ValueError):
            EconomicLedger(repo).calculate(scenario)


def test_current_batch_remaining_cost_uses_current_production_inputs_once():
    result = run()
    assert result.closing_inventory_cost_by_batch == {"batch-1": Decimal("7.50")}
    assert result.variable_cost == Decimal("25")


def test_batch_linked_sale_cost_is_expensed_without_entering_closing_inventory():
    data = base()
    data["variable_costs"][0].update(purpose="production", sale_id=None)
    data["variable_costs"][1].update(purpose="sale", sale_id="sale-1", batch_id="batch-1")
    result = run(data)
    assert result.closing_inventory_cost_by_batch == {"batch-1": Decimal("7.50")}
    assert result.variable_cost == Decimal("25")
    assert result.management_oi == Decimal("475")


def test_pre_dispatch_packaging_is_sale_cost_in_v_not_closing_inventory():
    data = base()
    data["variable_costs"] += ({
        "id": "packaging", "purpose": "sale", "batch_id": "batch-1",
        "sale_id": "sale-1", "incurred_at": T(15, 1),
        "quantity": n(5, "packaging-q"), "unit_cost": n(2, "packaging-rate", "KRW/kg"),
        "paid_at": T(23), "payment": n(10, "packaging-paid", "KRW"),
    },)
    result = run(data)
    assert result.variable_cost == Decimal("35")
    assert result.management_oi == Decimal("465")
    assert result.closing_inventory_cost_by_batch == {"batch-1": Decimal("7.50")}
    assert result.scenario_sha256 == canonical_scenario_sha256(EconomicScenario.model_validate(data))
    assert result.scenario_sha256 != run().scenario_sha256
    assert {"packaging-q", "packaging-rate", "packaging-paid"}.issubset(
        {item.input_id for item in result.input_provenance})


def test_sale_cost_incurrence_still_must_be_in_evaluation_period():
    data = base()
    data["variable_costs"][1]["incurred_at"] = T(15, 1).replace(month=12)
    with pytest.raises(ValueError, match="outside evaluation period"):
        run(data)


def test_cost_purpose_is_required_and_links_follow_purpose_matrix():
    data = base()
    del data["variable_costs"][0]["purpose"]
    with pytest.raises(ValidationError, match="purpose"):
        EconomicScenario.model_validate(data)
    data["variable_costs"][0].update(purpose="production", sale_id=None)
    data["variable_costs"][1].update(purpose="sale", sale_id="sale-1")
    assert EconomicScenario.model_validate(data)
    del data["variable_costs"][0]["sale_id"]
    with pytest.raises(ValidationError, match="sale_id"):
        EconomicScenario.model_validate(data)
    for change in ({"purpose": "production", "sale_id": "sale-1"},
                   {"purpose": "production", "batch_id": None},
                   {"purpose": "sale", "sale_id": None},
                   {"purpose": "period", "batch_id": "batch-1"},
                   {"purpose": "period", "sale_id": "sale-1"}):
        invalid = base()
        invalid["variable_costs"][0].update(purpose="production", sale_id=None)
        invalid["variable_costs"][1].update(purpose="sale", sale_id="sale-1")
        invalid["variable_costs"][0].update(change)
        with pytest.raises(ValidationError):
            EconomicScenario.model_validate(invalid)


def test_old_scenario_schema_version_is_rejected_after_cost_shape_change():
    data = base(schema_version="1")
    with pytest.raises(ValidationError, match="schema_version"):
        EconomicScenario.model_validate(data)


def test_production_cost_needs_a_harvested_batch():
    data = base()
    data["variable_costs"][0]["batch_id"] = "missing-batch"
    with pytest.raises(ValueError, match="production batch cost"):
        run(data)


@pytest.mark.parametrize("change", [
    {"sale_id": "missing-sale"},
    {"batch_id": "other-batch"},
])
def test_sale_cost_needs_existing_sale_and_matching_batch(change):
    data = base()
    data["variable_costs"][0].update(purpose="production", sale_id=None)
    data["variable_costs"][1].update(purpose="sale", sale_id="sale-1", batch_id="batch-1")
    data["variable_costs"][1].update(change)
    with pytest.raises(ValueError, match="sale cost"):
        run(data)


def test_all_culled_batch_has_zero_inventory_cost_and_period_expense():
    data = base(packouts=(), sales=(), collections=())
    data["culls"][0]["quantity"]["value"] = "10"
    data["cull_disposals"][0]["quantity"]["value"] = "10"
    data["variable_costs"] = (data["variable_costs"][0],)
    result = run(data)
    assert result.closing_inventory_cost_by_batch == {"batch-1": Decimal("0")}
    assert result.variable_cost == Decimal("20")
    assert result.revenue == Decimal("0")
    assert result.management_oi == Decimal("-20")


def test_batch_linked_fixed_production_cost_is_reported_in_remaining_inventory():
    data = base(fixed_costs=(
        {"id": "batch-labor", "purpose": "production", "batch_id": "batch-1",
         "sale_id": None, "incurred_at": T(15),
         "quantity": n(1, "labor-month", "month"),
         "unit_cost": n(40, "labor-rate", "KRW/month"),
         "paid_at": T(21), "payment": n(40, "labor-paid", "KRW")},
        {"id": "shared-rent", "purpose": "period", "batch_id": None,
         "sale_id": None, "incurred_at": T(15),
         "quantity": n(1, "rent-month", "month"),
         "unit_cost": n(10, "rent-rate", "KRW/month"),
         "paid_at": T(21), "payment": n(10, "rent-paid", "KRW")},
    ))
    result = run(data)
    assert result.closing_inventory_cost_by_batch == {"batch-1": Decimal("22.50")}
    assert result.variable_cost == Decimal("25")
    assert result.fixed_cost == Decimal("50")
    assert result.management_oi == Decimal("425")


def test_undeclared_fixed_cost_holds_closing_inventory_cost():
    result = run(base(fixed_costs=None))
    assert "FIXED_COSTS_UNDECLARED" in result.hold_reasons
    assert result.closing_inventory_cost_by_batch is None


def test_opening_lots_reject_duplicate_and_current_batch_overlap():
    lot = opening_lot()
    second = {**lot, "prior_cost_ref": "prior-batch-cost-2",
              "quantity": n(5, "opening-stock-2"),
              "prior_cost_amount": n(200, "prior-cost-2", "KRW"),
              "allocation_basis": n(5, "prior-basis-2")}
    with pytest.raises(ValueError, match="overlaps or duplicates"):
        run(base(harvests=(), packouts=(), culls=(), cull_disposals=(),
                 variable_costs=(), opening_inventory=(lot, second)))
    with pytest.raises(ValueError, match="overlaps or duplicates"):
        run(base(opening_inventory=(lot,)))


def test_linked_opening_lot_without_cost_holds_sale_results():
    incomplete = {key: value for key, value in opening_lot().items()
                  if key not in {"prior_cost_amount", "allocation_basis", "allocation_policy"}}
    result = run(base(harvests=(), packouts=(), culls=(), cull_disposals=(),
                      variable_costs=(), opening_inventory=(incomplete,)))
    assert "OPENING_INVENTORY_COST_UNKNOWN" in result.hold_reasons
    assert result.closing_inventory_cost_by_batch is None
    assert result.revenue is None and result.management_oi is None
