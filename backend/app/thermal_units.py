"""Versioned thermal-v1 SI checks and the registered NWS transcription."""

from datetime import datetime, timezone
from hashlib import sha256
from math import isfinite
import re


LAW_TEXT = (
    "p_sat_hPa=6.11*10^(7.5*t_C/(237.3+t_C)); "
    "t_C=T_K-273.15; p_sat_Pa=100*p_sat_hPa"
)
LAW_SHA256 = "ea8d52e0bb02e36afb796b245f7df5dd3ce267fb7f0ea5c57dfa9b4e491e6b4b"
LAW_BASIS = "nws-epz-vapor-pressure-pdf"
SI_BASIS = "bipm-si-unit-conversions"
LAW_VERSION = "nws-formula-transcription-v1"
SI_VERSION = "bipm-si-conversion-transcription-v1"
COEFFICIENTS = (
    ("pressure_coefficient", 6.11, "hPa", LAW_BASIS, LAW_VERSION),
    ("exponent_factor", 7.5, "1", LAW_BASIS, LAW_VERSION),
    ("denominator_offset", 237.3, "°C_interval", LAW_BASIS, LAW_VERSION),
    ("exponential_base", 10, "1", LAW_BASIS, LAW_VERSION),
    ("kelvin_to_celsius_offset", 273.15, "K", SI_BASIS, SI_VERSION),
    ("hpa_to_pa_factor", 100, "Pa/hPa", SI_BASIS, SI_VERSION),
)
UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def utc(text):
    if not isinstance(text, str) or not UTC_PATTERN.fullmatch(text):
        raise ValueError("TIMESTAMP_HOLD: calendar-valid UTC timestamp required")
    try:
        result = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("TIMESTAMP_HOLD: invalid UTC date") from exc
    if result.tzinfo != timezone.utc:
        raise ValueError("TIMESTAMP_HOLD: UTC required")
    return result


def sourced(record, unit, *, lower=None, upper=None, boolean=False):
    if not isinstance(record, dict) or record.get("unit") != unit:
        raise ValueError(f"UNIT_HOLD: expected {unit}")
    if not record.get("basis_ref") or not record.get("version") or record.get("origin") not in (
        "assumed", "measured", "literature"
    ):
        raise ValueError("INPUT_HOLD: missing sourced provenance")
    value = record.get("value")
    if boolean:
        if type(value) is not bool or record["origin"] not in ("assumed", "measured"):
            raise ValueError("INPUT_HOLD: invalid sourced boolean")
        return value
    if type(value) not in (int, float) or not isfinite(value):
        raise ValueError("INPUT_HOLD: missing or nonfinite value")
    if lower is not None and value < lower or upper is not None and value > upper:
        raise ValueError("INPUT_HOLD: outside declared domain")
    return float(value)


def quantity(value, unit):
    if not isfinite(value):
        raise ValueError("INPUT_HOLD: nonfinite trace value")
    return {"value": value, "unit": unit}


def saturation_pressure_pa(temperature_kelvin, rule):
    if rule.get("formula_id") != LAW_BASIS or rule.get("formula_ref") != LAW_BASIS or rule.get("formula_version") != LAW_VERSION or rule.get("formula_sha256") != LAW_SHA256:
        raise ValueError("LAW_HOLD: unregistered saturation rule")
    coefficients = rule.get("coefficients")
    if not isinstance(coefficients, list) or len(coefficients) != len(COEFFICIENTS):
        raise ValueError("LAW_HOLD: missing coefficients")
    values = []
    for row, (name, expected, unit, basis, version) in zip(coefficients, COEFFICIENTS):
        if row.get("name") != name or row.get("unit") != unit or row.get("basis_ref") != basis or row.get("version") != version or row.get("origin") != "literature" or row.get("value") != expected:
            raise ValueError("LAW_HOLD: unsupported coefficient")
        values.append(float(expected))
    minimum = sourced(rule.get("temperature_min"), "K")
    maximum = sourced(rule.get("temperature_max"), "K")
    if not minimum <= temperature_kelvin <= maximum:
        raise ValueError("LAW_HOLD: temperature outside project test domain")
    coefficient, factor, offset, base, kelvin_offset, hpa_factor = values
    celsius = temperature_kelvin - kelvin_offset
    denominator = offset + celsius
    if denominator <= 0:
        raise ValueError("LAW_HOLD: invalid law denominator")
    pressure = hpa_factor * coefficient * base ** (factor * celsius / denominator)
    if not isfinite(pressure) or pressure <= 0:
        raise ValueError("LAW_HOLD: invalid saturation pressure")
    return pressure


def validate_law_source(source):
    if source.get("basis_ref") != LAW_BASIS or source.get("formula_text") != LAW_TEXT or sha256(LAW_TEXT.encode()).hexdigest() != LAW_SHA256:
        raise ValueError("LAW_HOLD: source transcription differs")
    if source.get("raw_pdf_sha256") != "74e5a28ee21bde51d5ffad17f2418dc5c827c338d1bc11a09cbd7c623b87b621":
        raise ValueError("LAW_HOLD: source PDF pin differs")
