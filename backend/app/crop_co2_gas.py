"""Explicit ideal-mixture scalars; contracts/crop-co2-gas-v1.md defines scope.

GreenLight C8 conversion convention; retain
LICENSES/GreenLight-BSD-3-Clause-Clear.txt. No field/sensor basis is inferred.
"""
from hashlib import sha256
from math import isfinite
from pathlib import Path

VERSION = "greenlight-co2-ideal-gas-explicit-pressure-v1"
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
SOURCE_SHA256 = "c0fb7a025533f15b80cb6cd60aafdc19be9fe42df6b8183cf97b83fc086138b3"
GAS_CONSTANT = 8.3144598  # Pa*m3/(mol*K), pinned C8 numerical convention
CO2_MOLAR_MASS = 44.01e-3  # kg/mol, same source helper
KELVIN_OFFSET = 273.15


class Co2GasHold(ValueError):
    """The explicit concentration conversion cannot support this input."""


def _number(value, name):
    if type(value) not in (int, float):
        raise Co2GasHold(f"INPUT_HOLD: finite scalar required for {name}")
    try:
        result = float(value)
    except OverflowError as exc:
        raise Co2GasHold(f"INPUT_HOLD: unrepresentable {name}") from exc
    if not isfinite(result):
        raise Co2GasHold(f"INPUT_HOLD: nonfinite {name}")
    return result


def _environment(temperature_c, pressure_pa, basis, water_vapor_pressure_pa):
    temperature = _number(temperature_c, "temperature_c") + KELVIN_OFFSET
    pressure = _number(pressure_pa, "pressure_pa")
    if temperature <= 0 or pressure <= 0 or basis not in ("wet", "dry"):
        raise Co2GasHold("INPUT_HOLD: positive Kelvin/pressure and explicit wet/dry basis required")
    if water_vapor_pressure_pa is None:
        if basis == "dry":
            raise Co2GasHold("INPUT_HOLD: dry basis requires water vapor pressure")
        return temperature, pressure
    vapor = _number(water_vapor_pressure_pa, "water_vapor_pressure_pa")
    if not 0 <= vapor < pressure:
        raise Co2GasHold("INPUT_HOLD: water vapor pressure must be below total pressure")
    return temperature, pressure - vapor if basis == "dry" else pressure


def _result(value, nonzero):
    if not isfinite(value) or (nonzero and value == 0):
        raise Co2GasHold("NUMERIC_HOLD: unrepresentable concentration")
    return value


def density_to_ppm(*, density_mg_m3, temperature_c, pressure_pa, basis,
                   water_vapor_pressure_pa=None):
    """Convert mg_CO2/m3 to explicit wet/total or dry/water-excluded mole ppm."""
    temperature, pressure = _environment(temperature_c, pressure_pa, basis, water_vapor_pressure_pa)
    density = _number(density_mg_m3, "density_mg_m3")
    if density < 0:
        raise Co2GasHold("INPUT_HOLD: negative CO2 density")
    if density == 0:
        return 0.0
    try:
        ppm = _result(density * GAS_CONSTANT * temperature / (CO2_MOLAR_MASS * pressure), True)
    except (OverflowError, ZeroDivisionError) as exc:
        raise Co2GasHold("NUMERIC_HOLD: unrepresentable concentration arithmetic") from exc
    if ppm > 1e6:
        raise Co2GasHold("INPUT_HOLD: CO2 mole fraction exceeds one")
    return ppm


def ppm_to_density(*, ppm, temperature_c, pressure_pa, basis,
                   water_vapor_pressure_pa=None):
    """Convert explicit wet/dry mole ppm to mg_CO2/m3 at the supplied T/P."""
    temperature, pressure = _environment(temperature_c, pressure_pa, basis, water_vapor_pressure_pa)
    concentration = _number(ppm, "ppm")
    if not 0 <= concentration <= 1e6:
        raise Co2GasHold("INPUT_HOLD: CO2 mole fraction must be between zero and one")
    if concentration == 0:
        return 0.0
    try:
        return _result(concentration * CO2_MOLAR_MASS * pressure / (GAS_CONSTANT * temperature), True)
    except (OverflowError, ZeroDivisionError) as exc:
        raise Co2GasHold("NUMERIC_HOLD: unrepresentable concentration arithmetic") from exc
