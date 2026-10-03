"""Whole-ledger regression for a self-authored joint demand/supply/macro stress."""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from test_economics import T, n
from test_market_scenario import case, digest, edit, replacement, repin_shock, service, sidecar, two_lane_case
from app.economic_contracts import EconomicScenario
from app.economics import EconomicLedger, canonical_scenario_sha256
from app.market_scenario import settlement_path_sha256


def refresh_binding(repo, request):
    baseline = deepcopy(repo.scenarios[("scenario-1", "r1")])
    shock = repo.shocks[("joint-1", "r1")]
    for driver in shock["drivers"]:
        for change in driver["changes"]:
            event = next(item for item in baseline[change["event_group"]]
                         if item["id"] == change["event_id"])
            event[change["field"]] = change.get("number", change.get("time", change.get("reference")))
    binding = repo.bindings[("binding-1", "r2")]
    binding["path_sha256"] = settlement_path_sha256(EconomicScenario.model_validate(baseline), "sale-1")
    shock["settlement_bindings"][0]["sha256"] = digest(binding)
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)


def linked_return_case():
    repo, request = case()
    baseline_data = repo.scenarios[("scenario-1", "r1")]
    returned = {"id": "return-1", "sale_id": "sale-1", "at": T(23),
                "quantity": n(1, "return-q"), "disposition": "disposed",
                "refund": n(50, "refund", "KRW"), "refund_paid_at": T(24)}
    baseline_data["returns"] = (returned,)
    baseline_data["zero_declarations"] = tuple(
        item for item in baseline_data["zero_declarations"] if item["group"] != "returns")
    baseline = EconomicScenario.model_validate(baseline_data)
    baseline_hash = canonical_scenario_sha256(baseline)
    repo.pins[("scenario-1", "r1")]["payload_sha256"] = baseline_hash
    repo.pins[("scenario-1", "r1")]["immutable_job_input_sha256"] = baseline_hash
    request["baseline"]["sha256"] = baseline_hash
    repo.shocks[("joint-1", "r1")]["baseline_sha256"] = baseline_hash
    for value in (returned["quantity"], returned["refund"]):
        repo.records[(value["input_id"], value["revision"])] = {
            **value, "tenant_id": "tenant-1", "scope_start": baseline.period_start,
            "scope_end": baseline.period_end,
        }
        repo.rights[(value["input_id"], value["revision"])] = sidecar(value)
    refresh_binding(repo, request)
    return repo, request


@pytest.mark.parametrize("change", [
    lambda item: item["refund"].update(value="80"),
    lambda item: item.update(at=T(23, 1)),
    lambda item: item.update(refund_paid_at=T(25)),
    lambda item: item["quantity"].update(value="2"),
    lambda item: item.update(disposition="resaleable"),
    lambda item: item["refund"].update(revision="r2"),
])
def test_settlement_path_binds_every_linked_return_field(change):
    repo, _ = linked_return_case()
    baseline = deepcopy(repo.scenarios[("scenario-1", "r1")])
    changed = deepcopy(baseline)
    change(changed["returns"][0])
    assert settlement_path_sha256(EconomicScenario.model_validate(changed), "sale-1") != (
        settlement_path_sha256(EconomicScenario.model_validate(baseline), "sale-1"))


def test_changed_return_refund_rejects_stale_setoff_applicability():
    repo, request = linked_return_case()
    shock = repo.shocks[("joint-1", "r1")]
    refund = replacement(80, "refund", "KRW")
    shock["drivers"][1]["changes"].append(
        edit("returns", "return-1", "refund", number=refund))
    repo.rights[("refund", "r2")] = sidecar(refund)
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError, match="applicability"):
        service(repo).build_candidate(request, "tenant-1")
    assert repo.candidates == {}


def test_refreshed_return_binding_preserves_conditional_ledger_and_rate_hold():
    repo, request = linked_return_case()
    shock = repo.shocks[("joint-1", "r1")]
    refund = replacement(80, "refund", "KRW")
    shock["drivers"][1]["changes"].append(
        edit("returns", "return-1", "refund", number=refund))
    repo.rights[("refund", "r2")] = sidecar(refund)
    evidence = deepcopy(repo.settlements[("self-authored-settlement-1", "r2")])
    evidence["revision"] = "r3"
    evidence["raw_sha256"] = digest({key: value for key, value in evidence.items()
                                     if key != "raw_sha256"})
    repo.settlements[("self-authored-settlement-1", "r3")] = evidence
    for change in shock["drivers"][2]["changes"]:
        if change["field"] == "evidence_revision":
            change["reference"] = "r3"
        elif change["field"] == "evidence_sha256":
            change["reference"] = evidence["raw_sha256"]
    binding = repo.bindings[("binding-1", "r2")]
    binding["evidence_revision"] = "r3"
    binding["evidence_sha256"] = evidence["raw_sha256"]
    refresh_binding(repo, request)
    candidate = service(repo).build_candidate(request, "tenant-1")
    result = service(repo).calculate_pinned(candidate.scenario_id, candidate.revision, "tenant-1")
    ledger = result.economic_result
    assert (ledger.gross_sales, ledger.revenue, ledger.variable_cost, ledger.management_oi) == (
        Decimal(810), Decimal(640), Decimal(144), Decimal(496))
    assert ledger.operating_cash == ledger.operating_cash_bridge == Decimal(496)
    assert ledger.receivable_end == ledger.operating_payable_end == Decimal(0)
    assert ledger.sale_net_remittances[0].per_kg is None
    assert ledger.sale_net_remittances[0].hold_reason == "RETURN_PRESENT"
    assert result.assessment_status == "hold"
    assert not hasattr(result, "verified_net_p")


def test_joint_path_delegates_arithmetic_and_never_claims_verified_price():
    repo, request = case()
    candidate = service(repo).build_candidate(request, "tenant-1")
    result = service(repo).calculate_pinned(candidate.scenario_id, candidate.revision, "tenant-1")
    ledger = result.economic_result
    assert ledger.closing_inventory == {("batch-1", "grade-1", "direct"): Decimal(3)}
    assert (ledger.harvest_kg, ledger.packout_kg, ledger.recognized_kg) == (12, 12, 9)
    assert (ledger.gross_sales, ledger.revenue, ledger.variable_cost) == (810, 720, 144)
    assert (ledger.management_oi, ledger.operating_cash) == (576, 576)
    inputs = {(item.input_id, item.revision): item.value for item in ledger.input_provenance}
    assert inputs[("production-paid", "r2")] == "60"
    assert inputs[("separate-paid", "r1")] == "30"
    assert inputs[("fee-amount", "r2")] == "54"
    assert repo.get_settlement_evidence("self-authored-settlement-1", "r2")["raw_sha256"] == (
        repo.get_economic_scenario(candidate.scenario_id, candidate.revision)["setoffs"][0]["evidence_sha256"])
    assert (ledger.sale_net_remittances[0].per_kg,
            ledger.sale_net_remittances[0].status) == (Decimal(74), "conditional_user_assumption")
    assert result.assessment_status == "hold"
    assert result.calculation_status == "conditional_user_assumption"
    assert result.economic_scenario_sha256 == candidate.economic_scenario_sha256
    assert result.rights_manifest_sha256 == candidate.rights_manifest_sha256
    assert result.binding_manifest_sha256 == candidate.binding_manifest_sha256
    assert result.result_id and result.economic_result.result_id in result.economic_result_ids
    assert not hasattr(result, "verified_net_p")
    assert not hasattr(result, "predicted_margin")
    assert not hasattr(result, "ranking")


def test_harvest_packout_and_sale_inventory_are_checked_by_ledger():
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    h = shock["drivers"][0]["changes"][0]["number"]
    h["value"] = "11"
    repo.rights[("h", "r2")] = sidecar(h)
    refresh_binding(repo, request)
    candidate = service(repo).build_candidate(request, "tenant-1")
    with pytest.raises(ValueError):
        service(repo).calculate_pinned(candidate.scenario_id, candidate.revision, "tenant-1")


@pytest.mark.parametrize("driver_index,change_index,input_id,new_value", [
    (1, 1, "price", "91"),
    (1, 2, "discount", "91"),
    (1, 3, "collection", "665"),
    (2, 3, "fee-amount", "55"),
])
def test_stale_setoff_applicability_is_rejected(driver_index, change_index, input_id, new_value):
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    changed = shock["drivers"][driver_index]["changes"][change_index]["number"]
    changed["value"] = new_value
    repo.rights[(input_id, "r2")] = sidecar(changed)
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError, match="applicability"):
        service(repo).build_candidate(request, "tenant-1")


def test_double_paid_fee_with_setoff_is_rejected():
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    payment = replacement(54, "fee-paid", "KRW")
    shock["drivers"][2]["changes"].extend([
        {"event_group": "variable_costs", "event_id": "fee", "field": "payment", "number": payment},
        {"event_group": "variable_costs", "event_id": "fee", "field": "paid_at", "time": T(21)},
    ])
    repo.rights[("fee-paid", "r2")] = sidecar(payment)
    refresh_binding(repo, request)
    candidate = service(repo).build_candidate(request, "tenant-1")
    with pytest.raises(ValueError, match="setoff|payment"):
        service(repo).calculate_pinned(candidate.scenario_id, candidate.revision, "tenant-1")


@pytest.mark.parametrize("amount,when,expected_reason", [
    ("600", T(22), "COLLECTION_INCOMPLETE"),
    ("666", datetime(2026, 11, 1, tzinfo=timezone.utc), "COLLECTION_AFTER_PERIOD"),
])
def test_partial_or_future_collection_holds_only_sale_rate(amount, when, expected_reason):
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    collection = shock["drivers"][1]["changes"][3]
    if when == T(22):
        collection["number"]["value"] = amount
        repo.rights[("collection", "r2")] = sidecar(collection["number"])
    else:
        shock["drivers"][1]["changes"].append({"event_group": "collections",
            "event_id": "collection-1", "field": "at", "time": when})
    refresh_binding(repo, request)
    candidate = service(repo).build_candidate(request, "tenant-1")
    result = service(repo).calculate_pinned(candidate.scenario_id, candidate.revision, "tenant-1")
    rate = result.economic_result.sale_net_remittances[0]
    assert rate.per_kg is None and rate.hold_reason == expected_reason
    assert result.economic_result.revenue == Decimal(720)
    assert expected_reason in result.hold_reasons
    if expected_reason == "COLLECTION_INCOMPLETE":
        assert result.economic_result.receivable_end == Decimal(66)
    else:
        assert result.economic_result.receivable_end == Decimal(666)
        assert result.economic_result.future_cash_schedule[0].event_id == "collection-1"


def test_missing_edited_path_returns_explicit_hold_without_inventing_event():
    repo, request = case()
    baseline_data = repo.scenarios[("scenario-1", "r1")]
    baseline_data["collections"] = None
    baseline_hash = canonical_scenario_sha256(EconomicScenario.model_validate(baseline_data))
    repo.pins[("scenario-1", "r1")]["payload_sha256"] = baseline_hash
    repo.pins[("scenario-1", "r1")]["immutable_job_input_sha256"] = baseline_hash
    request["baseline"]["sha256"] = baseline_hash
    shock = repo.shocks[("joint-1", "r1")]
    shock["baseline_sha256"] = baseline_hash
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    result = service(repo).build_candidate(request, "tenant-1")
    assert result.status == "hold"
    assert "UNSUPPORTED_PATH" in result.hold_reasons
    assert repo.candidates == {}


def test_sale_cannot_exceed_packout_even_with_larger_assumed_cap():
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    sale = shock["drivers"][1]["changes"][0]["number"]
    sale["value"] = "13"
    repo.rights[("s", "r2")] = sidecar(sale)
    cap = shock["contract_caps"][0]["accepted_kg"]
    cap["value"] = "15"
    repo.rights[("cap-kg", "r2")] = sidecar(cap)
    refresh_binding(repo, request)
    candidate = service(repo).build_candidate(request, "tenant-1")
    with pytest.raises(ValueError, match="stock"):
        service(repo).calculate_pinned(candidate.scenario_id, candidate.revision, "tenant-1")


def test_collection_before_recognition_is_rejected():
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    shock["drivers"][1]["changes"].append({"event_group": "collections",
        "event_id": "collection-1", "field": "at", "time": T(14)})
    refresh_binding(repo, request)
    candidate = service(repo).build_candidate(request, "tenant-1")
    with pytest.raises(ValueError, match="DISCOUNT_AFTER_COLLECTION|earlier recognized sale"):
        service(repo).calculate_pinned(candidate.scenario_id, candidate.revision, "tenant-1")


def test_paired_lane_references_move_packout_and_sale_without_mutating_baseline():
    repo, request = two_lane_case()
    baseline_before = deepcopy(repo.scenarios[("scenario-1", "r1")])
    baseline_pin_before = deepcopy(repo.pins[("scenario-1", "r1")])
    baseline_ledger = EconomicLedger(repo).calculate(EconomicScenario.model_validate(baseline_before))
    candidate = service(repo).build_candidate(request, "tenant-1")
    derived = repo.get_economic_scenario(candidate.scenario_id, candidate.revision)
    result = service(repo).calculate_pinned(candidate.scenario_id, candidate.revision, "tenant-1")
    ledger = result.economic_result
    assert repo.scenarios[("scenario-1", "r1")] == baseline_before
    assert repo.pins[("scenario-1", "r1")] == baseline_pin_before
    assert [(p["grade"], p["channel"], p["quantity"]["value"]) for p in baseline_before["packouts"]] == [
        ("grade-1", "direct", "10"), ("grade-2", "wholesale", "2")]
    assert (baseline_ledger.gross_sales, baseline_ledger.revenue, baseline_ledger.management_oi,
            baseline_ledger.operating_cash, baseline_ledger.sale_net_remittances[0].per_kg) == (
        Decimal(1000), Decimal(900), Decimal(770), Decimal(770), Decimal(84))
    assert [(p["grade"], p["channel"], p["quantity"]["value"]) for p in derived["packouts"]] == [
        ("grade-2", "wholesale", "3"), ("grade-2", "wholesale", "9")]
    assert (derived["sales"][0]["grade"], derived["sales"][0]["channel"]) == (
        "grade-2", "wholesale")
    assert (ledger.harvest_kg, ledger.packout_kg, ledger.recognized_kg) == (
        Decimal(12), Decimal(12), Decimal(9))
    assert ledger.closing_inventory == {("batch-1", "grade-2", "wholesale"): Decimal(3)}
    assert (ledger.gross_sales, ledger.revenue, ledger.variable_cost, ledger.management_oi) == (
        Decimal(810), Decimal(720), Decimal(144), Decimal(576))
    assert (ledger.operating_cash, ledger.operating_cash_bridge, ledger.receivable_end) == (
        Decimal(576), Decimal(576), Decimal(0))
    assert (ledger.sale_net_remittances[0].per_kg, ledger.sale_net_remittances[0].status) == (
        Decimal(74), "conditional_user_assumption")
    assert candidate.economic_scenario_sha256 == canonical_scenario_sha256(EconomicScenario.model_validate(derived))
    assert result.assessment_status == "hold" and not hasattr(result, "verified_net_p")


def test_unknown_opening_inventory_returns_explicit_lane_hold_before_pin():
    repo, request = two_lane_case()
    baseline_data = repo.scenarios[("scenario-1", "r1")]
    baseline_data["opening_inventory"] = None
    baseline_data["zero_declarations"] = tuple(
        item for item in baseline_data["zero_declarations"]
        if item["group"] != "opening_inventory")
    baseline = EconomicScenario.model_validate(baseline_data)
    baseline_hash = canonical_scenario_sha256(baseline)
    repo.pins[("scenario-1", "r1")].update(
        payload_sha256=baseline_hash, immutable_job_input_sha256=baseline_hash)
    request["baseline"]["sha256"] = baseline_hash
    shock = repo.shocks[("joint-1", "r1")]
    shock["baseline_sha256"] = baseline_hash
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)

    baseline_ledger = EconomicLedger(repo).calculate(baseline)
    assert baseline_ledger.closing_inventory is None
    assert baseline_ledger.revenue is None and baseline_ledger.management_oi is None
    assert baseline_ledger.sale_net_remittances[0].hold_reason == "INVENTORY_UNRECONCILED"
    result = service(repo).build_candidate(request, "tenant-1")
    assert result.status == "hold"
    assert result.hold_reasons == ("INVENTORY_UNRESOLVED",)
    assert result.market_context.kind == "unavailable"
    assert result.market_context.hold_report_id == "hold-1"
    assert not hasattr(result, "candidate_id")
    assert not hasattr(result, "economic_result")
    assert not hasattr(result, "revenue")
    assert not hasattr(result, "management_oi")
    assert repo.candidates == {}
    assert set(repo.scenarios) == {("scenario-1", "r1")}


def test_unknown_opening_inventory_without_lane_edits_holds_before_pin():
    repo, request = case()
    baseline_data = repo.scenarios[("scenario-1", "r1")]
    baseline_data["opening_inventory"] = None
    baseline_data["zero_declarations"] = tuple(
        item for item in baseline_data["zero_declarations"]
        if item["group"] != "opening_inventory")
    baseline = EconomicScenario.model_validate(baseline_data)
    baseline_hash = canonical_scenario_sha256(baseline)
    repo.pins[("scenario-1", "r1")].update(
        payload_sha256=baseline_hash, immutable_job_input_sha256=baseline_hash)
    request["baseline"]["sha256"] = baseline_hash
    shock = repo.shocks[("joint-1", "r1")]
    assert all(change["field"] not in {"grade", "channel"}
               for driver in shock["drivers"] for change in driver["changes"])
    shock["baseline_sha256"] = baseline_hash
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)

    baseline_ledger = EconomicLedger(repo).calculate(baseline)
    assert baseline_ledger.closing_inventory is None
    assert baseline_ledger.revenue is None and baseline_ledger.management_oi is None
    assert baseline_ledger.sale_net_remittances[0].hold_reason == "INVENTORY_UNRECONCILED"
    result = service(repo).build_candidate(request, "tenant-1")
    assert result.status == "hold"
    assert result.hold_reasons == ("INVENTORY_UNRESOLVED",)
    assert result.market_context.kind == "unavailable"
    assert result.market_context.hold_report_id == "hold-1"
    assert not hasattr(result, "candidate_id")
    assert not hasattr(result, "economic_result")
    assert not hasattr(result, "revenue")
    assert not hasattr(result, "management_oi")
    assert repo.candidates == {}
    assert set(repo.scenarios) == {("scenario-1", "r1")}
    assert set(repo.pins) == {("scenario-1", "r1")}


@pytest.mark.parametrize("break_path", ["stranded_sale", "overallocated_packout"])
def test_invalid_revised_lane_inventory_is_rejected_before_pin(break_path):
    repo, request = two_lane_case()
    shock = repo.shocks[("joint-1", "r1")]
    if break_path == "stranded_sale":
        for change in shock["drivers"][1]["changes"]:
            if change["field"] in ("grade", "channel"):
                change["reference"] = "grade-1" if change["field"] == "grade" else "direct"
        shock["contract_caps"][0].update(grade="grade-1", channel="direct")
        refresh_binding(repo, request)
    else:
        moved = next(change["number"] for change in shock["drivers"][0]["changes"]
                     if change["event_id"] == "pack-2" and change["field"] == "quantity")
        moved["value"] = "10"
        repo.rights[("p-2", "r2")] = sidecar(moved)
        request["shock"]["sha256"] = digest(shock)
        repin_shock(repo)
    with pytest.raises(ValueError, match="stock|harvest|packout"):
        service(repo).build_candidate(request, "tenant-1")
    assert repo.candidates == {}


def test_sale_lane_edit_rejects_stale_settlement_applicability():
    old_repo, _ = case()
    old_path = old_repo.bindings[("binding-1", "r2")]["path_sha256"]
    repo, request = two_lane_case()
    assert repo.bindings[("binding-1", "r2")]["path_sha256"] != old_path
    binding = repo.bindings[("binding-1", "r2")]
    binding["path_sha256"] = old_path
    shock = repo.shocks[("joint-1", "r1")]
    shock["settlement_bindings"][0]["sha256"] = digest(binding)
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError, match="applicability"):
        service(repo).build_candidate(request, "tenant-1")
    assert repo.candidates == {}
