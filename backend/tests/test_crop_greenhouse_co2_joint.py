"""Independent full Solar derivatives with current CO2 mass feedback."""
from copy import deepcopy
from decimal import Decimal, localcontext
from importlib import import_module
from hashlib import sha256
import json
from math import inf
from pathlib import Path
import runpy

import pytest

from app import crop_greenhouse_solar_joint as solar_rhs
from app import crop_co2_gas as gas
from app import crop_co2_net_exchange as net
from app import crop_co2_air_mass as air
from app import crop_plant_startup_rates as startup
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "fixtures/crop-greenhouse-solar-integration-reference-cases-v1.json").read_bytes())["cases"]
PLANT = ("buffer", "leaf", "stem_root", "temperature_filtered_24h", "temperature_sum")
OLD_CLIMATE = ("canopy_sensible_energy", "air_temperature", "air_vapor_mass")


def q(value, unit):
    return {"value": value, "unit": unit}


def inputs(index=0, basis="wet"):
    case = deepcopy(CASES[index])
    result = {k: case[k] for k in ("scenario", "solar", "ventilation")}
    result["scenario"]["forcing"].pop("co2")
    result["scenario"]["climate_state"]["air_co2_mass"] = q(2500, "mg_CO2/m2_floor")
    result["co2"] = {"input_id": "synthetic-co2-stage", "origin": "synthetic", "basis": basis,
                     "parameters": {"air_pressure": q(101325, "Pa")},
                     "forcing": {"outdoor_co2_density": q(700, "mg_CO2/m3"),
                                 "external_co2_flux": q(0.4, "mg_CO2/m2_floor/s")}}
    return result


@pytest.fixture(scope="module")
def model():
    return import_module("app.crop_greenhouse_co2_joint")


@pytest.fixture(scope="module")
def profiles():
    return {key: kind((ROOT / "fixtures" / name).read_bytes()) for key, kind, name in (
        ("growth_profile", Growth, "crop-growth-reference-parameters-v1.json"),
        ("cohort_profile", Cohort, "crop-fruit-cohort-reference-parameters-v1.json"),
        ("transport_profile", Transport, "crop-fruit-transport-reference-parameters-v1.json"),
        ("exchange_profile", Exchange, "crop-canopy-exchange-reference-parameters-v1.json"))}


@pytest.fixture(scope="module")
def independent():
    oracle = runpy.run_path(str(ROOT / "research/crop-greenhouse-solar-integration-reference.py"))
    return oracle, oracle["environment"]()


def reference(args, independent):
    oracle, env = independent
    s, co2 = deepcopy(args["scenario"]), args["co2"]
    with localcontext() as context:
        context.prec = 80
        v = lambda row: Decimal(str(row["value"]))
        p, c = s["parameters"], s["climate_state"]
        height, kelvin = v(p["air_volume_per_floor_area"]), v(c["air_temperature"]) + Decimal("273.15")
        density = v(c.pop("air_co2_mass")) / height
        water = v(c["air_vapor_mass"]) / height * v(p["vapor_gas_constant"]) * kelvin
        pressure = v(co2["parameters"]["air_pressure"])
        total_moles = pressure / (Decimal("8.3144598") * kelvin)
        if co2["basis"] == "dry": total_moles -= water / (Decimal("8.3144598") * kelvin)
        ppm = (density / Decimal(1000) / Decimal("44.01")) / total_moles * Decimal("1e6")
        s["forcing"]["co2"] = q(ppm, "ppm")
        y = env["base"]["prior"]["initial"](s)
        result = oracle["rhs"](s, args["solar"], args["ventilation"], y, env)
        uptake = (result[108] - result[109] - sum(result[110:113])) * Decimal(44) / Decimal(30)
        flow = v(args["ventilation"]["forcing"]["volume_exchange_per_floor_area"])
        ventilation = flow * (v(co2["forcing"]["outdoor_co2_density"]) - density)
        mass_rate = ventilation + v(co2["forcing"]["external_co2_flux"]) - uptake
        return tuple(map(float, result[:108])) + (float(mass_rate),), tuple(map(float, (density, water, ppm, uptake)))


def flatten(result):
    d = result["derivatives"]
    return tuple([d["plant"][key]["value"] for key in PLANT] +
                 [row["value"] for key in ("fruit_carbohydrate", "fruit_number") for row in d["cohorts"][key]] +
                 [d["climate"][key]["value"] for key in (*OLD_CLIMATE, "air_co2_mass")])


@pytest.mark.parametrize("index", range(len(CASES)), ids=[c["case_id"] for c in CASES])
@pytest.mark.parametrize("basis", ["wet", "dry"])
def test_independent_full109_derivatives_and_gas_diagnostics(model, profiles, independent, index, basis):
    args = inputs(index, basis); before = deepcopy(args)
    actual = model.evaluate_rhs(**args, **profiles); expected, diag = reference(args, independent)
    assert len(flatten(actual)) == 109
    for value, target in zip(flatten(actual), expected, strict=True):
        assert value == pytest.approx(target, rel=5e-12, abs=5e-14)
    for key, target in zip(("air_co2_density", "air_vapor_pressure", "crop_co2_ppm"), diag[:3], strict=True):
        assert actual["derived"][key]["value"] == pytest.approx(target, rel=3e-15, abs=0)
    assert actual["net_exchange"]["co2"]["net_crop_uptake"]["value"] == pytest.approx(diag[3], rel=5e-12, abs=5e-14)
    assert len(actual["balance_residuals"]) == 9
    for key, quantity in actual["balance_residuals"].items():
        assert abs(quantity["value"]) <= actual["balance_budgets"][key]["value"]
    assert actual["state_schema_version"] == "crop-solar-co2-stage-state-v1"
    assert actual["scope"] == "software_research_only" and actual["G0_G4"] == "not_assessed"
    assert "co2" not in actual["scenario"]["forcing"]
    assert args == before and model.evaluate_rhs(**args, **profiles) == actual


def test_actual_single_calls_same_current_state_and_original_solar_result(model, profiles, monkeypatch):
    seen = {}
    for module, name, label in ((solar_rhs, "evaluate_rhs", "solar"), (gas, "density_to_ppm", "gas"),
            (net, "calculate_exchange", "net"), (air, "evaluate_rhs", "air"),
            (solar_rhs.par.radiation, "calculate_par", "PAR"), (solar_rhs.nir, "calculate_nir", "NIR"),
            (solar_rhs.vent, "calculate_ventilation", "vent"), (solar_rhs.joint, "evaluate_rhs", "joint"),
            (startup, "calculate_plant_startup_rates", "crop")):
        original = getattr(module, name); seen[label] = []
        def capture(*, _original=original, _label=label, **kwargs):
            result = _original(**kwargs); seen[_label].append((kwargs, result)); return result
        monkeypatch.setattr(module, name, capture)
    args = inputs(basis="dry"); result = model.evaluate_rhs(**args, **profiles)
    assert all(len(calls) == 1 for calls in seen.values())
    base = result["solar_rhs"]["joint_rhs"]
    assert seen["gas"][0][0]["temperature_c"] == args["scenario"]["climate_state"]["air_temperature"]["value"]
    assert seen["gas"][0][0]["water_vapor_pressure_pa"] == base["derived"]["air_vapor_pressure"]["value"]
    assert seen["net"][0][0]["rates"] is base["crop"]
    assert seen["air"][0][0]["crop_exchange"] is result["net_exchange"]
    assert seen["air"][0][0]["forcing"]["volume_exchange_per_floor_area"] == result["solar_rhs"]["ventilation"]["forcing"]["volume_exchange_per_floor_area"]
    for key, value in base["balance_residuals"].items():
        assert result["balance_residuals"][key] == value
        assert result["balance_budgets"][key] == base["balance_budgets"][key]
    assert result["code_sha256"] == sha256(Path(model.__file__).read_bytes()).hexdigest()


def test_mass_pressure_basis_response_and_same_derived_ppm_old_solar_equivalence(model, profiles):
    args = inputs(); first = model.evaluate_rhs(**args, **profiles)
    old = deepcopy(args["scenario"]); del old["climate_state"]["air_co2_mass"]
    old["forcing"]["co2"] = first["derived"]["crop_co2_ppm"]
    assert solar_rhs.evaluate_rhs(scenario=old, solar=args["solar"], ventilation=args["ventilation"], **profiles) == first["solar_rhs"]
    variants = []
    more = deepcopy(args); more["scenario"]["climate_state"]["air_co2_mass"]["value"] *= 1.2; variants.append(more)
    low_p = deepcopy(args); low_p["co2"]["parameters"]["air_pressure"]["value"] = 85000; variants.append(low_p)
    dry = deepcopy(args); dry["co2"]["basis"] = "dry"; variants.append(dry)
    for variant in variants:
        changed = model.evaluate_rhs(**variant, **profiles)
        assert changed["derived"]["crop_co2_ppm"]["value"] > first["derived"]["crop_co2_ppm"]["value"]
        assert changed["solar_rhs"]["joint_rhs"]["crop"]["photosynthesis"]["value"] > first["solar_rhs"]["joint_rhs"]["crop"]["photosynthesis"]["value"]
        assert changed["solar_rhs"]["heat_composition"] == first["solar_rhs"]["heat_composition"]
        assert changed["input_sha256"] != first["input_sha256"]


@pytest.mark.parametrize("fault", ["fixed-ppm", "missing-mass", "mass-unit", "zero-mass", "negative-mass",
    "bool-mass", "inf-mass", "missing-pressure", "zero-pressure", "vapor-exceeds-pressure", "basis", "origin",
    "blank-id", "extra-vapor", "outdoor-unit", "negative-outdoor", "external-inf", "profile", "weather-flow"])
def test_closed_domain_basis_and_propagated_old_holds(model, profiles, fault):
    args, p = inputs(), dict(profiles); c = args["co2"]; climate = args["scenario"]["climate_state"]
    if fault == "fixed-ppm": args["scenario"]["forcing"]["co2"] = q(500, "ppm")
    elif fault == "missing-mass": del climate["air_co2_mass"]
    elif fault == "mass-unit": climate["air_co2_mass"]["unit"] = "mg_CO2/m3"
    elif fault == "zero-mass": climate["air_co2_mass"]["value"] = 0
    elif fault == "negative-mass": climate["air_co2_mass"]["value"] = -1
    elif fault == "bool-mass": climate["air_co2_mass"]["value"] = True
    elif fault == "inf-mass": climate["air_co2_mass"]["value"] = inf
    elif fault == "missing-pressure": c["parameters"].clear()
    elif fault == "zero-pressure": c["parameters"]["air_pressure"]["value"] = 0
    elif fault == "vapor-exceeds-pressure": c["parameters"]["air_pressure"]["value"] = 1
    elif fault == "basis": c["basis"] = "unknown"
    elif fault == "origin": c["origin"] = "reference_calculation"
    elif fault == "blank-id": c["input_id"] = " "
    elif fault == "extra-vapor": c["parameters"]["water_vapor_pressure"] = q(1, "Pa")
    elif fault == "outdoor-unit": c["forcing"]["outdoor_co2_density"]["unit"] = "ppm"
    elif fault == "negative-outdoor": c["forcing"]["outdoor_co2_density"]["value"] = -1
    elif fault == "external-inf": c["forcing"]["external_co2_flux"]["value"] = inf
    elif fault == "profile": p["growth_profile"] = None
    else: args["ventilation"]["forcing"]["volume_exchange_per_floor_area"]["value"] = -1
    with pytest.raises(model.Co2JointHold): model.evaluate_rhs(**args, **p)


def test_impossible_combined_water_co2_mixture_is_held(model, profiles):
    args = inputs(); s = args["scenario"]; height = s["parameters"]["air_volume_per_floor_area"]["value"]
    temperature = s["climate_state"]["air_temperature"]["value"] + 273.15
    s["climate_state"]["air_co2_mass"]["value"] = 995000 * 0.04401 * 101325 / (8.3144598 * temperature) * height
    with pytest.raises(model.Co2JointHold): model.evaluate_rhs(**args, **profiles)


def test_nonzero_biomass_removal_preserves_gas_exchange_and_combined_ledger(model, profiles, independent):
    args = inputs(); first = model.evaluate_rhs(**args, **profiles)
    args["scenario"]["removals"]["leaf"]["value"] = 0.05
    args["scenario"]["removals"]["stem_root"]["value"] = 0.02
    removed = model.evaluate_rhs(**args, **profiles)
    expected, _ = reference(args, independent)
    for value, target in zip(flatten(removed), expected, strict=True):
        assert value == pytest.approx(target, rel=5e-12, abs=5e-14)
    assert removed["net_exchange"]["co2"] == first["net_exchange"]["co2"]
    assert removed["derivatives"]["climate"]["air_co2_mass"] == first["derivatives"]["climate"]["air_co2_mass"]
    assert abs(removed["balance_residuals"]["crop_air_carbon_equivalent"]["value"]) <= removed["balance_budgets"]["crop_air_carbon_equivalent"]["value"]
