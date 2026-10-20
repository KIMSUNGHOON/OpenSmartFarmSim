"""Fixed-volume CO2 inventory; contracts/crop-co2-air-mass-v1.md defines scope.

C8 mass capacity/exchange equations; retain
LICENSES/GreenLight-BSD-3-Clause-Clear.txt.
"""
from hashlib import sha256
import json
from math import fsum, isfinite, ulp
from pathlib import Path
import re

from . import crop_co2_net_exchange as crop

VERSION = "fixed-volume-main-air-co2-rhs-v1"
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
SOURCE_SHA256 = "c0fb7a025533f15b80cb6cd60aafdc19be9fe42df6b8183cf97b83fc086138b3"
MASS_UNIT = "mg_CO2/m2_floor"
DENSITY_UNIT = "mg_CO2/m3"
RATE_UNIT = MASS_UNIT + "/s"
STATE_UNITS = {"air_co2_mass": MASS_UNIT}
PARAMETER_UNITS = {"air_volume_per_floor_area": "m3/m2_floor"}
FORCING_UNITS = {"outdoor_co2_density": DENSITY_UNIT,
                 "volume_exchange_per_floor_area": "m3/m2_floor/s", "external_co2_flux": RATE_UNIT}
BALANCE_POLICY = "32ulp-largest-term-floor1-v1"


class Co2AirMassHold(ValueError):
    """No mass derivative is supplied outside the declared numerical boundary."""


def _need(condition, reason):
    if not condition:
        raise Co2AirMassHold(reason)


def _q(value, unit=RATE_UNIT):
    return {"value": value, "unit": unit}


def _value(row, unit):
    _need(type(row) is dict and set(row) == {"value", "unit"}, "INPUT_HOLD: closed quantity required")
    _need(type(row["unit"]) is str and row["unit"] == unit, "UNIT_HOLD: incompatible CO2 quantity")
    _need(type(row["value"]) in (int, float), "INPUT_HOLD: explicit numeric quantity required")
    try:
        value = float(row["value"])
    except OverflowError as exc:
        raise Co2AirMassHold("NUMERIC_HOLD: unrepresentable quantity") from exc
    _need(isfinite(value), "INPUT_HOLD: finite quantity required")
    return value


def _block(block, units):
    _need(type(block) is dict and set(block) == set(units), "INPUT_HOLD: closed quantity block required")
    return {name: _value(block[name], unit) for name, unit in units.items()}


def _finite(value, *, nonzero=False):
    _need(isfinite(value) and (not nonzero or value != 0), "NUMERIC_HOLD: unrepresentable mass arithmetic")
    return value


def _crop_exchange(result):
    if result is None:
        return 0.0, 0.0, {"kind": "explicit_no_crop"}
    _need(type(result) is dict and result.get("model_version") == crop.VERSION
          and result.get("code_sha256") == crop.CODE_SHA256
          and result.get("scope") == "software_research_only", "MODEL_HOLD: current net crop exchange required")
    digest = result.get("input_sha256")
    _need(type(digest) is str and re.fullmatch("[0-9a-f]{64}", digest), "IDENTITY_HOLD: canonical crop input SHA required")
    pair = _block(result.get("co2"), {"net_crop_uptake": RATE_UNIT, "air_flux": RATE_UNIT})
    uptake, flux = pair["net_crop_uptake"], pair["air_flux"]
    _need(flux == -uptake, "BALANCE_HOLD: conflicting crop/air transfers")
    return flux, uptake, {"kind": "crop", "model_version": crop.VERSION,
                          "code_sha256": crop.CODE_SHA256, "input_sha256": digest}


def evaluate_rhs(*, state, parameters, forcing, crop_exchange):
    """Return instantaneous fixed-geometry mass rates, without evolving state."""
    s, p, f = (_block(block, units) for block, units in (
        (state, STATE_UNITS), (parameters, PARAMETER_UNITS), (forcing, FORCING_UNITS)))
    mass, height = s["air_co2_mass"], p["air_volume_per_floor_area"]
    flow, outdoor = f["volume_exchange_per_floor_area"], f["outdoor_co2_density"]
    _need(mass >= 0 and height > 0 and flow >= 0 and outdoor >= 0,
          "INPUT_HOLD: nonnegative mass/exchange/density and positive fixed volume required")
    crop_flux, uptake, crop_identity = _crop_exchange(crop_exchange)
    density = _finite(mass / height, nonzero=mass != 0)
    difference = outdoor - density
    ventilation = _finite(flow * difference, nonzero=flow != 0 and difference != 0)
    external = f["external_co2_flux"]
    try:
        rate = _finite(fsum((ventilation, external, crop_flux)))
        density_rate = _finite(rate / height, nonzero=rate != 0)
        terms = (rate, -ventilation, uptake, -external)
        residual = _finite(fsum(terms))
        budget = _finite(32 * ulp(max(1.0, *map(abs, terms))))
    except (OverflowError, ValueError) as exc:
        if isinstance(exc, Co2AirMassHold):
            raise
        raise Co2AirMassHold("NUMERIC_HOLD: mass balance overflow") from exc
    _need(mass != 0 or rate >= 0, "DEPLETED_STATE_HOLD: outward derivative at zero CO2 inventory")
    _need(abs(residual) <= budget, "BALANCE_HOLD: unresolved CO2 inventory")
    normalized = {name: {key: _q(value, units[key]) for key, value in values.items()}
                  for name, values, units in (("state", s, STATE_UNITS),
                  ("parameters", p, PARAMETER_UNITS), ("forcing", f, FORCING_UNITS))}
    bound = {"model_version": VERSION, "code_sha256": CODE_SHA256, "balance_policy": BALANCE_POLICY,
             "inputs": normalized, "crop_identity": crop_identity,
             "crop_transfer": {"uptake": _q(uptake), "air_flux": _q(crop_flux)}}
    return {**bound, "input_sha256": sha256(json.dumps(bound, sort_keys=True, separators=(",", ":"),
                                                       allow_nan=False).encode()).hexdigest(),
            "source_sha256": SOURCE_SHA256, "scope": "software_research_only",
            "claim_scope": "fixed_volume_instantaneous_co2_mass_rhs_only", "G0_G4": "not_assessed",
            "air_co2_density": _q(density, DENSITY_UNIT),
            "derivatives": {"air_co2_mass": _q(rate), "air_co2_density": _q(density_rate, DENSITY_UNIT + "/s")},
            "transfers": {"ventilation_to_air": _q(ventilation), "ventilation_to_outdoor": _q(-ventilation),
                          "crop_to_air": _q(crop_flux), "crop_uptake": _q(uptake), "external_to_air": _q(external)},
            "balance_residual": _q(residual), "balance_budget": _q(budget)}
