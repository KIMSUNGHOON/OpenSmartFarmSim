"""Pinned Vanthoor/GreenLight carbon rates for software research; no Run approval.

Equation basis and retained third-party notice:
fixtures/crop-growth-reference-parameters-v1.json
LICENSES/GreenLight-BSD-3-Clause-Clear.txt
"""

from dataclasses import dataclass, field
from hashlib import sha256
import json
from math import exp, expm1, fsum, hypot, isfinite, log, sqrt, ulp
from types import MappingProxyType
from typing import Mapping


MODEL_VERSION = "vanthoor-greenlight-carbon-rates-v1"
PROFILE_SHA256 = "d606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca"
MASS_UNIT = "mg_CH2O/m2_floor"
RATE_UNIT = MASS_UNIT + "/s"
STATE_UNITS = {"buffer": MASS_UNIT, "leaf": MASS_UNIT, "stem_root": MASS_UNIT,
               "fruit": MASS_UNIT, "temperature_filtered_24h": "degC",
               "temperature_sum": "degC_day"}
FORCING_UNITS = {"canopy_temperature": "degC",
                 "par_above_canopy": "umol_photons/m2_floor/s", "co2": "ppm"}
REMOVAL_UNITS = {"leaf": RATE_UNIT, "stem_root": RATE_UNIT, "fruit": RATE_UNIT}


class CropRateHold(ValueError):
    """An unsupported input or equation domain; no replacement values supplied."""


def _need(condition, reason):
    if not condition:
        raise CropRateHold(reason)


@dataclass(frozen=True)
class ReferenceParameters:
    raw_bytes: bytes
    values: Mapping[str, float] = field(init=False, repr=False)
    sha256: str = field(init=False)
    profile_id: str = field(init=False)
    filtered_temperature_bounds: tuple[float, float] = field(init=False)

    def __post_init__(self):
        _need(type(self.raw_bytes) is bytes, "PROFILE_HOLD: bytes required")
        digest = sha256(self.raw_bytes).hexdigest()
        _need(digest == PROFILE_SHA256, "PROFILE_HOLD: unreviewed profile bytes")
        document = json.loads(self.raw_bytes)
        object.__setattr__(self, "values", MappingProxyType({
            k: float(v["value"]) for k, v in document["parameters"].items()}))
        object.__setattr__(self, "sha256", digest)
        object.__setattr__(self, "profile_id", document["profile_id"])
        object.__setattr__(self, "filtered_temperature_bounds",
                           tuple(document["domain"]["filtered_temperature_c"]))


def _block(block, units):
    _need(type(block) is dict and set(block) == {"input_id", "origin", "values"},
          "INPUT_HOLD: closed input block required")
    _need(type(block["input_id"]) is str and bool(block["input_id"].strip()) and
          block["origin"] in ("synthetic", "reference_calculation", "reference_observation"),
          "INPUT_HOLD: explicit provenance required")
    records = block["values"]
    _need(type(records) is dict and set(records) == set(units),
          "INPUT_HOLD: missing or unexpected quantity")
    numbers = {}
    for name, unit in units.items():
        record = records[name]
        _need(type(record) is dict and set(record) == {"value", "unit"},
              "INPUT_HOLD: closed quantity required")
        _need(record["unit"] == unit, "UNIT_HOLD: " + name)
        _need(type(record["value"]) in (int, float), "INPUT_HOLD: numeric value required")
        try:
            value = float(record["value"])
        except OverflowError as exc:
            raise CropRateHold("NUMERIC_HOLD: unrepresentable input") from exc
        _need(isfinite(value) and value >= 0, "INPUT_HOLD: finite nonnegative value required")
        numbers[name] = value
    normalized = {"input_id": block["input_id"], "origin": block["origin"],
                  "values": {k: {"value": v, "unit": units[k]} for k, v in numbers.items()}}
    return numbers, normalized


def _quantity(value, unit=RATE_UNIT):
    return {"value": value, "unit": unit}


def _sigmoid(value):
    if value >= 0:
        return 1 / (1 + exp(-value))
    numerator = exp(value)
    return numerator / (1 + numerator)


def _photosynthesis(state, forcing, p, lai):
    if forcing["par_above_canopy"] == 0:
        return 0.0, {"compensation_point_ppm": None, "electron_transport": 0.0}
    temperature = forcing["canopy_temperature"]
    pivot = p["compensation_pivot_c"]
    if lai == 0:
        _need(temperature == pivot, "COMPENSATION_POINT_HOLD: zero LAI has no finite temperature limit")
        return 0.0, {"compensation_point_ppm": p["cGamma"] * pivot, "electron_transport": 0.0}
    gamma = p["cGamma"] * (pivot + (temperature - pivot) / lai)
    stomata = p["etaCo2AirStom"] * forcing["co2"]
    _need(isfinite(gamma) and 0 <= gamma <= stomata and stomata > 0,
          "COMPENSATION_POINT_HOLD: outside supported photosynthetic domain")
    absorbed = forcing["par_above_canopy"] * (1 - p["rhoCanPar"]) * (
        -expm1(-p["k1Par"] * lai) +
        p["rhoFlrPar"] * exp(-p["k1Par"] * lai) * -expm1(-p["k2Par"] * lai))
    kelvin = temperature + p["kelvin_offset"]
    gas = p["gas_constant_scale"] * p["R"]
    potential = lai * p["j25LeafMax"] * exp(
        p["eJ"] * (kelvin - p["t25k"]) / (gas * kelvin * p["t25k"])) * (
        1 + exp((p["S"] * p["t25k"] - p["H"]) / (gas * p["t25k"]))) / (
        1 + exp((p["S"] * kelvin - p["H"]) / (gas * kelvin)))
    light = p["alpha"] * absorbed
    scale = max(potential, light)
    if scale == 0:
        transport = 0.0
    else:
        a, b = potential / scale, light / scale
        root = sqrt((a - b) ** 2 + 4 * (1 - p["theta"]) * a * b)
        transport = scale * (2 * a * b / (a + b + root))
    ratio = gamma / stomata
    photo = transport * (1 - ratio) / (
        p["electron_per_fixed_co2"] * (1 + p["compensation_denominator_factor"] * ratio))
    inhibition = _sigmoid(-p["buffer_full_slope"] * (state["buffer"] - p["cBufMax"]))
    assimilation = p["mCh2o"] * inhibition * photo * (1 - ratio)
    return assimilation, {"compensation_point_ppm": gamma, "electron_transport": transport}


def calculate_rates(*, state, forcing, removals, profile):
    """Return instantaneous unit-bearing research rates; inputs are not advanced."""
    _need(type(profile) is ReferenceParameters, "PROFILE_HOLD: pinned reference required")
    s, state_input = _block(state, STATE_UNITS)
    f, forcing_input = _block(forcing, FORCING_UNITS)
    r, removal_input = _block(removals, REMOVAL_UNITS)
    p = profile.values
    filtered = s["temperature_filtered_24h"]
    temperature = f["canopy_temperature"]
    lower, upper = profile.filtered_temperature_bounds
    _need(lower <= filtered <= upper and p["tCanMin"] <= temperature <= p["tCanMax"]
          and f["co2"] > 0, "INPUT_HOLD: outside reference calculation scope")
    lai = p["sla"] * s["leaf"]
    _need(s["leaf"] == 0 or lai > 0, "NUMERIC_HOLD: leaf area underflow")
    try:
        assimilation, diagnostics = _photosynthesis(s, f, p, lai)
        buffer_factor = _sigmoid(p["buffer_empty_slope"] * (s["buffer"] - p["cBufMin"]))
        instant_factor = _sigmoid(p["instant_low_slope"] * (temperature - p["tCanMin"])) * (
            _sigmoid(-p["instant_high_slope"] * (temperature - p["tCanMax"])))
        filtered_factor = _sigmoid(p["filtered_low_slope"] * (filtered - p["tCan24Min"])) * (
            _sigmoid(-p["filtered_high_slope"] * (filtered - p["tCan24Max"])))
        x = s["temperature_sum"] / p["tEndSum"]
        smoothing = sqrt(p["development_smoothing_squared"])
        development = 0.5 * (1 + (2 * x - 1) / (hypot(x, smoothing) + hypot(x - 1, smoothing)))
        temperature_factor = p["allocation_temperature_slope"] * filtered + p["allocation_temperature_intercept"]
        common = buffer_factor * filtered_factor * temperature_factor
        allocation = {"fruit": common * instant_factor * development * p["rgFruit"],
                      "leaf": common * p["rgLeaf"], "stem_root": common * p["rgStem"]}
        growth = fsum(p[key] * allocation[organ] for organ, key in (
            ("fruit", "cFruitG"), ("leaf", "cLeafG"), ("stem_root", "cStemG")))
        maintenance_factor = -expm1(-p["cRgr"] * p["rgr"]) * exp(
            log(p["q10m"]) * (filtered - p["maintenance_temperature_reference_c"]) /
            p["q10_temperature_interval_c"])
        maintenance = {organ: maintenance_factor * s[organ] * p[key] for organ, key in (
            ("fruit", "cFruitM"), ("leaf", "cLeafM"), ("stem_root", "cStemM"))}
        carbon = {organ: fsum((allocation[organ], -maintenance[organ], -r[organ])) for organ in allocation}
        carbon["buffer"] = fsum((assimilation, -growth, *[-v for v in allocation.values()]))
        terms = (assimilation, -growth, *[-v for v in maintenance.values()], *[-v for v in r.values()])
        external = fsum(terms)
        stored = fsum(carbon.values())
        residual = fsum((stored, -external))
        budget = 16 * ulp(max(1.0, *map(abs, terms), *map(abs, carbon.values())))
    except (OverflowError, ZeroDivisionError, ValueError) as exc:
        if isinstance(exc, CropRateHold):
            raise
        raise CropRateHold("NUMERIC_HOLD: equation evaluation failed") from exc
    _need(all(map(isfinite, (lai, assimilation, growth, *allocation.values(),
                            *maintenance.values(), *carbon.values(), residual))),
          "NUMERIC_HOLD: nonfinite output")
    _need(assimilation >= 0 and all(v >= 0 for v in (*allocation.values(), *maintenance.values())),
          "NUMERIC_HOLD: invalid nonnegative flux")
    _need(abs(residual) <= budget, "BALANCE_HOLD: unresolved carbon residual")
    _need(all(s[organ] != 0 or derivative >= 0 for organ, derivative in carbon.items()),
          "DEPLETED_STATE_HOLD: outward derivative at zero storage")
    bound_input = {"model_version": MODEL_VERSION, "profile_sha256": profile.sha256,
                   "state": state_input, "forcing": forcing_input, "removals": removal_input}
    input_hash = sha256(json.dumps(bound_input, sort_keys=True, separators=(",", ":"),
                                   allow_nan=False).encode()).hexdigest()
    derivatives = {k: _quantity(v) for k, v in carbon.items()}
    derivatives["temperature_filtered_24h"] = _quantity(
        (temperature - filtered) / p["seconds_per_day"], "degC/s")
    derivatives["temperature_sum"] = _quantity(temperature / p["seconds_per_day"], "degC_day/s")
    return {"model_version": MODEL_VERSION, "profile_id": profile.profile_id,
            "profile_sha256": profile.sha256, "input_sha256": input_hash,
            "scope": "software_research_only", "lai": _quantity(lai, "m2_leaf/m2_floor"),
            "photosynthesis": _quantity(assimilation), "growth_respiration": _quantity(growth),
            "allocation": {k: _quantity(v) for k, v in allocation.items()},
            "maintenance_respiration": {k: _quantity(v) for k, v in maintenance.items()},
            "removals": {k: _quantity(v) for k, v in r.items()}, "derivatives": derivatives,
            "carbon_residual": _quantity(residual), "carbon_residual_budget": _quantity(budget),
            "diagnostics": diagnostics}
