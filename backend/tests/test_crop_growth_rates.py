from copy import deepcopy
from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
from math import fsum, isfinite, ulp
from pathlib import Path

import pytest

from app.crop_growth_rates import CropRateHold, ReferenceParameters, calculate_rates


FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
PROFILE_BYTES = (FIXTURES / "crop-growth-reference-parameters-v1.json").read_bytes()
REFERENCE = json.loads((FIXTURES / "crop-growth-reference-cases-v1.json").read_bytes())


def inputs():
    return deepcopy(REFERENCE["cases"][0])


def run(case, profile=None):
    return calculate_rates(
        state=case["state"], forcing=case["forcing"], removals=case["removals"],
        profile=ReferenceParameters(PROFILE_BYTES) if profile is None else profile,
    )


@pytest.mark.parametrize("case", REFERENCE["cases"], ids=lambda c: c["case_id"])
def test_independent_decimal_equation_reference_and_carbon_balance(case):
    result = run(case)
    assert result["scope"] == "software_research_only"
    assert result["profile_sha256"] == REFERENCE["profile_sha256"]
    for field in ("lai", "photosynthesis", "growth_respiration"):
        assert result[field]["value"] == pytest.approx(
            float(case["expected"][field]), rel=5e-12, abs=5e-14)
    for group in ("allocation", "maintenance_respiration", "derivatives"):
        for field, expected in case["expected"][group].items():
            assert result[group][field]["value"] == pytest.approx(
                float(expected), rel=5e-12, abs=5e-14)
    organs = ("leaf", "stem_root", "fruit")
    external = fsum([
        result["photosynthesis"]["value"], -result["growth_respiration"]["value"],
        *[-result["maintenance_respiration"][k]["value"] for k in organs],
        *[-case["removals"]["values"][k]["value"] for k in organs],
    ])
    stored = fsum(result["derivatives"][k]["value"] for k in ("buffer", *organs))
    budget = 16 * ulp(max(abs(external), abs(stored), 1.0))
    assert abs(stored - external) <= budget
    assert abs(result["carbon_residual"]["value"]) <= budget
    assert result["photosynthesis"]["unit"] == "mg_CH2O/m2_floor/s"
    assert result["lai"]["unit"] == "m2_leaf/m2_floor"
    assert result["derivatives"]["temperature_sum"]["unit"] == "degC_day/s"


def test_profile_is_pinned_immutable_and_not_approved():
    profile = ReferenceParameters(PROFILE_BYTES)
    assert profile.sha256 == sha256(PROFILE_BYTES).hexdigest()
    with pytest.raises(CropRateHold, match="PROFILE_HOLD"):
        ReferenceParameters(PROFILE_BYTES + b" ")
    changed = json.loads(PROFILE_BYTES)
    changed["parameters"]["alpha"]["value"] = 0.4
    with pytest.raises(CropRateHold, match="PROFILE_HOLD"):
        ReferenceParameters(json.dumps(changed).encode())
    with pytest.raises(CropRateHold, match="PROFILE_HOLD"):
        ReferenceParameters("not bytes")
    with pytest.raises(TypeError):
        profile.values["alpha"] = 0.4
    with pytest.raises(FrozenInstanceError):
        profile.raw_bytes = b"changed"


def test_replay_hash_binds_units_provenance_and_explicit_removals():
    case = inputs()
    original = deepcopy(case)
    first = run(case)
    assert case == original
    assert run(deepcopy(case)) == first
    case["forcing"]["input_id"] += "-new-vintage"
    assert run(case)["input_sha256"] != first["input_sha256"]
    case = inputs()
    case["removals"]["values"]["fruit"]["value"] = 0.01
    removed = run(case)
    assert removed["input_sha256"] != first["input_sha256"]
    assert removed["photosynthesis"] == first["photosynthesis"]
    assert removed["derivatives"]["fruit"]["value"] == pytest.approx(
        first["derivatives"]["fruit"]["value"] - 0.01)


@pytest.mark.parametrize("temperature", [10, 17, 20, 23, 34])
def test_darkness_has_zero_photosynthesis_even_without_leaves(temperature):
    case = inputs()
    case["forcing"]["values"]["canopy_temperature"]["value"] = temperature
    case["forcing"]["values"]["par_above_canopy"]["value"] = 0
    case["state"]["values"]["leaf"]["value"] = 0
    result = run(case)
    assert result["photosynthesis"]["value"] == 0
    assert result["diagnostics"]["compensation_point_ppm"] is None
    assert all(isfinite(q["value"]) for q in result["derivatives"].values())


def test_daylight_zero_leaf_limit_and_weak_light_stability():
    case = inputs()
    values = []
    for leaf in (1, 0.001, 0.000001, 0):
        case["state"]["values"]["leaf"]["value"] = leaf
        values.append(run(case)["photosynthesis"]["value"])
    assert values[0] > values[1] > values[2] > values[3] == 0
    assert values[1] / values[0] == pytest.approx(0.001, rel=1e-5)
    case = inputs()
    case["forcing"]["values"]["par_above_canopy"]["value"] = 1e-15
    weak = run(case)["photosynthesis"]["value"]
    assert weak > 0
    case["forcing"]["values"]["par_above_canopy"]["value"] = 1e-14
    assert run(case)["photosynthesis"]["value"] / weak == pytest.approx(10)


@pytest.mark.parametrize("leaf,temperature", [(0, 23), (0.001, 17), (0.001, 23)])
def test_compensation_point_singular_or_nonphysical_domain_is_held(leaf, temperature):
    case = inputs()
    case["state"]["values"]["leaf"]["value"] = leaf
    case["forcing"]["values"]["canopy_temperature"]["value"] = temperature
    with pytest.raises(CropRateHold, match="COMPENSATION_POINT_HOLD"):
        run(case)


def test_depleted_buffer_is_held_instead_of_clipped():
    case = inputs()
    case["state"]["values"]["buffer"]["value"] = 0
    case["forcing"]["values"]["par_above_canopy"]["value"] = 0
    with pytest.raises(CropRateHold, match="DEPLETED_STATE_HOLD"):
        run(case)


@pytest.mark.parametrize("block,field", [
    ("state", "buffer"), ("state", "leaf"), ("state", "stem_root"), ("state", "fruit"),
    ("state", "temperature_sum"), ("state", "temperature_filtered_24h"),
    ("forcing", "canopy_temperature"), ("forcing", "par_above_canopy"), ("forcing", "co2"),
    ("removals", "leaf"), ("removals", "stem_root"), ("removals", "fruit"),
])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1, True, "1"])
def test_nonfinite_negative_wrong_type_is_rejected(block, field, bad):
    case = inputs()
    case[block]["values"][field]["value"] = bad
    with pytest.raises(CropRateHold):
        run(case)


@pytest.mark.parametrize("block", ["state", "forcing", "removals"])
def test_units_closed_fields_and_origin_cannot_be_silently_replaced(block):
    case = inputs()
    field = next(iter(case[block]["values"]))
    case[block]["values"][field]["unit"] = "g/m2"
    with pytest.raises(CropRateHold, match="UNIT_HOLD"):
        run(case)
    case = inputs()
    case[block]["values"]["invented"] = {"value": 0, "unit": "1"}
    with pytest.raises(CropRateHold, match="INPUT_HOLD"):
        run(case)
    case = inputs()
    del case[block]["values"][field]
    with pytest.raises(CropRateHold, match="INPUT_HOLD"):
        run(case)
    case = inputs()
    case[block]["origin"] = "approved"
    with pytest.raises(CropRateHold, match="INPUT_HOLD"):
        run(case)


@pytest.mark.parametrize("block,field,value", [
    ("forcing", "co2", 0), ("forcing", "co2", 1),
    ("forcing", "canopy_temperature", 9.9), ("forcing", "canopy_temperature", 34.1),
    ("state", "temperature_filtered_24h", 16.9), ("state", "temperature_filtered_24h", 23.1),
    ("state", "buffer", 10 ** 500),
])
def test_scope_boundaries_and_unrepresentable_numbers_are_rejected(block, field, value):
    case = inputs()
    case[block]["values"][field]["value"] = value
    with pytest.raises(CropRateHold):
        run(case)
