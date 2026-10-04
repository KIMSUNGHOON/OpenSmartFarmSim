from copy import deepcopy
from decimal import Decimal, localcontext
import json
from math import isfinite
from pathlib import Path

import pytest

from app.crop_growth_rates import CropRateHold, ReferenceParameters, calculate_rates


FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
PROFILE = ReferenceParameters((FIXTURES / "crop-growth-reference-parameters-v1.json").read_bytes())
BASE = json.loads((FIXTURES / "crop-growth-reference-cases-v1.json").read_bytes())["cases"][0]


def case_at(temperature, co2, lai, par=200):
    case = deepcopy(BASE)
    case["state"]["values"]["leaf"]["value"] = lai / PROFILE.values["sla"]
    for field, value in (("canopy_temperature", temperature), ("co2", co2),
                         ("par_above_canopy", par)):
        case["forcing"]["values"][field]["value"] = value
    return case


def run(case):
    return calculate_rates(state=case["state"], forcing=case["forcing"],
                           removals=case["removals"], profile=PROFILE)


def decimal_supported(case):
    # Independent multiplied inequalities; no product Gamma or flux is used.
    with localcontext() as context:
        context.prec = 60
        parameter = lambda key: Decimal(str(PROFILE.values[key]))
        lai = Decimal(str(case["state"]["values"]["leaf"]["value"])) * parameter("sla")
        delta = Decimal(str(case["forcing"]["values"]["canopy_temperature"]["value"])) - parameter("compensation_pivot_c")
        a = parameter("etaCo2AirStom") * Decimal(str(case["forcing"]["values"]["co2"]["value"])) / parameter("cGamma") - parameter("compensation_pivot_c")
        return (lai > 0 and parameter("compensation_pivot_c") * lai + delta >= 0
                and a * lai - delta >= 0)


@pytest.mark.parametrize("temperature,co2,lai,accepted", [
    (10, 400, 0.49, False), (10, 400, 0.51, True),
    (17, 400, 0.149, False), (17, 400, 0.151, True),
    (20, 400, 1e-6, True),
    (23, 400, 0.02, False), (23, 400, 0.023, True),
    (34, 400, 0.1, False), (34, 400, 0.11, True),
    (17, 40, 0.14, False), (17, 40, 0.3, True), (17, 40, 0.72, False),
    (10, 40, 1, True), (20, 40, 1, False), (23, 40, 1, False),
])
def test_source_domain_matches_independent_inequalities(temperature, co2, lai, accepted):
    case = case_at(temperature, co2, lai)
    assert decimal_supported(case) is accepted
    if accepted:
        result = run(case)
        assert result["scope"] == "software_research_only"
        assert result["photosynthesis"]["value"] >= 0
        assert all(isfinite(q["value"]) for q in result["derivatives"].values())
    else:
        with pytest.raises(CropRateHold, match="COMPENSATION_POINT_HOLD"):
            run(case)


@pytest.mark.parametrize("temperature,co2,boundary,lower", [
    (10, 400, "0.5", True), (17, 400, "0.15", True),
    (23, 400, "0.0217948717948717948717948717948717948717948717948717948717948", True),
    (34, 400, "0.101709401709401709401709401709401709401709401709401709401709", True),
    (17, 40, "0.708333333333333333333333333333333333333333333333333333333341", False),
])
def test_both_sides_of_independently_calculated_boundaries(temperature, co2, boundary, lower):
    for displacement in (Decimal("-1e-9"), Decimal("1e-9")):
        case = case_at(temperature, co2, float(Decimal(boundary) + displacement))
        accepted = displacement > 0 if lower else displacement < 0
        assert decimal_supported(case) is accepted
        if accepted:
            assert run(case)["photosynthesis"]["value"] > 0
        else:
            with pytest.raises(CropRateHold, match="COMPENSATION_POINT_HOLD"):
                run(case)


@pytest.mark.parametrize("temperature", [10, 17, 20, 23, 34])
def test_lai_one_matches_original_leaf_compensation_point(temperature):
    result = run(case_at(temperature, 400, 1))
    assert result["diagnostics"]["compensation_point_ppm"] == pytest.approx(
        float(Decimal("1.7") * Decimal(temperature)), rel=1e-14)


@pytest.mark.parametrize("temperature", [10, 17, 20, 23, 34])
def test_zero_leaf_day_and_night_limits_preserve_explicit_domain(temperature):
    night = run(case_at(temperature, 400, 0, par=0))
    assert night["photosynthesis"]["value"] == 0
    assert night["diagnostics"]["compensation_point_ppm"] is None
    if temperature == 20:
        day = run(case_at(temperature, 400, 0))
        assert day["photosynthesis"]["value"] == 0
        assert day["diagnostics"]["compensation_point_ppm"] == pytest.approx(34)
    else:
        with pytest.raises(CropRateHold, match="COMPENSATION_POINT_HOLD"):
            run(case_at(temperature, 400, 0))


def test_generic_initial_leaf_state_is_held_at_cool_day_without_invented_lai():
    case = deepcopy(BASE)
    assert case["state"]["values"]["leaf"]["value"] == 4368
    assert run(case)["lai"]["value"] == pytest.approx(0.1161888)
    case["forcing"]["values"]["canopy_temperature"]["value"] = 17
    assert decimal_supported(case) is False
    with pytest.raises(CropRateHold, match="COMPENSATION_POINT_HOLD"):
        run(case)
    assert case["state"]["values"]["leaf"]["value"] == 4368


def test_zero_a_floating_boundary_has_cool_interval_zero_at_pivot_and_warm_hold():
    co2 = PROFILE.values["cGamma"] * PROFILE.values["compensation_pivot_c"] / PROFILE.values["etaCo2AirStom"]
    assert PROFILE.values["etaCo2AirStom"] * co2 == 34
    cool = run(case_at(17, co2, 0.16))
    assert cool["diagnostics"]["compensation_point_ppm"] == pytest.approx(2.125)
    assert cool["photosynthesis"]["value"] > 0
    assert run(case_at(20, co2, 0.16))["photosynthesis"]["value"] == 0
    with pytest.raises(CropRateHold, match="COMPENSATION_POINT_HOLD"):
        run(case_at(23, co2, 0.16))
