"""Self-authored joint stresses test contracts, not market or farm evidence."""

from copy import deepcopy
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from test_economics import DECISION, MARKET, TrustedTestRepository, n, settlement_record
from test_economics_settlement import example
from app.economic_contracts import EconomicScenario, iter_economic_numbers
from app.economics import canonical_scenario_sha256
from app.market_scenario import MarketScenarioService, settlement_path_sha256

ROOT = Path(__file__).resolve().parents[2]
RIGHTS = {"use": "allowed", "display": "allowed", "redistribute": "denied"}


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                             default=lambda v: v.isoformat().replace("+00:00", "Z")).encode()).hexdigest()


def replacement(value, input_id, unit):
    item = n(value, input_id, unit)
    item["revision"] = "r2"
    return item


def edit(group, event_id, field, *, number=None, time=None, reference=None):
    return {"event_group": group, "event_id": event_id, "field": field,
            **({"number": number} if number is not None else {}),
            **({"time": time} if time is not None else {}),
            **({"reference": reference} if reference is not None else {})}


def driver(kind, changes):
    return {"kind": kind, "record_id": f"{kind}-assumption", "revision": "r1",
            "origin": "user", "evidence_level": "assumed", "available_at": DECISION,
            "effective_start": date(2026, 10, 1), "effective_end": date(2026, 10, 31),
            "rights": deepcopy(RIGHTS), "hypothesis": f"Self-authored {kind} stress hypothesis",
            "source_ref": "self-authored-test", "causal_status": "unvalidated_user_hypothesis",
            "changes": changes}


def sidecar(value, tenant="tenant-1"):
    return {"input_id": value["input_id"], "revision": value["revision"],
            "tenant_id": tenant, "raw_sha256": digest(value),
            "origin": "user", "evidence_level": "assumed", "rights": deepcopy(RIGHTS),
            "available_at": DECISION, "effective_start": date(2026, 10, 1),
            "effective_end": date(2026, 10, 31), "immutable": True}


class Repository(TrustedTestRepository):
    def __init__(self, baseline):
        super().__init__(baseline)
        self.scenarios = {(baseline.scenario_id, baseline.scenario_revision): baseline.model_dump(mode="python")}
        self.pins = {(baseline.scenario_id, baseline.scenario_revision): deepcopy(self.scenario_pin)}
        self.candidates = {}
        self.shocks = {}
        self.shock_pins = {}
        self.bindings = {}
        self.rights = { (item.input_id, item.revision): sidecar(item.model_dump(mode="python"))
                        for item in iter_economic_numbers(baseline)}

    def get_economic_scenario(self, scenario_id, revision):
        return self.scenarios.get((scenario_id, revision))

    def get_joint_shock(self, shock_id, revision):
        return self.shocks.get((shock_id, revision))

    def get_joint_shock_pin(self, shock_id, revision):
        return self.shock_pins.get((shock_id, revision))

    def get_input_rights(self, input_id, revision):
        return self.rights.get((input_id, revision))

    def get_settlement_applicability(self, binding_id, revision):
        return self.bindings.get((binding_id, revision))

    def pin_market_candidate(self, record, scenario, new_records):
        key = (scenario["scenario_id"], scenario["scenario_revision"])
        if key in self.scenarios:
            return False
        self.scenarios[key] = deepcopy(scenario)
        self.candidates[key] = deepcopy(record)
        scenario_model = EconomicScenario.model_validate(scenario)
        self.scenario_pin = {
            "tenant_id": scenario_model.tenant_id, "scenario_id": scenario_model.scenario_id,
            "scenario_revision": scenario_model.scenario_revision,
            "decision_at": scenario_model.decision_at,
            "payload_sha256": canonical_scenario_sha256(scenario_model),
            "immutable_job_input_ref": record["immutable_job_input_ref"],
            "immutable_job_input_sha256": record["economic_scenario_sha256"],
            "immutable": True,
        }
        self.pins[key] = deepcopy(self.scenario_pin)
        for item in new_records:
            self.records[(item["input_id"], item["revision"])] = deepcopy(item)
        return True

    def get_market_candidate(self, scenario_id, revision):
        return self.candidates.get((scenario_id, revision))

    def get_economic_scenario_pin(self, scenario_id, revision):
        return self.pins.get((scenario_id, revision))


def case():
    data = example()
    baseline = EconomicScenario.model_validate(data)
    repo = Repository(baseline)
    changes = [
        driver("supply", [edit("harvests", "harvest-1", "quantity", number=replacement(12, "h", "kg")),
                          edit("packouts", "pack-1", "quantity", number=replacement(12, "p", "kg"))]),
        driver("demand", [edit("sales", "sale-1", "quantity", number=replacement(9, "s", "kg")),
                          edit("sales", "sale-1", "price", number=replacement(90, "price", "KRW/kg")),
                          edit("discounts", "discount-1", "amount", number=replacement(90, "discount", "KRW")),
                          edit("collections", "collection-1", "amount", number=replacement(666, "collection", "KRW"))]),
        driver("macro", [edit("variable_costs", "production", "quantity", number=replacement(12, "production-q", "kg")),
                         edit("variable_costs", "production", "unit_cost", number=replacement(5, "production-rate", "KRW/kg")),
                         edit("variable_costs", "production", "payment", number=replacement(60, "production-paid", "KRW")),
                         edit("variable_costs", "fee", "unit_cost", number=replacement(54, "fee-amount", "KRW/kg")),
                         edit("setoffs", "setoff-1", "amount", number=replacement(54, "setoff-amount", "KRW")),
                         edit("setoffs", "setoff-1", "evidence_revision", reference="r2")]),
    ]
    patched = deepcopy(data)
    for item in changes:
        for change in item["changes"]:
            target = next(x for x in patched[change["event_group"]] if x["id"] == change["event_id"])
            target[change["field"]] = change.get("number", change.get("time", change.get("reference")))
    evidence = settlement_record(patched, patched["setoffs"][0])
    repo.settlements[("self-authored-settlement-1", "r2")] = evidence
    evidence_change = edit("setoffs", "setoff-1", "evidence_sha256", reference=evidence["raw_sha256"])
    changes[2]["changes"].append(evidence_change)
    patched["setoffs"][0]["evidence_sha256"] = evidence["raw_sha256"]
    cap = {"record_id": "cap-1", "revision": "r1", "contract_id": "contract-1",
           "sale_ids": ["sale-1"],
           "grade": "grade-1", "channel": "direct", "accepted_kg": replacement(10, "cap-kg", "kg"),
           "origin": "user", "evidence_level": "assumed", "available_at": DECISION,
           "effective_start": date(2026, 10, 1), "effective_end": date(2026, 10, 31),
           "rights": deepcopy(RIGHTS)}
    binding = {"binding_id": "binding-1", "revision": "r2", "tenant_id": "tenant-1",
               "setoff_id": "setoff-1", "sale_id": "sale-1", "path_sha256": settlement_path_sha256(
                   EconomicScenario.model_validate(patched), "sale-1"),
               "settlement_ref": "self-authored-settlement-1", "evidence_revision": "r2",
               "evidence_sha256": evidence["raw_sha256"], "origin": "user",
               "evidence_level": "assumed", "available_at": DECISION,
               "effective_start": date(2026, 10, 1), "effective_end": date(2026, 10, 31),
               "rights": deepcopy(RIGHTS), "immutable": True}
    shock = {"schema_version": "1", "shock_id": "joint-1", "revision": "r1",
             "tenant_id": "tenant-1", "baseline_sha256": canonical_scenario_sha256(baseline),
             "decision_at": DECISION, "effective_start": date(2026, 10, 1),
             "effective_end": date(2026, 10, 31), "available_at": DECISION,
             "origin": "user", "evidence_level": "assumed", "rights": deepcopy(RIGHTS),
             "drivers": changes, "contract_caps": [cap],
             "settlement_bindings": [{"binding_id": "binding-1", "revision": "r2",
                                       "sha256": digest(binding)}]}
    repo.shocks[("joint-1", "r1")] = deepcopy(shock)
    repin_shock(repo)
    repo.bindings[("binding-1", "r2")] = binding
    for driver_item in changes:
        for change in driver_item["changes"]:
            if "number" in change:
                value = change["number"]
                repo.rights[(value["input_id"], value["revision"])] = sidecar(value)
    repo.rights[("cap-kg", "r2")] = sidecar(cap["accepted_kg"])
    request = {"schema_version": "1", "baseline": {"scenario_id": "scenario-1",
               "revision": "r1", "sha256": canonical_scenario_sha256(baseline)},
               "shock": {"shock_id": "joint-1", "revision": "r1", "sha256": digest(shock)},
               "decision_at": DECISION, "market_context": MARKET}
    return repo, request


def two_lane_case():
    repo, request = case()
    baseline_data = deepcopy(repo.scenarios[("scenario-1", "r1")])
    baseline_data["harvests"][0]["quantity"]["value"] = "12"
    second = deepcopy(baseline_data["packouts"][0])
    second.update(id="pack-2", grade="grade-2", channel="wholesale", quantity=n(2, "p-2"))
    baseline_data["packouts"] = (*baseline_data["packouts"], second)
    baseline = EconomicScenario.model_validate(baseline_data)
    baseline_hash = canonical_scenario_sha256(baseline)
    repo.scenarios[("scenario-1", "r1")] = baseline_data
    repo.pins[("scenario-1", "r1")].update(
        payload_sha256=baseline_hash, immutable_job_input_sha256=baseline_hash)
    for number in iter_economic_numbers(baseline):
        value = number.model_dump(mode="python")
        repo.records[(number.input_id, number.revision)] = {
            **value, "tenant_id": "tenant-1", "scope_start": baseline.period_start,
            "scope_end": baseline.period_end,
        }
        repo.rights[(number.input_id, number.revision)] = sidecar(value)
    request["baseline"]["sha256"] = baseline_hash

    shock = repo.shocks[("joint-1", "r1")]
    shock["baseline_sha256"] = baseline_hash
    supply, demand = shock["drivers"][:2]
    supply["changes"][1]["number"]["value"] = "3"
    repo.rights[("p", "r2")] = sidecar(supply["changes"][1]["number"])
    moved = replacement(9, "p-2", "kg")
    repo.rights[("p-2", "r2")] = sidecar(moved)
    supply["changes"].extend([
        edit("packouts", "pack-2", "quantity", number=moved),
        edit("packouts", "pack-1", "grade", reference="grade-2"),
        edit("packouts", "pack-1", "channel", reference="wholesale"),
    ])
    demand["changes"].extend([
        edit("sales", "sale-1", "grade", reference="grade-2"),
        edit("sales", "sale-1", "channel", reference="wholesale"),
    ])
    shock["contract_caps"][0].update(grade="grade-2", channel="wholesale")
    revised = deepcopy(baseline_data)
    for driver_item in shock["drivers"]:
        for change in driver_item["changes"]:
            target = next(item for item in revised[change["event_group"]]
                          if item["id"] == change["event_id"])
            target[change["field"]] = change.get("number", change.get("time", change.get("reference")))
    binding = repo.bindings[("binding-1", "r2")]
    binding["path_sha256"] = settlement_path_sha256(EconomicScenario.model_validate(revised), "sale-1")
    shock["settlement_bindings"][0]["sha256"] = digest(binding)
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    return repo, request


def repin_shock(repo):
    shock = repo.shocks[("joint-1", "r1")]
    repo.shock_pins[("joint-1", "r1")] = {
        "shock_id": "joint-1", "revision": "r1", "tenant_id": shock["tenant_id"],
        "sha256": digest(shock), "immutable": True,
    }


def service(repo):
    return MarketScenarioService(repo)


def test_schema_is_strict_and_joint():
    schema = json.loads((ROOT / "contracts/market-scenario-v1.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    _, request = case()
    encoded = json.loads(json.dumps(request, default=lambda v: v.isoformat().replace("+00:00", "Z")))
    assert validator.is_valid(encoded)
    for extra in ({"snapshot_id": "fake"}, {"path": "/sales/0/price"}, {"probability": 0.7}):
        assert not validator.is_valid({**encoded, **extra})
    assert not validator.is_valid({**encoded, "decision_at": "2026-09-28T00:00:00"})
    assert not validator.is_valid({**encoded, "market_context": {"kind": "available",
                                                       "snapshot_id": "fake"}})


def test_joint_candidate_pins_complete_scenario_and_baseline_fields():
    repo, request = case()
    candidate = service(repo).build_candidate(request, "tenant-1")
    assert candidate.status == "pinned"
    derived = EconomicScenario.model_validate(repo.get_economic_scenario(candidate.scenario_id, candidate.revision))
    baseline = EconomicScenario.model_validate(repo.get_economic_scenario("scenario-1", "r1"))
    assert derived.schema_version == "3" and derived.scenario_id != baseline.scenario_id
    assert derived.market_context == baseline.market_context
    assert derived.opening_inventory == baseline.opening_inventory
    assert derived.fixed_costs == baseline.fixed_costs
    assert candidate.economic_scenario_sha256 == canonical_scenario_sha256(derived)
    assert candidate.baseline.sha256 == canonical_scenario_sha256(baseline)
    assert candidate.joint_shock.sha256 == request["shock"]["sha256"]
    assert len(candidate.rights_manifest_sha256) == len(candidate.binding_manifest_sha256) == 64
    assert repo.scenario_pin["immutable_job_input_sha256"] == candidate.economic_scenario_sha256


def test_json_request_and_stored_shock_use_the_same_utc_contract():
    repo, request = case()
    encode = lambda value: json.loads(json.dumps(value, default=lambda item: item.isoformat().replace("+00:00", "Z")))
    repo.shocks[("joint-1", "r1")] = encode(repo.shocks[("joint-1", "r1")])
    candidate = service(repo).build_candidate(encode(request), "tenant-1")
    assert candidate.status == "pinned"
    assert service(repo).calculate_pinned(candidate.scenario_id, candidate.revision,
                                          "tenant-1").assessment_status == "hold"


@pytest.mark.parametrize("change", [
    lambda s: s.update(snapshot_id="fake"),
    lambda s: s["drivers"][0]["changes"][0].update(path="/sales/0/price"),
    lambda s: s["drivers"][0]["changes"][0]["number"].update(value=12.0),
    lambda s: s["drivers"].pop(),
    lambda s: s["drivers"][0]["changes"].append(deepcopy(s["drivers"][0]["changes"][0])),
])
def test_bad_joint_shock_fails_closed(change):
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    change(shock)
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")


def test_contract_cap_rejects_sale_kg():
    repo, request = case()
    cap = repo.shocks[("joint-1", "r1")]["contract_caps"][0]["accepted_kg"]
    cap["value"] = "8"
    repo.rights[("cap-kg", "r2")] = sidecar(cap)
    request["shock"]["sha256"] = digest(repo.shocks[("joint-1", "r1")])
    repin_shock(repo)
    with pytest.raises(ValueError, match="contract cap"):
        service(repo).build_candidate(request, "tenant-1")


def test_cap_cannot_borrow_a_sale_input_revision():
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    shock["contract_caps"][0]["accepted_kg"] = deepcopy(shock["drivers"][1]["changes"][0]["number"])
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError, match="contract cap needs its own"):
        service(repo).build_candidate(request, "tenant-1")


def test_cap_cannot_borrow_replaced_baseline_harvest_revision():
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    shock["contract_caps"][0]["accepted_kg"] = deepcopy(repo.scenarios[("scenario-1", "r1")]["harvests"][0]["quantity"])
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError, match="contract cap needs its own"):
        service(repo).build_candidate(request, "tenant-1")


def test_contract_cap_aggregates_two_sales_and_checks_identity_scope():
    from app.market_scenario import JointShock
    from app.economics import day

    repo, _ = case()
    shock = deepcopy(repo.shocks[("joint-1", "r1")])
    shock["contract_caps"][0]["sale_ids"] = ["sale-1", "sale-2"]
    derived = deepcopy(repo.scenarios[("scenario-1", "r1")])
    sale = derived["sales"][0]
    sale["quantity"]["value"] = "6"
    second = deepcopy(sale)
    second["id"] = "sale-2"
    second["quantity"]["input_id"] = "s-2"
    derived["sales"] = (sale, second)
    scenario = EconomicScenario.model_validate(derived)
    cap = shock["contract_caps"][0]
    assert day(scenario.sales[0].recognized_at) == date(2026, 10, 15)
    with pytest.raises(ValueError, match="contract cap"):
        service(repo)._check_caps(JointShock.model_validate(shock), scenario)
    sale["quantity"]["value"] = "5"
    second["quantity"]["value"] = "5"
    scenario = EconomicScenario.model_validate(derived)
    service(repo)._check_caps(JointShock.model_validate(shock), scenario)
    for mutation in (
        lambda c: c.update(grade="other"),
        lambda c: c.update(channel="other"),
        lambda c: c.update(effective_start=date(2026, 10, 16)),
        lambda c: c.update(sale_ids=["sale-1"]),
    ):
        changed = deepcopy(shock)
        mutation(changed["contract_caps"][0])
        with pytest.raises(ValueError):
            service(repo)._check_caps(JointShock.model_validate(changed), scenario)
    duplicate = deepcopy(shock)
    duplicate["contract_caps"].append(deepcopy(cap))
    duplicate["contract_caps"][1]["record_id"] = "cap-2"
    with pytest.raises(ValueError, match="contract"):
        service(repo)._check_caps(JointShock.model_validate(duplicate), scenario)


def test_driver_kind_requires_matching_edits_and_user_hypothesis():
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    shock["drivers"][0]["kind"], shock["drivers"][2]["kind"] = "macro", "supply"
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError, match="driver kind"):
        service(repo).build_candidate(request, "tenant-1")
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    shock["drivers"][0].pop("hypothesis")
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")


@pytest.mark.parametrize("swap_labels", [False, True], ids=["moved_packout", "mixed_kind_swap"])
def test_every_driver_edit_matches_its_kind_before_pin(swap_labels):
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    supply, demand = shock["drivers"][:2]
    packout = supply["changes"].pop(1)
    demand["changes"].append(packout)
    if swap_labels:
        supply["kind"], demand["kind"] = "demand", "supply"
        sale = demand["changes"].pop(0)
        supply["changes"].append(sale)
        assert any(change["event_group"] == "sales" for change in supply["changes"])
        assert any(change["event_group"] == "packouts" for change in demand["changes"])
    else:
        assert any(change["event_group"] == "harvests" for change in supply["changes"])
        assert any(change["event_group"] == "sales" for change in demand["changes"])
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)

    with pytest.raises(ValueError, match="driver kind"):
        service(repo).build_candidate(request, "tenant-1")
    assert repo.candidates == {}
    assert set(repo.scenarios) == {("scenario-1", "r1")}
    schema = json.loads((ROOT / "contracts/market-scenario-v1.schema.json").read_text())
    validator = Draft202012Validator({"$ref": "#/$defs/jointShock", "$defs": schema["$defs"]})
    encoded = json.loads(json.dumps(shock, default=lambda value: value.isoformat().replace("+00:00", "Z")))
    assert not validator.is_valid(encoded)


@pytest.mark.parametrize("length,accepted", [(64, True), (65, False)])
def test_decimal_length_schema_matches_runtime(length, accepted):
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    cap = shock["contract_caps"][0]["accepted_kg"]
    cap["value"] = "10." + "0" * (length - 3)
    assert len(cap["value"]) == length
    repo.rights[("cap-kg", "r2")] = sidecar(cap)
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)

    schema = json.loads((ROOT / "contracts/market-scenario-v1.schema.json").read_text())
    validator = Draft202012Validator({"$ref": "#/$defs/jointShock", "$defs": schema["$defs"]})
    encoded = json.loads(json.dumps(shock, default=lambda value: value.isoformat().replace("+00:00", "Z")))
    assert validator.is_valid(encoded) is accepted
    if accepted:
        assert service(repo).build_candidate(request, "tenant-1").status == "pinned"
    else:
        with pytest.raises(ValueError):
            service(repo).build_candidate(request, "tenant-1")
        assert repo.candidates == {}


def test_schema_validates_stored_joint_shock_and_rejects_invalid_payloads():
    schema = json.loads((ROOT / "contracts/market-scenario-v1.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator({"$ref": "#/$defs/jointShock", "$defs": schema["$defs"]})
    repo, request = case()
    encode = lambda value: json.loads(json.dumps(value, default=lambda item: item.isoformat().replace("+00:00", "Z")))
    shock = encode(repo.shocks[("joint-1", "r1")])
    assert validator.is_valid(shock)
    root = Draft202012Validator(schema)
    assert root.is_valid(encode(request))
    assert not root.is_valid({**encode(request), "drivers": shock["drivers"]})
    mutations = (
        lambda s: s.update(snapshot_id="fake"),
        lambda s: s["drivers"][0]["changes"][0].update(extra="bad"),
        lambda s: s["drivers"][0]["changes"][0]["number"].update(value=12.0),
        lambda s: s["drivers"].pop(),
        lambda s: s["drivers"][0].update(hypothesis="   "),
        lambda s: s["rights"].update(use="denied"),
        lambda s: s["contract_caps"][0].update(sale_ids=[]),
        lambda s: s["contract_caps"][0]["accepted_kg"].update(unit="KRW"),
        lambda s: s["contract_caps"][0]["accepted_kg"].update(value="0"),
    )
    for mutate in mutations:
        changed = deepcopy(shock)
        mutate(changed)
        assert not validator.is_valid(changed)


@pytest.mark.parametrize("name", ["demand assumption", "수요 가정", "d" * 129])
def test_stored_shock_name_matches_runtime_for_valid_identifiers(name):
    schema = json.loads((ROOT / "contracts/market-scenario-v1.schema.json").read_text())
    validator = Draft202012Validator({"$ref": "#/$defs/jointShock", "$defs": schema["$defs"]})
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    shock["drivers"][1]["record_id"] = name
    encoded = json.loads(json.dumps(shock, default=lambda value: value.isoformat().replace("+00:00", "Z")))
    assert validator.is_valid(encoded)
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    assert service(repo).build_candidate(request, "tenant-1").status == "pinned"


@pytest.mark.parametrize("name", [" leading", "trailing ", "bad\x1fname", "\nleading"])
def test_stored_shock_name_rejects_surrounding_space_and_controls(name):
    schema = json.loads((ROOT / "contracts/market-scenario-v1.schema.json").read_text())
    validator = Draft202012Validator({"$ref": "#/$defs/jointShock", "$defs": schema["$defs"]})
    repo, request = case()
    shock = repo.shocks[("joint-1", "r1")]
    shock["drivers"][1]["record_id"] = name
    encoded = json.loads(json.dumps(shock, default=lambda value: value.isoformat().replace("+00:00", "Z")))
    assert not validator.is_valid(encoded)
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError):
        service(repo).build_candidate(request, "tenant-1")


def test_declared_lane_reference_edits_are_schema_valid_and_reject_bad_names():
    schema = json.loads((ROOT / "contracts/market-scenario-v1.schema.json").read_text())
    validator = Draft202012Validator({"$ref": "#/$defs/jointShock", "$defs": schema["$defs"]})
    repo, request = two_lane_case()
    shock = repo.shocks[("joint-1", "r1")]
    encoded = json.loads(json.dumps(shock, default=lambda value: value.isoformat().replace("+00:00", "Z")))
    assert validator.is_valid(encoded)
    assert service(repo).build_candidate(request, "tenant-1").status == "pinned"
    for bad in ("", " leading", "trailing ", "bad\x1fname"):
        changed = deepcopy(encoded)
        changed["drivers"][0]["changes"][-1]["reference"] = bad
        assert not validator.is_valid(changed)
        changed_shock = deepcopy(shock)
        changed_shock["drivers"][0]["changes"][-1]["reference"] = bad
        changed_repo, changed_request = two_lane_case()
        changed_repo.shocks[("joint-1", "r1")] = changed_shock
        changed_request["shock"]["sha256"] = digest(changed_shock)
        repin_shock(changed_repo)
        with pytest.raises(ValueError):
            service(changed_repo).build_candidate(changed_request, "tenant-1")
        assert changed_repo.candidates == {}


@pytest.mark.parametrize("group,event_id,field,wrong_kind", [
    ("packouts", "pack-1", "grade", "number"),
    ("packouts", "pack-1", "grade", "time"),
    ("sales", "sale-1", "channel", "number"),
    ("sales", "sale-1", "channel", "time"),
    ("packouts", "pack-1", "price", "number"),
])
def test_lane_edit_schema_and_runtime_reject_wrong_kind_or_group_field(
        group, event_id, field, wrong_kind):
    schema = json.loads((ROOT / "contracts/market-scenario-v1.schema.json").read_text())
    validator = Draft202012Validator({"$ref": "#/$defs/jointShock", "$defs": schema["$defs"]})
    repo, request = two_lane_case()
    shock = repo.shocks[("joint-1", "r1")]
    encoded = json.loads(json.dumps(shock, default=lambda value: value.isoformat().replace("+00:00", "Z")))
    assert validator.is_valid(encoded)
    assert any(change["field"] == "grade" and "reference" in change
               for change in shock["drivers"][0]["changes"])
    assert any(change["field"] == "channel" and "reference" in change
               for change in shock["drivers"][1]["changes"])
    wrong_value = replacement(3, "wrong-lane-kind", "kg") if wrong_kind == "number" else DECISION
    driver_index = 0 if group == "packouts" else 1
    changes = shock["drivers"][driver_index]["changes"]
    target = next(change for change in changes
                  if change["event_group"] == group and change["event_id"] == event_id
                  and change["field"] == ("grade" if group == "packouts" else "channel"))
    target["field"] = field
    target.pop("reference")
    target[wrong_kind] = wrong_value
    encoded = json.loads(json.dumps(shock, default=lambda value: value.isoformat().replace("+00:00", "Z")))
    assert not validator.is_valid(encoded)
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError, match="unsupported event field or edit type"):
        service(repo).build_candidate(request, "tenant-1")
    assert repo.candidates == {}


def test_edit_schema_matches_all_runtime_group_field_value_kinds():
    from app.market_scenario import _FIELDS

    schema = json.loads((ROOT / "contracts/market-scenario-v1.schema.json").read_text())
    validator = Draft202012Validator({"$ref": "#/$defs/edit", "$defs": schema["$defs"]})
    number = json.loads(json.dumps(replacement(1, "edit-kind", "kg"),
                                   default=lambda value: value.isoformat().replace("+00:00", "Z")))
    values = {"number": number,
              "time": "2026-09-27T00:00:00Z", "reference": "grade-1"}
    all_fields = {field for fields in _FIELDS.values() for field in fields}
    for group, fields in _FIELDS.items():
        for field in all_fields:
            expected_kind = fields.get(field)
            base = {"event_group": group, "event_id": "event-1", "field": field}
            for kind, value in values.items():
                assert validator.is_valid({**base, kind: value}) is (kind == expected_kind), (group, field, kind)
            if expected_kind is not None:
                other_kind = next(kind for kind in values if kind != expected_kind)
                assert not validator.is_valid({**base, expected_kind: values[expected_kind],
                                               other_kind: values[other_kind]})


@pytest.mark.parametrize("grade,channel", [
    ("grade-3", "wholesale"), ("grade-1", "wholesale"),
])
def test_reference_edits_cannot_create_new_baseline_grade_channel_pair(grade, channel):
    repo, request = two_lane_case()
    shock = repo.shocks[("joint-1", "r1")]
    for change in shock["drivers"][0]["changes"]:
        if change["field"] in ("grade", "channel"):
            change["reference"] = grade if change["field"] == "grade" else channel
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError, match="lane|grade|channel"):
        service(repo).build_candidate(request, "tenant-1")
    assert repo.candidates == {}


def test_revised_sale_lane_must_match_contract_cap_before_pin():
    repo, request = two_lane_case()
    shock = repo.shocks[("joint-1", "r1")]
    shock["contract_caps"][0]["channel"] = "direct"
    request["shock"]["sha256"] = digest(shock)
    repin_shock(repo)
    with pytest.raises(ValueError, match="contract cap"):
        service(repo).build_candidate(request, "tenant-1")
    assert repo.candidates == {}
