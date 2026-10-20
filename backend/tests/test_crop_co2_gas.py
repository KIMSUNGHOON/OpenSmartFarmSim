"""Independent mole-count references for the explicit CO2 concentration basis."""
from decimal import Decimal, localcontext
from hashlib import sha256
from importlib import import_module
import json
from math import inf, nan, nextafter
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def gas():
    return import_module("app.crop_co2_gas")


def mole_count_reference(value, temperature, pressure, basis, vapor, *, inverse=False):
    with localcontext() as context:
        context.prec = 80
        volume = Decimal("1.7")
        temperature_k = Decimal(temperature) + Decimal("273.15")
        total_moles = Decimal(pressure) * volume / (Decimal("8.3144598") * temperature_k)
        if basis == "dry":
            water_moles = Decimal(vapor) * volume / (Decimal("8.3144598") * temperature_k)
            total_moles -= water_moles
        if inverse:
            co2_moles = Decimal(value) / Decimal("1e6") * total_moles
            return float(co2_moles * Decimal("44.01") * Decimal("1000") / volume)
        mass_grams = Decimal(value) * volume / Decimal("1000")
        co2_moles = mass_grams / Decimal("44.01")
        return float(co2_moles / total_moles * Decimal("1e6"))


@pytest.mark.parametrize("temperature,pressure,basis,vapor", [
    (25, 101325, "wet", None), (0, 85000, "wet", 0),
    (40, 110000, "wet", 5000), (25, 101325, "dry", 3000),
    (0, 85000, "dry", 0), (40, 110000, "dry", 5000),
    (25, 101325, "dry", nextafter(101325.0, 0)),
])
def test_independent_mole_counts_in_both_directions(gas, temperature, pressure, basis, vapor):
    args = dict(temperature_c=temperature, pressure_pa=pressure, basis=basis,
                water_vapor_pressure_pa=vapor)
    # The near-water-only case uses a correspondingly small CO2 density.
    density = 1e-14 if vapor is not None and vapor > pressure - 1 else 725
    actual = gas.density_to_ppm(density_mg_m3=density, **args)
    assert actual == pytest.approx(
        mole_count_reference(density, temperature, pressure, basis, vapor), rel=3e-15, abs=0)
    actual_density = gas.ppm_to_density(ppm=420, **args)
    assert actual_density == pytest.approx(
        mole_count_reference(420, temperature, pressure, basis, vapor, inverse=True), rel=3e-15, abs=0)


def test_mass_density_is_constant_when_only_temperature_or_pressure_changes(gas):
    args = dict(density_mg_m3=725, temperature_c=25, pressure_pa=101325, basis="wet")
    base = gas.density_to_ppm(**args)
    warm = gas.density_to_ppm(**{**args, "temperature_c": 40})
    high_pressure = gas.density_to_ppm(**{**args, "pressure_pa": 110000})
    assert warm / base == pytest.approx(313.15 / 298.15, rel=3e-15)
    assert high_pressure / base == pytest.approx(101325 / 110000, rel=3e-15)
    for temperature, pressure, ppm in ((25, 101325, base), (40, 101325, warm), (25, 110000, high_pressure)):
        assert gas.ppm_to_density(ppm=ppm, temperature_c=temperature,
                                  pressure_pa=pressure, basis="wet") == pytest.approx(725, rel=3e-15)


def test_dry_air_requires_water_and_corrects_only_its_denominator(gas):
    args = dict(density_mg_m3=725, temperature_c=25, pressure_pa=101325)
    wet = gas.density_to_ppm(**args, basis="wet")
    wet_with_water = gas.density_to_ppm(**args, basis="wet", water_vapor_pressure_pa=3000)
    dry = gas.density_to_ppm(**args, basis="dry", water_vapor_pressure_pa=3000)
    assert wet == wet_with_water
    assert dry / wet == pytest.approx(101325 / 98325, rel=3e-15)
    with pytest.raises(gas.Co2GasHold):
        gas.density_to_ppm(**args, basis="dry")


@pytest.mark.parametrize("basis,vapor", [("wet", None), ("dry", 3000)])
def test_zero_is_exact_after_domain_validation(gas, basis, vapor):
    args = dict(temperature_c=25, pressure_pa=101325, basis=basis, water_vapor_pressure_pa=vapor)
    assert gas.density_to_ppm(density_mg_m3=0, **args) == 0.0
    assert gas.ppm_to_density(ppm=0, **args) == 0.0


@pytest.mark.parametrize("update", [
    {"temperature_c": -273.15}, {"temperature_c": -300}, {"pressure_pa": 0},
    {"pressure_pa": -1}, {"basis": "unknown"}, {"basis": None},
    {"water_vapor_pressure_pa": -1}, {"water_vapor_pressure_pa": 101325},
    {"water_vapor_pressure_pa": inf}, {"temperature_c": True},
    {"temperature_c": nan}, {"pressure_pa": "101325"}, {"pressure_pa": 10**1000},
])
def test_invalid_environment_is_held_including_zero_concentration(gas, update):
    args = {**dict(temperature_c=25, pressure_pa=101325, basis="wet"), **update}
    for function, key in ((gas.density_to_ppm, "density_mg_m3"), (gas.ppm_to_density, "ppm")):
        with pytest.raises(gas.Co2GasHold):
            function(**{key: 0}, **args)


@pytest.mark.parametrize("value", [-1, True, "420", None, Decimal("420"), nan, inf, -inf])
def test_invalid_concentration_is_held(gas, value):
    args = dict(temperature_c=25, pressure_pa=101325, basis="wet")
    for function, key in ((gas.density_to_ppm, "density_mg_m3"), (gas.ppm_to_density, "ppm")):
        with pytest.raises(gas.Co2GasHold):
            function(**{key: value}, **args)


def test_impossible_mole_fraction_and_unrepresentable_arithmetic_are_held(gas):
    with pytest.raises(gas.Co2GasHold):
        gas.ppm_to_density(ppm=nextafter(1e6, inf), temperature_c=25, pressure_pa=101325, basis="wet")
    with pytest.raises(gas.Co2GasHold):
        gas.density_to_ppm(density_mg_m3=1e9, temperature_c=25, pressure_pa=101325, basis="wet")
    for density, temperature, pressure in ((1e308, 1e308, 101325), (5e-324, 25, 1e308), (1, 25, 5e-324)):
        with pytest.raises(gas.Co2GasHold):
            gas.density_to_ppm(density_mg_m3=density, temperature_c=temperature, pressure_pa=pressure, basis="wet")
    with pytest.raises(gas.Co2GasHold):
        gas.ppm_to_density(ppm=1, temperature_c=25, pressure_pa=5e-324, basis="wet")


def test_no_implicit_pressure_or_basis(gas):
    with pytest.raises(TypeError):
        gas.density_to_ppm(density_mg_m3=725, temperature_c=25, basis="wet")
    with pytest.raises(TypeError):
        gas.ppm_to_density(ppm=420, temperature_c=25, pressure_pa=101325)


def test_parameter_and_model_identity_match_reviewed_source(gas):
    root = Path(__file__).resolve().parents[2]
    register = json.loads((root / "research/crop-co2-stomatal-source-register-20261021.json").read_text())
    policy = register["interpretations"]["P01"]
    assert gas.GAS_CONSTANT == float(policy["R_Pa_m3_per_mol_K"])
    assert gas.CO2_MOLAR_MASS == float(policy["M_CO2_kg_per_mol"])
    assert gas.SOURCE_SHA256 == next(s["raw_sha256"] for s in register["sources"] if s["source_id"] == "chapter8.json")
    assert gas.VERSION == "greenlight-co2-ideal-gas-explicit-pressure-v1"
    assert gas.CODE_SHA256 == sha256(Path(gas.__file__).read_bytes()).hexdigest()
