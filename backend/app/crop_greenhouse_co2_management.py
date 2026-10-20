"""Atomic removal for current CO2/Solar states; see its versioned contract."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path

from . import crop_climate_joint_management as previous
from . import crop_greenhouse_co2_joint as rhs

VERSION = "joint-co2-solar-management-research-v1"
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
POLICY = {"quantity_rule": "cohort-decimal-rational-removal-v1",
          "roundoff_rule": "64-ulp-event-inventory-v1",
          "bulk_air_invariants": "exact_zero", "time_coordinate": "instantaneous_no_clock"}


class Co2ManagementHold(previous.JointManagementHold):
    """The entire event is held with its confirmed pre-event snapshot."""


def _snapshot(result):
    return {**{k: result[k] for k in ("scenario", "solar", "ventilation", "co2",
                                     "input_sha256", "calculation_sha256")},
            "derived": {**result["solar_rhs"]["joint_rhs"]["derived"], **result["derived"]}}


def _carbon(scenario):
    return previous._sum([scenario["plant_state"][k]["value"] for k in ("buffer", "leaf", "stem_root")]
                         + [q["value"] for q in scenario["cohort_state"]["fruit_carbohydrate"]])


def apply_management(*, scenario, solar, ventilation, co2, event, growth_profile,
                     cohort_profile, transport_profile, exchange_profile):
    """Return a copied candidate only after both actual RHS and event balances pass."""
    profiles = dict(growth_profile=growth_profile, cohort_profile=cohort_profile,
                    transport_profile=transport_profile, exchange_profile=exchange_profile)
    before = None; phase = "initial"
    try:
        first = rhs.evaluate_rhs(scenario=scenario, solar=solar, ventilation=ventilation, co2=co2, **profiles)
        before = _snapshot(first); base = first["scenario"]
        phase = "event_schema"
        organs, fractions, normalized = previous._event(event)
        previous._need(normalized["origin"] == base["origin"], "INPUT_HOLD: mixed event research origins")
        candidate = deepcopy(base)
        removed = {k: previous._q(v, previous.MASS) for k, v in organs.items()}
        phase = "event_removal"
        for key, amount in organs.items():
            candidate["plant_state"][key]["value"] = previous._remove(base["plant_state"][key]["value"], amount)
        for key, unit in (("fruit_carbohydrate", previous.MASS), ("fruit_number", previous.NUMBER)):
            amounts = []
            for old, fraction, row in zip(base["cohort_state"][key], fractions, candidate["cohort_state"][key], strict=True):
                value = old["value"]; exact = Fraction(str(value)) * Fraction(str(fraction)); amount = float(exact)
                previous._need(isfinite(amount) and (value == 0 or fraction == 0 or amount != 0),
                               "NUMERIC_HOLD: fractional removal underflow")
                after = float(Fraction(str(value)) - exact)
                previous._need(isfinite(after) and (exact == 0 or after < value),
                               "NUMERIC_HOLD: removal lost to rounding")
                row["value"] = after; amounts.append(previous._q(amount, unit))
            removed[key] = amounts
        capacity = previous.joint.inventory.calculate_leaf_removal(event={"input_id": normalized["input_id"],
            "origin": normalized["origin"], "values": {
                "leaf_carbohydrate": base["plant_state"]["leaf"], "leaf_removed": removed["leaf"],
                "leaf_heat_capacity": base["parameters"]["leaf_heat_capacity"],
                "canopy_sensible_energy": base["climate_state"]["canopy_sensible_energy"],
                "reference_temperature": base["parameters"]["reference_temperature"]}}, profile=growth_profile)
        previous._need(candidate["plant_state"]["leaf"] == capacity["after"]["leaf_carbohydrate"],
                       "BALANCE_HOLD: conflicting event leaf")
        candidate["climate_state"]["canopy_sensible_energy"] = capacity["after"]["canopy_sensible_energy"]
        removed["canopy_sensible_energy"] = capacity["outgoing_sensible_energy"]
        removed["canopy_capacity"] = previous._q(growth_profile.values["sla"] * organs["leaf"] *
            base["parameters"]["leaf_heat_capacity"]["value"], previous.CAPACITY)
        phase = "candidate"
        last = rhs.evaluate_rhs(scenario=candidate, solar=first["solar"], ventilation=first["ventilation"],
                                co2=first["co2"], **profiles)
        after = _snapshot(last)
        removed_c = previous._sum([organs["leaf"], organs["stem_root"],
                                  *[q["value"] for q in removed["fruit_carbohydrate"]]])
        removed_n = previous._sum(q["value"] for q in removed["fruit_number"])
        total_n = lambda s: previous._sum(q["value"] for q in s["cohort_state"]["fruit_number"])
        ratio = rhs.net.CO2_MOLAR_MASS / rhs.net.CH2O_MOLAR_MASS
        equivalent_removed = previous.joint._product(ratio, removed_c)
        phase = "event_balance"; residuals, budgets = {}, {}
        for key, start, end, terms, unit in (
            ("carbohydrate", _carbon(base), _carbon(candidate), (removed_c,), previous.MASS),
            ("number", total_n(base), total_n(candidate), (removed_n,), previous.NUMBER),
            ("canopy_sensible", base["climate_state"]["canopy_sensible_energy"]["value"],
             candidate["climate_state"]["canopy_sensible_energy"]["value"],
             (removed["canopy_sensible_energy"]["value"],), previous.ENERGY),
            ("crop_capacity", before["derived"]["canopy_capacity"]["value"],
             after["derived"]["canopy_capacity"]["value"], (removed["canopy_capacity"]["value"],), previous.CAPACITY),
            ("crop_air_carbon_equivalent", previous._sum((base["climate_state"]["air_co2_mass"]["value"],
                 previous.joint._product(ratio, _carbon(base)))),
             previous._sum((candidate["climate_state"]["air_co2_mass"]["value"],
                 previous.joint._product(ratio, _carbon(candidate)))), (equivalent_removed,), rhs.air.MASS_UNIT)):
            residuals[key], budgets[key] = previous._ledger(start, end, terms, unit)
        temperature = after["derived"]["canopy_temperature"]["value"] - before["derived"]["canopy_temperature"]["value"]
        previous._need(abs(temperature) <= 2e-13, "NUMERIC_HOLD: event changed canopy temperature")
        residuals["temperature"] = previous._q(temperature, "K"); budgets["temperature"] = previous._q(2e-13, "K")
        for key, start, end, unit in (
            ("air_co2", base["climate_state"]["air_co2_mass"], candidate["climate_state"]["air_co2_mass"], rhs.air.MASS_UNIT),
            ("air_vapor", base["climate_state"]["air_vapor_mass"], candidate["climate_state"]["air_vapor_mass"], "kg_water/m2_floor"),
            ("air_temperature", base["climate_state"]["air_temperature"], candidate["climate_state"]["air_temperature"], "K"),
            ("co2_ppm", before["derived"]["crop_co2_ppm"], after["derived"]["crop_co2_ppm"], "ppm")):
            previous._need(start == end, f"BALANCE_HOLD: event changed {key}")
            residuals[key] = previous._q(0.0, unit); budgets[key] = previous._q(0.0, unit)
    except (previous.joint.JointClimateHold, previous.joint.inventory.CanopyEnergyHold,
            previous.JointManagementHold, OverflowError, ValueError, ZeroDivisionError) as exc:
        reason = str(exc) if isinstance(exc, (previous.joint.JointClimateHold,
            previous.joint.inventory.CanopyEnergyHold, previous.JointManagementHold)) else "NUMERIC_HOLD: event arithmetic failed"
        held = Co2ManagementHold(f"{reason}: phase={phase}")
        held.failed_phase = phase; held.last_confirmed = before
        raise held from exc
    bound = {"model_version": VERSION, "code_sha256": CODE_SHA256, "state_schema_version": rhs.STATE_SCHEMA,
        "component_code_sha256": {**previous.joint.COMPONENT_CODE_SHA256, **first["component_code_sha256"],
                                 "event_primitives": previous.CODE_SHA256, "CO2_RHS": rhs.CODE_SHA256},
        "profile_sha256": first["profile_sha256"],
        "policy_sha256": previous._hash({"event": POLICY, "RHS": first["policy_sha256"],
                                        "solar": first["solar_rhs"]["policy_sha256"]}),
        "event_sha256": previous._hash(normalized), "input_sha256": first["input_sha256"],
        "before_calculation_sha256": first["calculation_sha256"], "after_calculation_sha256": last["calculation_sha256"],
        **POLICY}
    return {**bound, "calculation_sha256": previous._hash(bound), "event": normalized,
        "before": before, "after": after, "after_rhs": last, "removed": removed,
        "removed_totals": {"carbohydrate": previous._q(removed_c, previous.MASS),
                           "number": previous._q(removed_n, previous.NUMBER),
                           "co2_basis_carbohydrate": previous._q(equivalent_removed, rhs.air.MASS_UNIT)},
        "balance_residuals": residuals, "balance_budgets": budgets,
        "source_sha256": {**first["source_sha256"], "solar": first["solar_rhs"]["source_sha256"]},
        "notice_sha256": first["solar_rhs"]["notice_sha256"], "scope": "software_research_only",
        "claim_scope": "synthetic_joint_co2_solar_management_only", "G0_G4": "not_assessed"}
