"""As-of and immutable-rights boundary tests for synthetic user assumptions."""

from copy import deepcopy
from datetime import date, timedelta

import pytest

from test_market_scenario import case, digest, edit, repin_shock, service, two_lane_case
from app.economic_contracts import EconomicScenario
from app.economics import canonical_scenario_sha256
from app.market_scenario import settlement_path_sha256
from app.market_scenario import MarketScenarioRequest


def unresolved_inventory_case():
    repo, request = case()
    baseline_data = repo.scenarios[("scenario-1", "r1")]
    baseline_data["opening_inventory"] = None
    baseline_data["zero_declarations"] = tuple(
        item for item in baseline_data["zero_declarations"]
        if item["group"] != "opening_inventory")
    baseline_hash = canonical_scenario_sha256(EconomicScenario.model_validate(baseline_data))
    repo.pins[("scenario-1", "r1")].update(
        payload_sha256=baseline_hash, immutable_job_input_sha256=baseline_hash)
    request["baseline"]["sha256"] = baseline_hash
    shock = repo.shocks[("joint-1", "r1")]
    assert all(change["field"] not in {"grade", "channel"}
               for driver in shock["drivers"] for change in driver["changes"])
    shock["baseline_sha256"] = baseline_hash
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    return repo, request


def test_valid_unresolved_inventory_holds_without_pinning():
    repo, request = unresolved_inventory_case()
    result = service(repo).build_candidate(request, "tenant-1")
    assert result.status == "hold"
    assert result.hold_reasons == ("INVENTORY_UNRESOLVED",)
    assert repo.candidates == {}
    assert set(repo.scenarios) == set(repo.pins) == {("scenario-1", "r1")}


@pytest.mark.parametrize("bad_input", [
    "shock_request_digest", "foreign_shock_pin", "foreign_shock_record",
    "future_shock", "denied_shock_display", "future_driver",
    "denied_driver_display", "bad_baseline_sidecar_hash",
    "denied_baseline_sidecar_display", "overdrawn_contract_cap",
    "bad_settlement_applicability",
])
def test_invalid_provenance_precedes_unresolved_inventory_hold(bad_input):
    repo, request = unresolved_inventory_case()
    shock = repo.shocks[("joint-1", "r1")]
    if bad_input == "shock_request_digest":
        request["shock"]["sha256"] = "0" * 64
    elif bad_input == "foreign_shock_pin":
        repo.shock_pins[("joint-1", "r1")]["tenant_id"] = "tenant-2"
    elif bad_input == "foreign_shock_record":
        shock["tenant_id"] = "tenant-2"
        shock["drivers"][0]["hypothesis"] = "foreign-secret-marker"
        request["shock"]["sha256"] = digest(shock)
        repin_shock(repo)
        repo.shock_pins[("joint-1", "r1")]["tenant_id"] = "tenant-1"
    elif bad_input == "future_shock":
        shock["available_at"] += timedelta(seconds=1)
    elif bad_input == "denied_shock_display":
        shock["rights"]["display"] = "denied"
    elif bad_input == "future_driver":
        shock["drivers"][0]["available_at"] += timedelta(seconds=1)
    elif bad_input == "denied_driver_display":
        shock["drivers"][0]["rights"]["display"] = "denied"
    elif bad_input == "bad_baseline_sidecar_hash":
        repo.rights[("opening-cash", "r1")]["raw_sha256"] = "f" * 64
    elif bad_input == "denied_baseline_sidecar_display":
        repo.rights[("opening-cash", "r1")]["rights"]["display"] = "denied"
    elif bad_input == "overdrawn_contract_cap":
        cap = shock["contract_caps"][0]["accepted_kg"]
        cap["value"] = "8"
        repo.rights[("cap-kg", "r2")]["raw_sha256"] = digest(cap)
    elif bad_input == "bad_settlement_applicability":
        repo.bindings[("binding-1", "r2")]["path_sha256"] = "f" * 64
    if bad_input in {"future_shock", "denied_shock_display", "future_driver",
                     "denied_driver_display", "overdrawn_contract_cap"}:
        request["shock"]["sha256"] = digest(shock)
        repin_shock(repo)

    with pytest.raises(ValueError) as error:
        service(repo).build_candidate(request, "tenant-1")
    assert "tenant-2" not in str(error.value)
    assert "foreign-secret-marker" not in str(error.value)
    assert repo.candidates == {}
    assert set(repo.scenarios) == set(repo.pins) == {("scenario-1", "r1")}


@pytest.mark.parametrize("bad_request", ["decision_at", "tenant"])
def test_unresolved_inventory_still_rejects_wrong_decision_or_tenant(bad_request):
    repo, request = unresolved_inventory_case()
    if bad_request == "decision_at":
        request["decision_at"] += timedelta(seconds=1)
    tenant = "tenant-2" if bad_request == "tenant" else "tenant-1"
    with pytest.raises(ValueError) as error:
        service(repo).build_candidate(request, tenant)
    assert "tenant-2" not in str(error.value)
    assert repo.candidates == {}
    assert set(repo.scenarios) == set(repo.pins) == {("scenario-1", "r1")}


@pytest.mark.parametrize("foreign_record", ["baseline", "shock", "shock_pin"])
def test_foreign_malformed_record_never_leaks_structured_validation_input(foreign_record):
    repo, request = unresolved_inventory_case()
    if foreign_record == "baseline":
        raw = repo.scenarios[("scenario-1", "r1")]
        raw["tenant_id"] = "tenant-2"
        raw["opening_cash"]["value"] = "foreign-secret-marker"
    elif foreign_record == "shock":
        raw = repo.shocks[("joint-1", "r1")]
        raw["tenant_id"] = "tenant-2"
        raw["rights"]["display"] = "foreign-secret-marker"
        request["shock"]["sha256"] = digest(raw)
        repin_shock(repo)
    else:
        raw = repo.shock_pins[("joint-1", "r1")]
        raw["tenant_id"] = "tenant-2"
        raw["sha256"] = "foreign-secret-marker"

    with pytest.raises(ValueError) as error:
        service(repo).build_candidate(request, "tenant-1")
    assert "foreign-secret-marker" not in str(error.value)
    if hasattr(error.value, "errors"):
        assert "foreign-secret-marker" not in repr(error.value.errors())
    assert repo.candidates == {}
    assert set(repo.scenarios) == set(repo.pins) == {("scenario-1", "r1")}


@pytest.mark.parametrize("foreign_record", ["input_rights", "settlement_binding"])
def test_foreign_malformed_sidecar_never_leaks_structured_validation_input(foreign_record):
    repo, request = case()
    records = repo.rights.values() if foreign_record == "input_rights" else repo.bindings.values()
    for raw in records:
        raw["tenant_id"] = "tenant-2"
        raw["rights"]["display"] = "foreign-secret-marker"
    with pytest.raises(ValueError) as error:
        service(repo).build_candidate(request, "tenant-1")
    assert "foreign-secret-marker" not in str(error.value)
    if hasattr(error.value, "errors"):
        assert "foreign-secret-marker" not in repr(error.value.errors())
    assert repo.candidates == {}


@pytest.mark.parametrize("mutation", [
    lambda repo: repo.shocks[("joint-1", "r1")].update(tenant_id="tenant-2"),
    lambda repo: repo.shocks[("joint-1", "r1")].update(available_at=repo.hold["decision_at"] + timedelta(seconds=1)),
    lambda repo: repo.shocks[("joint-1", "r1")]["rights"].update(display="denied"),
    lambda repo: repo.shocks[("joint-1", "r1")]["drivers"][0].update(origin="provider"),
])
def test_shock_ownership_time_and_rights_fail_closed(mutation):
    repo, request = case()
    mutation(repo)
    request["shock"]["sha256"] = digest(repo.shocks[("joint-1", "r1")])
    repin_shock(repo)
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")


def test_tamper_under_same_shock_revision_fails():
    repo, request = case()
    repo.shocks[("joint-1", "r1")]["drivers"][1]["changes"][0]["number"]["value"] = "7"
    with pytest.raises(ValueError, match="shock"):
        service(repo).build_candidate(request, "tenant-1")


def test_caller_cannot_repin_tampered_shock_revision():
    repo, request = case()
    original = deepcopy(repo.get_joint_shock_pin("joint-1", "r1"))
    repo.shocks[("joint-1", "r1")]["drivers"][1]["changes"][0]["number"]["value"] = "7"
    request["shock"]["sha256"] = digest(repo.shocks[("joint-1", "r1")])
    assert repo.get_joint_shock_pin("joint-1", "r1") == original
    with pytest.raises(ValueError, match="shock.*pin|immutable revision"):
        service(repo).build_candidate(request, "tenant-1")


@pytest.mark.parametrize("change", [
    lambda pin: pin.update(tenant_id="tenant-2"),
    lambda pin: pin.update(immutable=False),
    lambda pin: pin.update(sha256="0" * 64),
])
def test_independent_shock_pin_must_be_owned_immutable_and_match_digest(change):
    repo, request = case()
    change(repo.shock_pins[("joint-1", "r1")])
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")


def test_cap_and_accepted_kg_rights_only_need_recognition_kst_date():
    repo, request = case()
    cap = repo.shocks[("joint-1", "r1")]["contract_caps"][0]
    cap["effective_start"] = cap["effective_end"] = date(2026, 10, 15)
    rights = repo.rights[("cap-kg", "r2")]
    rights["effective_start"] = rights["effective_end"] = date(2026, 10, 15)
    request["shock"]["sha256"] = digest(repo.shocks[("joint-1", "r1")])
    repin_shock(repo)
    assert service(repo).build_candidate(request, "tenant-1").status == "pinned"
    repo, request = case()
    cap = repo.shocks[("joint-1", "r1")]["contract_caps"][0]
    cap["effective_start"] = cap["effective_end"] = date(2026, 10, 16)
    request["shock"]["sha256"] = digest(repo.shocks[("joint-1", "r1")])
    repin_shock(repo)
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")
    repo, request = case()
    rights = repo.rights[("cap-kg", "r2")]
    rights["effective_start"] = rights["effective_end"] = date(2026, 10, 16)
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")


def test_cap_sidecar_hash_and_rights_remain_independent():
    repo, request = case()
    repo.rights[("cap-kg", "r2")]["raw_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="sidecar"):
        service(repo).build_candidate(request, "tenant-1")
    repo, request = case()
    repo.rights[("cap-kg", "r2")]["rights"]["use"] = "denied"
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")


@pytest.mark.parametrize("mutation", [
    lambda record: record.update(tenant_id="tenant-2"),
    lambda record: record["rights"].update(use="denied"),
    lambda record: record["rights"].update(display="denied"),
    lambda record: record.update(available_at=record["available_at"] + timedelta(days=1)),
    lambda record: record.update(raw_sha256="f" * 64),
])
def test_retained_numeric_sidecar_fail_closed(mutation):
    repo, request = case()
    mutation(repo.rights[("opening-cash", "r1")])
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")


def test_replacement_numeric_sidecar_cannot_be_backdated_or_reused():
    repo, request = case()
    repo.rights[("price", "r2")]["available_at"] += timedelta(days=1)
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")
    repo, request = case()
    changed = repo.shocks[("joint-1", "r1")]["drivers"][1]["changes"][1]["number"]
    changed["revision"] = "r1"
    request["shock"]["sha256"] = digest(repo.shocks[("joint-1", "r1")])
    repin_shock(repo)
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")


def test_foreign_tenant_and_changed_baseline_hash_fail_closed():
    repo, request = case()
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-2")
    repo.scenarios[("scenario-1", "r1")]["harvests"][0]["quantity"]["value"] = "99"
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")


def test_calculation_rechecks_pin_and_does_not_accept_forged_candidate():
    repo, request = case()
    candidate = service(repo).build_candidate(request, "tenant-1")
    repo.candidates[(candidate.scenario_id, candidate.revision)]["economic_scenario_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        service(repo).calculate_pinned(candidate.scenario_id, candidate.revision, "tenant-1")


def test_calculation_rejects_changed_stored_candidate_scenario_data():
    repo, request = two_lane_case()
    candidate = service(repo).build_candidate(request, "tenant-1")
    stored = repo.scenarios[(candidate.scenario_id, candidate.revision)]
    stored["packouts"][0]["grade"] = "grade-1"
    with pytest.raises(ValueError, match="derived economic scenario changed"):
        service(repo).calculate_pinned(candidate.scenario_id, candidate.revision, "tenant-1")


def test_rights_change_after_pin_cannot_relabel_the_existing_candidate():
    repo, request = case()
    candidate = service(repo).build_candidate(request, "tenant-1")
    repo.rights[("opening-cash", "r1")]["rights"]["redistribute"] = "allowed"
    with pytest.raises(ValueError):
        service(repo).calculate_pinned(candidate.scenario_id, candidate.revision, "tenant-1")


def test_same_hold_id_is_preserved_at_both_stages():
    repo, request = case()
    candidate = service(repo).build_candidate(request, "tenant-1")
    result = service(repo).calculate_pinned(candidate.scenario_id, candidate.revision, "tenant-1")
    assert candidate.market_context.hold_report_id == "hold-1"
    assert result.market_context.hold_report_id == "hold-1"
    assert result.economic_result.market_context.hold_report_id == "hold-1"
    assert result.assessment_status == "hold"
    assert not hasattr(result, "net_p")
    assert not hasattr(result, "market_snapshot")


def test_forged_pydantic_request_extra_field_is_rejected():
    repo, request = case()
    forged = MarketScenarioRequest.model_validate(request).model_copy(update={"snapshot_id": "fake"})
    with pytest.raises(ValueError):
        service(repo).build_candidate(forged, "tenant-1")


@pytest.mark.parametrize("mutation", [
    lambda record: record["rights"].update(display="denied"),
    lambda record: record.update(tenant_id="tenant-2"),
    lambda record: record.update(available_at=record["available_at"] + timedelta(days=1)),
    lambda record: record.update(path_sha256="f" * 64),
])
def test_settlement_applicability_rights_time_and_path_fail_closed(mutation):
    repo, request = case()
    mutation(repo.bindings[("binding-1", "r2")])
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")


def test_settlement_evidence_must_be_available_by_decision():
    repo, request = case()
    repo.settlements[("self-authored-settlement-1", "r2")]["available_at"] += timedelta(days=1)
    with pytest.raises(ValueError, match="settlement evidence"):
        service(repo).build_candidate(request, "tenant-1")


def test_rights_revision_changes_candidate_and_result_identity():
    repo_a, request_a = case()
    a = service(repo_a).build_candidate(request_a, "tenant-1")
    result_a = service(repo_a).calculate_pinned(a.scenario_id, a.revision, "tenant-1")
    repo_b, request_b = case()
    repo_b.rights[("opening-cash", "r1")]["rights"]["redistribute"] = "allowed"
    b = service(repo_b).build_candidate(request_b, "tenant-1")
    result_b = service(repo_b).calculate_pinned(b.scenario_id, b.revision, "tenant-1")
    assert a.economic_scenario_sha256 != b.economic_scenario_sha256
    assert a.candidate_id != b.candidate_id
    assert result_a.result_id != result_b.result_id


def test_lane_reference_edit_requires_unchanged_independent_shock_pin():
    repo, request = two_lane_case()
    original = deepcopy(repo.get_joint_shock_pin("joint-1", "r1"))
    shock = repo.shocks[("joint-1", "r1")]
    shock["drivers"][0]["changes"][-1]["reference"] = "direct"
    request["shock"]["sha256"] = digest(shock)
    assert repo.get_joint_shock_pin("joint-1", "r1") == original
    with pytest.raises(ValueError, match="shock.*pin|immutable revision"):
        service(repo).build_candidate(request, "tenant-1")
    assert repo.candidates == {}


def test_lane_quantity_revision_and_sidecar_are_checked_before_pin():
    repo, request = two_lane_case()
    shock = repo.shocks[("joint-1", "r1")]
    moved = next(change["number"] for change in shock["drivers"][0]["changes"]
                 if change["event_id"] == "pack-2" and change["field"] == "quantity")
    moved["revision"] = "r1"
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError, match="new immutable input revision"):
        service(repo).build_candidate(request, "tenant-1")
    assert repo.candidates == {}

    repo, request = two_lane_case()
    repo.rights[("p-2", "r2")]["raw_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="sidecar"):
        service(repo).build_candidate(request, "tenant-1")
    assert repo.candidates == {}


def test_new_shock_revision_for_revised_lane_references_has_distinct_pins():
    repo, request = two_lane_case()
    first = service(repo).build_candidate(request, "tenant-1")
    first_result = service(repo).calculate_pinned(first.scenario_id, first.revision, "tenant-1")
    baseline_bytes = deepcopy(repo.scenarios[("scenario-1", "r1")])
    old_shock = deepcopy(repo.shocks[("joint-1", "r1")])
    shock = deepcopy(old_shock)
    shock["revision"] = "r2"
    for change in shock["drivers"][0]["changes"]:
        if change["field"] in ("grade", "channel"):
            change["reference"] = "grade-1" if change["field"] == "grade" else "direct"
    shock["drivers"][0]["changes"].extend([
        edit("packouts", "pack-2", "grade", reference="grade-1"),
        edit("packouts", "pack-2", "channel", reference="direct"),
    ])
    for change in shock["drivers"][1]["changes"]:
        if change["field"] in ("grade", "channel"):
            change["reference"] = "grade-1" if change["field"] == "grade" else "direct"
    shock["contract_caps"][0].update(grade="grade-1", channel="direct")
    revised = deepcopy(baseline_bytes)
    for driver in shock["drivers"]:
        for change in driver["changes"]:
            target = next(item for item in revised[change["event_group"]]
                          if item["id"] == change["event_id"])
            target[change["field"]] = change.get("number", change.get("time", change.get("reference")))
    binding = deepcopy(repo.bindings[("binding-1", "r2")])
    binding["revision"] = "r3"
    binding["path_sha256"] = settlement_path_sha256(EconomicScenario.model_validate(revised), "sale-1")
    repo.bindings[("binding-1", "r3")] = binding
    shock["settlement_bindings"][0].update(revision="r3", sha256=digest(binding))
    repo.shocks[("joint-1", "r2")] = shock
    repo.shock_pins[("joint-1", "r2")] = {
        "shock_id": "joint-1", "revision": "r2", "tenant_id": "tenant-1",
        "sha256": digest(shock), "immutable": True,
    }
    revised_request = deepcopy(request)
    revised_request["shock"].update(revision="r2", sha256=digest(shock))
    second = service(repo).build_candidate(revised_request, "tenant-1")
    second_result = service(repo).calculate_pinned(second.scenario_id, second.revision, "tenant-1")
    assert repo.scenarios[("scenario-1", "r1")] == baseline_bytes
    assert repo.shocks[("joint-1", "r1")] == old_shock
    assert first.joint_shock.revision == "r1" and second.joint_shock.revision == "r2"
    assert first.candidate_id != second.candidate_id
    assert first.economic_scenario_sha256 != second.economic_scenario_sha256
    assert first_result.result_id != second_result.result_id
