"""Net gas exchange from independent references and actual current crop families."""
from copy import deepcopy
from decimal import Decimal, localcontext
from importlib import import_module
import json
from math import fsum, inf, nan
from pathlib import Path

import pytest

from app import crop_growth_rates as organ
from app import crop_plant_cohort_rates as cohort
from app import crop_plant_startup_rates as startup
from app import crop_climate_joint_rhs as joint
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters
from app.crop_canopy_exchange import ReferenceParameters as ExchangeParameters

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"
RAW = (FIXTURES / "crop-growth-reference-parameters-v1.json").read_bytes()
PARAMETERS = json.loads(RAW)["parameters"]
PROFILES = {
    "growth_profile": organ.ReferenceParameters(RAW),
    "cohort_profile": ReferenceFruitCohortParameters((FIXTURES / "crop-fruit-cohort-reference-parameters-v1.json").read_bytes()),
    "transport_profile": ReferenceFruitTransportParameters((FIXTURES / "crop-fruit-transport-reference-parameters-v1.json").read_bytes()),
}
FAMILIES = {
    "organ": ("crop-growth-reference-cases-v1.json", None),
    "cohort": ("crop-plant-cohort-reference-cases-v1.json", cohort.calculate_plant_cohort_rates),
    "startup": ("crop-plant-startup-reference-cases-v1.json", startup.calculate_plant_startup_rates),
}
CASES = [(family, case) for family, (name, _) in FAMILIES.items()
         for case in json.loads((FIXTURES / name).read_text())["cases"]]


@pytest.fixture(scope="module")
def gas():
    return import_module("app.crop_co2_net_exchange")


def produce(family, case):
    if family == "organ":
        return organ.calculate_rates(**{k: case[k] for k in ("state", "forcing", "removals")},
                                     profile=PROFILES["growth_profile"])
    return FAMILIES[family][1](**{k: case[k] for k in ("state", "cohort_state", "forcing", "removals", "fruit_entry")}, **PROFILES)


def independent_expected(family, case):
    with localcontext() as context:
        context.prec = 80
        expected = case["expected"]
        if family == "organ":
            maintenance = sum(Decimal(q) for q in expected["maintenance_respiration"].values())
        else:
            # Reconstruct vegetative maintenance directly from the source parameters;
            # aggregate fruit respiration is supplied by the independent cohort oracle.
            p = lambda key: Decimal(str(PARAMETERS[key]["value"]))
            state = case["state"]["values"]
            t24 = Decimal(str(state["temperature_filtered_24h"]["value"]))
            factor = (1 - (-p("cRgr") * p("rgr")).exp()) * (
                p("q10m").ln() * (t24 - p("maintenance_temperature_reference_c")) /
                p("q10_temperature_interval_c")).exp()
            maintenance = factor * sum(Decimal(str(state[key]["value"])) * p(coefficient)
                                      for key, coefficient in (("leaf", "cLeafM"), ("stem_root", "cStemM")))
            maintenance += Decimal(expected["fruit_maintenance"])
        net = Decimal(expected["photosynthesis"]) - Decimal(expected["growth_respiration"]) - maintenance
        return float(net * Decimal(44) / Decimal(30))


@pytest.mark.parametrize("family,case", CASES, ids=[f"{f}-{c['case_id']}" for f, c in CASES])
def test_all_independent_crop_family_references(gas, family, case):
    rates = produce(family, case)
    before = deepcopy(rates)
    result = gas.calculate_exchange(rates=rates)
    actual = result["co2"]["net_crop_uptake"]["value"]
    assert actual == pytest.approx(independent_expected(family, case), rel=5e-12, abs=5e-14)
    maintenance = (rates["maintenance_respiration"] if family == "organ" else
                   {**rates["vegetative_maintenance"], "fruit": rates["fruit_maintenance"]})
    with localcontext() as context:
        context.prec = 80
        exact = (Decimal(rates["photosynthesis"]["value"]) - Decimal(rates["growth_respiration"]["value"]) -
                 sum(Decimal(q["value"]) for q in maintenance.values())) * Decimal(44) / Decimal(30)
    assert actual == pytest.approx(float(exact), rel=3e-15, abs=0)
    assert result["co2"]["air_flux"] == {"value": -actual, "unit": "mg_CO2/m2_floor/s"}
    assert result["transfer_residual"] == {"value": 0.0, "unit": "mg_CO2/m2_floor/s"}
    assert result["scope"] == "software_research_only" and result["G0_G4"] == "not_assessed"
    assert rates == before


def test_actual_dark_crop_emits_and_removal_is_not_respiration(gas):
    case = deepcopy(CASES[0][1]); case["forcing"]["values"]["par_above_canopy"]["value"] = 0
    first = gas.calculate_exchange(rates=produce("organ", case))
    case["removals"]["values"]["fruit"]["value"] = 0.1
    second = gas.calculate_exchange(rates=produce("organ", case))
    assert first["co2"]["net_crop_uptake"]["value"] < 0 < first["co2"]["air_flux"]["value"]
    assert first["co2"] == second["co2"]
    assert first["input_sha256"] != second["input_sha256"]


def test_startup_uses_realized_growth_respiration(gas):
    case = next(c for f, c in CASES if f == "startup" and c["case_id"] == "synthetic-startup-20C-empty-no-entry")
    rates = produce("startup", case); result = gas.calculate_exchange(rates=rates)
    assert rates["fruit_startup"]["deferred_carbohydrate_inflow"]["value"] > 0
    assert result["carbohydrate"]["growth_respiration"] == rates["growth_respiration"]
    assert result["co2"]["net_crop_uptake"]["value"] == pytest.approx(independent_expected("startup", case), rel=5e-12)


def test_consumes_actual_joint_stage_without_recalculating_crop(gas, monkeypatch):
    reference = json.loads((FIXTURES / "crop-climate-joint-rhs-reference-cases-v1.json").read_text())
    scenario = reference["cases"][0]["scenario"]
    result = joint.evaluate_rhs(scenario=scenario, **PROFILES,
        exchange_profile=ExchangeParameters((FIXTURES / "crop-canopy-exchange-reference-parameters-v1.json").read_bytes()))
    rates = result["crop"]; before = deepcopy(rates)
    def forbidden(**kwargs):
        raise AssertionError("adapter recalculated an existing crop stage")
    monkeypatch.setattr(organ, "calculate_rates", forbidden)
    monkeypatch.setattr(startup, "calculate_plant_startup_rates", forbidden)
    exchange = gas.calculate_exchange(rates=rates)
    assert exchange["source_identity"]["model_version"] == startup.MODEL_VERSION
    assert exchange["source_identity"]["input_sha256"] == rates["input_sha256"]
    assert rates == before


def test_exact_zero_and_convention_are_not_gas_converter_mass(gas):
    rates = produce("organ", CASES[0][1])
    rates["photosynthesis"]["value"] = 1.0
    rates["growth_respiration"]["value"] = 0.25
    for name in rates["maintenance_respiration"]:
        rates["maintenance_respiration"][name]["value"] = 0.25
    zero = gas.calculate_exchange(rates=rates)
    assert zero["co2"]["net_crop_uptake"]["value"] == 0.0
    rates["photosynthesis"]["value"] = 2.0
    assert gas.calculate_exchange(rates=rates)["co2"]["net_crop_uptake"]["value"] == pytest.approx(44 / 30, rel=3e-15)
    assert gas.CO2_MOLAR_MASS == 44e-3 and gas.CH2O_MOLAR_MASS == 30e-3


@pytest.mark.parametrize("field,value", [
    ("model_version", "unknown"), ("scope", "approved"), ("input_sha256", "bad"),
    ("profile_sha256", "0" * 64), ("photosynthesis", {"value": 1, "unit": "mg_CO2/m2_floor/s"}),
    ("photosynthesis", {"value": -1, "unit": organ.RATE_UNIT}),
    ("growth_respiration", {"value": True, "unit": organ.RATE_UNIT}),
    ("growth_respiration", {"value": inf, "unit": organ.RATE_UNIT}),
    ("growth_respiration", {"value": nan, "unit": organ.RATE_UNIT}),
])
def test_rejects_incompatible_identity_units_and_quantities(gas, field, value):
    rates = produce("organ", CASES[0][1]); rates[field] = value
    with pytest.raises(gas.Co2NetExchangeHold):
        gas.calculate_exchange(rates=rates)


@pytest.mark.parametrize("mutation", ["profiles", "components", "policy", "missing-maintenance", "extra-maintenance"])
def test_startup_identity_and_maintenance_are_explicit(gas, mutation):
    case = next(c for f, c in CASES if f == "startup")
    rates = produce("startup", case)
    if mutation == "profiles": rates["profile_sha256"]["growth_profile"] = "0" * 64
    elif mutation == "components": rates["component_model_versions"]["startup"] = "unknown"
    elif mutation == "policy": rates["policy_sha256"] = "0" * 64
    elif mutation == "missing-maintenance": del rates["vegetative_maintenance"]["leaf"]
    else: rates["vegetative_maintenance"]["fruit"] = rates["fruit_maintenance"]
    with pytest.raises(gas.Co2NetExchangeHold):
        gas.calculate_exchange(rates=rates)


def test_unrepresentable_net_flux_is_held(gas):
    rates = produce("organ", CASES[0][1]); rates["photosynthesis"]["value"] = 1.7e308
    rates["growth_respiration"]["value"] = 0.0
    for row in rates["maintenance_respiration"].values(): row["value"] = 0.0
    with pytest.raises(gas.Co2NetExchangeHold):
        gas.calculate_exchange(rates=rates)


def test_mutating_output_does_not_change_source_rates(gas):
    case = next(c for f, c in CASES if f == "startup")
    rates = produce("startup", case); before = deepcopy(rates)
    result = gas.calculate_exchange(rates=rates)
    result["source_identity"]["profile_sha256"]["growth_profile"] = "changed"
    result["carbohydrate"]["maintenance_respiration"]["leaf"]["value"] = 0
    assert rates == before
