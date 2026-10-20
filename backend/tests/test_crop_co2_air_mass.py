"""Independent total-inventory and analytic checks for the fixed-volume RHS."""
from copy import deepcopy
from decimal import Decimal, localcontext
from importlib import import_module
import json
from math import inf
from pathlib import Path

import pytest

from app import crop_co2_net_exchange as net
from app import crop_climate_joint_rhs as joint
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_canopy_exchange import ReferenceParameters as Exchange
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport


def q(value, unit):
    return {"value": value, "unit": unit}


def inputs(mass=2000, height=3, outdoor=450, flow=0.02, external=0):
    return {"state": {"air_co2_mass": q(mass, "mg_CO2/m2_floor")},
            "parameters": {"air_volume_per_floor_area": q(height, "m3/m2_floor")},
            "forcing": {"outdoor_co2_density": q(outdoor, "mg_CO2/m3"),
                        "volume_exchange_per_floor_area": q(flow, "m3/m2_floor/s"),
                        "external_co2_flux": q(external, "mg_CO2/m2_floor/s")},
            "crop_exchange": None}


@pytest.fixture(scope="module")
def air():
    return import_module("app.crop_co2_air_mass")


@pytest.mark.parametrize("mass,height,outdoor,flow,external", [
    (2000, 3, 450, 0, 0), (2000, 3, 450, 0.02, 0),
    (600, 3, 450, 0.02, 0), (1500, 3, 500, 0.02, 0),
    (2000, 3, 450, 0, 2.4), (2000, 3, 450, 0, -2.4),
    (0, 3, 450, 0.02, 0), (2000, 5.5, 0, 0.03, -0.1),
])
def test_independent_total_mass_volume_and_floor_area(air, mass, height, outdoor, flow, external):
    args = inputs(mass, height, outdoor, flow, external); before = deepcopy(args)
    result = air.evaluate_rhs(**args)
    with localcontext() as context:
        context.prec = 80
        area = Decimal(17); volume = Decimal(height) * area
        total_mass = Decimal(mass) * area
        total_volume_flow = Decimal(flow) * area
        ventilation_total = total_volume_flow * (Decimal(outdoor) - total_mass / volume)
        rate = (ventilation_total + Decimal(external) * area) / area
        expected_density = total_mass / volume
        expected_ventilation = ventilation_total / area
    assert result["derivatives"]["air_co2_mass"]["value"] == pytest.approx(float(rate), rel=3e-15, abs=0)
    assert result["air_co2_density"]["value"] == pytest.approx(float(expected_density), rel=3e-15, abs=0)
    assert result["transfers"]["ventilation_to_air"]["value"] == pytest.approx(float(expected_ventilation), rel=3e-15, abs=0)
    assert result["transfers"]["ventilation_to_outdoor"]["value"] == -result["transfers"]["ventilation_to_air"]["value"]
    assert abs(result["balance_residual"]["value"]) <= result["balance_budget"]["value"]
    assert result["scope"] == "software_research_only" and result["G0_G4"] == "not_assessed"
    assert args == before


def test_no_flux_preserves_mass_for_distinct_explicit_volumes(air):
    first = air.evaluate_rhs(**inputs(flow=0))
    second = air.evaluate_rhs(**inputs(height=6, flow=0))
    assert first["derivatives"]["air_co2_mass"]["value"] == second["derivatives"]["air_co2_mass"]["value"] == 0
    assert second["air_co2_density"]["value"] == first["air_co2_density"]["value"] / 2


def test_constant_exchange_matches_analytic_mass_decay(air):
    def integrate(step):
        mass = 2000.0
        def rhs(value):
            return air.evaluate_rhs(**inputs(mass=value))["derivatives"]["air_co2_mass"]["value"]
        for _ in range(int(100 / step)):
            a = rhs(mass); b = rhs(mass + step * a / 2)
            c = rhs(mass + step * b / 2); d = rhs(mass + step * c)
            mass += step * (a + 2 * b + 2 * c + d) / 6
        return mass
    with localcontext() as context:
        context.prec = 80
        exact = Decimal(1350) + Decimal(650) * (-Decimal("0.02") * Decimal(100) / Decimal(3)).exp()
    coarse, fine = (abs(integrate(step) - float(exact)) for step in (10, 5))
    assert fine < coarse and 14 < coarse / fine < 18


@pytest.mark.parametrize("light", [None, 0], ids=["day-uptake", "night-emission"])
def test_actual_joint_crop_net_flux_cancels_air_transfer(air, monkeypatch, light):
    root = Path(__file__).resolve().parents[2] / "fixtures"
    profiles = {"growth_profile": Growth((root / "crop-growth-reference-parameters-v1.json").read_bytes()),
                "cohort_profile": Cohort((root / "crop-fruit-cohort-reference-parameters-v1.json").read_bytes()),
                "transport_profile": Transport((root / "crop-fruit-transport-reference-parameters-v1.json").read_bytes()),
                "exchange_profile": Exchange((root / "crop-canopy-exchange-reference-parameters-v1.json").read_bytes())}
    scenario = json.loads((root / "crop-climate-joint-rhs-reference-cases-v1.json").read_text())["cases"][0]["scenario"]
    if light is not None:
        scenario["forcing"]["par_above_canopy"]["value"] = light
    crop = joint.evaluate_rhs(scenario=scenario, **profiles)["crop"]
    exchange = net.calculate_exchange(rates=crop)
    def forbidden(**kwargs):
        raise AssertionError("air RHS recalculated net crop exchange")
    monkeypatch.setattr(net, "calculate_exchange", forbidden)
    args = inputs(flow=0); args["crop_exchange"] = exchange; before = deepcopy(args)
    result = air.evaluate_rhs(**args)
    uptake = exchange["co2"]["net_crop_uptake"]["value"]
    assert (uptake > 0 if light is None else uptake < 0)
    assert result["derivatives"]["air_co2_mass"]["value"] == -uptake
    assert result["transfers"]["crop_uptake"] == exchange["co2"]["net_crop_uptake"]
    assert result["balance_residual"]["value"] == 0
    assert args == before


@pytest.mark.parametrize("block,field,value", [
    ("state", "air_co2_mass", -1), ("state", "air_co2_mass", True),
    ("state", "air_co2_mass", inf), ("parameters", "air_volume_per_floor_area", 0),
    ("parameters", "air_volume_per_floor_area", -1), ("forcing", "outdoor_co2_density", -1),
    ("forcing", "volume_exchange_per_floor_area", -0.1), ("forcing", "external_co2_flux", "0"),
])
def test_invalid_domains_and_types_are_held(air, block, field, value):
    args = inputs(); args[block][field]["value"] = value
    with pytest.raises(air.Co2AirMassHold): air.evaluate_rhs(**args)


@pytest.mark.parametrize("block,field,unit", [
    ("state", "air_co2_mass", "mg_CO2/m3"),
    ("parameters", "air_volume_per_floor_area", "m3"),
    ("forcing", "volume_exchange_per_floor_area", "m3/s"),
])
def test_total_density_and_floor_area_units_cannot_be_mixed(air, block, field, unit):
    args = inputs(); args[block][field]["unit"] = unit
    with pytest.raises(air.Co2AirMassHold): air.evaluate_rhs(**args)


def test_missing_boundaries_unrelated_state_and_omitted_crop_are_held(air):
    args = inputs(); del args["forcing"]["external_co2_flux"]
    with pytest.raises(air.Co2AirMassHold): air.evaluate_rhs(**args)
    args = inputs(); args["state"]["air_temperature"] = q(25, "degC")
    with pytest.raises(air.Co2AirMassHold): air.evaluate_rhs(**args)
    args = inputs(); del args["crop_exchange"]
    with pytest.raises(TypeError): air.evaluate_rhs(**args)


def test_depleted_outward_flow_and_unrepresentable_density_are_held(air):
    with pytest.raises(air.Co2AirMassHold): air.evaluate_rhs(**inputs(mass=0, flow=0, external=-1))
    with pytest.raises(air.Co2AirMassHold): air.evaluate_rhs(**inputs(mass=1e308, height=1e-308))


@pytest.mark.parametrize("change", ["version", "pair", "unit", "hash", "code"])
def test_crop_identity_and_signed_pair_are_checked(air, change):
    exchange = {"model_version": net.VERSION, "code_sha256": net.CODE_SHA256,
                "scope": "software_research_only", "input_sha256": "a" * 64,
                "co2": {"net_crop_uptake": q(-1, net.CO2_UNIT), "air_flux": q(1, net.CO2_UNIT)}}
    if change == "version": exchange["model_version"] = "unknown"
    elif change == "pair": exchange["co2"]["air_flux"]["value"] = -1
    elif change == "unit": exchange["co2"]["air_flux"]["unit"] = "ppm/s"
    elif change == "hash": exchange["input_sha256"] = "bad"
    else: exchange["code_sha256"] = "b" * 64
    args = inputs(); args["crop_exchange"] = exchange
    with pytest.raises(air.Co2AirMassHold): air.evaluate_rhs(**args)
