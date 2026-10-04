"""Instantaneous isolated fruit-compartment transport from Vanthoor Ch9.

Equation/parameter provenance: crop-fruit-transport-reference-parameters-v1.json.
"""

from dataclasses import dataclass, field
from hashlib import sha256
import json
from math import fsum, isfinite, ulp
from types import MappingProxyType
from typing import Mapping


MODEL_VERSION = "vanthoor-fruit-transport-research-v1"
PROFILE_SHA256 = "09ea5e176bc745361e8e3ec8945b0f8abb0b2b427b4e9c459d0663cf390e9070"
PROFILE_BYTES = 3427
UNITS = {"fruit_number": "fruits_equivalent/m2_floor",
         "fruit_carbohydrate": "mg_CH2O/m2_floor"}


class FruitTransportHold(ValueError):
    """An input or numeric domain for which no transport result is supplied."""


def _need(condition, reason):
    if not condition:
        raise FruitTransportHold(reason)


@dataclass(frozen=True)
class ReferenceFruitTransportParameters:
    raw_bytes: bytes
    values: Mapping[str, float] = field(init=False, repr=False)
    sha256: str = field(init=False)
    profile_id: str = field(init=False)
    stages: int = field(init=False)
    filtered_temperature_bounds: tuple[float, float] = field(init=False)
    onset_temperature_sum: float = field(init=False)

    def __post_init__(self):
        _need(type(self.raw_bytes) is bytes and len(self.raw_bytes) == PROFILE_BYTES,
              "PROFILE_HOLD: fixed reference bytes required")
        digest = sha256(self.raw_bytes).hexdigest()
        _need(digest == PROFILE_SHA256, "PROFILE_HOLD: unreviewed profile bytes")
        document = json.loads(self.raw_bytes)
        object.__setattr__(self, "values", MappingProxyType({
            k: float(v["value"]) for k, v in document["parameters"].items()}))
        object.__setattr__(self, "sha256", digest)
        object.__setattr__(self, "profile_id", document["profile_id"])
        object.__setattr__(self, "stages", document["parameters"]["nDev"]["value"])
        object.__setattr__(self, "filtered_temperature_bounds",
                           tuple(document["domain"]["filtered_temperature_c"]))
        object.__setattr__(self, "onset_temperature_sum",
                           document["domain"]["temperature_sum_onset_exclusive"]["value"])


def _number(quantity, unit):
    _need(type(quantity) is dict and set(quantity) == {"value", "unit"},
          "INPUT_HOLD: closed quantity required")
    _need(quantity["unit"] == unit, "UNIT_HOLD: unexpected quantity unit")
    _need(type(quantity["value"]) in (int, float), "INPUT_HOLD: numeric value required")
    try:
        value = float(quantity["value"])
    except OverflowError as exc:
        raise FruitTransportHold("NUMERIC_HOLD: unrepresentable input") from exc
    _need(isfinite(value) and value >= 0, "INPUT_HOLD: finite nonnegative value required")
    return value


def _state(block, stages):
    _need(type(block) is dict and set(block) == {"input_id", "origin", "values"},
          "INPUT_HOLD: closed state block required")
    _need(type(block["input_id"]) is str and 0 < len(block["input_id"]) <= 256
          and bool(block["input_id"].strip()) and type(block["origin"]) is str
          and block["origin"] in ("synthetic", "reference_calculation", "reference_observation"),
          "INPUT_HOLD: explicit bounded provenance required")
    values = block["values"]
    _need(type(values) is dict and set(values) == {*UNITS, "temperature_filtered_24h", "temperature_sum"},
          "INPUT_HOLD: missing or unexpected quantity")
    numbers, normalized = {}, {}
    for group, unit in UNITS.items():
        quantities = values[group]
        _need(type(quantities) is list and len(quantities) == stages,
              "INPUT_HOLD: exact compartment array required")
        numbers[group] = [_number(q, unit) for q in quantities]
        normalized[group] = [{"value": v, "unit": unit} for v in numbers[group]]
    for name, unit in (("temperature_filtered_24h", "degC"), ("temperature_sum", "degC_day")):
        numbers[name] = _number(values[name], unit)
        normalized[name] = {"value": numbers[name], "unit": unit}
    return numbers, {"input_id": block["input_id"], "origin": block["origin"], "values": normalized}


def _quantity(value, unit):
    return {"value": value, "unit": unit}


def calculate_transport_rates(*, state, profile):
    """Return unit-bearing derivatives/edge flows; do not advance the state."""
    _need(type(profile) is ReferenceFruitTransportParameters,
          "PROFILE_HOLD: pinned reference required")
    values, normalized = _state(state, profile.stages)
    temperature = values["temperature_filtered_24h"]
    lower, upper = profile.filtered_temperature_bounds
    _need(lower <= temperature <= upper and values["temperature_sum"] > profile.onset_temperature_sum,
          "FRUIT_TRANSPORT_DOMAIN_HOLD: outside post-onset shared research domain")
    _need(all(carbon == 0 or number > 0 for number, carbon in zip(
        values["fruit_number"], values["fruit_carbohydrate"], strict=True)),
        "FRUIT_COHORT_STATE_HOLD: carbohydrate without modelled fruit number")
    development = fsum((profile.values["cDev1"], profile.values["cDev2"] * temperature))
    transfer = profile.stages * development
    _need(isfinite(transfer) and transfer > 0, "NUMERIC_HOLD: invalid development rate")
    derivatives, outflows, totals, residuals, budgets = {}, {}, {}, {}, {}
    try:
        for group, unit in UNITS.items():
            quantities = values[group]
            flux = [transfer * v for v in quantities]
            _need(all(isfinite(v) for v in flux), "NUMERIC_HOLD: nonfinite transport")
            _need(all(q == 0 or f > 0 for q, f in zip(quantities, flux, strict=True)),
                  "NUMERIC_HOLD: positive transport underflow")
            change = [-flux[0], *[transfer * (quantities[j - 1] - quantities[j])
                                 for j in range(1, profile.stages)]]
            _need(all(quantities[j - 1] == quantities[j] or change[j] != 0
                      for j in range(1, profile.stages)),
                  "NUMERIC_HOLD: compartment derivative underflow")
            total = fsum(quantities)
            residual = fsum([*change, flux[-1]])
            budget = 2 * (profile.stages + 1) * ulp(max(flux))
            _need(isfinite(total) and all(isfinite(v) for v in change) and isfinite(residual),
                  "NUMERIC_HOLD: nonfinite aggregate")
            _need(abs(residual) <= budget, "BALANCE_HOLD: unresolved compartment residual")
            derivatives[group] = [_quantity(v, unit + "/s") for v in change]
            outflows[group] = [_quantity(v, unit + "/s") for v in flux]
            totals[group] = _quantity(total, unit)
            residuals[group] = _quantity(residual, unit + "/s")
            budgets[group] = _quantity(budget, unit + "/s")
    except OverflowError as exc:
        raise FruitTransportHold("NUMERIC_HOLD: aggregate overflow") from exc
    bound_input = {"model_version": MODEL_VERSION, "profile_sha256": profile.sha256,
                   "state": normalized}
    digest = sha256(json.dumps(bound_input, sort_keys=True, separators=(",", ":"),
                               allow_nan=False).encode()).hexdigest()
    return {"model_version": MODEL_VERSION, "profile_id": profile.profile_id,
        "profile_sha256": profile.sha256, "input_sha256": digest,
        "scope": "software_research_only", "development_rate": _quantity(development, "1/s"),
        "transport_rate": _quantity(transfer, "1/s"), "totals": totals,
        "derivatives": derivatives, "outflows": outflows,
        "terminal_outflow": {group: _quantity(outflows[group][-1]["value"], unit + "/s")
                             for group, unit in UNITS.items()},
        "balance_residual": residuals, "balance_budget": budgets}
