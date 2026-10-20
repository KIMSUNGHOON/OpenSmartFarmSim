"""Current CO2 inventory/solar trial; crop-greenhouse-co2-joint-v1.md defines scope.

Source conventions and notice: research/crop-co2-stomatal-source-register-20261021.json
and LICENSES/GreenLight-BSD-3-Clause-Clear.txt.
"""
from hashlib import sha256
from math import ulp
from pathlib import Path

from . import crop_climate_joint_rhs as joint
from . import crop_greenhouse_solar_joint as solar_rhs
from . import crop_co2_gas as gas
from . import crop_co2_net_exchange as net
from . import crop_co2_air_mass as air

VERSION = "current-state-solar-crop-co2-joint-rhs-v1"
STATE_SCHEMA = "crop-solar-co2-stage-state-v1"
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
CLIMATE_UNITS = {**joint.CLIMATE_UNITS, "air_co2_mass": air.MASS_UNIT}
FORCING_UNITS = {k: v for k, v in solar_rhs.FORCING_UNITS.items() if k != "co2"}
CO2_PARAMETER_UNITS = {"air_pressure": "Pa"}
CO2_FORCING_UNITS = {k: v for k, v in air.FORCING_UNITS.items() if k != "volume_exchange_per_floor_area"}
POLICY = {"CO2_state": "positive_mass_per_floor_area_fixed_volume",
          "gas": "C8_explicit_pressure_current_air_temperature_and_vapor_wet_or_dry",
          "sink": "C9_44_over_30_actual_startup_realized_rates",
          "stomata": "existing_explicit_resistance_P03_hold",
          "evaluation": "one_gas_one_solar_one_net_one_air",
          "combined_carbon": "include_removed_terminal_biomass_once_64ulp_plus_component_budgets"}


class Co2JointHold(joint.JointClimateHold):
    """A whole CO2/crop/climate trial is unavailable; no partial result returned."""


def _need(condition, reason):
    if not condition:
        raise Co2JointHold(reason)


def evaluate_rhs(*, scenario, solar, ventilation, co2, growth_profile, cohort_profile,
                 transport_profile, exchange_profile):
    """Derive ppm and compose actual same-stage109 derivatives without advancing time."""
    try:
        _need(type(scenario) is dict and set(scenario) == {"input_id", "origin", *joint.SCALAR_BLOCKS,
              *joint.ARRAY_BLOCKS}, "INPUT_HOLD: closed CO2 joint scenario required")
        _need(type(co2) is dict and set(co2) == {"input_id", "origin", "basis", "parameters", "forcing"},
              "INPUT_HOLD: closed explicit CO2 boundary required")
        _need(type(co2["input_id"]) is str and 1 <= len(co2["input_id"]) <= 200
              and bool(co2["input_id"].strip()), "INPUT_HOLD: CO2 boundary identity required")
        _need(co2["origin"] == scenario["origin"], "INPUT_HOLD: mixed CO2 research origins")
        _need(type(co2["basis"]) is str and co2["basis"] in ("wet", "dry"),
              "INPUT_HOLD: explicit wet/dry basis required")
        climate, normalized_climate = joint._quantities(scenario["climate_state"], CLIMATE_UNITS)
        parameters, normalized_parameters = joint._quantities(scenario["parameters"], joint.PARAMETER_UNITS)
        _, normalized_forcing = joint._quantities(scenario["forcing"], FORCING_UNITS)
        cp, normalized_cp = joint._quantities(co2["parameters"], CO2_PARAMETER_UNITS)
        cf, normalized_cf = joint._quantities(co2["forcing"], CO2_FORCING_UNITS)
        mass, height = climate["air_co2_mass"], parameters["air_volume_per_floor_area"]
        _need(mass > 0 and height > 0 and parameters["vapor_gas_constant"] > 0
              and climate["air_vapor_mass"] >= 0 and cf["outdoor_co2_density"] >= 0,
              "CO2_DOMAIN_HOLD: positive crop CO2 inventory/volume and valid vapor/outdoor density required")
        density = joint._divide(mass, height)
        vapor = joint._product(joint._product(joint._divide(climate["air_vapor_mass"], height),
            parameters["vapor_gas_constant"]), joint._sum(climate["air_temperature"], gas.KELVIN_OFFSET))
        ppm = gas.density_to_ppm(density_mg_m3=density, temperature_c=climate["air_temperature"],
            pressure_pa=cp["air_pressure"], basis=co2["basis"], water_vapor_pressure_pa=vapor)
        if co2["basis"] == "wet":
            maximum = joint._product(1e6, joint._divide(cp["air_pressure"] - vapor, cp["air_pressure"]))
            _need(ppm <= maximum, "CO2_MIXTURE_HOLD: CO2 plus water exceeds total mole fraction")
        base = {**scenario, "climate_state": {k: normalized_climate[k] for k in joint.CLIMATE_UNITS},
                "parameters": normalized_parameters, "forcing": {**normalized_forcing, "co2": joint._q(ppm, "ppm")}}
        result = solar_rhs.evaluate_rhs(scenario=base, solar=solar, ventilation=ventilation,
            growth_profile=growth_profile, cohort_profile=cohort_profile,
            transport_profile=transport_profile, exchange_profile=exchange_profile)
        core = result["joint_rhs"]
        _need(core["derived"]["air_vapor_pressure"]["value"] == vapor,
              "BALANCE_HOLD: conflicting same-stage vapor pressure")
        crop = net.calculate_exchange(rates=core["crop"])
        inventory = air.evaluate_rhs(state={"air_co2_mass": normalized_climate["air_co2_mass"]},
            parameters={"air_volume_per_floor_area": normalized_parameters["air_volume_per_floor_area"]},
            forcing={**normalized_cf, "volume_exchange_per_floor_area": result["ventilation"]["forcing"]["volume_exchange_per_floor_area"]},
            crop_exchange=crop)
        ratio = net.CO2_MOLAR_MASS / net.CH2O_MOLAR_MASS
        plant = core["crop"]
        stored_rate = joint._sum(*(plant["derivatives"][k]["value"] for k in ("buffer", "leaf", "stem_root")),
                                 *(q["value"] for q in plant["cohorts"]["derivatives"]["fruit_carbohydrate"]))
        removed = joint._sum(*(q["value"] for q in plant["removals"].values()))
        terminal = plant["cohorts"]["terminal_outflow"]["fruit_carbohydrate"]["value"]
        terms = (inventory["derivatives"]["air_co2_mass"]["value"],
                 inventory["transfers"]["ventilation_to_outdoor"]["value"], -cf["external_co2_flux"],
                 joint._product(ratio, stored_rate), joint._product(ratio, removed), joint._product(ratio, terminal))
        residual = joint._sum(*terms)
        budget = joint._sum(inventory["balance_budget"]["value"],
            joint._product(ratio, core["balance_budgets"]["carbohydrate"]["value"]),
            64 * ulp(max(1.0, *map(abs, terms))))
        _need(abs(residual) <= budget, "BALANCE_HOLD: unresolved crop/air carbon equivalent")
        normalized = {**result["scenario"], "forcing": normalized_forcing,
            "climate_state": {**result["scenario"]["climate_state"], "air_co2_mass": normalized_climate["air_co2_mass"]}}
        boundary = {**co2, "parameters": normalized_cp, "forcing": normalized_cf}
        identity = {"model_version": VERSION, "state_schema_version": STATE_SCHEMA, "code_sha256": CODE_SHA256,
            "component_code_sha256": {"solar": solar_rhs.CODE_SHA256, "gas": gas.CODE_SHA256,
                                      "net": net.CODE_SHA256, "air_mass": air.CODE_SHA256},
            "profile_sha256": dict(core["profile_sha256"]), "policy_sha256": joint._hash(POLICY),
            "input_sha256": joint._hash({"scenario": normalized, "solar": result["solar"],
                                         "ventilation": result["ventilation"], "co2": boundary}),
            "solar_calculation_sha256": result["calculation_sha256"],
            "net_input_sha256": crop["input_sha256"], "air_mass_input_sha256": inventory["input_sha256"]}
        return {**identity, "calculation_sha256": joint._hash(identity), "scenario": normalized,
            "solar": result["solar"], "ventilation": result["ventilation"], "co2": boundary,
            "solar_rhs": result, "net_exchange": crop, "air_co2_rhs": inventory,
            "source_sha256": {"gas": gas.SOURCE_SHA256, "net": net.SOURCE_SHA256, "air_mass": air.SOURCE_SHA256},
            "scope": "software_research_only", "claim_scope": "synthetic_current_stage_co2_crop_climate_only",
            "G0_G4": "not_assessed", "time_coordinate": "derivatives_per_second_no_time_advance",
            "derived": {"air_co2_density": inventory["air_co2_density"], "air_vapor_pressure": joint._q(vapor, "Pa"),
                        "crop_co2_ppm": joint._q(ppm, "ppm")},
            "derivatives": {**core["derivatives"], "climate": {**core["derivatives"]["climate"],
                            "air_co2_mass": inventory["derivatives"]["air_co2_mass"]}},
            "balance_residuals": {**core["balance_residuals"], "air_co2": inventory["balance_residual"],
                                  "crop_air_carbon_equivalent": joint._q(residual, air.RATE_UNIT)},
            "balance_budgets": {**core["balance_budgets"], "air_co2": inventory["balance_budget"],
                                "crop_air_carbon_equivalent": joint._q(budget, air.RATE_UNIT)}}
    except (joint.JointClimateHold, gas.Co2GasHold, net.Co2NetExchangeHold, air.Co2AirMassHold) as exc:
        if isinstance(exc, Co2JointHold):
            raise
        raise Co2JointHold(str(exc)) from exc
    except (OverflowError, ZeroDivisionError) as exc:
        raise Co2JointHold("NUMERIC_HOLD: unrepresentable shared trial") from exc
