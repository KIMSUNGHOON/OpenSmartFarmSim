"""Finite-grid break-even trials rerun the pinned joint market and ledger path."""

from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.break_even import (BreakEvenService, canonical_request_sha256,
                            fixed_shock_sha256, fixed_trial_sha256)
from app.economic_contracts import EconomicScenario
from app.market_scenario import settlement_path_sha256
from test_market_scenario import case, digest, service, sidecar


def trial_plan(values, *, target="oi", variable="KRW/kg", vary_cap=False,
               collection_overrides=None):
    repo, template = case()
    baseline = EconomicScenario.model_validate(repo.scenarios[("scenario-1", "r1")])
    sale = baseline.sales[0]
    refs = []
    fixed_hash = None
    fixed_shock_hash = None
    for index, value in enumerate(values):
        shock = deepcopy(repo.shocks[("joint-1", "r1")])
        shock_id = f"joint-trial-{index}"
        shock["shock_id"] = shock_id
        if vary_cap and index == 1:
            cap_number = shock["contract_caps"][0]["accepted_kg"]
            cap_number["value"] = "11"
            cap_number["revision"] = "r-cap-1"
            repo.rights[("cap-kg", "r-cap-1")] = sidecar(cap_number)
        sale_kg = Decimal(value) if variable == "kg" else Decimal(9)
        price = Decimal(value) if variable == "KRW/kg" else Decimal(90)
        collection = sale_kg * price - Decimal(144)
        if collection_overrides and index in collection_overrides:
            collection = Decimal(collection_overrides[index])
        for change in shock["drivers"][1]["changes"]:
            if (change["event_group"], change["field"]) == (
                    "sales", "price" if variable == "KRW/kg" else "quantity"):
                change["number"]["value"] = str(value)
                change["number"]["revision"] = f"r-variable-{index}"
                input_id = "price" if variable == "KRW/kg" else "s"
                repo.rights[(input_id, f"r-variable-{index}")] = sidecar(change["number"])
            elif (change["event_group"], change["field"]) == ("collections", "amount"):
                change["number"]["value"] = str(collection)
                change["number"]["revision"] = f"r-collection-{index}"
                repo.rights[("collection", f"r-collection-{index}")] = sidecar(change["number"])
        revised = deepcopy(repo.scenarios[("scenario-1", "r1")])
        for driver in shock["drivers"]:
            for change in driver["changes"]:
                event = next(item for item in revised[change["event_group"]]
                             if item["id"] == change["event_id"])
                event[change["field"]] = change.get("number", change.get("time", change.get("reference")))
        binding = deepcopy(repo.bindings[("binding-1", "r2")])
        binding["binding_id"] = f"binding-trial-{index}"
        binding["path_sha256"] = settlement_path_sha256(
            EconomicScenario.model_validate(revised), "sale-1")
        repo.bindings[(binding["binding_id"], "r2")] = binding
        shock["settlement_bindings"] = [{"binding_id": binding["binding_id"],
                                          "revision": "r2", "sha256": digest(binding)}]
        repo.shocks[(shock_id, "r1")] = deepcopy(shock)
        repo.shock_pins[(shock_id, "r1")] = {"shock_id": shock_id, "revision": "r1",
                                                "tenant_id": "tenant-1", "sha256": digest(shock),
                                                "immutable": True}
        trial_request = deepcopy(template)
        trial_request["shock"] = {"shock_id": shock_id, "revision": "r1",
                                  "sha256": digest(shock)}
        candidate = service(repo).build_candidate(trial_request, "tenant-1")
        assert candidate.status == "pinned"
        scenario = EconomicScenario.model_validate(repo.scenarios[
            (candidate.scenario_id, candidate.revision)])
        current = fixed_trial_sha256(scenario, variable, "sale-1")
        fixed_hash = current if fixed_hash is None else fixed_hash
        assert current == fixed_hash
        current_shock = fixed_shock_sha256(shock, variable, "sale-1", "collection-1")
        fixed_shock_hash = current_shock if fixed_shock_hash is None else fixed_shock_hash
        if not vary_cap:
            assert current_shock == fixed_shock_hash
        refs.append({"ordinal": index, "value": str(value),
                     "scenario_id": candidate.scenario_id, "revision": candidate.revision,
                     "scenario_sha256": candidate.economic_scenario_sha256})
    request = {"schema_version": "1", "plan_id": "price-plan-1",
               "baseline": template["baseline"], "market_context": template["market_context"],
               "decision_at": template["decision_at"],
               "period_start": baseline.period_start, "period_end": baseline.period_end,
               "target": target, "variable": variable, "sale_id": "sale-1",
               "grade": "grade-1", "channel": "direct", "batch_id": "batch-1",
               "dispatch_at": sale.dispatch_at, "delivery_at": sale.delivery_at,
               "inspection_at": sale.inspection_at, "recognized_at": sale.recognized_at,
               "collection_id": "collection-1", "collection_at": baseline.collections[0].at,
               "minimum": str(values[0]), "maximum": str(values[-1]),
               "step": str(Decimal(values[1]) - Decimal(values[0]))}
    repo.break_even_plan = {"plan_id": request["plan_id"], "tenant_id": "tenant-1",
                            "request_sha256": canonical_request_sha256(request),
                            "fixed_inputs_sha256": fixed_hash, "immutable": True,
                            "fixed_shock_sha256": fixed_shock_hash,
                            "trials": refs}
    repo.get_break_even_plan = lambda plan_id: (
        repo.break_even_plan if plan_id == request["plan_id"] else None)
    return repo, request


@pytest.mark.parametrize("target", ["oi", "operating_cash", "cumulative_equity_cash"])
def test_price_zero_recomputes_each_pinned_joint_scenario(target):
    repo, request = trial_plan([20, 26, 32], target=target)
    result = BreakEvenService(repo).scan(request, "tenant-1")
    assert result.status == "zero_on_grid"
    assert result.zero_values == (Decimal("26"),)
    assert tuple(item.target_value for item in result.trials) == (
        Decimal("-54"), Decimal("0"), Decimal("54"))
    assert len({item.market_result_id for item in result.trials}) == 3
    assert result.assessment_status == "hold"
    assert result.scope == "conditional_user_grid_only"


def test_no_grid_zero_does_not_claim_continuous_no_root():
    repo, request = trial_plan([20, 22, 24])
    result = BreakEvenService(repo).scan(request, "tenant-1")
    assert result.status == "no_zero_on_grid"
    assert result.zero_values == ()
    assert result.brackets == ()


def test_sign_change_only_brackets_an_uncomputed_continuous_root():
    repo, request = trial_plan([20, 24, 28])
    result = BreakEvenService(repo).scan(request, "tenant-1")
    assert result.status == "bracket_only"
    assert result.zero_values == ()
    assert result.brackets == ((Decimal("24"), Decimal("28")),)


def test_nonmonotone_cash_path_is_flagged_without_a_single_threshold():
    repo, request = trial_plan([20, 26, 32], target="operating_cash",
                               collection_overrides={1: "0"})
    result = BreakEvenService(repo).scan(request, "tenant-1")
    assert result.status == "nonmonotone_on_grid"
    assert result.zero_values == ()
    assert tuple(item.target_value for item in result.trials) == (
        Decimal("-54"), Decimal("-90"), Decimal("54"))


def test_sale_kg_grid_reruns_inventory_contract_and_cash_path():
    repo, request = trial_plan(["2", "2.6", "3.2"], variable="kg")
    result = BreakEvenService(repo).scan(request, "tenant-1")
    assert result.status == "zero_on_grid"
    assert result.zero_values == (Decimal("2.6"),)
    assert tuple(item.target_value for item in result.trials) == (
        Decimal("-54"), Decimal("0"), Decimal("54"))


def test_plan_pin_and_fixed_assumptions_are_required():
    repo, request = trial_plan([20, 26, 32])
    repo.break_even_plan["request_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        BreakEvenService(repo).scan(request, "tenant-1")
    repo.break_even_plan["request_sha256"] = canonical_request_sha256(request)
    repo.break_even_plan["fixed_inputs_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        BreakEvenService(repo).scan(request, "tenant-1")


def test_contract_capacity_cannot_change_between_grid_points():
    repo, request = trial_plan([20, 26, 32], vary_cap=True)
    with pytest.raises(ValueError, match="fixed"):
        BreakEvenService(repo).scan(request, "tenant-1")


def test_foreign_or_repeated_trial_is_not_a_break_even_plan():
    repo, request = trial_plan([20, 26, 32])
    repo.break_even_plan["tenant_id"] = "tenant-2"
    with pytest.raises(ValueError):
        BreakEvenService(repo).scan(request, "tenant-1")
    repo.break_even_plan["tenant_id"] = "tenant-1"
    repo.break_even_plan["trials"][1] = deepcopy(repo.break_even_plan["trials"][0])
    with pytest.raises(ValueError, match="repeats"):
        BreakEvenService(repo).scan(request, "tenant-1")


def test_requested_grid_must_be_exact_and_bounded():
    repo, request = trial_plan([20, 26, 32])
    for step in ("0", "5", "0.01"):
        with pytest.raises(ValueError):
            BreakEvenService(repo).scan({**request, "step": step}, "tenant-1")
