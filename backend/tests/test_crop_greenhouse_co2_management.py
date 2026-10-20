"""Independent removal and real CO2/Solar pre/post event composition."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
from importlib import import_module
import json
from math import fsum, inf
from pathlib import Path
import runpy

import pytest

from app import crop_greenhouse_co2_joint as rhs
from app import crop_greenhouse_co2_integration as solver
from app import crop_climate_joint_management as previous
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT = Path(__file__).resolve().parents[2]
SOURCE = json.loads((ROOT / "fixtures/crop-climate-joint-management-reference-cases-v1.json").read_bytes())
TEMPLATE = json.loads((ROOT / "fixtures/crop-greenhouse-co2-integration-reference-cases-v1.json").read_bytes())["cases"][0]


@pytest.fixture(scope="module")
def model(): return import_module("app.crop_greenhouse_co2_management")


@pytest.fixture(scope="module")
def profiles():
    return {key: kind((ROOT / "fixtures" / name).read_bytes()) for key, kind, name in (
        ("growth_profile", Growth, "crop-growth-reference-parameters-v1.json"),
        ("cohort_profile", Cohort, "crop-fruit-cohort-reference-parameters-v1.json"),
        ("transport_profile", Transport, "crop-fruit-transport-reference-parameters-v1.json"),
        ("exchange_profile", Exchange, "crop-canopy-exchange-reference-parameters-v1.json"))}


def inputs(index=0, basis="wet"):
    c = deepcopy(SOURCE["cases"][index]); template = deepcopy(TEMPLATE)
    s = c["scenario"]
    s["forcing"]["canopy_non_solar_heat"] = s["forcing"].pop("canopy_external_heat")
    del s["forcing"]["par_above_canopy"]; del s["forcing"]["co2"]
    s["climate_state"]["air_co2_mass"] = {"value": 2500.0, "unit": "mg_CO2/m2_floor"}
    template["co2"]["basis"] = basis
    return {"scenario": s, "event": c["event"], **{k: template[k] for k in ("solar", "ventilation", "co2")}}


def state(s):
    return list(solver.core._state(s)) + [s["climate_state"]["air_co2_mass"]["value"]]


@pytest.mark.parametrize("index", range(9), ids=[c["case_id"] for c in SOURCE["cases"]])
@pytest.mark.parametrize("basis", ["wet", "dry"])
def test_independent_event_states_removed_inventories_and_gas(model, profiles, index, basis):
    args = inputs(index, basis); before = deepcopy(args)
    actual = model.apply_management(**args, **profiles); expected = SOURCE["cases"][index]["expected_decimal"]
    for found, text in zip(state(actual["after"]["scenario"]), [*expected["state"], "2500"], strict=True):
        assert found == pytest.approx(float(text), rel=5e-12, abs=5e-14)
    for key, target in expected["removed"].items():
        pairs = zip(actual["removed"][key], target, strict=True) if isinstance(target, list) else [(actual["removed"][key], target)]
        for row, text in pairs: assert row["value"] == pytest.approx(float(text), rel=5e-12, abs=5e-14)
    for key, text in expected["totals"].items():
        assert actual["removed_totals"][key]["value"] == pytest.approx(float(text), rel=5e-12, abs=5e-14)
    with localcontext() as context:
        context.prec = 80
        equivalent = Decimal(expected["totals"]["carbohydrate"]) * Decimal(44) / Decimal(30)
        s = args["scenario"]; p, c = s["parameters"], s["climate_state"]
        v = lambda q: Decimal(str(q["value"]))
        height, kelvin = v(p["air_volume_per_floor_area"]), v(c["air_temperature"]) + Decimal("273.15")
        vapor = v(c["air_vapor_mass"]) / height * v(p["vapor_gas_constant"]) * kelvin
        pressure = Decimal(101325) - (vapor if basis == "dry" else 0)
        ppm = (Decimal(2500) / height) * Decimal("8.3144598") * kelvin / (Decimal("0.04401") * pressure)
    assert actual["removed_totals"]["co2_basis_carbohydrate"]["value"] == pytest.approx(float(equivalent), rel=5e-12, abs=5e-14)
    assert actual["after"]["derived"]["crop_co2_ppm"]["value"] == pytest.approx(float(ppm), rel=3e-15, abs=0)
    for key, text in expected["derived"].items():
        assert actual["after"]["derived"][key]["value"] == pytest.approx(float(text), rel=5e-12, abs=5e-14)
    assert abs(actual["after"]["derived"]["canopy_temperature"]["value"] - float(expected["derived"]["canopy_temperature"])) <= 2e-13
    assert len(actual["balance_residuals"]) == 10
    for key, row in actual["balance_residuals"].items(): assert abs(row["value"]) <= actual["balance_budgets"][key]["value"]
    for key in ("air_temperature", "air_vapor_mass", "air_co2_mass"):
        assert actual["before"]["scenario"]["climate_state"][key] == actual["after"]["scenario"]["climate_state"][key]
    assert actual["before"]["derived"]["crop_co2_ppm"] == actual["after"]["derived"]["crop_co2_ppm"]
    assert actual["G0_G4"] == "not_assessed" and actual["scope"] == "software_research_only"
    assert args == before and model.apply_management(**args, **profiles) == actual


def test_two_actual_new_rhs_and_reduced_LAI_optics_no_old_management(model, profiles, monkeypatch):
    calls = []; original = rhs.evaluate_rhs
    def capture(**kwargs):
        result = original(**kwargs); calls.append(result); return result
    def forbidden(**kwargs): raise AssertionError("old fixed-ppm management was called")
    monkeypatch.setattr(rhs, "evaluate_rhs", capture); monkeypatch.setattr(previous, "apply_management", forbidden)
    result = model.apply_management(**inputs(1), **profiles)
    assert len(calls) == 2 and result["after_rhs"] is calls[1]
    a, b = (r["solar_rhs"] for r in calls)
    assert b["joint_rhs"]["derived"]["leaf_area_index"]["value"] < a["joint_rhs"]["derived"]["leaf_area_index"]["value"]
    for key in ("canopy_absorbed_par", "canopy_absorbed_nir"):
        assert a["heat_composition"][key] != b["heat_composition"][key]
    assert result["after"]["calculation_sha256"] == calls[1]["calculation_sha256"]


def test_zero_event_is_identity(model, profiles):
    result = model.apply_management(**inputs(0), **profiles)
    assert result["before"] == result["after"]
    assert all(row["value"] == 0 for row in result["removed_totals"].values())


def test_independent_source_pins():
    path = ROOT / "fixtures/crop-climate-joint-management-reference-cases-v1.json"
    assert sha256(path.read_bytes()).hexdigest() == "74f3aa4e9f75acc83a60c2c8bfecd3aadfc7a4359685b3e4e2ab45c6f93eb747"
    assert sha256((ROOT / "research/crop-climate-joint-management-reference.py").read_bytes()).hexdigest() == "7982b0af6adc72a894255db06e7b4b3db2088a4fe58c84830a87b37235ed0fa4"


@pytest.mark.parametrize("fault", ["origin", "leaf-over", "leaf-all", "negative", "bool", "infinite", "unit",
    "fraction-shape", "fraction-over", "fraction-negative", "fraction-lost", "extra", "profile"])
def test_atomic_failure_keeps_pre_event_state(model, profiles, fault):
    args = inputs(4); p = dict(profiles); e = args["event"]["values"]
    if fault == "origin": args["event"]["origin"] = "reference_calculation"
    elif fault == "leaf-over": e["leaf"]["value"] = args["scenario"]["plant_state"]["leaf"]["value"] + 1
    elif fault == "leaf-all": e["leaf"]["value"] = args["scenario"]["plant_state"]["leaf"]["value"]
    elif fault == "negative": e["stem_root"]["value"] = -1
    elif fault == "bool": e["leaf"]["value"] = True
    elif fault == "infinite": e["stem_root"]["value"] = inf
    elif fault == "unit": e["leaf"]["unit"] = "mg_CO2/m2_floor"
    elif fault == "fraction-shape": e["fruit_fraction"].pop()
    elif fault == "fraction-over": e["fruit_fraction"][0]["value"] = 1.01
    elif fault == "fraction-negative": e["fruit_fraction"][0]["value"] = -0.1
    elif fault == "fraction-lost":
        for row in e["fruit_fraction"]: row["value"] = 1e-200
    elif fault == "extra": e["air_co2_mass"] = {"value": 1, "unit": "mg_CO2/m2_floor"}
    else: p["growth_profile"] = None
    before = deepcopy(args)
    with pytest.raises(model.Co2ManagementHold) as caught: model.apply_management(**args, **p)
    assert args == before
    if fault == "profile": assert caught.value.last_confirmed is None
    else: assert caught.value.last_confirmed["scenario"] == args["scenario"]


def test_actual32s_composition_matches_independent_decimal_and_combined_carbon(model, profiles):
    args = inputs(4)
    first = solver.integrate(**{k: args[k] for k in ("scenario", "solar", "ventilation", "co2")}, step_seconds=2, step_count=8, **profiles)
    current = deepcopy(args)
    for key in ("plant_state", "cohort_state", "climate_state"): current["scenario"][key] = first["samples"][-1][key]
    event = model.apply_management(**current, **profiles)
    second = solver.integrate(**{k: event["after"][k] for k in ("scenario", "solar", "ventilation", "co2")}, step_seconds=2, step_count=8, **profiles)
    ref = runpy.run_path(str(ROOT / "research/crop-greenhouse-co2-integration-reference.py"))
    removal = runpy.run_path(str(ROOT / "research/crop-climate-joint-management-reference.py"))["removal"]
    with localcontext() as context:
        context.prec = 80; env = ref["environment"]()
        a = ref["trajectory"](args["scenario"], args["solar"], args["ventilation"], args["co2"], Decimal(2), 8, env)
        y = tuple(map(Decimal, a["state"])); prior = env["env"]["base"]["prior"]; core_env = env["env"]["base"]["env"]
        s = prior["trial"](args["scenario"], y[:108])
        s["climate_state"]["air_co2_mass"] = {"value": y[108], "unit": "mg_CO2/m2_floor"}
        after, _ = removal(s, args["event"], prior, core_env)
        after["climate_state"]["air_co2_mass"] = s["climate_state"]["air_co2_mass"]
        b = ref["trajectory"](after, args["solar"], args["ventilation"], args["co2"], Decimal(2), 8, env)
        expected_transfers = {k: Decimal(a["integrated_transfers"][k]) + Decimal(b["integrated_transfers"][k]) for k in a["integrated_transfers"]}
    for found, text in zip(state(second["samples"][-1]), b["state"], strict=True):
        assert found == pytest.approx(float(text), rel=5e-12, abs=5e-14)
    total = {k: fsum((first["integrated_transfers"][k]["value"], second["integrated_transfers"][k]["value"])) for k in expected_transfers}
    for key, expected in expected_transfers.items(): assert total[key] == pytest.approx(float(expected), rel=5e-12, abs=5e-14)
    initial, final = state(args["scenario"]), state(second["samples"][-1])
    carbon = lambda y: fsum((*y[:3], *y[5:55]))
    removed = event["removed_totals"]["carbohydrate"]["value"]
    combined = fsum((final[108], -initial[108], 44 / 30 * fsum((carbon(final), -carbon(initial), removed,
        total["removal_leaf"], total["removal_stem_root"], total["terminal_fruit_carbohydrate"])),
        -total["co2_ventilation_to_air"], -total["co2_external_to_air"]))
    assert abs(combined) <= 1e-7
